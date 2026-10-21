# -*- coding: utf-8 -*-
"""Diálogos de "Formatar trabalho acadêmico": opções, prévia, relatório de conformidade e modelo da instituição.

O motor (sem interface) está em ay_academico.py. Tudo roda na thread principal.
SPDX-License-Identifier: MPL-2.0
"""
import json
import os
import traceback

import uno

import ay_academico as A
import ay_dialogos as D

NO_CONFIG = '/br.ayescreva.Configuracao/Academico'
PERFIS = ('trabalho', 'projeto', 'artigo', 'relatorio', 'instituicao')
FONTES = ('Times New Roman', 'Arial', 'Liberation Serif', 'Liberation Sans', 'Carlito', 'Calibri')
ALINHAMENTOS = (('justificado', 'Justificado'), ('esquerda', 'À esquerda'))
registrar = print            # trocado pelo registro da extensão em ayescreva.py


# ---------------------------------------------------------------- configuração
def _config(ctx, escrita=False):
    prov = D.servico(ctx, 'com.sun.star.configuration.ConfigurationProvider')
    pv = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
    pv.Name, pv.Value = 'nodepath', NO_CONFIG
    tipo = 'com.sun.star.configuration.ConfigurationUpdateAccess' if escrita else 'com.sun.star.configuration.ConfigurationAccess'
    return prov.createInstanceWithArguments(tipo, (pv,))


def ler_config(ctx):
    c = _config(ctx)

    def js(nome, padrao):
        try:
            v = c.getPropertyValue(nome)
            return json.loads(v) if v else padrao
        except Exception:
            return padrao
    return {'perfil': c.getPropertyValue('Perfil') or 'trabalho', 'opcoes': js('Opcoes', {}), 'instituicao': js('Instituicao', None)}


def gravar_config(ctx, **kw):
    c = _config(ctx, escrita=True)
    mapa = {'perfil': 'Perfil'}
    for k, v in kw.items():
        if k in ('opcoes', 'instituicao'):
            c.setPropertyValue('Opcoes' if k == 'opcoes' else 'Instituicao', json.dumps(v, ensure_ascii=False) if v else '')
        else:
            c.setPropertyValue(mapa[k], v)
    c.commitChanges()


def instituicao_valida(dados):
    """Modelo da instituição vindo de arquivo é dado, não instrução: só chaves e tipos conhecidos passam."""
    if not isinstance(dados, dict):
        raise ValueError('o arquivo não tem um modelo da instituição')
    base = dados.get('base', 'trabalho')
    if base not in ('trabalho', 'projeto', 'artigo', 'relatorio'):
        raise ValueError('perfil base desconhecido')
    man = dados.get('manual') or {}
    r = {'nome': str(dados.get('nome', ''))[:200], 'base': base,
         'manual': {k: str(man.get(k, ''))[:500] for k in ('titulo', 'edicao', 'url', 'arquivo') if man.get(k)}, 'parametros': {}}
    numeros = {'fonte_tamanho': (10, 14), 'fonte_menor_tamanho': (8, 11), 'entrelinhas': (1.0, 2.0), 'recuo_paragrafo_cm': (0, 5)}
    for k, v in (dados.get('parametros') or {}).items():
        if k in numeros:
            if isinstance(v, (int, float)) and not isinstance(v, bool) and numeros[k][0] <= v <= numeros[k][1]:
                r['parametros'][k] = v
        elif k == 'fonte_familia' and isinstance(v, str) and 0 < len(v) <= 80:
            r['parametros'][k] = v
        elif k == 'alinhamento' and v in ('justificado', 'esquerda'):
            r['parametros'][k] = v
        elif k == 'ponto_apos_indicativo' and isinstance(v, bool):
            r['parametros'][k] = v
        elif k == 'margens_cm' and isinstance(v, dict):
            m = {n: float(v[n]) for n in ('superior', 'esquerda', 'inferior', 'direita')
                 if isinstance(v.get(n), (int, float)) and not isinstance(v.get(n), bool) and 0.5 <= v[n] <= 6}
            if m:
                r['parametros'][k] = m
    return r


def _nome_perfil(pid, inst):
    d = A.dados_perfis()['perfis']
    if pid == 'instituicao':
        return 'Modelo da instituição — ' + (inst['nome'] if inst and inst.get('nome') else 'ainda não definido')
    return f'{d[pid]["nome"]} — {A.rotulo_norma(d[pid]["norma"])}'


