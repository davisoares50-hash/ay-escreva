# -*- coding: utf-8 -*-
"""Testes de segurança e privacidade do AY ESCREVA.

1. Macro no evento "ao abrir" de um ODT:
   - controle positivo: abrindo com MacroExecutionMode=ALWAYS_EXECUTE_NO_WARN a macro executa
     (prova que o teste detecta execução);
   - caso real: abrindo como a interface abre (USE_CONFIG) e até aprovando confirmações
     (USE_CONFIG_APPROVE_CONFIRMATION), a macro NÃO pode executar.
2. Recurso externo: DOCX com imagem vinculada a um servidor HTTP local (127.0.0.1). Ao abrir,
   exportar PDF e fechar, o servidor não pode receber nenhuma requisição.

Uso: python.exe seguranca.py
SPDX-License-Identifier: MPL-2.0
"""
import sys
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, Relatorio, SAIDA_TESTES, RAIZ, props, salvar, fechar  # noqa: E402

import uno  # noqa: E402

PASTA = SAIDA_TESTES / 'seguranca'
# com.sun.star.document.MacroExecMode
ALWAYS_EXECUTE_NO_WARN, USE_CONFIG, USE_CONFIG_APPROVE_CONFIRMATION = 4, 3, 6


def criar_doc_com_macro(motor, destino, marcador):
    doc = motor.novo()
    doc.Text.setString('Documento de teste com macro no evento de abertura.')
    libs = doc.BasicLibraries
    if not libs.hasByName('Standard'):
        libs.createLibrary('Standard')
    codigo = ('Sub Marcar\n'
              '  Dim n As Integer\n'
              '  n = FreeFile\n'
              f'  Open "{marcador}" For Output As #n\n'
              '  Print #n, "a macro executou"\n'
              '  Close #n\n'
              'End Sub\n')
    libs.getByName('Standard').insertByName('Modulo1', codigo)
    evento = uno.Any('[]com.sun.star.beans.PropertyValue', props(
        EventType='Script', Script='vnd.sun.star.script:Standard.Modulo1.Marcar?language=Basic&location=document'))
    uno.invoke(doc.Events, 'replaceByName', ('OnLoad', evento))
    salvar(doc, destino)
    fechar(doc)


class Contador(BaseHTTPRequestHandler):
    pedidos = []

    def do_GET(self):  # noqa: N802
        Contador.pedidos.append(self.path)
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        dados = (RAIZ / 'out' / 'marca' / 'icone-64.png').read_bytes()
        self.send_header('Content-Length', str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, *a):
        pass


def criar_docx_com_imagem_remota(destino, url_imagem):
    W = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
         'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
         'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
         'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
         'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>'
           '<w:p><w:r><w:t>Imagem vinculada a servidor externo abaixo:</w:t></w:r></w:p>'
           '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="914400" cy="914400"/><wp:docPr id="1" name="Remota"/>'
           '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
           '<pic:nvPicPr><pic:cNvPr id="1" name="remota.png"/><pic:cNvPicPr/></pic:nvPicPr>'
           '<pic:blipFill><a:blip r:link="rIdRemota"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
           '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="914400" cy="914400"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>'
           '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
           '</w:body></w:document>')
    tipos = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    drels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             f'<Relationship Id="rIdRemota" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{url_imagem}" TargetMode="External"/></Relationships>')
    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', tipos)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', doc)
        z.writestr('word/_rels/document.xml.rels', drels)


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    rel = Relatorio('Segurança')
    marcador = PASTA / 'macro-executou.txt'
    doc_macro = PASTA / 'com-macro.odt'

    srv = HTTPServer(('127.0.0.1', 0), Contador)
    porta = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    docx_remoto = PASTA / 'imagem-remota.docx'
    criar_docx_com_imagem_remota(docx_remoto, f'http://127.0.0.1:{porta}/imagem-remota.png')

    with Motor('seguranca') as motor:
        # Documentos precisam de quadro não oculto para disparar "ao abrir"; no modo sem tela (headless)
        # a faixa por abas derruba o motor ao criar o quadro, então este perfil descartável usa a barra clássica.
        motor.configurar('/org.openoffice.Office.UI.ToolbarMode/Applications/Writer', 'Active', 'Default')
        criar_doc_com_macro(motor, doc_macro, str(marcador))

        # Controle positivo: execução forçada pela API
        marcador.unlink(missing_ok=True)
        d = motor.abrir(doc_macro, MacroExecutionMode=ALWAYS_EXECUTE_NO_WARN, Hidden=False)
        time.sleep(2)
        fechar(d)
        rel.verificar('controle positivo: macro executa quando forçada pela API', marcador.exists(),
                      'o teste consegue detectar execução')

        for modo, nome in ((USE_CONFIG, 'abertura normal (configuração)'),
                           (USE_CONFIG_APPROVE_CONFIRMATION, 'abertura aprovando confirmações')):
            marcador.unlink(missing_ok=True)
            d = motor.abrir(doc_macro, MacroExecutionMode=modo, Hidden=False)
            time.sleep(2)
            fechar(d)
            rel.verificar(f'macro NÃO executa — {nome}', not marcador.exists())

        Contador.pedidos.clear()
        d = motor.abrir(docx_remoto, MacroExecutionMode=USE_CONFIG, Hidden=False)
        salvar(d, PASTA / 'imagem-remota.pdf')
        time.sleep(2)
        fechar(d)
        rel.verificar('imagem remota NÃO é baixada ao abrir e exportar PDF', len(Contador.pedidos) == 0,
                      f'{len(Contador.pedidos)} requisição(ões) ao servidor local')
        # Informativo: o que acontece quando o usuário pede explicitamente para atualizar vínculos
        d = motor.abrir(docx_remoto, MacroExecutionMode=USE_CONFIG, Hidden=False)
        try:
            d.updateLinks()
        except Exception as e:  # noqa: BLE001
            print(f'  (updateLinks: {e})')
        time.sleep(3)
        fechar(d)
        print(f'[INFO] atualização de vínculos pedida pelo usuário: {len(Contador.pedidos)} requisição(ões) — '
              + ('a política permite carregar com autorização' if Contador.pedidos else
                 'a política bloqueia mesmo com pedido explícito (BlockUntrustedRefererLinks)'))
    srv.shutdown()
    return rel.finalizar()


if __name__ == '__main__':
    sys.exit(main())
