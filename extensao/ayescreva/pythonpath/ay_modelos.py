# -*- coding: utf-8 -*-
"""Galeria de modelos (entrega B): documentos montados pelo próprio AY, com estilos reais e campos de preenchimento.

- Modelo é aparência e estrutura; formato é como o arquivo é gravado (ODT ou DOCX, escolhido ao salvar).
- Todo modelo cria um documento novo, sem título: o documento aberto nunca muda.
- Ofício e memorando seguem o padrão ofício do Manual de Redação da Presidência da República (3ª ed., 2018, item 5);
  os demais não têm norma oficial e são marcados como "modelo de uso comum".
- "Salvar como modelo" grava um modelo ODT (.ott) na pasta de modelos do perfil do usuário ($(user)/template/AY).
SPDX-License-Identifier: MPL-2.0
"""
import datetime
import os
import re

import uno

MESES = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro')
ESQ, DIR, JUST, CENTRO = 0, 1, 2, 3


def cm(v):
    return int(round(v * 1000))


def pt(v):
    return int(round(v * 2540 / 72))


def data_extenso(d=None):
    """Data no formato do Manual de Redação: '1º de março de 2026', '2 de fevereiro de 2026' (sem zero à esquerda)."""
    d = d or datetime.date.today()
    dia = '1º' if d.day == 1 else str(d.day)
    return f'{dia} de {MESES[d.month - 1]} de {d.year}'


def _pv(**kw):
    r = []
    for k, v in kw.items():
        p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        p.Name, p.Value = k, v
        r.append(p)
    return tuple(r)


def fontes_instaladas(ctx):
    try:
        tk = ctx.getServiceManager().createInstanceWithContext('com.sun.star.awt.Toolkit', ctx)
        dev = tk.createScreenCompatibleDevice(1, 1)
        return {f.Name for f in dev.getFontDescriptors()}
    except Exception:
        return set()