NOTA_COPIA = ('A formatação é feita numa cópia sem título, aberta numa janela nova: o documento aberto, as alterações ainda '
              'não salvas e o histórico de desfazer não mudam. Na cópia, Ctrl+Z desfaz a formatação inteira.')


def _janela(frame):
    return frame.getContainerWindow()


# ---------------------------------------------------------------- diálogo principal
def formatar(ctx, frame):
    """Comando ayescreva:FormatarTrabalho."""
    doc = frame.getController().getModel()
    cfg = ler_config(ctx)
    base = A.dados_perfis()['parametros_base']
    while True:
        escolha = _dialogo_formatar(ctx, frame, cfg, base)
        if escolha is None:
            return
        acao, cfg = escolha
        gravar_config(ctx, perfil=cfg['perfil'], opcoes=cfg['opcoes'])
        if acao == 'instituicao':
            nova = editar_instituicao(ctx, frame, cfg['instituicao'])
            if nova is not False:
                cfg['instituicao'] = nova
                gravar_config(ctx, instituicao=nova)
                if nova is None and cfg['perfil'] == 'instituicao':
                    cfg['perfil'] = 'trabalho'
            continue
        if cfg['perfil'] == 'instituicao' and not cfg['instituicao']:
            D.mensagem(ctx, _janela(frame), 'Modelo da instituição', 'Defina primeiro o modelo da instituição (botão "Modelo da instituição…").', 'WARNINGBOX')
            continue
        perfil = A.montar_perfil(cfg['perfil'], instituicao=cfg['instituicao'], opcoes=_opcoes_perfil(cfg))
        if acao == 'relatorio':
            relatorio(ctx, frame, doc, perfil)
            continue
        plano = A.planejar(doc, perfil, numeracao=cfg['opcoes'].get('numeracao'), inserir_sumario=cfg['opcoes'].get('sumario', True))
        if acao == 'previa':
            if not previa(ctx, frame, plano):
                continue
        _aplicar(ctx, frame, doc, perfil, cfg)
        return


def _opcoes_perfil(cfg):
    """Escolhas do diálogo que viram parâmetros do perfil (camada 'preferência', salvo se a instituição já define)."""
    o = cfg['opcoes']
    da_instituicao = set((cfg.get('instituicao') or {}).get('parametros', {})) if cfg['perfil'] == 'instituicao' else set()
    r = {}
    for k in ('fonte_familia', 'recuo_paragrafo_cm', 'alinhamento', 'fonte_menor_tamanho', 'frente_e_verso',
              'capa_fora_da_contagem', 'ficha_fora_da_contagem'):
        if k in o and k not in da_instituicao:          # o que a instituição define vale sobre a preferência
            r[k] = o[k]
    return r


