# -*- coding: utf-8 -*-
"""Recuperação após falha: o AY é encerrado à força com documentos alterados e não salvos; ao abrir de novo,
oferece a recuperação e os documentos voltam com as alterações.

  1. abre um documento novo e um documento já salvo; altera os dois sem salvar;
  2. grava a informação de recuperação (o mesmo que o salvamento automático faz a cada 5 minutos);
  3. encerra o motor à força (como uma queda);
  4. confere no perfil: lista de recuperação e arquivos de recuperação com o texto não salvo;
  5. abre o AY com interface no mesmo perfil e confere que a janela de recuperação aparece;
  6. executa a recuperação e confere que os dois documentos voltam com as alterações.

Usa um perfil descartável. Uso: python.exe recuperacao.py
SPDX-License-Identifier: MPL-2.0
"""
import ctypes
import ctypes.wintypes as wt
import json
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import PROGRAMA, SAIDA_TESTES, props, url  # noqa: E402

import uno  # noqa: E402
from com.sun.star.connection import NoConnectException  # noqa: E402

SAIDA = SAIDA_TESTES / 'recuperacao'
NOVO = 'Texto que só existe na memória: documento novo 4821.'
ALTERADO = 'Alteração não salva no documento existente 7395.'
itens = []


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


def iniciar(perfil, aceitar=True, headless=True):
    pipe = 'rec_' + uuid.uuid4().hex[:8]
    args = [str(PROGRAMA / 'soffice.exe'), f'-env:UserInstallation={url(perfil)}', '--nologo', '--nolockcheck']
    if aceitar:
        args.append(f'--accept=pipe,name={pipe};urp;StarOffice.ComponentContext')
    if headless:
        args += ['--headless', '--invisible']
    proc = subprocess.Popen(args)
    if not aceitar:
        return proc, None
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
    limite = time.time() + 120
    while True:
        try:
            return proc, resolver.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
        except NoConnectException:
            if time.time() > limite or proc.poll() is not None:
                raise RuntimeError('motor não respondeu')
            time.sleep(0.5)


def matar_tudo(pid_pai):
    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid_pai)], capture_output=True)
    time.sleep(2)


def janelas_do_processo(nome_exe='soffice.bin'):
    """Títulos das janelas visíveis dos processos soffice.bin."""
    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32
    titulos = []
    pids = set()
    saida = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {nome_exe}', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    for linha in saida.splitlines():
        partes = [p.strip('"') for p in linha.split('","')]
        if len(partes) > 1 and partes[1].isdigit():
            pids.add(int(partes[1]))

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cada(h, _):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in pids and u32.IsWindowVisible(h):
            n = u32.GetWindowTextLengthW(h)
            buf = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(h, buf, n + 1)
            if buf.value:
                titulos.append(buf.value)
        return True
    u32.EnumWindows(cada, 0)
    return titulos