class Construtor:
    """Monta um documento: estilos de parágrafo e de página, parágrafos com campos de preenchimento e tabelas."""

    def __init__(self, ctx, doc, fonte, tamanho=12.0):
        self.ctx, self.doc = ctx, doc
        self.texto = doc.getText()
        self.cur = self.texto.createTextCursor()
        self.primeiro = True
        self.fonte, self.tamanho = fonte, tamanho
        fam = doc.getStyleFamilies().getByName('ParagraphStyles')
        for n in ('Standard',):
            s = fam.getByName(n)
            s.CharFontName, s.CharHeight = fonte, float(tamanho)
            s.CharFontNameAsian = s.CharFontNameComplex = fonte
        for n in ('Heading', 'Title', 'Subtitle', 'Header', 'Footer', 'Table Contents', 'Footnote'):
            if fam.hasByName(n):
                fam.getByName(n).CharFontName = fonte

    def estilo(self, nome, pai='Standard', **props):
        fam = self.doc.getStyleFamilies().getByName('ParagraphStyles')
        if not fam.hasByName(nome):
            s = self.doc.createInstance('com.sun.star.style.ParagraphStyle')
            fam.insertByName(nome, s)
            fam.getByName(nome).setParentStyle(pai)
        s = fam.getByName(nome)
        for k, v in props.items():
            if k == 'ParaLineSpacing':
                ls = uno.createUnoStruct('com.sun.star.style.LineSpacing')
                ls.Mode, ls.Height = 0, int(round(v * 100))
                v = ls
            if k == 'CharPosture':
                v = uno.Enum('com.sun.star.awt.FontSlant', 'ITALIC' if v else 'NONE')
            s.setPropertyValue(k, v)
        return s

    def lista_numerada(self, nome, recuo_cm):
        """Número na margem e o texto da primeira linha no recuo (tabulação), sem ponto: '1  Texto' (exemplos do Manual)."""
        fam = self.doc.getStyleFamilies().getByName('NumberingStyles')
        if not fam.hasByName(nome):
            fam.insertByName(nome, self.doc.createInstance('com.sun.star.style.NumberingStyle'))
        s = fam.getByName(nome)
        regras = s.NumberingRules
        nivel = {p.Name: p.Value for p in regras.getByIndex(0)}
        nivel.update(NumberingType=4, Suffix='', Prefix='', ListFormat='%1%', PositionAndSpaceMode=1, LabelFollowedBy=0,
                     IndentAt=0, FirstLineIndent=0, ListtabStopPosition=cm(recuo_cm))
        pvs = []
        for k, v in nivel.items():
            p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
            p.Name, p.Value = k, v
            pvs.append(p)
        uno.invoke(regras, 'replaceByIndex', (0, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(pvs))))
        s.NumberingRules = regras
        return nome

    def pagina(self, nome, margens, seguinte=None, cabecalho_cm=None, rodape_numero=False, numero_alinhamento=CENTRO):
        fam = self.doc.getStyleFamilies().getByName('PageStyles')
        if not fam.hasByName(nome):
            s = self.doc.createInstance('com.sun.star.style.PageStyle')
            s.Width, s.Height = cm(21.0), cm(29.7)
            fam.insertByName(nome, s)
        s = fam.getByName(nome)
        s.LeftMargin, s.RightMargin = cm(margens['esquerda']), cm(margens['direita'])
        s.TopMargin, s.BottomMargin = cm(margens['superior']), cm(margens['inferior'])
        if cabecalho_cm:
            s.HeaderIsOn = True
            s.HeaderIsDynamicHeight = False
            s.HeaderBodyDistance = cm(0.3)
            s.HeaderHeight = cm(cabecalho_cm - margens['superior'])
        if rodape_numero:
            # número dentro da área de rodapé (nos 2 cm da margem inferior): margem menor + rodapé de altura fixa
            s.BottomMargin = cm(0.8)
            s.FooterIsOn = True
            s.FooterIsDynamicHeight = False
            s.FooterBodyDistance = cm(0.4)
            s.FooterHeight = cm(margens['inferior'] - 0.8)
            ft = s.FooterText
            ft.setString('')
            c = ft.createTextCursor()
            c.setPropertyValue('ParaStyleName', 'Footer')
            c.setPropertyValue('ParaAdjust', numero_alinhamento)
            campo = self.doc.createInstance('com.sun.star.text.TextField.PageNumber')
            campo.NumberingType = 4
            campo.SubType = uno.Enum('com.sun.star.text.PageNumberType', 'CURRENT')
            ft.insertTextContent(c, campo, False)
        if seguinte:
            s.FollowStyle = seguinte
        return s

    def par(self, partes, estilo='Standard', **direto):
        """partes: texto, ou lista de texto e ('campo', 'texto exibido', 'dica')."""
        if not self.primeiro:
            self.texto.insertControlCharacter(self.cur, 0, False)
        self.primeiro = False
        self.cur.setPropertyValue('ParaStyleName', estilo)
        for k, v in direto.items():
            self.cur.setPropertyValue(k, v)
        for p in ([partes] if isinstance(partes, (str, tuple)) else partes):
            if isinstance(p, tuple):
                self.campo(p[1], p[2] if len(p) > 2 else '')
            else:
                self.texto.insertString(self.cur, p, False)
        return self

    def campo(self, exibido, dica=''):
        controle(self.doc, self.texto, self.cur, exibido, dica)

    def tabela(self, linhas, larguras=None):
        self.texto.insertControlCharacter(self.cur, 0, False)
        t = self.doc.createInstance('com.sun.star.text.TextTable')
        t.initialize(len(linhas), len(linhas[0]))
        self.texto.insertTextContent(self.cur, t, False)
        for i, lin in enumerate(linhas):
            for j, val in enumerate(lin):
                cel = t.getCellByPosition(j, i)
                if isinstance(val, tuple):
                    controle(self.doc, cel, cel.createTextCursor(), val[1], val[2] if len(val) > 2 else '')
                else:
                    cel.setString(val)
                if i == 0:
                    for par in _pars(cel):
                        par.CharWeight = 150.0
        self.cur.gotoEnd(False)
        self.primeiro = True
        return t

    def quebra_pagina_estilo(self, estilo_pagina):
        self.cur.setPropertyValue('PageDescName', estilo_pagina)


def controle(doc, xtexto, cur, exibido, dica=''):
    """Campo de preenchimento como controle de conteúdo: mostra o texto entre colchetes, um clique o seleciona e o que for
    digitado o substitui. No DOCX vira o espaço reservado do Word (w:sdt); o JumpEdit do motor some ao salvar em DOCX."""
    cur.gotoEndOfParagraph(False)
    inicio = cur.getEnd()
    xtexto.insertString(cur, exibido, False)
    sel = xtexto.createTextCursorByRange(inicio)
    sel.gotoEndOfParagraph(True)
    cc = doc.createInstance('com.sun.star.text.ContentControl')
    cc.ShowingPlaceHolder = True
    if dica:
        cc.Alias = dica
    xtexto.insertTextContent(sel, cc, True)
    cur.gotoEndOfParagraph(False)


def _pars(xtexto):
    e = xtexto.createEnumeration()
    while e.hasMoreElements():
        yield e.nextElement()


# ---------------------------------------------------------------- modelos
def _fonte_oficio(ctx):
    instaladas = fontes_instaladas(ctx)
    return 'Calibri' if 'Calibri' in instaladas else 'Carlito'