def _dialogo_formatar(ctx, frame, cfg, base):
    dados = A.dados_perfis()['perfis']
    d = D.Dialogo(ctx, 'Formatar trabalho acadêmico', 330, 262, nome='formatar')
    d.rotulo('r_perfil', 6, 6, 80, '~Tipo de trabalho:')
    d.add('ListBox', 'perfil', 90, 6, 234, 14, Dropdown=True, LineCount=6,
          StringItemList=tuple(_nome_perfil(p, cfg['instituicao']) for p in PERFIS))
    d.add('FixedText', 'descricao', 6, 24, 318, 30, MultiLine=True)
    d.add('GroupBox', 'g_pref', 6, 56, 318, 52, Label='Preferências (a norma não define)')
    d.rotulo('r_fonte', 12, 68, 60, '~Fonte:')
    d.add('ComboBox', 'fonte', 76, 68, 100, 14, Dropdown=True, StringItemList=FONTES, LineCount=8)
    d.rotulo('r_alin', 186, 68, 56, '~Alinhamento:')
    d.add('ListBox', 'alinhamento', 244, 68, 74, 14, Dropdown=True, StringItemList=tuple(n for _, n in ALINHAMENTOS))
    d.rotulo('r_recuo', 12, 88, 90, 'Rec~uo da 1ª linha (cm):')
    d.add('NumericField', 'recuo', 104, 88, 44, 14, DecimalAccuracy=2, ValueMin=0.0, ValueMax=5.0, ValueStep=0.25, Spin=True, StrictFormat=True)
    d.rotulo('r_menor', 186, 88, 70, 'Letra ~menor (pt):')
    d.add('NumericField', 'menor', 258, 88, 40, 14, DecimalAccuracy=0, ValueMin=8.0, ValueMax=11.0, ValueStep=1.0, Spin=True, StrictFormat=True)
    d.add('GroupBox', 'g_imp', 6, 112, 318, 92, Label='Impressão, contagem de páginas e títulos')
    d.add('CheckBox', 'frente', 12, 124, 306, 12, Label='Frente e ~verso (margens espelhadas; seções primárias no anverso)')
    d.add('CheckBox', 'capa', 12, 137, 306, 12, Label='A primeira página é a ~capa (não entra na contagem)')
    d.add('CheckBox', 'ficha', 12, 150, 306, 12, Label='A página depois da folha de rosto é a fic~ha catalográfica (não entra na contagem)')
    d.rotulo('r_num', 12, 165, 90, '~Numeração dos títulos:')
    d.add('ListBox', 'numeracao', 104, 165, 214, 14, Dropdown=True,
          StringItemList=('Pelo documento (automática se não houver número digitado)', 'Automática (1, 1.1, 1.1.1)',
                          'Manter como está (número digitado)'))
    d.add('CheckBox', 'sumario', 12, 186, 306, 12, Label='Inserir ~sumário automático depois do título SUMÁRIO')
    d.add('FixedText', 'nota_copia', 6, 208, 318, 28, MultiLine=True, Label=NOTA_COPIA)
    estado = {'cfg': dict(cfg, opcoes=dict(cfg['opcoes']))}

    def ler():
        c = estado['cfg']
        o = c['opcoes']
        c['perfil'] = PERFIS[max(0, d.c('perfil').getSelectedItemPos())]
        o['fonte_familia'] = d.c('fonte').getText().strip() or base['fonte_familia']
        o['alinhamento'] = ALINHAMENTOS[max(0, d.c('alinhamento').getSelectedItemPos())][0]
        o['recuo_paragrafo_cm'] = round(d.m('recuo').Value, 2)
        o['fonte_menor_tamanho'] = int(d.m('menor').Value)
        o['frente_e_verso'] = d.m('frente').State == 1
        o['capa_fora_da_contagem'] = d.m('capa').State == 1
        o['ficha_fora_da_contagem'] = d.m('ficha').State == 1
        o['numeracao'] = (None, 'automatica', 'manter')[max(0, d.c('numeracao').getSelectedItemPos())]
        o['sumario'] = d.m('sumario').State == 1
        return c

    def descrever():
        c = ler()
        pid = c['perfil']
        if pid == 'instituicao':
            inst = c['instituicao']
            if inst:
                man = inst.get('manual') or {}
                t = (f'Modelo da instituição "{inst.get("nome", "")}" sobre o perfil {dados[inst["base"]]["nome"]}. '
                     + (f'Manual: {man.get("titulo", "")} {man.get("edicao", "")}. ' if man else 'Manual não informado. ')
                     + 'O relatório mostra onde a instituição diverge da norma.')
            else:
                t = 'Ainda não há modelo da instituição. Use "Modelo da instituição…" para informar o manual e o que ele pede.'
        else:
            t = dados[pid]['descricao']
        d.m('descricao').Label = t + f' Normas conferidas em {A._data_br(A.normas()["verificado_em"])}.'
        # o que a instituição define aparece no campo e fica bloqueado (vale sobre a preferência)
        par = (c['instituicao'] or {}).get('parametros', {}) if pid == 'instituicao' else {}
        for ctl, chave in (('fonte', 'fonte_familia'), ('alinhamento', 'alinhamento'), ('recuo', 'recuo_paragrafo_cm'),
                           ('menor', 'fonte_menor_tamanho')):
            d.m(ctl).Enabled = chave not in par
            if chave in par:
                if ctl == 'fonte':
                    d.c('fonte').setText(par[chave])
                elif ctl == 'alinhamento':
                    d.c('alinhamento').selectItemPos(0 if par[chave] == 'justificado' else 1, True)
                else:
                    d.m(ctl).Value = float(par[chave])

    def acao(nome):
        def f():
            d.fechar((nome, ler()))
        return f

    d.botao('instituicao', 6, 242, 82, 'Modelo da ~instituição…', acao('instituicao'))
    d.botao('previa', 92, 242, 56, '~Prévia…', acao('previa'))
    d.botao('relatorio', 152, 242, 60, 'Re~latório…', acao('relatorio'))
    d.botao('aplicar', 216, 242, 58, 'F~ormatar cópia', acao('aplicar'), padrao=True)
    d.botao('fechar', 278, 242, 46, 'F~echar', lambda: d.fechar(None))
    for nome in ('perfil', 'alinhamento', 'numeracao', 'frente', 'capa', 'ficha', 'sumario'):
        d.ao_mudar(nome, descrever)

    def iniciar():
        o = cfg['opcoes']
        d.c('perfil').selectItemPos(PERFIS.index(cfg['perfil']) if cfg['perfil'] in PERFIS else 0, True)
        d.c('fonte').setText(o.get('fonte_familia', base['fonte_familia']))
        d.c('alinhamento').selectItemPos(0 if o.get('alinhamento', base['alinhamento']) == 'justificado' else 1, True)
        d.m('recuo').Value = float(o.get('recuo_paragrafo_cm', base['recuo_paragrafo_cm']))
        d.m('menor').Value = float(o.get('fonte_menor_tamanho', base['fonte_menor_tamanho']))
        perfil_base = dados['projeto' if cfg['perfil'] == 'projeto' else 'trabalho']
        d.m('frente').State = 1 if o.get('frente_e_verso', base['frente_e_verso']) else 0
        d.m('capa').State = 1 if o.get('capa_fora_da_contagem', perfil_base['parametros'].get('capa_fora_da_contagem', base['capa_fora_da_contagem'])) else 0
        d.m('ficha').State = 1 if o.get('ficha_fora_da_contagem', base['ficha_fora_da_contagem']) else 0
        d.c('numeracao').selectItemPos({None: 0, 'automatica': 1, 'manter': 2}.get(o.get('numeracao'), 0), True)
        d.m('sumario').State = 1 if o.get('sumario', True) else 0
        descrever()
    return d.executar(_janela(frame), iniciar)


