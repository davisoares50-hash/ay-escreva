# -*- coding: utf-8 -*-
"""Verificar atualizações (entrega E): consulta só quando a pessoa pede, com confirmação antes de baixar e de instalar.

Segurança (não é um atualizador que baixa e executa qualquer endereço):
  - o arquivo de versões vem só de um endereço fixo do site oficial (MANIFESTO), por https;
  - ele precisa estar assinado (Ed25519) pela chave do projeto, cuja parte pública está aqui (CHAVE_PUBLICA); a chave
    privada fica fora do repositório, com quem publica;
  - o instalador só pode vir das versões publicadas do projeto no GitHub (PREFIXO), com nome, tamanho e SHA-256 do
    arquivo de versões assinado; o SHA-256 é conferido antes de abrir o instalador;
  - nada é enviado além do pedido do arquivo (nenhum documento, nenhum dado pessoal).
Documentos e preferências: o instalador atualiza por cima, sem mexer em documentos nem no perfil (testado); antes de
instalar, o AY exige que os documentos com alterações sejam salvos ou fechados, e só então fecha e instala.
SPDX-License-Identifier: MPL-2.0
"""
import json
import os
import re
import subprocess
import threading
import time
import traceback
import urllib.error
import urllib.request

import ay_ed25519

MANIFESTO = 'https://davisoares50-hash.github.io/ay-escreva/atualizacoes.json'
PREFIXO = 'https://github.com/davisoares50-hash/ay-escreva/releases/download/'
CHAVE_PUBLICA = bytes.fromhex('ad50bd7986ca377c9335f9846293bcf56c0ac889e6e3bbfaf1b95f6e3f7d8a10')
CANAIS = {'testes': 'Versões de testes', 'estavel': 'Versões estáveis'}
LIMITE_MANIFESTO = 64 * 1024
registrar = print


class SemInformacao(Exception):
    """Não foi possível consultar (sem conexão, arquivo ainda não publicado): nada muda."""


class Recusado(Exception):
    """O arquivo de versões ou o instalador não passou nas conferências de segurança: nada é baixado nem instalado."""


def numeros(versao):
    if not re.fullmatch(r'\d+\.\d+\.\d+', versao or ''):
        raise ValueError(f'versão inválida: {versao!r}')
    return tuple(int(x) for x in versao.split('.'))


def buscar(url, limite=LIMITE_MANIFESTO, tempo=20):
    """Lê um arquivo pequeno por https (o endereço final também precisa ser https)."""
    if not url.startswith('https://'):
        raise Recusado('só endereços https')
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'AY-ESCREVA'}), timeout=tempo) as r:
            if not r.geturl().startswith('https://'):
                raise Recusado('o endereço redirecionou para uma conexão sem https')
            dados = r.read(limite + 1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise SemInformacao('ainda não há informação de atualização publicada no site oficial')
        raise SemInformacao(f'o site respondeu {e.code}')
    except (urllib.error.URLError, OSError) as e:
        raise SemInformacao(f'sem conexão com o site oficial ({getattr(e, "reason", e)})')
    if len(dados) > limite:
        raise Recusado('arquivo de versões grande demais')
    return dados


def validar(c, prefixo=PREFIXO):
    """Confere os dados de um canal do arquivo de versões (depois da assinatura)."""
    numeros(c.get('versao'))
    inst = c.get('instalador') or {}
    url, arq = inst.get('url', ''), inst.get('arquivo', '')
    if not url.startswith(prefixo) or not url.endswith('.exe') or url.rsplit('/', 1)[-1] != arq:
        raise Recusado('o instalador não vem das versões publicadas do projeto')
    if not re.fullmatch(rf'AYEscreva-{re.escape(c["versao"])}-[\w.-]+\.exe', arq):
        raise Recusado('nome do instalador não corresponde à versão')
    if not re.fullmatch(r'[0-9a-f]{64}', inst.get('sha256', '')):
        raise Recusado('SHA-256 do instalador ausente ou inválido')
    if not isinstance(inst.get('tamanho'), int) or not 10 * 2**20 < inst['tamanho'] < 2**30:
        raise Recusado('tamanho do instalador fora do esperado')
    if not isinstance(c.get('notas', ''), str) or len(c.get('notas', '')) > 4000:
        raise Recusado('notas da versão inválidas')


def consultar(versao_atual, canal='testes', manifesto=MANIFESTO, chave=CHAVE_PUBLICA, prefixo=PREFIXO, ler=buscar):
    """{'situacao': 'nova'|'atual'|'sem_canal', 'versao', 'data', 'notas', 'instalador', 'pagina'}.
    SemInformacao: não deu para consultar. Recusado: o que veio não é confiável (nada é baixado)."""
    corpo = ler(manifesto)
    try:
        assinatura = bytes.fromhex(ler(manifesto + '.sig', 512).decode('ascii').strip())
    except SemInformacao:
        raise Recusado('o arquivo de versões não tem assinatura')
    except ValueError:
        raise Recusado('assinatura em formato inválido')
    if not ay_ed25519.verificar(chave, corpo, assinatura):
        raise Recusado('a assinatura do arquivo de versões não confere: ele não foi publicado pelo projeto')
    try:
        m = json.loads(corpo.decode('utf-8'))
    except ValueError:
        raise Recusado('arquivo de versões ilegível')
    c = (m.get('canais') or {}).get(canal)
    if not c:
        return {'situacao': 'sem_canal'}
    validar(c, prefixo)
    nova = numeros(c['versao']) > numeros(versao_atual)
    return {'situacao': 'nova' if nova else 'atual', 'versao': c['versao'], 'data': c.get('data', ''), 'notas': c.get('notas', ''),
            'instalador': c['instalador'], 'pagina': c.get('pagina', '')}


def pasta_atualizacoes():
    return os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'AYEscreva', 'atualizacoes')