def _padrao_oficio(ctx, doc, tipo):
    """Padrão ofício (Manual de Redação da Presidência da República, 3ª ed., 2018, itens 5.1 e 5.2)."""
    fonte = _fonte_oficio(ctx)
    b = Construtor(ctx, doc, fonte, 12)
    margens = {'superior': 2.0, 'inferior': 2.0, 'esquerda': 3.0, 'direita': 1.5}
    b.pagina('AY Padrão ofício', margens, rodape_numero=True)
    b.pagina('AY Padrão ofício (1ª página)', margens, seguinte='AY Padrão ofício', cabecalho_cm=5.0)
    simples = dict(ParaLineSpacing=1.0)
    b.estilo('Ofício — identificação', ParaAdjust=ESQ, ParaTopMargin=pt(6), ParaBottomMargin=pt(6), **simples)
    b.estilo('Ofício — local e data', ParaAdjust=DIR, ParaBottomMargin=pt(12), **simples)
    b.estilo('Ofício — endereçamento', ParaAdjust=ESQ, **simples)
    b.estilo('Ofício — assunto', ParaAdjust=ESQ, CharWeight=150.0, ParaTopMargin=pt(12), ParaBottomMargin=pt(12), **simples)
    b.estilo('Ofício — vocativo', ParaAdjust=ESQ, ParaFirstLineIndent=cm(2.5), ParaBottomMargin=pt(6), **simples)
    b.estilo('Ofício — texto', ParaAdjust=JUST, ParaFirstLineIndent=cm(2.5), ParaBottomMargin=pt(6), **simples)
    lista = b.lista_numerada('Ofício — parágrafos numerados', 2.5)
    b.estilo('Ofício — texto numerado', pai='Ofício — texto', NumberingStyleName=lista, ParaFirstLineIndent=0)
    b.estilo('Ofício — citação', pai='Ofício — texto', CharHeight=11.0, ParaLeftMargin=cm(4.0), ParaFirstLineIndent=0)
    b.estilo('Ofício — fecho', ParaAdjust=ESQ, ParaFirstLineIndent=cm(2.5), ParaBottomMargin=pt(6), **simples)
    b.estilo('Ofício — signatário', ParaAdjust=CENTRO, CharWeight=100.0, **simples)
    b.estilo('Ofício — cargo', ParaAdjust=CENTRO, **simples)
    fam = doc.getStyleFamilies().getByName('ParagraphStyles')
    fam.getByName('Footnote').CharHeight = 10.0
    fam.getByName('Footer').CharFontName = fonte
    # cabeçalho só na primeira página, centralizado, entrelinhas simples
    p1 = doc.getStyleFamilies().getByName('PageStyles').getByName('AY Padrão ofício (1ª página)')
    ht = p1.HeaderText
    c = ht.createTextCursor()
    c.ParaAdjust = CENTRO
    for k, (exib, dica) in enumerate((('[Brasão de Armas da República]', 'Insira o brasão (Inserir › Imagem). Não use marca da instituição.'),
                                      ('[Nome do órgão]', 'Órgão principal'),
                                      ('[Secretaria/Departamento/Setor]', 'Órgãos secundários, da maior para a menor hierarquia, separados por barra'))):
        c.gotoEnd(False)
        if k:
            ht.insertControlCharacter(c, 0, False)
        controle(doc, ht, c, exib, dica)
    b.cur.setPropertyValue('PageDescName', 'AY Padrão ofício (1ª página)')
    ano = datetime.date.today().year
    nome = 'OFÍCIO' if tipo == 'oficio' else 'MEMORANDO'
    b.par([f'{nome} Nº ', ('campo', '[número]', 'Número do expediente'), f'/{ano}/', ('campo', '[SIGLA DO SETOR]', 'Siglas do setor que expede, da menor para a maior hierarquia, separadas por barra')],
          'Ofício — identificação')
    b.par([('campo', '[Cidade]', 'Cidade onde o documento é expedido, sem a sigla do estado'), f', {data_extenso()}.'], 'Ofício — local e data')
    if tipo == 'oficio':
        b.par([('campo', '[A Sua Excelência o Senhor]', 'Vossa Excelência: "A Sua Excelência o Senhor"; Vossa Senhoria: "Ao Senhor" ou "À Senhora"')], 'Ofício — endereçamento')
        b.par([('campo', '[Nome]', 'Nome do destinatário')], 'Ofício — endereçamento')
        b.par([('campo', '[Cargo]', 'Cargo do destinatário')], 'Ofício — endereçamento')
        b.par([('campo', '[Endereço]', 'Localidade e logradouro (ou setor, se for no mesmo órgão)')], 'Ofício — endereçamento')
        b.par([('campo', '[CEP]', 'CEP'), ' ', ('campo', '[Cidade/UF]', 'Cidade e unidade da federação')], 'Ofício — endereçamento')
    else:
        b.par([('campo', '[Ao Senhor]', '"Ao Senhor" ou "À Senhora"')], 'Ofício — endereçamento')
        b.par([('campo', '[Nome]', 'Nome do destinatário')], 'Ofício — endereçamento')
        b.par([('campo', '[Cargo]', 'Cargo do destinatário')], 'Ofício — endereçamento')
        b.par([('campo', '[Unidade administrativa]', 'Setor de destino')], 'Ofício — endereçamento')
    b.par(['Assunto: ', ('campo', '[Descrição do assunto em quatro ou cinco palavras]', 'Sem verbo; inicial maiúscula'), '.'], 'Ofício — assunto')
    b.par(['Senhor ', ('campo', '[Cargo]', 'Vocativo: "Senhor" ou "Senhora" seguido do cargo'), ','], 'Ofício — vocativo')
    b.par([('campo', '[Introdução: o objetivo da comunicação. Prefira a forma direta: Informo, Solicito, Comunico.]', 'Introdução')], 'Ofício — texto numerado')
    b.par([('campo', '[Desenvolvimento: detalhe o assunto; uma ideia por parágrafo.]', 'Desenvolvimento')], 'Ofício — texto numerado')
    b.par([('campo', '[Conclusão: a posição sobre o assunto.]', 'Conclusão')], 'Ofício — texto numerado')
    b.par([('campo', '[Atenciosamente,]', '"Respeitosamente," para autoridade de hierarquia superior; "Atenciosamente," nos demais casos')], 'Ofício — fecho')
    b.par('', 'Ofício — signatário')
    b.par('', 'Ofício — signatário')
    b.par([('campo', '[NOME DO SIGNATÁRIO]', 'Nome em maiúsculas, sem negrito e sem linha acima')], 'Ofício — signatário')
    b.par([('campo', '[Cargo do signatário]', 'Só as iniciais maiúsculas; preposições em minúsculas')], 'Ofício — cargo')
    return doc


