# -*- coding: utf-8 -*-
"""Galeria de modelos (entrega B, 0.4.0).

  1. cada modelo cria um documento novo, sem título, sem alterações pendentes e sem histórico de desfazer;
  2. ofício e memorando: padrão ofício do Manual de Redação da Presidência da República (margens, fonte, recuo,
     espaço entre parágrafos, parágrafos numerados, cabeçalho só na primeira página, número no rodapé a partir da 2ª);
  3. campos de preenchimento presentes; data por extenso no formato do Manual;
  4. salvar em DOCX e ODT e reabrir: margens, estilos, número de página e textos de preenchimento preservados;
  5. salvar como modelo (pasta pessoal), listar, criar documento a partir dele, nomes inválidos e remoção.

Uso: "dist\\AY ESCREVA\\program\\python.exe" tests\\uno\\modelos.py
SPDX-License-Identifier: MPL-2.0
"""
import json
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ay_uno import Motor, RAIZ, SAIDA_TESTES, props, salvar, fechar  # noqa: E402

sys.path.insert(0, str(RAIZ / 'extensao' / 'ayescreva' / 'pythonpath'))
import ay_modelos as M  # noqa: E402

SAIDA = SAIDA_TESTES / 'modelos'
itens = []


def verificar(descricao, ok, detalhe=''):
    itens.append({'ok': bool(ok), 'verificacao': descricao, 'detalhe': str(detalhe)})
    print(f"[{'OK  ' if ok else 'FALHA'}] {descricao}{' — ' + str(detalhe) if detalhe else ''}", flush=True)


def pars(xtexto):
    e = xtexto.createEnumeration()
    while e.hasMoreElements():
        o = e.nextElement()
        if o.supportsService('com.sun.star.text.Paragraph'):
            yield o


def campos(doc):
    """Campos de preenchimento (controles de conteúdo mostrando o texto reservado) no corpo do documento."""
    n = 0
    for p in pars(doc.getText()):
        e = p.createEnumeration()
        while e.hasMoreElements():
            por = e.nextElement()
            if por.TextPortionType == 'ContentControl' and por.ContentControl.ShowingPlaceHolder:
                n += 1
    return n


def texto_total(doc):
    return '\n'.join(p.getString() for p in pars(doc.getText()))


