# -*- coding: utf-8 -*-
"""IA local opcional (entrega C): catálogo, download verificado, servidor local e pedidos canceláveis.

- Nada é baixado nem enviado sem o usuário pedir. O download vem só dos endereços fixos do catálogo
  (dados/ia.json), confere o SHA-256 e pode ser cancelado; o texto dos documentos nunca escolhe endereço nenhum.
- O motor de execução é o llama.cpp (llama-server, licença MIT), rodando como processo separado, preso a
  127.0.0.1: sem acesso de fora do computador e sem enviar nada para a internet.
- Os pedidos rodam numa thread de trabalho que só recebe texto (regra da 0.3.0: nenhuma thread Python toca no
  documento); o resultado volta para a thread principal.
SPDX-License-Identifier: MPL-2.0
"""
import hashlib
import http.client
import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
import urllib.request
import zipfile

DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'dados')
registrar = print


def catalogo():
    with open(os.path.join(DADOS, 'ia.json'), encoding='utf-8') as f:
        return json.load(f)


def pasta_padrao():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'AYEscreva', 'IA')


def espaco_livre(pasta):
    alvo = pasta
    while not os.path.exists(alvo):
        alvo = os.path.dirname(alvo)
    return shutil.disk_usage(alvo).free


class Cancelado(Exception):
    pass


def baixar(url, destino, sha256, tamanho=None, progresso=None, cancelar=None, tempo_limite=60):
    """Baixa para destino + '.parcial', confere o SHA-256 e só então dá o nome final. progresso(feito, total)."""
    if not url.startswith('https://'):
        raise ValueError('só endereços https do catálogo')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    parcial = destino + '.parcial'
    h = hashlib.sha256()
    req = urllib.request.Request(url, headers={'User-Agent': 'AY-ESCREVA'})
    try:
        with urllib.request.urlopen(req, timeout=tempo_limite) as r, open(parcial, 'wb') as f:
            total = int(r.headers.get('Content-Length') or tamanho or 0)
            feito = 0
            while True:
                if cancelar is not None and cancelar.is_set():
                    raise Cancelado()
                bloco = r.read(1 << 20)
                if not bloco:
                    break
                f.write(bloco)
                h.update(bloco)
                feito += len(bloco)
                if progresso:
                    progresso(feito, total)
        if h.hexdigest().lower() != sha256.lower():
            raise ValueError(f'SHA-256 não confere: {h.hexdigest()}')
        os.replace(parcial, destino)
        return destino
    except BaseException:
        try:
            os.remove(parcial)
        except OSError:
            pass
        raise


def extrair_motor(zip_caminho, pasta, arquivos):
    """Extrai só os arquivos listados no catálogo, sem pastas (protege contra caminhos maliciosos no zip)."""
    os.makedirs(pasta, exist_ok=True)
    with zipfile.ZipFile(zip_caminho) as z:
        nomes = {os.path.basename(n): n for n in z.namelist() if not n.endswith('/')}
        for a in arquivos:
            if a not in nomes:
                raise ValueError(f'{a} não está no pacote do motor')
            with z.open(nomes[a]) as o, open(os.path.join(pasta, a), 'wb') as d:
                shutil.copyfileobj(o, d)