def _carta(ctx, doc, tipo):
    fonte = _fonte_oficio(ctx)
    b = Construtor(ctx, doc, fonte, 11)
    b.pagina('AY Carta', {'superior': 2.5, 'inferior': 2.5, 'esquerda': 2.5, 'direita': 2.5})
    b.estilo('Carta — remetente', ParaAdjust=ESQ, ParaLineSpacing=1.0, CharHeight=10.0)
    b.estilo('Carta — local e data', ParaAdjust=DIR, ParaTopMargin=pt(18), ParaBottomMargin=pt(18), ParaLineSpacing=1.0)
    b.estilo('Carta — destinatário', ParaAdjust=ESQ, ParaLineSpacing=1.0)
    b.estilo('Carta — texto', ParaAdjust=JUST, ParaBottomMargin=pt(10), ParaLineSpacing=1.15)
    b.estilo('Carta — assinatura', ParaAdjust=ESQ, ParaLineSpacing=1.0)
    b.cur.setPropertyValue('PageDescName', 'AY Carta')
    b.par([('campo', '[Seu nome ou empresa]', 'Remetente')], 'Carta — remetente')
    b.par([('campo', '[Endereço · telefone · e-mail]', 'Contato do remetente')], 'Carta — remetente')
    b.par([('campo', '[Cidade]', 'Cidade'), f', {data_extenso()}.'], 'Carta — local e data')
    b.par([('campo', '[Nome do destinatário]', 'Destinatário')], 'Carta — destinatário')
    b.par([('campo', '[Cargo e empresa]', 'Cargo e empresa')], 'Carta — destinatário')
    b.par([('campo', '[Endereço]', 'Endereço')], 'Carta — destinatário')
    b.par(['Prezado(a) ', ('campo', '[Nome]', 'Saudação'), ','], 'Carta — texto', ParaTopMargin=pt(18))
    b.par([('campo', '[Primeiro parágrafo: o motivo da carta.]', 'Motivo')], 'Carta — texto')
    b.par([('campo', '[Segundo parágrafo: os detalhes.]', 'Detalhes')], 'Carta — texto')
    b.par([('campo', '[Último parágrafo: o que você espera do destinatário.]', 'Pedido ou encerramento')], 'Carta — texto')
    b.par('Atenciosamente,', 'Carta — texto')
    b.par('', 'Carta — assinatura')
    b.par([('campo', '[Seu nome]', 'Nome de quem assina')], 'Carta — assinatura')
    b.par([('campo', '[Cargo]', 'Cargo')], 'Carta — assinatura')
    return doc


