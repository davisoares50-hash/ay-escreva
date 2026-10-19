# -*- coding: utf-8 -*-
"""Investigação: sequência de abrir/fechar documentos na MESMA sessão do motor com a faixa por abas.

Reproduz o padrão do teste de segurança que derrubou o motor: criar documento oculto com macro, salvar,
fechar e então abrir/fechar documentos em quadros visíveis várias vezes.

Uso: python.exe notebookbar_sequencia.py <modo> <headless:0|1> <ciclos> [sequencia] [criar:0|1]
  sequencia: passos separados por vírgula, padrão "m4,m3,s3"
             m = documento com macro, s = documento simples, n = documento novo; dígito = MacroExecutionMode
  criar:     1 (padrão) cria o documento com macro nesta mesma sessão; 0 usa tests/output/seguranca/com-macro.odt
SPDX-License-Identifier: MPL-2.0
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'uno'))
from ay_uno import Motor, SAIDA_TESTES, props, url, salvar, fechar  # noqa: E402

import uno  # noqa: E402


def main():
    modo, headless, ciclos = sys.argv[1], sys.argv[2] == '1', int(sys.argv[3])
    sequencia = (sys.argv[4] if len(sys.argv) > 4 else 'm4,m3,s3').split(',')
    criar = (sys.argv[5] if len(sys.argv) > 5 else '1') == '1'
    pasta = SAIDA_TESTES / 'investigacao'
    pasta.mkdir(parents=True, exist_ok=True)
    for f in pasta.glob('.~lock.*'):
        f.unlink()
    simples = SAIDA_TESTES / 'etapa1' / 'teste-etapa1.odt'
    passos = []
    etapa = 'iniciar'
    try:
        with Motor('seq', visivel=not headless) as m:
            m.configurar('/org.openoffice.Office.UI.ToolbarMode/Applications/Writer', 'Active', modo)
            if criar:
                etapa = 'criar documento oculto com macro'
                doc = m.desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, props(Hidden=True))
                doc.Text.setString('x')
                libs = doc.BasicLibraries
                if not libs.hasByName('Standard'):
                    libs.createLibrary('Standard')
                libs.getByName('Standard').insertByName('M', 'Sub A\nEnd Sub\n')
                ev = uno.Any('[]com.sun.star.beans.PropertyValue', props(EventType='Script', Script='vnd.sun.star.script:Standard.M.A?language=Basic&location=document'))
                uno.invoke(doc.Events, 'replaceByName', ('OnLoad', ev))
                comMacro = salvar(doc, pasta / 'seq-macro.odt')
                fechar(doc)
                passos.append(etapa)
            else:
                comMacro = SAIDA_TESTES / 'seguranca' / 'com-macro.odt'
            for i in range(1, ciclos + 1):
                for passo in sequencia:
                    tipo, mm = passo[0], int(passo[1:] or 3)
                    alvo = {'m': url(comMacro), 's': url(simples), 'n': 'private:factory/swriter'}[tipo]
                    etapa = f'ciclo {i}: abrir {passo} visível'
                    d = m.desktop.loadComponentFromURL(alvo, '_blank', 0, props(Hidden=False, MacroExecutionMode=mm))
                    time.sleep(1)
                    etapa = f'ciclo {i}: fechar {passo}'
                    fechar(d)
                    time.sleep(0.5)
                    passos.append(f'{i}:{passo}')
        print(f'RESULTADO: sobreviveu a {len(passos)} passos (modo={modo} headless={headless})')
        return 0
    except Exception as e:  # noqa: BLE001
        print(f'RESULTADO: falhou em "{etapa}" depois de {len(passos)} passos: {type(e).__name__}: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