def despachar_recuperacao(ctx, comando):
    smgr = ctx.ServiceManager
    ar = smgr.createInstanceWithContext('com.sun.star.frame.AutoRecovery', ctx)
    u = uno.createUnoStruct('com.sun.star.util.URL')
    u.Complete = 'vnd.sun.star.autorecovery:/' + comando
    _, u = smgr.createInstanceWithContext('com.sun.star.util.URLTransformer', ctx).parseStrict(u)
    ar.dispatch(u, ())


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    perfil = SAIDA_TESTES / 'perfis' / ('recuperacao_' + uuid.uuid4().hex[:6])
    perfil.mkdir(parents=True)
    existente = SAIDA / 'existente.odt'
    for p in (existente, SAIDA / '.~lock.existente.odt#'):
        if p.exists():
            p.unlink()

    # 1-3: alterar sem salvar, esperar o salvamento automático de recuperação e cair
    proc, ctx = iniciar(perfil, headless=False)   # sem tela, a recuperação automática não acompanha documentos
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    cfg = smgr.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider', ctx)

    def configurar(no, nome, valor):
        a = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationUpdateAccess', props(nodepath=no))
        a.setPropertyValue(nome, valor)
        a.commitChanges()
    configurar('/org.openoffice.Office.UI.ToolbarMode/Applications/Writer', 'Active', 'Default')  # UNO externo: barra clássica
    configurar('/org.openoffice.Office.Recovery/AutoSave', 'TimeIntervall', 1)   # 1 min só neste perfil de teste (o AY usa 5)
    d0 = desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, props(Hidden=True))
    d0.Text.setString('Conteúdo salvo do documento existente.')
    d0.storeAsURL(url(existente), props(FilterName='writer8'))
    d0.close(True)
    novo = desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, props(Hidden=False))
    novo.Text.setString(NOVO)
    ex = desktop.loadComponentFromURL(url(existente), '_blank', 0, props(Hidden=False))
    ex.Text.insertString(ex.Text.getEnd(), ' ' + ALTERADO, False)
    verificar('dois documentos alterados e não salvos', novo.isModified() and ex.isModified())
    backup = perfil / 'user' / 'backup'
    achados = {NOVO: False, ALTERADO: False}
    inicio = time.time()
    while time.time() - inicio < 180 and not all(achados.values()):
        time.sleep(5)
        for arq in backup.glob('*') if backup.exists() else []:
            try:
                with zipfile.ZipFile(arq) as z:
                    conteudo = z.read('content.xml').decode('utf-8', 'replace')
                for k in achados:
                    achados[k] = achados[k] or (k in conteudo)
            except Exception:
                pass
    espera = round(time.time() - inicio)
    verificar('salvamento automático gravou a recuperação dos dois documentos, com o texto não salvo', all(achados.values()),
              f'{espera} s; arquivos: {[p.name for p in backup.glob("*")] if backup.exists() else []}')
    matar_tudo(proc.pid)
    verificar('motor encerrado à força (simulação de queda)', proc.poll() is not None)
    xcu = (perfil / 'user' / 'registrymodifications.xcu').read_text(encoding='utf-8', errors='replace')
    verificar('lista de recuperação gravada no perfil', 'RecoveryList' in xcu and 'TempURL' in xcu)

    # 4-6: abrir com interface, a janela de recuperação aparece; Enter em "Iniciar" e depois em "Concluir"
    proc, ctx = iniciar(perfil, headless=False)
    titulo = ''
    limite = time.time() + 90
    while time.time() < limite and not titulo:
        time.sleep(1)
        titulo = next((t for t in janelas_do_processo() if 'ecupera' in t), '')
    verificar('ao abrir de novo, o AY oferece a recuperação', bool(titulo), titulo or 'janela não encontrada em 90 s')
    smgr = ctx.ServiceManager
    tk = smgr.createInstanceWithContext('com.sun.star.awt.Toolkit', ctx)
    robo = tk.queryInterface(uno.getTypeByName('com.sun.star.awt.XToolkitRobot'))

    def enter():
        janela = tk.getActiveTopWindow()
        if janela is None:
            return False
        ev = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
        ev.Source, ev.KeyCode, ev.KeyChar = janela, 1280, chr(13)
        robo.keyPress(ev)
        robo.keyRelease(ev)
        return True
    desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    textos = []
    if titulo:
        enter()                     # "Iniciar"
        time.sleep(8)
        if any('ecupera' in t for t in janelas_do_processo()):
            enter()                 # "Concluir"
            time.sleep(6)
        comps = desktop.getComponents().createEnumeration()
        while comps.hasMoreElements():
            c = comps.nextElement()
            try:
                textos.append(c.Text.getString())
            except Exception:
                pass
    verificar('documento novo recuperado com o texto não salvo', any(NOVO in t for t in textos), f'{len(textos)} documento(s) abertos')
    verificar('documento existente recuperado com a alteração não salva', any(ALTERADO in t for t in textos))
    matar_tudo(proc.pid)
    shutil.rmtree(perfil, ignore_errors=True)

    ok = sum(1 for i in itens if i['ok'])
    (SAIDA / 'resultado.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Recuperação: {ok}/{len(itens)} verificações aprovadas')
    return 0 if ok == len(itens) else 1


if __name__ == '__main__':
    sys.exit(main())