def _ata(ctx, doc, tipo):
    fonte = _fonte_oficio(ctx)
    b = Construtor(ctx, doc, fonte, 12)
    b.pagina('AY Ata', {'superior': 2.5, 'inferior': 2.0, 'esquerda': 3.0, 'direita': 2.0}, rodape_numero=True)
    b.estilo('Ata — título', ParaAdjust=CENTRO, CharWeight=150.0, ParaBottomMargin=pt(12), ParaLineSpacing=1.0)
    b.estilo('Ata — dados', ParaAdjust=ESQ, ParaLineSpacing=1.0, ParaBottomMargin=pt(3))
    b.estilo('Ata — seção', ParaAdjust=ESQ, CharWeight=150.0, ParaTopMargin=pt(12), ParaBottomMargin=pt(6), ParaLineSpacing=1.0)
    b.estilo('Ata — texto', ParaAdjust=JUST, ParaLineSpacing=1.15, ParaBottomMargin=pt(6))
    b.estilo('Ata — assinatura', ParaAdjust=CENTRO, ParaTopMargin=pt(30), ParaLineSpacing=1.0)
    b.cur.setPropertyValue('PageDescName', 'AY Ata')
    b.par(['ATA DA ', ('campo', '[Nª]', 'Número da reunião'), ' REUNIÃO ', ('campo', '[ORDINÁRIA]', 'Ordinária ou extraordinária'),
           ' DE ', ('campo', '[ÓRGÃO, EQUIPE OU COLEGIADO]', 'Quem se reuniu')], 'Ata — título')
    b.par(['Data: ', ('campo', '[dd/mm/aaaa]', 'Data'), ' · Horário: ', ('campo', '[hh:mm]', 'Início'), ' às ', ('campo', '[hh:mm]', 'Término')], 'Ata — dados')
    b.par(['Local: ', ('campo', '[local ou plataforma]', 'Local')], 'Ata — dados')
    b.par(['Presentes: ', ('campo', '[nomes e funções]', 'Participantes')], 'Ata — dados')
    b.par(['Ausências justificadas: ', ('campo', '[nomes ou "nenhuma"]', 'Ausências')], 'Ata — dados')
    b.par('Pauta', 'Ata — seção')
    b.par(['1. ', ('campo', '[primeiro item]', 'Item da pauta')], 'Ata — texto')
    b.par(['2. ', ('campo', '[segundo item]', 'Item da pauta')], 'Ata — texto')
    b.par('Discussões', 'Ata — seção')
    b.par([('campo', '[Resumo do que foi discutido em cada item, sem juízo de valor.]', 'Discussões')], 'Ata — texto')
    b.par('Deliberações e encaminhamentos', 'Ata — seção')
    b.tabela([('Item', 'Decisão', 'Responsável', 'Prazo'),
              ('1', ('campo', '[decisão]'), ('campo', '[nome]'), ('campo', '[dd/mm]')),
              ('2', ('campo', '[decisão]'), ('campo', '[nome]'), ('campo', '[dd/mm]'))])
    b.par('Encerramento', 'Ata — seção')
    b.par(['Nada mais havendo a tratar, a reunião foi encerrada às ', ('campo', '[hh:mm]', 'Hora do encerramento'),
           ', e eu, ', ('campo', '[nome de quem redigiu]', 'Secretário(a) da reunião'),
           ', lavrei a presente ata, que, lida e aprovada, vai assinada por mim e pelos presentes.'], 'Ata — texto')
    b.par([('campo', '[Nome — função]', 'Assinatura')], 'Ata — assinatura')
    b.par([('campo', '[Nome — função]', 'Assinatura')], 'Ata — assinatura')
    return doc