def margens(doc, estilo):
    s = doc.getStyleFamilies().getByName('PageStyles').getByName(estilo)
    return s, (s.LeftMargin, s.RightMargin, s.TopMargin)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    with Motor('modelos') as mo:
        oculto = props(Hidden=True)
        for m in M.MODELOS:
            d = M.criar(mo.ctx, m['id'], extra=oculto)
            um = d.getUndoManager()
            n = campos(d)
            verificar(f'{m["nome"]}: documento novo sem título, sem alterações pendentes, sem histórico de desfazer e com campos',
                      d.getURL() == '' and not d.isModified() and not um.isUndoPossible() and n >= 3, f'{n} campos de preenchimento')
            for ext in ('docx', 'odt'):
                arq = salvar(d, SAIDA / f'{m["id"]}.{ext}')
                d2 = mo.abrir(arq)
                t1, t2 = texto_total(d), texto_total(d2)
                pagina1 = d.getText().createEnumeration().nextElement().PageStyleName
                s1 = d.getStyleFamilies().getByName('PageStyles').getByName(pagina1)
                pg2 = d2.getText().createEnumeration().nextElement().PageStyleName
                s2 = d2.getStyleFamilies().getByName('PageStyles').getByName(pg2)
                mesmo_texto = [x for x in t1.split('\n') if x.strip()] == [x for x in t2.split('\n') if x.strip()]
                mesmas_margens = (abs(s1.LeftMargin - s2.LeftMargin) < 30 and abs(s1.RightMargin - s2.RightMargin) < 30)
                verificar(f'{m["nome"]}: {ext.upper()} salvo e reaberto com o mesmo texto (inclusive o dos campos) e as mesmas margens',
                          mesmo_texto and mesmas_margens, f'campos depois: {campos(d2)}; margens {s2.LeftMargin}/{s2.RightMargin}')
                fechar(d2)
            if m['id'] == 'oficio':
                conferir_oficio(mo, d)
            salvar(d, SAIDA / f'{m["id"]}.pdf')
            fechar(d)
        pessoais(mo)
    Path(SAIDA / 'resultado.json').write_text(json.dumps({'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Galeria de modelos: {sum(1 for x in itens if x["ok"])}/{len(itens)}')


def conferir_oficio(mo, d):
    fam = d.getStyleFamilies().getByName('ParagraphStyles')
    ps = d.getStyleFamilies().getByName('PageStyles')
    p1, seg = ps.getByName('AY Padrão ofício (1ª página)'), ps.getByName('AY Padrão ofício')
    fonte = fam.getByName('Standard').CharFontName
    tx = fam.getByName('Ofício — texto')
    verificar('Ofício: margens esquerda 3 cm, direita 1,5 cm, superior e inferior 2 cm; A4',
              all(abs(a - b) <= 10 for a, b in zip((p1.LeftMargin, p1.RightMargin, p1.TopMargin, p1.BottomMargin, p1.Width, p1.Height,
                                                    seg.LeftMargin, seg.RightMargin), (3000, 1500, 2000, 2000, 21000, 29700, 3000, 1500))),
              (p1.LeftMargin, p1.RightMargin, p1.TopMargin, p1.BottomMargin))
    verificar('Ofício: Calibri ou Carlito 12; texto justificado, entrelinhas simples, 6 pt depois, recuo de 2,5 cm',
              fonte in ('Calibri', 'Carlito') and fam.getByName('Standard').CharHeight == 12.0
              and fam.getByName('Ofício — texto').ParaAdjust == 2 and fam.getByName('Ofício — texto').ParaLineSpacing.Height == 100
              and abs(fam.getByName('Ofício — texto').ParaBottomMargin - M.pt(6)) < 5 and abs(fam.getByName('Ofício — texto').ParaFirstLineIndent - 2500) <= 10,
              (fonte, tx.ParaAdjust, tx.ParaLineSpacing.Mode, tx.ParaLineSpacing.Height, tx.ParaBottomMargin, tx.ParaFirstLineIndent))
    verificar('Ofício: citação 11 pt e nota de rodapé 10 pt', fam.getByName('Ofício — citação').CharHeight == 11.0 and fam.getByName('Footnote').CharHeight == 10.0)
    rotulos = [p.ListLabelString for p in pars(d.getText()) if p.ParaStyleName == 'Ofício — texto numerado']
    verificar('Ofício: três parágrafos de texto numerados 1, 2, 3 (sem numerar vocativo e fecho)', rotulos == ['1', '2', '3'], rotulos)
    cab = p1.HeaderText.getString()
    verificar('Ofício: cabeçalho só na primeira página (brasão, órgão, setor), com 5 cm a partir da borda; rodapé com número a partir da 2ª',
              p1.HeaderIsOn and not seg.HeaderIsOn and p1.TopMargin + p1.HeaderHeight == 5000 and seg.FooterIsOn and not p1.FooterIsOn
              and p1.FollowStyle == 'AY Padrão ofício', f'cabeçalho: {cab!r}; altura {p1.HeaderHeight}')
    data = M.data_extenso()
    t = texto_total(d)
    verificar('Ofício: identificação "OFÍCIO Nº …/ano/…", local e data por extenso, "Assunto:" em negrito e fecho',
              'OFÍCIO Nº [número]/' in t and f', {data}.' in t and 'Assunto: ' in t and '[Atenciosamente,]' in t
              and fam.getByName('Ofício — assunto').CharWeight == 150.0, data)
    import datetime
    verificar('Data por extenso: "1º" no primeiro dia do mês e sem zero à esquerda nos demais',
              M.data_extenso(datetime.date(2026, 3, 1)) == '1º de março de 2026' and M.data_extenso(datetime.date(2026, 2, 2)) == '2 de fevereiro de 2026')


def pessoais(mo):
    d = mo.novo()
    d.getText().setString('Modelo pessoal de teste com acentuação: ação, coração.')
    caminho = M.salvar_como_modelo(mo.ctx, d, 'Meu modelo de teste')
    lista = M.pessoais(mo.ctx)
    verificar('Salvar como modelo: grava .ott na pasta pessoal e aparece na lista; o documento aberto continua o mesmo',
              os.path.exists(caminho) and ('Meu modelo de teste', caminho) in lista and d.getURL() == '', caminho)
    try:
        M.salvar_como_modelo(mo.ctx, d, 'Meu modelo de teste')
        repetido = False
    except FileExistsError:
        repetido = True
    invalidos = []
    for nome in ('', 'a/b', 'nome:ruim', '..oculto', 'x' * 81):
        try:
            M.salvar_como_modelo(mo.ctx, d, nome)
        except ValueError:
            invalidos.append(nome[:10])
    verificar('Salvar como modelo: não sobrescreve sem confirmação e recusa nomes inválidos', repetido and len(invalidos) == 5, invalidos)
    novo = M.criar_de_pessoal(mo.ctx, caminho, extra=props(Hidden=True))
    verificar('Modelo pessoal: cria documento sem título com o conteúdo do modelo',
              novo.getURL() == '' and 'coração' in novo.getText().getString())
    fechar(novo)
    fechar(d)
    with zipfile.ZipFile(caminho) as z:
        tipo = z.read('mimetype').decode()
    verificar('Modelo pessoal gravado como modelo ODT', tipo == 'application/vnd.oasis.opendocument.text-template', tipo)
    try:
        M.remover_pessoal(mo.ctx, str(SAIDA / 'qualquer.ott'))
        fora = False
    except ValueError:
        fora = True
    M.remover_pessoal(mo.ctx, caminho)
    verificar('Remover modelo pessoal: só dentro da pasta pessoal; o arquivo sai da lista', fora and not os.path.exists(caminho) and not M.pessoais(mo.ctx))


if __name__ == '__main__':
    main()