def baixar_instalador(info, progresso=None, cancelar=None, pasta=None, exigir_https=True):
    """Baixa (com retomada e conferência de SHA-256, o mesmo código do modelo de IA) e devolve o caminho."""
    import ay_ia
    inst = info['instalador']
    destino = os.path.join(pasta or pasta_atualizacoes(), inst['arquivo'])
    if os.path.exists(destino) and os.path.getsize(destino) == inst['tamanho']:
        if ay_ia._conferir_parcial(destino + '', None, cancelar)[1].hexdigest() == inst['sha256']:
            return destino                            # já baixado e íntegro
        os.remove(destino)
    ay_ia._baixar(inst['url'], destino, inst['sha256'], inst['tamanho'], progresso, cancelar, exigir_https=exigir_https)
    return destino


def documentos_alterados(desktop):
    """Títulos dos documentos abertos com alterações não salvas."""
    r = []
    e = desktop.getComponents().createEnumeration()
    while e.hasMoreElements():
        d = e.nextElement()
        try:
            if d.isModified():
                r.append(d.getTitle() if hasattr(d, 'getTitle') else (d.getURL() or 'sem título'))
        except Exception:
            pass
    return r


def pasta_programa():
    """Pasta da instalação do AY (onde está o AYEscreva.exe): duas acima do uno.py (…\\program\\uno.py)."""
    import uno
    return os.path.dirname(os.path.dirname(os.path.abspath(uno.__file__)))


def roteiro_instalacao(instalador, programa, pasta=None):
    """Cria o roteiro que espera o AY fechar, instala por cima (sem perguntas, por usuário) e reabre o AY."""
    pasta = pasta or os.path.dirname(instalador)
    roteiro = os.path.join(pasta, 'instalar-atualizacao.cmd')
    log = os.path.join(pasta, 'instalacao.log')
    exe = os.path.join(programa, 'AYEscreva.exe')
    linhas = ['@echo off', 'rem Gerado pelo AY ESCREVA: instala a atualização baixada e conferida e reabre o AY.',
              'timeout /t 4 /nobreak >nul',
              f'start "" /wait "{instalador}" /SILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER /CLOSEAPPLICATIONS /LOG="{log}"',
              f'if exist "{exe}" start "" "{exe}"']
    with open(roteiro, 'w', encoding='mbcs' if os.name == 'nt' else 'utf-8', errors='replace') as f:
        f.write('\r\n'.join(linhas) + '\r\n')
    return roteiro


