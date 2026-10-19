# -*- coding: utf-8 -*-
"""Utilitários para dirigir o motor do AY ESCREVA via UNO nos testes automatizados.

Executar sempre com o Python que acompanha a distribuição:
    "dist\\AY ESCREVA\\program\\python.exe" tests\\uno\\<teste>.py

Cada sessão usa um perfil de usuário descartável (não toca no perfil real do usuário).
SPDX-License-Identifier: MPL-2.0
"""
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

RAIZ = Path(__file__).resolve().parents[2]
PROGRAMA = Path(sys.executable).resolve().parent          # ...\AY ESCREVA\program
SAIDA_TESTES = RAIZ / 'tests' / 'output'


def props(**kw):
    """Converte argumentos nomeados em uma tupla de PropertyValue."""
    res = []
    for k, v in kw.items():
        p = PropertyValue()
        p.Name = k
        p.Value = v
        res.append(p)
    return tuple(res)


def url(caminho):
    return uno.systemPathToFileUrl(str(Path(caminho).resolve()))


class Motor:
    """Inicia o motor em modo invisível, conecta por pipe e encerra ao sair."""

    def __init__(self, nome='ay', visivel=False):
        self.nome_pipe = f'{nome}_{uuid.uuid4().hex[:8]}'
        self.perfil = SAIDA_TESTES / 'perfis' / self.nome_pipe
        self.visivel = visivel
        self.proc = None
        self.ctx = None
        self.desktop = None

    def __enter__(self):
        self.perfil.mkdir(parents=True, exist_ok=True)
        args = [str(PROGRAMA / 'soffice.exe'),
                f'-env:UserInstallation={url(self.perfil)}',
                f'--accept=pipe,name={self.nome_pipe};urp;StarOffice.ComponentContext',
                '--norestore', '--nologo', '--nodefault', '--nolockcheck']
        if not self.visivel:
            args += ['--headless', '--invisible']
        self.proc = subprocess.Popen(args)
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
        limite = time.time() + 120
        while True:
            try:
                self.ctx = resolver.resolve(f'uno:pipe,name={self.nome_pipe};urp;StarOffice.ComponentContext')
                break
            except NoConnectException:
                if time.time() > limite or self.proc.poll() is not None:
                    raise RuntimeError('motor não respondeu na conexão UNO')
                time.sleep(0.5)
        self.smgr = self.ctx.ServiceManager
        self.desktop = self.smgr.createInstanceWithContext('com.sun.star.frame.Desktop', self.ctx)
        return self

    def __exit__(self, *exc):
        try:
            if self.desktop is not None:
                self.desktop.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=60)
        except Exception:
            self.proc.kill()
        shutil.rmtree(self.perfil, ignore_errors=True)
        return False

    def servico(self, nome):
        return self.smgr.createInstanceWithContext(nome, self.ctx)

    def configurar(self, no, propriedade, valor):
        """Altera uma configuração no perfil descartável do teste (camada do usuário)."""
        prov = self.servico('com.sun.star.configuration.ConfigurationProvider')
        acesso = prov.createInstanceWithArguments('com.sun.star.configuration.ConfigurationUpdateAccess', props(nodepath=no))
        acesso.setPropertyValue(propriedade, valor)
        acesso.commitChanges()

    def novo(self):
        return self.desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, props(Hidden=not self.visivel))

    def abrir(self, caminho, **extra):
        # Hidden pode ser sobrescrito: documentos ocultos não são ativados e não disparam o evento "ao abrir"
        args = {'Hidden': not self.visivel, **extra}
        doc = self.desktop.loadComponentFromURL(url(caminho), '_blank', 0, props(**args))
        if doc is None:
            raise RuntimeError(f'falha ao abrir {caminho}')
        return doc


FILTROS = {
    '.odt': 'writer8',
    '.docx': 'MS Word 2007 XML',
    '.doc': 'MS Word 97',
    '.rtf': 'Rich Text Format',
    '.txt': 'Text (encoded)',
    '.pdf': 'writer_pdf_Export',
}


def salvar(doc, caminho, **opcoes):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    filtro = FILTROS[caminho.suffix.lower()]
    extra = {}
    if caminho.suffix.lower() == '.txt':
        extra['FilterOptions'] = 'UTF8,CRLF,,'
    if caminho.suffix.lower() == '.pdf':
        doc.storeToURL(url(caminho), props(FilterName=filtro, **opcoes))
    else:
        doc.storeToURL(url(caminho), props(FilterName=filtro, Overwrite=True, **extra))
    return caminho


def fechar(doc):
    try:
        doc.close(True)
    except Exception:
        doc.dispose()


def paginas(doc):
    doc.getCurrentController()  # garante a formatação do layout
    return doc.getCurrentController().getPropertyValue('PageCount')


def paginas_pdf(caminho):
    import re
    dados = Path(caminho).read_bytes()
    return len(re.findall(rb'/Type\s*/Page[^s]', dados))


class Relatorio:
    """Coleta verificações e imprime um resumo legível; código de saída != 0 se algo falhar."""

    def __init__(self, titulo):
        self.titulo = titulo
        self.itens = []

    def verificar(self, descricao, condicao, detalhe=''):
        self.itens.append((bool(condicao), descricao, detalhe))
        marca = 'OK  ' if condicao else 'FALHA'
        print(f'[{marca}] {descricao}' + (f' — {detalhe}' if detalhe else ''), flush=True)
        return bool(condicao)

    def finalizar(self):
        falhas = [i for i in self.itens if not i[0]]
        print(f'\n{self.titulo}: {len(self.itens) - len(falhas)}/{len(self.itens)} verificações aprovadas')
        return 1 if falhas else 0