def _curriculo(ctx, doc, tipo):
    fonte = _fonte_oficio(ctx)
    b = Construtor(ctx, doc, fonte, 11)
    b.pagina('AY Currículo', {'superior': 2.0, 'inferior': 2.0, 'esquerda': 2.0, 'direita': 2.0})
    b.estilo('Currículo — nome', ParaAdjust=ESQ, CharHeight=20.0, CharWeight=150.0, ParaLineSpacing=1.0)
    b.estilo('Currículo — contato', ParaAdjust=ESQ, CharHeight=10.0, ParaBottomMargin=pt(10), ParaLineSpacing=1.0)
    b.estilo('Currículo — seção', ParaAdjust=ESQ, CharHeight=12.0, CharWeight=150.0, CharCaseMap=1, ParaTopMargin=pt(12),
             ParaBottomMargin=pt(4), ParaLineSpacing=1.0, OutlineLevel=1)
    b.estilo('Currículo — item', ParaAdjust=ESQ, CharWeight=150.0, ParaTopMargin=pt(4), ParaLineSpacing=1.0)
    b.estilo('Currículo — texto', ParaAdjust=JUST, ParaBottomMargin=pt(3), ParaLineSpacing=1.1)
    b.cur.setPropertyValue('PageDescName', 'AY Currículo')
    b.par([('campo', '[Seu nome completo]', 'Nome')], 'Currículo — nome')
    b.par([('campo', '[Cidade/UF]', 'Cidade'), ' · ', ('campo', '[telefone]', 'Telefone'), ' · ', ('campo', '[e-mail]', 'E-mail'),
           ' · ', ('campo', '[portfólio ou perfil profissional]', 'Link (opcional)')], 'Currículo — contato')
    b.par('Resumo profissional', 'Currículo — seção')
    b.par([('campo', '[Três ou quatro linhas sobre sua experiência e o que você procura.]', 'Resumo')], 'Currículo — texto')
    b.par('Experiência profissional', 'Currículo — seção')
    b.par([('campo', '[Cargo]', 'Cargo'), ' — ', ('campo', '[Empresa]', 'Empresa'), ' (', ('campo', '[mês/ano]', 'Início'), ' a ',
           ('campo', '[mês/ano ou atual]', 'Fim'), ')'], 'Currículo — item')
    b.par([('campo', '[Principais resultados, com números quando possível.]', 'Resultados')], 'Currículo — texto')
    b.par('Formação', 'Currículo — seção')
    b.par([('campo', '[Curso]', 'Curso'), ' — ', ('campo', '[Instituição]', 'Instituição'), ' (', ('campo', '[ano de conclusão]', 'Ano'), ')'], 'Currículo — item')
    b.par('Cursos e certificações', 'Currículo — seção')
    b.par([('campo', '[Curso — instituição (ano)]', 'Curso')], 'Currículo — texto')
    b.par('Idiomas', 'Currículo — seção')
    b.par([('campo', '[Idioma — nível]', 'Idioma')], 'Currículo — texto')
    b.par('Competências', 'Currículo — seção')
    b.par([('campo', '[Competências técnicas e ferramentas]', 'Competências')], 'Currículo — texto')
    return doc


def _proposta(ctx, doc, tipo):
    fonte = _fonte_oficio(ctx)
    b = Construtor(ctx, doc, fonte, 11)
    b.pagina('AY Proposta', {'superior': 2.5, 'inferior': 2.0, 'esquerda': 2.5, 'direita': 2.0}, rodape_numero=True, numero_alinhamento=DIR)
    b.estilo('Proposta — título', ParaAdjust=ESQ, CharHeight=16.0, CharWeight=150.0, ParaBottomMargin=pt(6), ParaLineSpacing=1.0)
    b.estilo('Proposta — dados', ParaAdjust=ESQ, ParaLineSpacing=1.0, ParaBottomMargin=pt(2))
    b.estilo('Proposta — texto', ParaAdjust=JUST, ParaLineSpacing=1.15, ParaBottomMargin=pt(6))
    fam = doc.getStyleFamilies().getByName('ParagraphStyles')
    for n, tam in (('Heading 1', 13.0),):
        h = fam.getByName(n)
        h.CharFontName, h.CharHeight, h.CharWeight = fonte, tam, 150.0
    _numeracao_titulos(doc)
    b.cur.setPropertyValue('PageDescName', 'AY Proposta')
    b.par(['PROPOSTA ', ('campo', '[COMERCIAL OU TÉCNICA]', 'Tipo da proposta'), ' Nº ', ('campo', '[número]', 'Número'),
           f'/{datetime.date.today().year}'], 'Proposta — título')
    b.par(['Para: ', ('campo', '[cliente]', 'Cliente')], 'Proposta — dados')
    b.par(['Data: ', datetime.date.today().strftime('%d/%m/%Y')], 'Proposta — dados')
    b.par(['Validade: ', ('campo', '[30]', 'Dias de validade'), ' dias'], 'Proposta — dados')
    for t, campo in (('Objeto', '[O que será fornecido, em uma frase.]'), ('Escopo', '[O que está incluído e o que não está.]'),
                     ('Prazo e cronograma', '[Etapas e datas.]')):
        b.par(t, 'Heading 1')
        b.par([('campo', campo, t)], 'Proposta — texto')
    b.par('Investimento', 'Heading 1')
    b.tabela([('Item', 'Descrição', 'Qtd.', 'Valor unitário', 'Total'),
              ('1', ('campo', '[descrição]'), ('campo', '[1]'), ('campo', '[R$ 0,00]'), ('campo', '[R$ 0,00]')),
              ('', 'Total geral', '', '', ('campo', '[R$ 0,00]'))])
    for t, campo in (('Condições de pagamento', '[Forma e datas de pagamento.]'), ('Validade da proposta', '[Prazo e condições de reajuste.]')):
        b.par(t, 'Heading 1')
        b.par([('campo', campo, t)], 'Proposta — texto')
    b.par([('campo', '[Cidade]', 'Cidade'), f', {data_extenso()}.'], 'Proposta — texto', ParaTopMargin=pt(18))
    b.par([('campo', '[Nome — cargo — empresa]', 'Quem assina')], 'Proposta — texto', ParaTopMargin=pt(30))
    return doc