# ---------------------------------------------------------------- aplicar
def _aplicar(ctx, frame, doc, perfil, cfg):
    """Sempre numa cópia sem título: no motor, criar o número de página no cabeçalho apaga o histórico de desfazer, e o
    documento aberto (com suas alterações não salvas e seu histórico) não pode perder isso."""
    alvo = A.copia_sem_titulo(ctx, doc)
    if alvo is None:
        D.mensagem(ctx, _janela(frame), 'Formatar trabalho acadêmico', 'Não foi possível abrir a cópia.', 'ERRORBOX')
        return
    plano = A.planejar(alvo, perfil, numeracao=cfg['opcoes'].get('numeracao'), inserir_sumario=cfg['opcoes'].get('sumario', True))
    feito = A.aplicar(alvo, plano)
    registrar(f'formatar: {perfil["id"]}, {feito}')
    quadro = alvo.getCurrentController().getFrame()
    itens = A.conferir(alvo, perfil)
    seg = f'{feito["segundos"]:.1f}'.replace('.', ',')
    nota = (f'Cópia sem título formatada em {seg} s; o documento original não mudou. Na cópia, Ctrl+Z desfaz a formatação '
            'inteira e Ctrl+Y a refaz.')
    relatorio(ctx, quadro, alvo, perfil, itens=itens, nota=nota)


# ---------------------------------------------------------------- prévia
def previa(ctx, frame, plano):
    """Lista do que vai mudar; devolve True se o usuário escolher formatar a cópia."""
    perfil = plano.perfil
    d = D.Dialogo(ctx, 'Prévia — o que vai mudar', 420, 266, nome='previa')
    d.rotulo('r_mud', 6, 4, 408, '~Mudanças (de → para), na ordem em que são feitas. O texto do documento não muda:')
    linhas = [f'[{m.grupo}] {m.descricao}' for m in plano.mudancas]
    d.add('ListBox', 'mudancas', 6, 18, 408, 110, StringItemList=tuple(linhas), Border=1)
    d.rotulo('r_det', 6, 132, 408, 'Mudança ~escolhida, por inteiro, e de onde vem a regra:')
    d.add('Edit', 'detalhe', 6, 144, 408, 44, MultiLine=True, ReadOnly=True, VScroll=True, Border=1,
          Text='Escolha uma mudança na lista.')
    d.rotulo('r_av', 6, 192, 408, '~Avisos (pontos que o AY não muda):')
    d.add('Edit', 'avisos', 6, 204, 408, 40, MultiLine=True, ReadOnly=True, VScroll=True, Border=1,
          Text='\n'.join('• ' + a for a in plano.avisos) or 'Nenhum aviso.')
    d.botao('aplicar', 300, 248, 62, 'Formatar ~cópia', lambda: d.fechar(True), padrao=True)
    d.botao('voltar', 366, 248, 48, '~Voltar', lambda: d.fechar(False))

    def mostrar():
        i = d.c('mudancas').getSelectedItemPos()
        if i < 0:
            return
        m = plano.mudancas[i]
        r = perfil['regras'].get(m.regra) if m.regra else None
        d.m('detalhe').Text = (f'[{m.grupo}] {m.descricao}\n' + (f'Regra: {r["titulo"]}. {A.origem(r, perfil)}.' if r else
                               'Ajuste de estilo para as regras do perfil.') + (f' {m.detalhe}' if m.detalhe else ''))
    d.ao_mudar('mudancas', mostrar)

    def iniciar():
        if plano.mudancas:
            d.c('mudancas').selectItemPos(0, True)
            mostrar()
    return bool(d.executar(_janela(frame), iniciar))


