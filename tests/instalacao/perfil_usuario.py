# -*- coding: utf-8 -*-
"""Grava ou confere preferências no perfil REAL do AY ESCREVA instalado (teste de atualização de versão).

Roda com o Python do programa instalado e abre o motor instalado, sem tela, com o perfil indicado.

  python.exe perfil_usuario.py gravar   <pasta do perfil> <saida.json>
  python.exe perfil_usuario.py conferir <pasta do perfil> <saida.json>

Gravar: palavra no dicionário pessoal, unidade de medida do Writer (milímetros) e, se a extensão da versão já tiver a
revisão de texto, uma palavra na lista "não corrigir". Conferir: lê os mesmos valores e o que a versão nova trouxe
(versão da extensão e comandos da formatação acadêmica e da galeria registrados no perfil antigo).
SPDX-License-Identifier: MPL-2.0
"""
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

PALAVRA = 'Ayzteste'
UNIDADE_MM = 1


def pv(**kw):
    r = []
    for k, v in kw.items():
        p = PropertyValue()
        p.Name, p.Value = k, v
        r.append(p)
    return tuple(r)


def conectar(perfil):
    programa = Path(sys.executable).resolve().parent
    pipe = 'ayperfil_' + uuid.uuid4().hex[:8]
    proc = subprocess.Popen([str(programa / 'soffice.exe'), f'-env:UserInstallation={uno.systemPathToFileUrl(str(perfil))}',
                             f'--accept=pipe,name={pipe};urp;StarOffice.ComponentContext', '--headless', '--invisible',
                             '--norestore', '--nologo', '--nodefault', '--nolockcheck'])
    local = uno.getComponentContext()
    res = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
    fim = time.time() + 180
    while True:
        try:
            ctx = res.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext')
            return proc, ctx
        except NoConnectException:
            if time.time() > fim or proc.poll() is not None:
                raise RuntimeError('motor instalado não respondeu')
            time.sleep(0.5)


def config(ctx, no, escrita=False):
    prov = ctx.ServiceManager.createInstanceWithContext('com.sun.star.configuration.ConfigurationProvider', ctx)
    tipo = 'com.sun.star.configuration.ConfigurationUpdateAccess' if escrita else 'com.sun.star.configuration.ConfigurationAccess'
    return prov.createInstanceWithArguments(tipo, pv(nodepath=no))


def dicionario(ctx):
    lista = ctx.ServiceManager.createInstanceWithContext('com.sun.star.linguistic2.DictionaryList', ctx)
    d = lista.getDictionaryByName('standard.dic')
    if d is None:
        loc = uno.createUnoStruct('com.sun.star.lang.Locale')
        subst = ctx.ServiceManager.createInstanceWithContext('com.sun.star.util.PathSubstitution', ctx)
        d = lista.createDictionary('standard.dic', loc, uno.Enum('com.sun.star.linguistic2.DictionaryType', 'POSITIVE'),
                                   subst.substituteVariables('$(user)/wordbook/standard.dic', True))
        lista.addDictionary(d)
        d.setActive(True)
    return d


def main():
    modo, perfil, saida = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    proc, ctx = conectar(perfil)
    r = {'modo': modo}
    try:
        if modo == 'gravar':
            d = dicionario(ctx)
            d.add(PALAVRA, False, '')
            d.store()
            c = config(ctx, '/org.openoffice.Office.Writer/Layout/Other', escrita=True)
            c.setPropertyValue('MeasureUnit', UNIDADE_MM)
            c.commitChanges()
            try:
                c = config(ctx, '/br.ayescreva.Configuracao/Revisao', escrita=True)
                c.setPropertyValue('NaoCorrigir', uno.Any('[]string', ('nao',)))
                c.commitChanges()
                r['nao_corrigir'] = True
            except Exception as e:
                r['nao_corrigir'] = f'sem revisão de texto nesta versão ({type(e).__name__})'
        r['dicionario'] = PALAVRA in [e.getDictionaryWord() for e in dicionario(ctx).getEntries()]
        r['unidade_mm'] = config(ctx, '/org.openoffice.Office.Writer/Layout/Other').getPropertyValue('MeasureUnit') == UNIDADE_MM
        try:
            r['lista_nao_corrigir'] = list(config(ctx, '/br.ayescreva.Configuracao/Revisao').getPropertyValue('NaoCorrigir'))
        except Exception:
            r['lista_nao_corrigir'] = None
        try:
            cmds = config(ctx, '/org.openoffice.Office.UI.GenericCommands/UserInterface/Commands')
            r['comandos_entrega_b'] = all(cmds.hasByName(n) for n in ('ayescreva:FormatarTrabalho', 'ayescreva:Galeria', 'ayescreva:Conformidade'))
            r['comandos_entrega_c'] = all(cmds.hasByName(n) for n in ('ayescreva:RevisaoIA', 'ayescreva:GerenciarIA'))
        except Exception:
            r['comandos_entrega_b'] = r['comandos_entrega_c'] = False
        try:
            # configuração da IA local presente no perfil antigo, sem modelo escolhido (a IA continua opcional)
            r['ia_sem_modelo'] = config(ctx, '/br.ayescreva.Configuracao/IA').getPropertyValue('Modelo') == ''
        except Exception:
            r['ia_sem_modelo'] = None
        info = ctx.getValueByName('/singletons/com.sun.star.deployment.PackageInformationProvider')
        r['versao_extensao'] = next((v for i, v in info.getExtensionList() if i == 'br.ayescreva.extensao'), None)
    finally:
        try:
            ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx).terminate()
        except Exception:
            pass
        try:
            proc.wait(timeout=60)
        except Exception:
            proc.kill()
    saida.write_text(json.dumps(r, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