def _relatorio(ctx, doc, tipo):
    fonte = _fonte_oficio(ctx)
    b = Construtor(ctx, doc, fonte, 12)
    b.pagina('AY Relatório', {'superior': 3.0, 'inferior': 2.0, 'esquerda': 3.0, 'direita': 2.0}, rodape_numero=True, numero_alinhamento=DIR)
    b.estilo('Relatório — título', ParaAdjust=CENTRO, CharHeight=14.0, CharWeight=150.0, ParaBottomMargin=pt(6), ParaLineSpacing=1.0)
    b.estilo('Relatório — subtítulo', ParaAdjust=CENTRO, ParaBottomMargin=pt(18), ParaLineSpacing=1.0)
    b.estilo('Relatório — texto', ParaAdjust=JUST, ParaLineSpacing=1.5, ParaFirstLineIndent=cm(1.25))
    fam = doc.getStyleFamilies().getByName('ParagraphStyles')
    h = fam.getByName('Heading 1')
    h.CharFontName, h.CharHeight, h.CharWeight = fonte, 12.0, 150.0
    _numeracao_titulos(doc)
    b.cur.setPropertyValue('PageDescName', 'AY Relatório')
    b.par(['RELATÓRIO DE ', ('campo', '[ATIVIDADES]', 'Tipo do relatório')], 'Relatório — título')
    b.par([('campo', '[Unidade ou projeto]', 'Unidade'), ' · ', ('campo', '[período]', 'Período coberto')], 'Relatório — subtítulo')
    for t, campo in (('Apresentação', '[Objetivo do relatório e período.]'), ('Atividades realizadas', '[O que foi feito.]')):
        b.par(t, 'Heading 1')
        b.par([('campo', campo, t)], 'Relatório — texto')
    b.par('Resultados', 'Heading 1')
    b.tabela([('Indicador', 'Meta', 'Resultado', 'Observação'),
              (('campo', '[indicador]'), ('campo', '[meta]'), ('campo', '[resultado]'), ('campo', '[observação]'))])
    for t, campo in (('Dificuldades e providências', '[O que atrapalhou e o que foi feito.]'), ('Próximos passos', '[O que vem a seguir.]')):
        b.par(t, 'Heading 1')
        b.par([('campo', campo, t)], 'Relatório — texto')
    b.par([('campo', '[Cidade]', 'Cidade'), f', {data_extenso()}.'], 'Relatório — texto', ParaTopMargin=pt(18))
    b.par([('campo', '[Nome — cargo]', 'Responsável')], 'Relatório — texto', ParaTopMargin=pt(30), ParaFirstLineIndent=0)
    return doc


def _numeracao_titulos(doc):
    regras = doc.getChapterNumberingRules()
    nivel = {p.Name: p.Value for p in regras.getByIndex(0)}
    nivel.update(NumberingType=4, Suffix='', Prefix='', ListFormat='%1%', LabelFollowedBy=1, PositionAndSpaceMode=1, IndentAt=0,
                 FirstLineIndent=0, HeadingStyleName='Heading 1')
    pvs = []
    for k, v in nivel.items():
        p = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        p.Name, p.Value = k, v
        pvs.append(p)
    uno.invoke(regras, 'replaceByIndex', (0, uno.Any('[]com.sun.star.beans.PropertyValue', tuple(pvs))))