# ---------------------------------------------------------------- relatório
def relatorio(ctx, frame, doc, perfil, itens=None, nota=''):
    analise = A.Analise(doc, perfil)
    itens = itens if itens is not None else A.conferir(doc, perfil, analise)
    d = D.Dialogo(ctx, 'Relatório de conformidade', 420, 276, nome='relatorio')
    topo = (nota + '\n' if nota else '') + A.cabecalho_relatorio(perfil, itens)
    d.add('FixedText', 'cabecalho', 6, 4, 408, 52, MultiLine=True, Label=topo)
    d.rotulo('r_itens', 6, 56, 408, 'Itens ~por grupo (✓ conforme, ✗ não conforme, ! aviso, ? não avaliado, – não se aplica, · preferência):')
    linhas, mapa = [], []
    for cid, rot, lista in A.agrupar(itens):
        if not lista:
            continue
        linhas.append(f'▸ {rot} ({len(lista)})')
        mapa.append(cid)
        for it in lista:
            linhas.append('    ' + A.linha_item(it))
            mapa.append(it)
    d.add('ListBox', 'itens', 6, 70, 408, 120, StringItemList=tuple(linhas), Border=1)
    d.rotulo('r_det', 6, 192, 100, '~Detalhe:')
    d.add('Edit', 'detalhe', 6, 204, 408, 48, MultiLine=True, ReadOnly=True, VScroll=True, Border=1)
    estado = {'local': 0}
    explica = {'verificada': 'Regras da norma que o AY confere no documento. O texto oficial das normas não foi consultado: cada item indica '
                             'o guia público de onde a regra foi tirada.',
               'instituicao': 'Regras do modelo da instituição que você informou. Quando diverge da norma, o item diz.',
               'preferencia': 'O que a norma não define (ou o que o perfil usa como preferência). Não conta como exigência.',
               'nao_avaliado': 'Itens que o AY não confere. Confira você com a norma e com o manual da instituição.',
               'nao_se_aplica': 'Regras sem objeto neste documento (por exemplo, sem notas de rodapé).'}

    def atual():
        i = d.c('itens').getSelectedItemPos()
        return mapa[i] if 0 <= i < len(mapa) else None

    def mostrar():
        x = atual()
        if x is None:
            return
        if isinstance(x, str):
            d.m('detalhe').Text = explica.get(x, '')
            d.m('ir').Enabled = False
        else:
            d.m('detalhe').Text = A.detalhe_item(x, perfil)
            d.m('ir').Enabled = bool(x.locais)
        estado['local'] = 0

    def ir():
        x = atual()
        if x is None or isinstance(x, str) or not x.locais:
            return
        try:
            A.ir_para(doc, analise, x.locais[estado['local'] % len(x.locais)])
        except Exception:
            registrar('relatório ir para: ' + traceback.format_exc())
        estado['local'] += 1

    def documento():
        desk = D.servico(ctx, 'com.sun.star.frame.Desktop')
        titulo = doc.getTitle() if hasattr(doc, 'getTitle') else ''
        A.documento_relatorio(desk, itens, perfil, nome_documento=titulo)
        d.fechar(None)

    d.botao('ir', 6, 256, 76, '~Ir para (próximo)', ir)
    d.botao('documento', 86, 256, 130, 'Criar documento com o relató~rio', documento)
    d.botao('fechar', 364, 256, 50, '~Fechar', lambda: d.fechar(None), padrao=True)
    d.ao_mudar('itens', mostrar)

    def iniciar():
        d.m('ir').Enabled = False
        if itens:
            d.c('itens').selectItemPos(0, True)
            mostrar()
    d.executar(_janela(frame), iniciar)