def porta_livre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _amarrar_ao_aplicativo(proc):
    """Windows: o servidor entra num "job" que é encerrado com o AY; assim ele não fica rodando se o AY fechar ou cair."""
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.windll.kernel32

        class BASIC(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64),
                        ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
                        ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wintypes.DWORD),
                        ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ('R', 'W', 'O', 'RT', 'WT', 'OT')]

        class EXT(ctypes.Structure):
            _fields_ = [('Basic', BASIC), ('Io', IO), ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                        ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        job = k32.CreateJobObjectW(None, None)
        info = EXT()
        info.Basic.LimitFlags = 0x2000          # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
        h = k32.OpenProcess(0x0001 | 0x0100, False, proc.pid)      # PROCESS_TERMINATE | PROCESS_SET_QUOTA
        k32.AssignProcessToJobObject(job, h)
        k32.CloseHandle(h)
        return job                                # o handle fica aberto até o AY terminar
    except Exception as e:
        registrar(f'IA: não foi possível amarrar o servidor ao aplicativo: {e}')
        return None


class Servidor:
    """llama-server num processo separado, só em 127.0.0.1.

    Fechado para o resto do computador: chave aleatória a cada início (sem ela o servidor recusa os pedidos; um site
    aberto no navegador não a conhece), sem a lista de "slots" (que mostraria o texto em análise), sem interface web,
    CORS só para localhost e modo offline (o motor não baixa nada)."""

    def __init__(self, exe, modelo, contexto=4096, threads=None, extra=()):
        self.exe, self.modelo, self.contexto = os.path.abspath(exe), os.path.abspath(modelo), contexto
        self.threads = threads or max(1, (os.cpu_count() or 2) - 1)
        self.extra = list(extra)
        self.proc = None
        self.porta = None
        self.chave = None

    def iniciar(self, limite=300):
        if self.proc is not None and self.proc.poll() is None:
            return
        self.porta = porta_livre()
        self.chave = secrets.token_urlsafe(24)
        args = [self.exe, '-m', self.modelo, '--host', '127.0.0.1', '--port', str(self.porta), '-c', str(self.contexto),
                '-t', str(self.threads), '-ngl', '0', '--no-ui', '--no-slots', '--offline', '--cors-origins', 'localhost',
                '--no-cors-credentials', '--api-key', self.chave,
                # sem "raciocínio" oculto: para editar texto ele só atrasa (Gemma 4 gastava ~500 palavras internas por frase)
                '--reasoning', 'off'] + self.extra
        # prioridade abaixo do normal: quando o editor e a IA disputam o processador, a digitação ganha
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0)
        self.log = open(os.path.join(os.path.dirname(self.modelo), 'servidor.log'), 'w', encoding='utf-8', errors='replace')
        self.proc = subprocess.Popen(args, stdout=self.log, stderr=subprocess.STDOUT, creationflags=flags)
        self.job = _amarrar_ao_aplicativo(self.proc)
        fim = time.time() + limite
        while time.time() < fim:
            if self.proc.poll() is not None:
                raise RuntimeError(f'o motor de IA terminou ao iniciar (código {self.proc.returncode}); veja servidor.log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{self.porta}/health', timeout=2) as r:
                    if r.status == 200:
                        return
            except Exception:
                pass
            time.sleep(0.5)
        raise RuntimeError('o motor de IA não ficou pronto a tempo')

    def ativo(self):
        return self.proc is not None and self.proc.poll() is None

    def parar(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        self.proc = None
        try:
            self.log.close()
        except Exception:
            pass

    def pid(self):
        return self.proc.pid if self.proc is not None else None


class Pedido:
    """Um pedido ao servidor, numa thread de trabalho, com cancelamento. Só recebe e devolve texto."""

    def __init__(self, servidor, mensagens, max_tokens=1024, temperatura=0.2, sem_pensar=True, ao_terminar=None, ao_avancar=None):
        self.servidor, self.mensagens = servidor, mensagens
        self.max_tokens, self.temperatura, self.sem_pensar = max_tokens, temperatura, sem_pensar
        self.ao_terminar, self.ao_avancar = ao_terminar, ao_avancar
        self.cancelado = threading.Event()
        self.texto = ''
        self.erro = None
        self.medidas = {}
        self.thread = None

    def iniciar(self):
        self.thread = threading.Thread(target=self._rodar, daemon=True)
        self.thread.start()
        return self

    def cancelar(self):
        """Pode ser chamado de qualquer thread. Fecha a conexão na hora (também durante a leitura do trecho, antes
        da primeira palavra); o servidor percebe a conexão fechada e para de gerar."""
        self.cancelado.set()
        conexao = self._conexao
        if conexao is not None and conexao.sock is not None:
            try:
                conexao.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    _conexao = None

    def _rodar(self):
        t0 = time.time()
        corpo = {'messages': self.mensagens, 'max_tokens': self.max_tokens, 'temperature': self.temperatura,
                 'stream': True, 'cache_prompt': True}
        if self.sem_pensar:
            corpo['chat_template_kwargs'] = {'enable_thinking': False}
        partes, primeiro, n = [], None, 0
        try:
            if self.cancelado.is_set():
                raise Cancelado()
            self._conexao = http.client.HTTPConnection('127.0.0.1', self.servidor.porta, timeout=600)
            self._conexao.request('POST', '/v1/chat/completions', body=json.dumps(corpo).encode('utf-8'),
                                  headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.servidor.chave}'})
            r = self._conexao.getresponse()
            if r.status != 200:
                raise RuntimeError(f'resposta {r.status} do servidor local: {r.read(300).decode("utf-8", "replace")}')
            with r:
                for linha in r:
                    if self.cancelado.is_set():
                        break          # fechar a conexão faz o servidor parar a geração
                    linha = linha.decode('utf-8', 'replace').strip()
                    if not linha.startswith('data:'):
                        continue
                    dado = linha[5:].strip()
                    if dado == '[DONE]':
                        break
                    ev = json.loads(dado)
                    for esc in ev.get('choices', []):
                        pedaco = (esc.get('delta') or {}).get('content') or ''
                        if pedaco:
                            if primeiro is None:
                                primeiro = time.time() - t0
                            partes.append(pedaco)
                            n += 1
                            if self.ao_avancar:
                                self.ao_avancar(''.join(partes))
                    if 'timings' in ev:
                        self.medidas['servidor'] = ev['timings']
        except Exception as e:
            if not self.cancelado.is_set():
                self.erro = f'{type(e).__name__}: {e}'
        finally:
            if self._conexao is not None:
                self._conexao.close()
        self.texto = ''.join(partes)
        total = time.time() - t0
        self.medidas.update(segundos=round(total, 2), primeiro_token_s=round(primeiro, 2) if primeiro else None, pedacos=n,
                            cancelado=self.cancelado.is_set())
        if self.ao_terminar:
            self.ao_terminar(self)