SEM_NORMA = 'Modelo de uso comum: não há norma oficial para este documento. A aparência é preferência do AY.'
MODELOS = [
    {'id': 'oficio', 'nome': 'Ofício (padrão ofício)', 'montar': _padrao_oficio, 'camada': 'norma',
     'origem': 'Manual de Redação da Presidência da República, 3ª ed. (2018), itens 5.1 e 5.2',
     'descricao': 'Comunicação oficial: cabeçalho só na primeira página, identificação, local e data, endereçamento, assunto em '
                  'negrito, texto com parágrafos numerados (recuo de 2,5 cm, 6 pt depois), fecho e signatário centralizado. '
                  'Margens 3 cm (esquerda), 1,5 cm (direita) e 2 cm (superior e inferior); Calibri ou Carlito 12; número de '
                  'página a partir da segunda, centralizado no rodapé.'},
    {'id': 'memorando', 'nome': 'Memorando (padrão ofício)', 'montar': _padrao_oficio, 'camada': 'norma',
     'origem': 'Manual de Redação da Presidência da República, 3ª ed. (2018), item 5',
     'descricao': 'Atenção: na administração pública federal, a 3ª edição do Manual aboliu o memorando e o aviso; o termo '
                  '"ofício" vale para todas as comunicações. Use este modelo só onde o nome memorando ainda é usado (outros '
                  'órgãos ou empresas). A diagramação é a do padrão ofício, com endereçamento interno.'},
    {'id': 'relatorio', 'nome': 'Relatório (administrativo ou de atividades)', 'montar': _relatorio, 'camada': 'preferencia',
     'origem': 'Sem norma obrigatória: a NBR 10719:2025 trata do relatório técnico e/ou científico e é opcional para os demais',
     'descricao': 'Título, unidade e período, seções numeradas (apresentação, atividades, resultados com tabela, dificuldades, '
                  'próximos passos), local, data e assinatura. Para relatório técnico ou científico, use Referências › '
                  'Formatar trabalho acadêmico.'},
    {'id': 'curriculo', 'nome': 'Currículo', 'montar': _curriculo, 'camada': 'preferencia', 'origem': SEM_NORMA,
     'descricao': 'Nome, contato, resumo profissional, experiência, formação, cursos, idiomas e competências. Inclua só os dados '
                  'pessoais necessários para a vaga.'},
    {'id': 'carta', 'nome': 'Carta', 'montar': _carta, 'camada': 'preferencia', 'origem': SEM_NORMA,
     'descricao': 'Remetente, local e data, destinatário, saudação, três parágrafos, despedida e assinatura.'},
    {'id': 'ata', 'nome': 'Ata de reunião', 'montar': _ata, 'camada': 'preferencia',
     'origem': SEM_NORMA + ' Atas de condomínios, sociedades e órgãos colegiados seguem a lei, o estatuto ou o regimento de cada um.',
     'descricao': 'Título, data, horário, local, presentes, pauta, discussões, tabela de deliberações (decisão, responsável, '
                  'prazo), encerramento e assinaturas.'},
    {'id': 'proposta', 'nome': 'Proposta comercial ou técnica', 'montar': _proposta, 'camada': 'preferencia', 'origem': SEM_NORMA,
     'descricao': 'Número, cliente, data, validade e seções numeradas: objeto, escopo, prazo, investimento (tabela), condições de '
                  'pagamento e validade.'},
]


def modelo(mid):
    return next(m for m in MODELOS if m['id'] == mid)


def criar(ctx, mid, extra=()):
    """Cria um documento novo (sem título) a partir de um modelo do AY."""
    m = modelo(mid)
    desk = ctx.getServiceManager().createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    doc = desk.loadComponentFromURL('private:factory/swriter', '_blank', 0, tuple(extra))
    doc.lockControllers()
    try:
        m['montar'](ctx, doc, mid)
        props = doc.getDocumentProperties()
        props.Title = m['nome']
    finally:
        doc.unlockControllers()
    um = doc.getUndoManager()
    try:
        um.clear()
    except Exception:
        pass
    doc.setModified(False)
    return doc


# ---------------------------------------------------------------- modelos pessoais
def pasta_pessoal(ctx):
    subst = ctx.getServiceManager().createInstanceWithContext('com.sun.star.util.PathSubstitution', ctx)
    p = os.path.join(uno.fileUrlToSystemPath(subst.substituteVariables('$(user)/template', True)), 'AY')
    os.makedirs(p, exist_ok=True)
    return p


def pessoais(ctx):
    p = pasta_pessoal(ctx)
    return sorted((os.path.splitext(n)[0], os.path.join(p, n)) for n in os.listdir(p) if n.lower().endswith('.ott'))


def nome_valido(nome):
    nome = ' '.join(nome.split()).strip()
    if not nome or len(nome) > 80 or re.search(r'[\\/:*?"<>|]', nome) or nome.startswith('.'):
        return None
    return nome


def salvar_como_modelo(ctx, doc, nome, substituir=False):
    """Grava o documento como modelo ODT (.ott) na pasta pessoal; o documento aberto continua o mesmo."""
    n = nome_valido(nome)
    if n is None:
        raise ValueError('nome inválido: use até 80 caracteres, sem \\ / : * ? " < > |')
    caminho = os.path.join(pasta_pessoal(ctx), n + '.ott')
    if os.path.exists(caminho) and not substituir:
        raise FileExistsError(caminho)
    doc.storeToURL(uno.systemPathToFileUrl(caminho), _pv(FilterName='writer8_template', Overwrite=True))
    return caminho


def criar_de_pessoal(ctx, caminho, extra=()):
    desk = ctx.getServiceManager().createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    return desk.loadComponentFromURL(uno.systemPathToFileUrl(caminho), '_blank', 0, _pv(AsTemplate=True) + tuple(extra))


def remover_pessoal(ctx, caminho):
    pasta = os.path.realpath(pasta_pessoal(ctx))
    if os.path.dirname(os.path.realpath(caminho)) != pasta or not caminho.lower().endswith('.ott'):
        raise ValueError('só modelos da pasta pessoal do AY podem ser removidos')
    os.remove(caminho)