def instalar(ctx, instalador, executar=True):
    """Fecha o AY e instala. Recusa se houver documentos com alterações não salvas (a pessoa salva antes)."""
    desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    pendentes = documentos_alterados(desktop)
    if pendentes:
        raise Recusado('salve ou feche antes os documentos com alterações: ' + ', '.join(pendentes))
    roteiro = roteiro_instalacao(instalador, pasta_programa())
    registrar(f'atualização: roteiro {roteiro}')
    if executar:
        flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) | \
            getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        subprocess.Popen(['cmd.exe', '/c', roteiro], creationflags=flags, close_fds=True)
        desktop.terminate()
    return roteiro


# ---------------------------------------------------------------- diálogo
def versao_instalada(ctx):
    info = ctx.getValueByName('/singletons/com.sun.star.deployment.PackageInformationProvider')
    return next((v for i, v in info.getExtensionList() if i == 'br.ayescreva.extensao'), '0.0.0')


def _mb(n):
    return f'{n / 2**20:.0f} MB'


def dialogo(ctx, frame):
    import ay_dialogos as D
    import ay_revisao
    atual = versao_instalada(ctx)
    d = D.Dialogo(ctx, 'Verificar atualizações', 330, 214, nome='atualizacoes')
    d.add('FixedText', 'explica', 6, 4, 318, 40, MultiLine=True,
          Label='O AY só consulta o site oficial quando você clica em "Verificar agora". É enviado apenas o pedido do arquivo de '
                'versões: nenhum documento e nenhum dado pessoal. A atualização só é baixada e instalada se você confirmar, e '
                'precisa estar assinada pelo projeto.')
    d.add('FixedText', 'versao', 6, 46, 318, 10, Label=f'Versão instalada: {atual}')
    d.rotulo('r_canal', 6, 58, 50, '~Canal:')
    d.add('ListBox', 'canal', 58, 60, 140, 12, Dropdown=True, StringItemList=tuple(CANAIS.values()))
    d.botao('verificar', 204, 58, 120, '~Verificar agora', lambda: verificar())
    d.add('FixedText', 'situacao', 6, 78, 318, 28, MultiLine=True, Label='Nenhuma consulta feita.')
    d.rotulo('r_notas', 6, 106, 200, 'N~ovidades da versão:')
    d.add('Edit', 'notas', 6, 118, 318, 68, MultiLine=True, ReadOnly=True, VScroll=True, Border=1)
    estado = {'info': None, 'baixando': False, 'cancelar': None, 'fechado': False}

    def canal():
        i = d.c('canal').getSelectedItemPos()
        return list(CANAIS)[max(0, i)]

    def verificar():
        # a consulta roda em segundo plano (sem conexão, ela pode demorar); o diálogo continua respondendo
        d.m('situacao').Label = 'Consultando o site oficial…'
        d.m('baixar').Enabled = False
        d.m('verificar').Enabled = False
        c = canal()

        def trabalho():
            try:
                r = consultar(atual, c)
            except (SemInformacao, Recusado) as e:
                r = e
            except Exception as e:
                r = SemInformacao(f'erro inesperado: {e}')
                registrar('atualização: ' + traceback.format_exc())
            ay_revisao.adiar(ctx, lambda: estado['fechado'] or mostrar_resultado(r, c))
        threading.Thread(target=trabalho, daemon=True).start()

    def mostrar_resultado(r, c):
        d.m('verificar').Enabled = True
        if isinstance(r, SemInformacao):
            d.m('situacao').Label = f'Não foi possível verificar: {r}. Nada foi alterado.'
            registrar(f'atualização: sem informação ({r})')
            return
        if isinstance(r, Recusado):
            d.m('situacao').Label = f'Atualização recusada por segurança: {r}. Nada foi baixado. Instale só pelo site oficial.'
            registrar(f'atualização: recusada ({r})')
            return
        estado['info'] = r
        if r['situacao'] == 'sem_canal':
            d.m('situacao').Label = 'Não há versões publicadas neste canal.'
        elif r['situacao'] == 'atual':
            d.m('situacao').Label = f'Você já tem a versão mais recente deste canal ({r["versao"]}).'
        else:
            inst = r['instalador']
            d.m('situacao').Label = (f'Há uma versão nova: {r["versao"]} ({r["data"]}), {_mb(inst["tamanho"])}. Seus documentos e '
                                     'preferências são mantidos na atualização.')
            d.m('notas').Text = r['notas']
            d.m('baixar').Enabled = True
        registrar(f'atualização: consulta {c}: {r["situacao"]} {r.get("versao", "")}')

    def baixar():
        r = estado['info']
        if not r or r['situacao'] != 'nova':
            return
        inst = r['instalador']
        janela = frame.getContainerWindow()
        if D.mensagem(ctx, janela, 'Baixar atualização',
                      f'Baixar o AY ESCREVA {r["versao"]} ({_mb(inst["tamanho"])}) das versões publicadas do projeto no GitHub? '
                      'O arquivo é conferido (SHA-256) antes de instalar.', 'QUERYBOX', 3) != 2:
            return
        cancelar = threading.Event()
        estado.update(baixando=True, cancelar=cancelar)
        d.m('baixar').Enabled = False
        d.m('cancelar').Enabled = True

        def progresso(feito, total, fase='baixando'):
            texto = (f'Conferindo a parte já baixada: {_mb(feito)} de {_mb(total)}…' if fase == 'conferindo'
                     else f'Baixando: {_mb(feito)} de {_mb(total)} ({100 * feito // max(1, total)}%). Pode cancelar.')
            ay_revisao.adiar(ctx, lambda: estado['fechado'] or setattr(d.m('situacao'), 'Label', texto))

        def trabalho():
            caminho, msg = None, ''
            try:
                caminho = baixar_instalador(r, progresso, cancelar)
                msg = f'Atualização {r["versao"]} baixada e conferida (SHA-256).'
            except Exception as e:
                import ay_ia
                if isinstance(e, ay_ia.Cancelado):
                    msg = 'Download cancelado; o que já veio fica guardado para continuar depois.'
                else:
                    msg = f'Falha no download: {e}'
                registrar('atualização: download ' + msg)

            def fim():
                estado['baixando'] = False
                if estado['fechado']:
                    return
                d.m('cancelar').Enabled = False
                d.m('situacao').Label = msg
                if caminho:
                    perguntar_instalar(caminho)
                else:
                    d.m('baixar').Enabled = True
            ay_revisao.adiar(ctx, fim)
        threading.Thread(target=trabalho, daemon=True).start()

    def perguntar_instalar(caminho):
        janela = frame.getContainerWindow()
        if D.mensagem(ctx, janela, 'Instalar atualização',
                      f'Instalar agora o AY ESCREVA {estado["info"]["versao"]}? O AY vai fechar, instalar e abrir de novo. Seus '
                      'documentos e preferências são mantidos.', 'QUERYBOX', 3) != 2:
            d.m('situacao').Label = f'Atualização baixada em {caminho}. Instale quando quiser (Verificar atualizações › Baixar).'
            d.m('baixar').Enabled = True
            return
        try:
            instalar(ctx, caminho)
        except Recusado as e:
            D.mensagem(ctx, janela, 'Instalar atualização', f'Ainda não: {e}. Depois, clique de novo em "Baixar e instalar".',
                       'WARNINGBOX')
            d.m('baixar').Enabled = True

    def cancelar():
        if estado['cancelar'] is not None:
            estado['cancelar'].set()

    d.botao('baixar', 6, 194, 100, '~Baixar e instalar…', baixar)
    d.botao('cancelar', 110, 194, 80, 'Ca~ncelar download', cancelar)
    d.botao('fechar', 264, 194, 60, '~Fechar', lambda: d.fechar(None), padrao=True)

    def iniciar():
        d.c('canal').selectItemPos(0, True)
        d.m('baixar').Enabled = False
        d.m('cancelar').Enabled = False
    d.executar(frame.getContainerWindow(), iniciar)
    estado['fechado'] = True
    if estado['cancelar'] is not None:
        estado['cancelar'].set()