def relatorio_comando(ctx, frame):
    """Comando ayescreva:Conformidade: relatório com o último perfil escolhido."""
    cfg = ler_config(ctx)
    pid = cfg['perfil'] if cfg['perfil'] != 'instituicao' or cfg['instituicao'] else 'trabalho'
    perfil = A.montar_perfil(pid, instituicao=cfg['instituicao'], opcoes=_opcoes_perfil(cfg))
    relatorio(ctx, frame, frame.getController().getModel(), perfil)


# ---------------------------------------------------------------- modelo da instituição
ROTULOS_PARAM = {'fonte_familia': 'Fonte', 'fonte_tamanho': 'Tamanho da letra', 'entrelinhas': 'Entrelinhas', 'recuo_paragrafo_cm': 'Recuo da 1ª linha',
                 'fonte_menor_tamanho': 'Letra menor', 'alinhamento': 'Alinhamento', 'ponto_apos_indicativo': 'Ponto depois do número da seção',
                 'margens_cm': 'Margens'}


def _valor_txt(k, v):
    if k == 'margens_cm':
        return ', '.join(f'{n} {v[n]:g}' for n in ('superior', 'esquerda', 'inferior', 'direita')).replace('.', ',') + ' cm'
    if k == 'ponto_apos_indicativo':
        return 'sim' if v else 'não'
    if k == 'alinhamento':
        return dict(ALINHAMENTOS).get(v, v)
    if isinstance(v, float):
        return f'{v:g}'.replace('.', ',') + (' cm' if k.endswith('_cm') else '')
    return str(v) + (' pt' if k in ('fonte_tamanho', 'fonte_menor_tamanho') else '')


def diferencas_instituicao(inst):
    """Prévia do modelo da instituição: cada parâmetro que muda, o valor do perfil base e se diverge da norma."""
    ref = A.montar_perfil(inst.get('base', 'trabalho'))
    linhas = []
    for k, v in (inst.get('parametros') or {}).items():
        regras = [ref['regras'][r] for r in A.PARAM_REGRAS.get(k, [])]
        norma = next((r for r in regras if r['camada'] == 'norma'), None)
        nota = (f'diverge da norma ({A.rotulo_norma(norma["norma"])})' if norma else 'troca uma preferência (a norma não define)')
        linhas.append(f'{ROTULOS_PARAM.get(k, k)}: {_valor_txt(k, v)} (perfil base: {_valor_txt(k, ref["parametros"].get(k))}) — {nota}')
    return linhas


