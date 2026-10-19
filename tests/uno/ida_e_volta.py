# -*- coding: utf-8 -*-
"""Teste de ida e volta (abrir -> salvar -> reabrir) com documentos representativos.

Para cada arquivo de entrada:
  1. abre no AY e faz o inventário estrutural (páginas, seções, tabelas, notas, comentários,
     alterações controladas, campos, imagens, formas, listas, equações, fontes) e exporta um PDF;
  2. salva como DOCX, como ODT e (se for DOC/RTF) no próprio formato; reabre cada cópia,
     refaz o inventário e exporta outro PDF;
  3. compara os inventários e grava as diferenças;
  4. aponta fontes usadas no documento que não existem no sistema (serão substituídas).

A comparação visual dos PDFs é feita depois por tools/comparar-pdf.mjs (veja scripts/testar.ps1).

Uso: python.exe ida_e_volta.py <pasta-saida> <arquivo1> [arquivo2 ...]
SPDX-License-Identifier: MPL-2.0
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, salvar, fechar, paginas, paginas_pdf  # noqa: E402

CLSID_MATH = '078b7aba-54fc-457f-8551-6147e776a997'


def enumerar(obj):
    e = obj.createEnumeration()
    while e.hasMoreElements():
        yield e.nextElement()


def prop(obj, nome, padrao=None):
    try:
        return obj.getPropertyValue(nome)
    except Exception:
        return padrao


def paragrafos(texto):
    """Percorre parágrafos do corpo, incluindo os de dentro das tabelas."""
    for el in enumerar(texto):
        if el.supportsService('com.sun.star.text.Paragraph'):
            yield el
        elif el.supportsService('com.sun.star.text.TextTable'):
            for nome in el.getCellNames():
                yield from paragrafos(el.getCellByName(nome).getText())


def inventario(motor, doc):
    inv = {'paginas': paginas(doc)}
    try:
        stats = {nv.Name: nv.Value for nv in doc.DocumentProperties.DocumentStatistics}
        inv['palavras'] = stats.get('WordCount')
        inv['caracteres'] = stats.get('CharacterCount')
    except Exception:
        pass
    texto_total = doc.Text.getString()
    inv['palavrasTexto'] = len(re.findall(r'\w+', texto_total))

    pars = list(paragrafos(doc.Text))
    inv['paragrafos'] = len(pars)
    estilos_pagina = [prop(p, 'PageDescName') for p in pars]
    inv['quebrasComEstiloDePagina'] = sum(1 for s in estilos_pagina if s)
    inv['estilosDePaginaUsados'] = sorted({s for s in estilos_pagina if s} | {prop(pars[0], 'PageStyleName')} if pars else set())
    inv['secoesDeTexto'] = doc.TextSections.Count
    inv['tabelas'] = doc.TextTables.Count
    inv['imagens'] = doc.GraphicObjects.Count
    inv['quadros'] = doc.TextFrames.Count
    inv['objetosDesenho'] = doc.DrawPage.Count
    inv['notasRodape'] = doc.Footnotes.Count
    inv['notasFim'] = doc.Endnotes.Count
    campos = list(enumerar(doc.TextFields))
    inv['comentarios'] = sum(1 for f in campos if f.supportsService('com.sun.star.text.textfield.Annotation'))
    tipos_campo = Counter(next((s.split('.')[-1] for s in f.getSupportedServiceNames()
                                if s.startswith('com.sun.star.text.textfield.') or s.startswith('com.sun.star.text.TextField.')), '?')
                          for f in campos)
    inv['campos'] = dict(sorted(tipos_campo.items()))
    redlines = list(doc.Redlines) if hasattr(doc, 'Redlines') else []
    inv['alteracoesControladas'] = dict(Counter(prop(r, 'RedlineType', '?') for r in enumerar(doc.Redlines))) if redlines is not None else {}
    inv['autoresAlteracoes'] = sorted({prop(r, 'RedlineAuthor', '') for r in enumerar(doc.Redlines)})
    inv['indices'] = doc.DocumentIndexes.Count
    inv['indicadores'] = len([n for n in doc.Bookmarks.getElementNames() if not n.startswith('_Toc')])
    inv['itensDeLista'] = sum(1 for p in pars if prop(p, 'NumberingIsNumber') and prop(p, 'NumberingStyleName', '') != '' or prop(p, 'ListId', ''))
    inv['titulos'] = sum(1 for p in pars if (prop(p, 'OutlineLevel', 0) or 0) > 0)
    objs = [doc.EmbeddedObjects.getByName(n) for n in doc.EmbeddedObjects.getElementNames()]
    inv['equacoes'] = sum(1 for o in objs if str(prop(o, 'CLSID', '')).lower() == CLSID_MATH)
    links = set()
    fontes = Counter()
    for p in pars:
        for porcao in enumerar(p):
            u = prop(porcao, 'HyperLinkURL', '')
            if u:
                links.add(u)
            if porcao.getString().strip():
                fontes[prop(porcao, 'CharFontName', '')] += 1
    inv['hiperlinks'] = sorted(links)
    inv['fontesUsadas'] = sorted(f for f in fontes if f)

    # Cabeçalho/rodapé do estilo de página da primeira página
    try:
        ep = doc.StyleFamilies.getByName('PageStyles').getByName(prop(pars[0], 'PageStyleName'))
        inv['cabecalho'] = ep.HeaderText.getString().strip() if ep.HeaderIsOn else ''
        if ep.HeaderIsOn and not prop(ep, 'FirstIsShared', True):
            inv['cabecalhoPrimeiraPagina'] = ep.HeaderTextFirst.getString().strip()
        inv['rodapeTemCampoPagina'] = bool(ep.FooterIsOn) and any(
            f.supportsService('com.sun.star.text.TextField.PageNumber') for f in enumerar(ep.FooterText.createEnumeration().nextElement()) if hasattr(f, 'supportsService')) or 'PageNumber' in inv['campos']
    except Exception as e:  # noqa: BLE001
        inv['cabecalhoErro'] = str(e)
    inv['_palavras'] = Counter(re.findall(r'\w+', texto_total.lower()))
    return inv


def fontes_disponiveis(motor):
    tk = motor.servico('com.sun.star.awt.Toolkit')
    dev = tk.createScreenCompatibleDevice(1, 1)
    return {fd.Name for fd in dev.getFontDescriptors()}


IGNORAR = {'_palavras', 'palavras', 'caracteres'}


def comparar(a, b):
    difs = {}
    for k in sorted(set(a) | set(b)):
        if k in IGNORAR:
            continue
        if a.get(k) != b.get(k):
            difs[k] = {'antes': a.get(k), 'depois': b.get(k)}
    pa, pb = a['_palavras'], b['_palavras']
    faltando = pa - pb
    sobrando = pb - pa
    if faltando or sobrando:
        difs['texto'] = {'palavrasPerdidas': sum(faltando.values()), 'palavrasNovas': sum(sobrando.values()),
                         'exemplosPerdidas': [w for w, _ in faltando.most_common(8)],
                         'exemplosNovas': [w for w, _ in sobrando.most_common(8)]}
    return difs


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    saida = Path(sys.argv[1])
    entradas = [Path(a) for a in sys.argv[2:]]
    saida.mkdir(parents=True, exist_ok=True)
    relatorio = {'documentos': []}
    falhas = 0
    with Motor('idaevolta') as motor:
        disponiveis = fontes_disponiveis(motor)
        for entrada in entradas:
            nome = entrada.stem + '-' + entrada.suffix[1:]
            print(f'\n=== {entrada.name}', flush=True)
            reg = {'arquivo': entrada.name, 'rodadas': []}
            try:
                doc = motor.abrir(entrada)
            except Exception as e:  # noqa: BLE001
                reg['erroAoAbrir'] = str(e)
                relatorio['documentos'].append(reg)
                falhas += 1
                print(f'  FALHA ao abrir: {e}')
                continue
            inv0 = inventario(motor, doc)
            pdf0 = salvar(doc, saida / f'{nome}.original.pdf')
            reg['inventario'] = {k: v for k, v in inv0.items() if not k.startswith('_')}
            reg['pdf'] = pdf0.name
            reg['paginasPdf'] = paginas_pdf(pdf0)
            # "A;B" é lista de alternativas: o motor usa a primeira disponível
            reg['fontesAusentes'] = [f for f in inv0['fontesUsadas']
                                     if not any(p.strip() in disponiveis for p in f.split(';'))]
            reg['fontesComAlternativa'] = [f for f in inv0['fontesUsadas'] if ';' in f and f.split(';')[0].strip() not in disponiveis
                                           and any(p.strip() in disponiveis for p in f.split(';')[1:])]
            formatos = ['.docx', '.odt']
            if entrada.suffix.lower() in ('.doc', '.rtf'):
                formatos.append(entrada.suffix.lower())
            copias = []
            for fmt in formatos:
                copias.append(salvar(doc, saida / f'{nome}.salvo{fmt}'))
            fechar(doc)
            for copia in copias:
                doc = motor.abrir(copia)
                inv1 = inventario(motor, doc)
                pdf1 = salvar(doc, saida / f'{copia.name}.pdf')
                fechar(doc)
                difs = comparar(inv0, inv1)
                reg['rodadas'].append({'formato': copia.suffix, 'arquivo': copia.name, 'pdf': pdf1.name, 'diferencas': difs})
                estado = 'sem diferenças estruturais' if not difs else 'diferenças: ' + ', '.join(difs)
                print(f'  {copia.suffix:6} {estado}', flush=True)
            print(f'  fontes ausentes no sistema: {reg["fontesAusentes"] or "nenhuma"}')
            relatorio['documentos'].append(reg)
    (saida / 'ida-e-volta.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
