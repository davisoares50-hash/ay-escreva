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
import time
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
            cmd = item['comando'] or item.get('comandoAY')
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
                    resultados.append({'aba': aba['rotulo'], 'rotuloAba': aba['rotulo'], 'grupo': grupo['rotulo'], **item,
                                       'rotuloBase': rot, 'registrado': reg, 'despacho': desp})
        despachante = motor.servico('com.sun.star.frame.DispatchHelper')
        for aba in abas['contextuais']:
            previa = aba.get('id') == 'previa'
            if previa:
                # Os comandos da visualização de impressão só existem com o documento nessa vista
                despachante.executeDispatch(frame, '.uno:PrintPreview', '', 0, ())
                time.sleep(2)
            for item in aba['itens']:
                rot, reg, desp = verificar(item)
                resultados.append({'aba': aba['rotulo'] + ' (contextual)', 'rotuloAba': aba['rotulo'], 'grupo': '', **item,
                                   'rotuloBase': rot, 'registrado': reg, 'despacho': desp})
            if previa:
                despachante.executeDispatch(frame, '.uno:ClosePreview', '', 0, ())
                time.sleep(1)
        fechar(doc)

    SAIDA_TESTES.mkdir(parents=True, exist_ok=True)
    (SAIDA_TESTES / 'comandos.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding='utf-8')
    gerar_matriz(resultados)

    com_cmd = [r for r in resultados if r['comando'] or r.get('comandoAY')]
    ok = [r for r in com_cmd if r['despacho']]
    falhos = [r for r in com_cmd if not r['despacho']]
    print(f'Funções: {len(resultados)} | com comando: {len(com_cmd)} | encontrados: {len(ok)} | '
          f'não encontrados: {len(falhos)} | pendentes sem comando: {len(resultados) - len(com_cmd)}')
    for r in falhos:
        print(f'  NÃO ENCONTRADO: {r["aba"]} / {r["funcao"]} -> {r["comando"] or r.get("comandoAY")}')
    return 1 if falhos else 0


def _carregar(caminho):
    try:
        return json.loads(caminho.read_text(encoding='utf-8-sig'))
    except Exception:
        return None


def niveis(r, mapa, faixa):
    """Três níveis pedidos: comando encontrado / funcionalidade implementada / funcionamento validado."""
    cmd = r['comando'] or r.get('comandoAY')
    chave = f"{r['rotuloAba']} › {r['funcao']}"
    t = (faixa or {}).get('funcoes', {}).get(chave, {})
    if not cmd:
        encontrado = '—'
    elif r['despacho']:
        encontrado = 'Sim (extensão AY)' if not r['comando'] else 'Sim'
    else:
        encontrado = 'Não'
    no_mapa = any(b['comando'] == cmd and b['rotuloAba'] == r['rotuloAba'] for b in (mapa or {}).get('botoes', []))
    if not cmd:
        impl = 'Não — pendente'
    elif r.get('botao') is False:
        impl = f"Sim, por outro controle ({r.get('via', '')})"
    elif no_mapa and t.get('presente'):
        impl = 'Sim — botão na faixa (confirmado pela interface)'
    elif no_mapa:
        impl = 'Sim — botão na faixa (presença não confirmada pelo teste)'
    else:
        impl = 'Não — fora da faixa'
    val = []
    if t.get('validado'):
        val.append('Pela interface: ' + '; '.join(d for d in t.get('detalhes', []) if not d.startswith(('na aba', 'clique na faixa', 'aba contextual')))[:160])
    elif t.get('acionado'):
        det = next((d for d in t.get('detalhes', []) if d.startswith('abriu')), '')
        val.append('Acionado pela interface' + (f': {det}' if det else '') + ' (efeito não conferido)')
    if EVIDENCIA.get(r['comando'] or ''):
        val.append('Por API: ' + EVIDENCIA[r['comando']])
    return encontrado, impl, ' · '.join(val) or 'Não validado'


def gerar_matriz(res):
    mapa = _carregar(RAIZ / 'out' / 'faixa' / 'mapa.json')
    faixa = _carregar(SAIDA_TESTES / 'interface' / 'faixa-resultado.json')
    linhas_n = [(r, *niveis(r, mapa, faixa)) for r in res]
    tot = len(res)
    n_enc = sum(1 for _, e, _i, _v in linhas_n if e.startswith('Sim'))
    n_impl = sum(1 for _, _e, i, _v in linhas_n if i.startswith('Sim'))
    n_conf = sum(1 for _, _e, i, _v in linhas_n if 'confirmado pela interface' in i)
    n_val_ui = sum(1 for _, _e, _i, v in linhas_n if v.startswith('Pela interface'))
    n_acion = sum(1 for _, _e, _i, v in linhas_n if v.startswith('Acionado'))
    n_val_api = sum(1 for _, _e, _i, v in linhas_n if 'Por API' in v)
    n_pend = sum(1 for _, _e, i, _v in linhas_n if i.startswith('Não'))
    teste_ui = f"teste pela interface de {faixa.get('inicio', '?')}" if faixa else 'teste pela interface ainda não executado'
    lin = [
        '# Matriz de funcionalidades do AY ESCREVA',
        '',
        f'> Gerado por `tests/uno/comandos.py` a partir de `ui/abas.json`, do mapa da faixa e do {teste_ui}, em {date.today().isoformat()}. Não editar à mão.',
        '',
        '**Como ler as colunas**',
        '',
        '- **Comando encontrado**: o comando existe no motor (o quadro do Writer devolveu um despachante, ou há controlador de menu) — verificado em `tests/uno/comandos.py`. Não diz nada sobre botão.',
        '- **Funcionalidade implementada**: há um botão na faixa de opções do AY ligado a esse comando (ou a função é oferecida por outro controle, indicado). *Confirmado pela interface* = o teste dentro do aplicativo encontrou o botão na aba (`tests/interface`).',
        '- **Funcionamento validado**: *Pela interface* = o teste clicou no botão da faixa, confirmou o comando disparado e conferiu o efeito no documento ou na exibição. *Acionado pela interface* = o clique disparou o comando certo (e o diálogo/lista que abriu foi registrado), mas o efeito não tem verificação automática. *Por API* = a função foi exercitada de ponta a ponta pelos testes de documento, sem clicar no botão.',
        '- **Prioridade**: P0 = Etapas 1-2, P1 = Etapa 3, P2 = Etapa 4, P3 = avaliar.',
        '',
        f'**Resumo** ({tot} funções): comando encontrado {n_enc} · implementadas {n_impl} (botão confirmado pela interface: {n_conf}) · validadas pela interface {n_val_ui} · só acionadas pela interface {n_acion} · validadas por API {n_val_api} · pendentes {n_pend}',
        '',
    ]
    aba_atual = None
    cel = lambda s: (s or '').replace('|', '\\|').replace('~', '')
    for r, enc, impl, val in linhas_n:
        if r['aba'] != aba_atual:
            aba_atual = r['aba']
            lin += ['', f'## {aba_atual}', '',
                    '| Grupo | Função | Comando | Comando encontrado | Funcionalidade implementada | Funcionamento validado | Prioridade | Critério de aceite | Pendências e observações |',
                    '|---|---|---|---|---|---|---|---|---|']
        cmd = r['comando'] or r.get('comandoAY')
        lin.append('| ' + ' | '.join([
            cel(r['grupo']), cel(r['funcao']), f'`{cmd}`' if cmd else '—', enc, cel(impl), cel(val), r['prioridade'],
            cel(r['criterio']), cel(r.get('lacuna', ''))]) + ' |')
    destino = RAIZ / 'docs' / 'MATRIZ-FUNCIONALIDADES.md'
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(chr(10).join(lin) + chr(10), encoding='utf-8')
    print(f'Matriz gerada: {destino}')
    print(f'  encontrados {n_enc} · implementadas {n_impl} (confirmadas {n_conf}) · validadas UI {n_val_ui} · acionadas {n_acion} · API {n_val_api} · pendentes {n_pend}')


if __name__ == '__main__':
    sys.exit(main())