def editar_instituicao(ctx, frame, atual):
    """Devolve o novo modelo, None se removido, ou False se cancelado."""
    base_p = A.dados_perfis()['parametros_base']
    inst = atual or {'nome': '', 'base': 'trabalho', 'manual': {}, 'parametros': {}}
    par = inst.get('parametros', {})
    man = inst.get('manual', {})
    bases = ('trabalho', 'projeto', 'artigo', 'relatorio')
    d = D.Dialogo(ctx, 'Modelo da instituição', 330, 276, nome='instituicao')
    d.rotulo('r_nome', 6, 6, 100, '~Nome da instituição:')
    d.add('Edit', 'nome', 110, 6, 214, 14, Text=inst.get('nome', ''))
    d.rotulo('r_man', 6, 22, 100, 'Título do ~manual:')
    d.add('Edit', 'man_titulo', 110, 22, 214, 14, Text=man.get('titulo', ''))
    d.rotulo('r_ed', 6, 38, 100, '~Edição ou ano:')
    d.add('Edit', 'man_edicao', 110, 38, 60, 14, Text=man.get('edicao', ''))
    d.rotulo('r_base', 176, 38, 50, 'Perfil ~base:')
    d.add('ListBox', 'base', 228, 38, 96, 14, Dropdown=True,
          StringItemList=('Trabalho acadêmico', 'Projeto de pesquisa', 'Artigo', 'Relatório técnico'))
    d.rotulo('r_loc', 6, 54, 100, 'En~dereço ou arquivo:')
    d.add('Edit', 'man_local', 110, 54, 214, 14, Text=man.get('url') or man.get('arquivo', ''))
    d.botao('escolher', 110, 70, 100, 'Escolher ar~quivo…')
    d.botao('abrir', 214, 70, 110, 'Abrir o manual')
    d.add('GroupBox', 'g', 6, 88, 318, 110, Label='O que o manual pede (o que ele não mencionar fica como no perfil base)')
    d.rotulo('r_fonte', 12, 100, 80, '~Fonte:')
    d.add('ComboBox', 'fonte', 96, 100, 100, 14, Dropdown=True, StringItemList=FONTES, Text=par.get('fonte_familia', base_p['fonte_familia']))
    d.rotulo('r_tam', 204, 100, 60, '~Tamanho (pt):')
    d.add('NumericField', 'tamanho', 268, 100, 50, 14, DecimalAccuracy=0, ValueMin=10.0, ValueMax=14.0, Spin=True,
          Value=float(par.get('fonte_tamanho', base_p['fonte_tamanho'])))
    d.rotulo('r_ent', 12, 116, 80, 'Entre~linhas:')
    d.add('NumericField', 'entrelinhas', 96, 116, 50, 14, DecimalAccuracy=2, ValueMin=1.0, ValueMax=2.0, ValueStep=0.25, Spin=True,
          Value=float(par.get('entrelinhas', base_p['entrelinhas'])))
    d.rotulo('r_rec', 204, 116, 60, 'Rec~uo (cm):')
    d.add('NumericField', 'recuo', 268, 116, 50, 14, DecimalAccuracy=2, ValueMin=0.0, ValueMax=5.0, ValueStep=0.25, Spin=True,
          Value=float(par.get('recuo_paragrafo_cm', base_p['recuo_paragrafo_cm'])))
    d.rotulo('r_menor', 12, 132, 80, 'Letra menor (pt):')
    d.add('NumericField', 'menor', 96, 132, 50, 14, DecimalAccuracy=0, ValueMin=8.0, ValueMax=11.0, Spin=True,
          Value=float(par.get('fonte_menor_tamanho', base_p['fonte_menor_tamanho'])))
    d.rotulo('r_alin', 204, 132, 60, '~Alinhamento:')
    d.add('ListBox', 'alinhamento', 268, 132, 50, 14, Dropdown=True, StringItemList=tuple(n for _, n in ALINHAMENTOS))
    mg = dict(base_p['margens_cm'], **par.get('margens_cm', {}))
    for k, (rot, x, y) in {'superior': ('Margem superior (cm):', 12, 148), 'inferior': ('Margem inferior (cm):', 168, 148),
                           'esquerda': ('Margem esquerda (cm):', 12, 164), 'direita': ('Margem direita (cm):', 168, 164)}.items():
        d.rotulo('r_' + k, x, y, 84, rot)
        d.add('NumericField', 'm_' + k, x + 86, y, 50, 14, DecimalAccuracy=2, ValueMin=0.5, ValueMax=6.0, ValueStep=0.25, Spin=True, Value=float(mg[k]))
    d.add('CheckBox', 'ponto', 12, 182, 306, 12, Label='P~onto depois do número da seção (ex.: "1. INTRODUÇÃO"; a NBR 6024 não usa)',
          State=1 if par.get('ponto_apos_indicativo') else 0)
    d.rotulo('r_dif', 6, 200, 318, 'Pré~via: o que o modelo muda em relação ao perfil base (valores iguais não são gravados)')
    d.add('ListBox', 'diferencas', 6, 214, 318, 40, Border=1)

    def ler():
        b = bases[max(0, d.c('base').getSelectedItemPos())]
        ref = A.montar_perfil(b)['parametros']
        novo = {'nome': d.c('nome').getText().strip(), 'base': b, 'manual': {}, 'parametros': {}}
        if d.c('man_titulo').getText().strip():
            novo['manual']['titulo'] = d.c('man_titulo').getText().strip()
        if d.c('man_edicao').getText().strip():
            novo['manual']['edicao'] = d.c('man_edicao').getText().strip()
        loc = d.c('man_local').getText().strip()
        if loc:
            novo['manual']['url' if loc.lower().startswith(('http://', 'https://')) else 'arquivo'] = loc
        pr = novo['parametros']
        valores = {'fonte_familia': d.c('fonte').getText().strip(), 'fonte_tamanho': int(d.m('tamanho').Value),
                   'entrelinhas': round(d.m('entrelinhas').Value, 2), 'recuo_paragrafo_cm': round(d.m('recuo').Value, 2),
                   'fonte_menor_tamanho': int(d.m('menor').Value),
                   'alinhamento': ALINHAMENTOS[max(0, d.c('alinhamento').getSelectedItemPos())][0],
                   'ponto_apos_indicativo': d.m('ponto').State == 1}
        for k, v in valores.items():
            if v != ref.get(k) and v not in ('', None):
                pr[k] = v
        margens = {k: round(d.m('m_' + k).Value, 2) for k in ('superior', 'esquerda', 'inferior', 'direita')}
        if any(abs(margens[k] - ref['margens_cm'][k]) > 0.001 for k in margens):
            pr['margens_cm'] = margens
        return novo

    def escolher():
        fp = D.servico(ctx, 'com.sun.star.ui.dialogs.FilePicker')
        fp.initialize((0,))
        fp.appendFilter('PDF, documentos e páginas', '*.pdf;*.odt;*.docx;*.doc;*.htm;*.html')
        fp.appendFilter('Todos os arquivos', '*.*')
        if fp.execute() == 1:
            d.c('man_local').setText(uno.fileUrlToSystemPath(fp.getSelectedFiles()[0]))

    def abrir():
        loc = d.c('man_local').getText().strip()
        if not loc:
            return
        alvo = loc if loc.lower().startswith(('http://', 'https://')) else uno.systemPathToFileUrl(loc)
        if not loc.lower().startswith(('http://', 'https://')) and not os.path.exists(loc):
            D.mensagem(ctx, _janela(frame), 'Manual da instituição', 'Arquivo não encontrado: ' + loc, 'WARNINGBOX')
            return
        shell = D.servico(ctx, 'com.sun.star.system.SystemShellExecute')
        shell.execute(alvo, '', 1)

    def exportar():
        fp = D.servico(ctx, 'com.sun.star.ui.dialogs.FilePicker')
        fp.initialize((1,))
        fp.appendFilter('Modelo da instituição (JSON)', '*.json')
        fp.setDefaultName('modelo-instituicao.json')
        if fp.execute() == 1:
            caminho = uno.fileUrlToSystemPath(fp.getSelectedFiles()[0])
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(ler(), f, ensure_ascii=False, indent=1)

    def importar():
        fp = D.servico(ctx, 'com.sun.star.ui.dialogs.FilePicker')
        fp.initialize((0,))
        fp.appendFilter('Modelo da instituição (JSON)', '*.json')
        if fp.execute() == 1:
            try:
                with open(uno.fileUrlToSystemPath(fp.getSelectedFiles()[0]), encoding='utf-8') as f:
                    dados = instituicao_valida(json.load(f))
                d.fechar(('importado', dados))
            except Exception as e:
                D.mensagem(ctx, _janela(frame), 'Importar modelo', f'O arquivo não é um modelo da instituição válido ({e}).', 'WARNINGBOX')

    def previa_dif():
        d.m('diferencas').StringItemList = tuple(diferencas_instituicao(ler())) or ('Nenhuma diferença: o modelo segue o perfil base.',)

    d.botao('salvar', 6, 258, 52, '~Salvar', lambda: d.fechar(('salvar', ler())), padrao=True)
    d.botao('exportar', 62, 258, 60, 'E~xportar…', exportar)
    d.botao('importar', 126, 258, 60, '~Importar…', importar)
    d.botao('remover', 190, 258, 60, 'Remove~r', lambda: d.fechar(('remover', None)))
    d.botao('cancelar', 272, 258, 52, '~Cancelar', lambda: d.fechar(None))
    d._acoes.append(('acao', 'escolher', escolher))
    d._acoes.append(('acao', 'abrir', abrir))
    for n in ('base', 'alinhamento', 'ponto'):
        d.ao_mudar(n, previa_dif)
    for n in ('fonte', 'tamanho', 'entrelinhas', 'recuo', 'menor', 'm_superior', 'm_inferior', 'm_esquerda', 'm_direita'):
        d.ao_digitar(n, previa_dif)

    def iniciar():
        d.c('base').selectItemPos(bases.index(inst.get('base', 'trabalho')), True)
        d.c('alinhamento').selectItemPos(0 if par.get('alinhamento', base_p['alinhamento']) == 'justificado' else 1, True)
        previa_dif()
    r = d.executar(_janela(frame), iniciar)
    if r is None:
        return False
    acao, dados = r
    if acao == 'remover':
        return None
    if acao == 'importado':
        return editar_instituicao(ctx, frame, dados)
    return dados
