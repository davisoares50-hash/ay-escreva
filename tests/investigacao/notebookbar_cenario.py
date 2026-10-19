# -*- coding: utf-8 -*-
"""Investigação: em que condições o motor cai ao criar um quadro de documento com a faixa por abas?

Executa UM cenário e informa se o motor sobreviveu. Rode com o python.exe da instalação que quer testar
(base pura em _cache\\base\\<versão>\\program ou a distribuição AY em dist\\AY ESCREVA\\program).

Uso: python.exe notebookbar_cenario.py <modo> <headless:0|1> <oculto:0|1> [ui:0|1]
  modo: Default (barra clássica) ou notebookbar.ui (faixa por abas)
  ui:   1 = também tenta clicar uma aba e um botão da faixa via UITest
SPDX-License-Identifier: MPL-2.0
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'uno'))
from ay_uno import Motor, fechar  # noqa: E402


def main():
    modo, headless, oculto = sys.argv[1], sys.argv[2] == '1', sys.argv[3] == '1'
    usar_ui = len(sys.argv) > 4 and sys.argv[4] == '1'
    etapa = 'iniciar'
    try:
        with Motor('nb', visivel=not headless) as m:
            etapa = 'configurar modo'
            m.configurar('/org.openoffice.Office.UI.ToolbarMode/Applications/Writer', 'Active', modo)
            etapa = 'criar documento'
            from ay_uno import props
            doc = m.desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, props(Hidden=oculto))
            etapa = 'digitar'
            doc.Text.setString('teste')
            time.sleep(2)
            if usar_ui:
                etapa = 'UITest'
                ui = m.servico('org.libreoffice.uitest.UITest')
                print('UITest disponível:', ui is not None)
                top = ui.getTopFocusWindow()
                print('filhos da janela (amostra):', list(top.getChildren())[:40])
            etapa = 'fechar'
            fechar(doc)
        print(f'RESULTADO: sobreviveu (modo={modo} headless={headless} oculto={oculto})')
        return 0
    except Exception as e:  # noqa: BLE001
        print(f'RESULTADO: falhou na etapa "{etapa}": {type(e).__name__}: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
