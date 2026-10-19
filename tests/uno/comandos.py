# -*- coding: utf-8 -*-
"""Verifica, no motor em execução, cada comando previsto em ui/abas.json e gera a matriz de funcionalidades.

Para cada função com comando:
  - o comando está registrado para o módulo de texto (UICommandDescription) e tem rótulo pt-BR;
  - o quadro do Writer devolve um despachante para ele (queryDispatch != None).
Funções sem comando são lacunas. O resultado vai para tests/output/comandos.json e
docs/MATRIZ-FUNCIONALIDADES.md (gerado; não editar à mão).

Uso: python.exe comandos.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, RAIZ, SAIDA_TESTES, fechar  # noqa: E402

import uno  # noqa: E402

# Evidência de funcionamento validado (teste automatizado que exercita a função, não o botão)
EVIDENCIA = {
    '.uno:AddDirect': 'aceite_etapa1', '.uno:Open': 'ida_e_volta', '.uno:Save': 'aceite_etapa1',
    '.uno:SaveAs': 'aceite_etapa1, ida_e_volta', '.uno:CloseDoc': 'aceite_etapa1',
    '.uno:ExportToPDF': 'aceite_etapa1 (PDF e PDF/UA)', '.uno:ExportDirectToPDF': 'aceite_etapa1',
    '.uno:Print': 'impressao', '.uno:Bold': 'aceite_etapa1', '.uno:Italic': 'aceite_etapa1',
    '.uno:Underline': 'aceite_etapa1', '.uno:Strikeout': 'aceite_etapa1', '.uno:SuperScript': 'aceite_etapa1',
    '.uno:FontColor': 'aceite_etapa1', '.uno:FontHeight': 'aceite_etapa1', '.uno:CharFontName': 'aceite_etapa1',
    '.uno:CharBackColor': 'aceite_etapa1 (realce no DOCX)', '.uno:CenterPara': 'aceite_etapa1',
    '.uno:JustifyPara': 'aceite_etapa1', '.uno:StyleApply': 'aceite_etapa1 (Título 1)',
    '.uno:InsertTable': 'aceite_etapa1, ida_e_volta (mescladas)', '.uno:InsertGraphic': 'aceite_etapa1',
    '.uno:ObjectTitleDescription': 'aceite_etapa1, ida_e_volta', '.uno:InsertPagebreak': 'aceite_etapa1',
    '.uno:InsertPageHeader': 'aceite_etapa1, ida_e_volta', '.uno:InsertPageFooter': 'aceite_etapa1, ida_e_volta',
    '.uno:PageNumberWizard': 'aceite_etapa1 (campo de página)', '.uno:InsertFootnote': 'ida_e_volta',
    '.uno:InsertEndnote': 'ida_e_volta', '.uno:InsertAnnotation': 'ida_e_volta', '.uno:TrackChanges': 'ida_e_volta',
    '.uno:InsertMultiIndex': 'ida_e_volta (sumário)', '.uno:HyperlinkDialog': 'ida_e_volta',
    '.uno:InsertBookmark': 'ida_e_volta', '.uno:InsertReferenceField': 'ida_e_volta',
    '.uno:DefaultNumbering': 'ida_e_volta', '.uno:DefaultBullet': 'ida_e_volta', '.uno:Orientation': 'ida_e_volta (paisagem)',
    '.uno:PageColumnType': 'ida_e_volta (2 colunas)', '.uno:InsertObjectStarMath': 'ida_e_volta (OMML)',
    '.uno:DrawText': 'ida_e_volta (caixa de texto)', '.uno:InsertBreak': 'ida_e_volta (3 seções)',
}


def main():
    abas = json.loads((RAIZ / 'ui' / 'abas.json').read_text(encoding='utf-8'))
    resultados = []
    with Motor('comandos') as motor:
        doc = motor.novo()
        frame = doc.getCurrentController().getFrame()
        transf = motor.servico('com.sun.star.util.URLTransformer')
        desc = motor.servico('com.sun.star.frame.UICommandDescription').getByName('com.sun.star.text.TextDocument')
        menus = motor.servico('com.sun.star.frame.PopupMenuControllerFactory')
        modulo = 'com.sun.star.text.TextDocument'

        def verificar(item):
            cmd = item['comando']
            if not cmd:
                return None, False, False
            rotulo = None
            registrado = desc.hasByName(cmd)
            if registrado:
                rotulo = next((p.Value for p in desc.getByName(cmd) if p.Name == 'Label'), None)
            if item.get('tipo') == 'menu':
                # Menus suspensos não são despachados: dependem de um controlador de menu registrado
                return rotulo, registrado, bool(menus.hasController(cmd, modulo))
            u = uno.createUnoStruct('com.sun.star.util.URL')
            u.Complete = cmd
            _, u = transf.parseStrict(u)
            despacho = frame.queryDispatch(u, '', 0) is not None
            return rotulo, registrado, despacho

        for aba in abas['abas']:
            for grupo in aba['grupos']:
                for item in grupo['itens']:
                    rot, reg, desp = verificar(item)
                    resultados.append({'aba': aba['rotulo'], 'grupo': grupo['rotulo'], **item,
                                       'rotuloBase': rot, 'registrado': reg, 'despacho': desp})
        for aba in abas['contextuais']:
            for item in aba['itens']:
                rot, reg, desp = verificar(item)
                resultados.append({'aba': aba['rotulo'] + ' (contextual)', 'grupo': '', **item,
                                   'rotuloBase': rot, 'registrado': reg, 'despacho': desp})
        fechar(doc)

    SAIDA_TESTES.mkdir(parents=True, exist_ok=True)
    (SAIDA_TESTES / 'comandos.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding='utf-8')
    gerar_matriz(resultados)

    com_cmd = [r for r in resultados if r['comando']]
    ok = [r for r in com_cmd if r['despacho']]
    falhos = [r for r in com_cmd if not r['despacho']]
    print(f'Funções: {len(resultados)} | com comando: {len(com_cmd)} | despachados: {len(ok)} | '
          f'sem despacho: {len(falhos)} | lacunas: {len(resultados) - len(com_cmd)}')
    for r in falhos:
        print(f'  SEM DESPACHO: {r["aba"]} / {r["funcao"]} -> {r["comando"]}')
    return 1 if falhos else 0


def situacao(r):
    if not r['comando']:
        return 'Lacuna'
    if r['despacho']:
        return 'Na base (comando verificado)'
    return 'Comando não encontrado'


def gerar_matriz(res):
    contagem = {}
    for r in res:
        contagem[situacao(r)] = contagem.get(situacao(r), 0) + 1
    lin = [
        '# Matriz de funcionalidades do AY ESCREVA',
        '',
        f'> Gerado por `tests/uno/comandos.py` a partir de `ui/abas.json` em {date.today().isoformat()}. Não editar à mão.',
        '',
        '**Como ler as colunas**',
        '',
        '- **Implementação na base**: *Na base (comando verificado)* quer dizer que o comando existe no motor e o quadro do',
        '  Writer devolveu um despachante para ele no teste automático; não quer dizer que o botão já esteja na faixa do AY.',
        '  *Lacuna* quer dizer que não há comando pronto: o caminho previsto está na coluna de lacunas e dependências.',
        '- **Validado por**: teste automatizado que exercitou a função de ponta a ponta (via API, sem clicar no botão).',
        '  Vazio = ainda não validado.',
        '- **Faixa AY**: estado do botão na faixa de opções própria do AY. Na Etapa 1 as funções com comando da base estão acessíveis pelos',
        '  menus e pela faixa por abas da base; as lacunas não estão acessíveis. As abas AY, na ordem pedida, são a Etapa 3.',
        '- **Prioridade**: P0 = Etapas 1-2, P1 = Etapa 3, P2 = Etapa 4, P3 = avaliar.',
        '',
        '**Resumo**: ' + ' · '.join(f'{k}: {v}' for k, v in sorted(contagem.items())) + f' · Total: {len(res)}',
        '',
    ]
    aba_atual = None
    for r in res:
        if r['aba'] != aba_atual:
            aba_atual = r['aba']
            lin += ['', f'## {aba_atual}', '',
                    '| Grupo | Função | Comando da base | Rótulo na base | Implementação na base | Validado por | Faixa AY | Prioridade | Critério de aceite | Lacunas e dependências |',
                    '|---|---|---|---|---|---|---|---|---|---|']
        cel = lambda s: (s or '').replace('|', '\\|').replace('~', '')
        lin.append('| ' + ' | '.join([
            cel(r['grupo']), cel(r['funcao']), f'`{r["comando"]}`' if r['comando'] else '—', cel(r['rotuloBase']),
            situacao(r), cel(EVIDENCIA.get(r['comando'] or '', '')), 'Pendente (Etapa 3)', r['prioridade'],
            cel(r['criterio']), cel(r.get('lacuna', ''))]) + ' |')
    destino = RAIZ / 'docs' / 'MATRIZ-FUNCIONALIDADES.md'
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text('\n'.join(lin) + '\n', encoding='utf-8')
    print(f'Matriz gerada: {destino}')


if __name__ == '__main__':
    sys.exit(main())
