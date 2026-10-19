# -*- coding: utf-8 -*-
"""Extensão do AY ESCREVA (componentes UNO em Python, carregados pelo próprio aplicativo).

Componentes:
  br.ayescreva.Comandos  - protocolo "ayescreva:" para os comandos próprios da faixa de opções
                           (PaginaEmBranco, Recuperacao, Guia, Atalhos, Limitacoes, Diagnostico,
                           DetalhesFontes, DetalhesFormato)
  br.ayescreva.Inicio    - tarefa executada ao iniciar: acompanha os documentos abertos para
                           (1) avisar fontes substituídas e (2) interceptar Salvar / Salvar como /
                           Salvar uma cópia, informando possíveis perdas ANTES de gravar fora do ODT
                           e oferecendo salvar também uma cópia em ODT.

Nada aqui acessa a rede nem lê conteúdo de documentos para fora do computador.
SPDX-License-Identifier: MPL-2.0
"""
import os
import platform
import time
import traceback

import uno
import unohelper
from com.sun.star.awt import XActionListener, XCallback
from com.sun.star.beans import PropertyValue, StringPair
from com.sun.star.document import XDocumentEventListener
from com.sun.star.frame import (XDispatch, XDispatchProvider, XDispatchProviderInterceptor, XNotifyingDispatch,
                                XInterceptorInfo, FeatureStateEvent)
from com.sun.star.lang import XEventListener, XInitialization, XServiceInfo
from com.sun.star.task import XJob

ID_EXTENSAO = 'br.ayescreva.extensao'
CLSID_MATH = '078b7aba-54fc-457f-8551-6147e776a997'
CLSID_GRAFICO = '12dcae26-281f-416f-a234-c3086127382e'

# Fontes ausentes comuns e a substituta de mesmas métricas incluída no AY
SUBSTITUTAS = {
    'calibri': 'Carlito', 'cambria': 'Caladea', 'arial': 'Liberation Sans', 'helvetica': 'Liberation Sans',
    'times new roman': 'Liberation Serif', 'times': 'Liberation Serif', 'courier new': 'Liberation Mono',
    'courier': 'Liberation Mono', 'arial narrow': 'Liberation Sans Narrow',
}

FORMATOS = {
    # filtro: (rótulo, extensão, nativo)
    'writer8': ('Documento de texto ODF (.odt) - formato nativo, sem perdas', 'odt', True),
    'MS Word 2007 XML': ('Documento do Word 2007-365 (.docx)', 'docx', False),
    'MS Word 97': ('Documento do Word 97-2003 (.doc)', 'doc', False),
    'Rich Text Format': ('Rich Text (.rtf)', 'rtf', False),
    'Text (encoded)': ('Texto sem formatação (.txt)', 'txt', False),
}
NOME_CURTO = {'writer8': 'ODT', 'MS Word 2007 XML': 'DOCX', 'MS Word 97': 'DOC', 'Rich Text Format': 'RTF', 'Text (encoded)': 'TXT'}
# O filtro detectado ao abrir pode ser outro nome do mesmo formato (ex.: um DOCX de outro programa abre como
# "Office Open XML Text"); para os avisos, vale o formato equivalente de FORMATOS.
EQUIVALENTES = {
    'Office Open XML Text': 'MS Word 2007 XML',
    'Office Open XML Text Template': 'MS Word 2007 XML',
    'MS Word 2007 XML Template': 'MS Word 2007 XML',
    'MS Word 2007 XML VBA': 'MS Word 2007 XML',
    'MS Word 97 Vorlage': 'MS Word 97',
    'Text': 'Text (encoded)',
}
NATIVOS = {'writer8', 'writer8_template', 'OpenDocument Text Flat XML'}


def canonico(filtro):
    return EQUIVALENTES.get(filtro, filtro)


def _log(msg):
    """Registro local de diagnóstico da extensão (no perfil do usuário; sem conteúdo de documentos)."""
    try:
        caminho = os.path.join(os.environ.get('TEMP', '.'), 'ayescreva-extensao.log')
        with open(caminho, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + msg + '\n')
    except Exception:
        pass


def _props(**kw):
    res = []
    for k, v in kw.items():
        p = PropertyValue()
        p.Name, p.Value = k, v
        res.append(p)
    return tuple(res)


def _servico(ctx, nome, *args):
    smgr = ctx.ServiceManager
    if args:
        return smgr.createInstanceWithArgumentsAndContext(nome, args, ctx)
    return smgr.createInstanceWithContext(nome, ctx)


def _abrir_no_sistema(ctx, caminho):
    """Abre um arquivo ou pasta local com o programa padrão do Windows (sem rede)."""
    if os.environ.get('AY_SIMULAR_ABERTURA') == '1':
        # Testes automatizados: registra o que seria aberto, sem abrir janelas de outros programas
        _log('abrir: ' + caminho + (' (existe)' if os.path.exists(caminho) else ' (NÃO EXISTE)'))
        return
    shell = _servico(ctx, 'com.sun.star.system.SystemShellExecute')
    shell.execute(caminho, '', 0)


def _pasta_extensao(ctx):
    pip = ctx.getValueByName('/singletons/com.sun.star.deployment.PackageInformationProvider')
    return uno.fileUrlToSystemPath(pip.getPackageLocation(ID_EXTENSAO))


def _mensagem(ctx, frame, titulo, texto, tipo='infobox'):
    tk = _servico(ctx, 'com.sun.star.awt.Toolkit')
    pai = frame.getContainerWindow() if frame else None
    from com.sun.star.awt.MessageBoxType import INFOBOX, WARNINGBOX
    from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK
    caixa = tk.createMessageBox(pai, WARNINGBOX if tipo == 'aviso' else INFOBOX, BUTTONS_OK, titulo, texto)
    caixa.execute()
    caixa.dispose()


# ---------------------------------------------------------------------------------------------
# Análise do documento: fontes e recursos que podem se perder em cada formato
# ---------------------------------------------------------------------------------------------
_FONTES_DISPONIVEIS = None


def fontes_disponiveis(ctx):
    global _FONTES_DISPONIVEIS
    if _FONTES_DISPONIVEIS is None:
        tk = _servico(ctx, 'com.sun.star.awt.Toolkit')
        dev = tk.createScreenCompatibleDevice(1, 1)
        _FONTES_DISPONIVEIS = {fd.Name.lower() for fd in dev.getFontDescriptors()}
    return _FONTES_DISPONIVEIS


def _paragrafos(texto, limite):
    pilha = [texto.createEnumeration()]
    n = 0
    while pilha and n < limite:
        e = pilha[-1]
        if not e.hasMoreElements():
            pilha.pop()
            continue
        el = e.nextElement()
        if el.supportsService('com.sun.star.text.Paragraph'):
            n += 1
            yield el
        elif el.supportsService('com.sun.star.text.TextTable'):
            for nome in el.getCellNames():
                pilha.append(el.getCellByName(nome).getText().createEnumeration())


def fontes_usadas(doc, limite=4000):
    usadas = set()
    try:
        estilos = doc.StyleFamilies.getByName('ParagraphStyles')
        for nome in estilos.getElementNames():
            st = estilos.getByName(nome)
            if st.isInUse():
                usadas.add(st.CharFontName)
    except Exception:
        pass
    for par in _paragrafos(doc.Text, limite):
        e = par.createEnumeration()
        while e.hasMoreElements():
            por = e.nextElement()
            try:
                if por.getString().strip():
                    usadas.add(por.CharFontName)
            except Exception:
                pass
    return {f for f in usadas if f}


def fontes_ausentes(ctx, doc):
    disp = fontes_disponiveis(ctx)
    ausentes = []
    for f in sorted(fontes_usadas(doc)):
        nomes = [p.strip() for p in f.split(';') if p.strip()]
        if not any(n.lower() in disp for n in nomes):
            ausentes.append(nomes[0])
        elif nomes[0].lower() not in disp:
            ausentes.append(nomes[0])  # primeira opção ausente: o motor usa a alternativa declarada
    return sorted(set(ausentes))


def descrever_substituta(nome):
    s = SUBSTITUTAS.get(nome.lower())
    return f'“{nome}” → “{s}” (mesmas medidas)' if s else f'“{nome}” → fonte semelhante escolhida pelo sistema'


def inventario(doc):
    inv = {}
    def seguro(f, padrao=0):
        try:
            return f()
        except Exception:
            return padrao
    inv['tabelas'] = seguro(lambda: doc.TextTables.Count)
    inv['imagens'] = seguro(lambda: doc.GraphicObjects.Count)
    inv['quadros'] = seguro(lambda: doc.TextFrames.Count)
    inv['secoes'] = seguro(lambda: doc.TextSections.Count)
    inv['notas'] = seguro(lambda: doc.Footnotes.Count) + seguro(lambda: doc.Endnotes.Count)
    inv['indices'] = seguro(lambda: doc.DocumentIndexes.Count)
    inv['alteracoes'] = seguro(lambda: sum(1 for _ in _enum(doc.Redlines)))
    campos = seguro(lambda: list(_enum(doc.TextFields)), [])
    inv['comentarios'] = sum(1 for c in campos if c.supportsService('com.sun.star.text.textfield.Annotation'))
    objs = seguro(lambda: [doc.EmbeddedObjects.getByName(n) for n in doc.EmbeddedObjects.getElementNames()], [])
    inv['equacoes'] = sum(1 for o in objs if str(seguro(lambda: o.CLSID, '')).lower() == CLSID_MATH)
    inv['graficos'] = sum(1 for o in objs if str(seguro(lambda: o.CLSID, '')).lower() == CLSID_GRAFICO)
    inv['formas'] = max(0, seguro(lambda: doc.DrawPage.Count) - inv['imagens'] - inv['quadros'] - len(objs))
    estilos_pagina = set()
    titulos = 0
    for par in _paragrafos(doc.Text, 4000):
        s = seguro(lambda: par.PageDescName, '')
        if s:
            estilos_pagina.add(s)
        if seguro(lambda: par.OutlineLevel, 0) > 0:
            titulos += 1
    inv['estilosPagina'] = len(estilos_pagina) + 1
    inv['titulos'] = titulos
    inv['macros'] = 0
    try:
        libs = doc.BasicLibraries
        for n in libs.getElementNames():
            if not libs.isLibraryLoaded(n):
                libs.loadLibrary(n)
            inv['macros'] += len(libs.getByName(n).getElementNames())
    except Exception:
        pass
    try:
        estilos = doc.StyleFamilies.getByName('PageStyles')
        inv['paisagem'] = any(estilos.getByName(n).IsLandscape for n in estilos.getElementNames()
                              if estilos.getByName(n).isInUse())
    except Exception:
        inv['paisagem'] = False
    return inv


def _enum(acesso):
    e = acesso.createEnumeration()
    while e.hasMoreElements():
        yield e.nextElement()


def riscos(doc, filtro):
    """Lista de possíveis perdas ao salvar o documento no filtro indicado (vazia = nada conhecido)."""
    if not filtro or filtro in NATIVOS:
        return []
    filtro = canonico(filtro)
    inv = inventario(doc)
    r = []
    def add(cond, texto):
        if cond:
            r.append(texto)
    if filtro == 'Text (encoded)':
        r.append('Toda a formatação (fontes, negrito, cores, estilos, alinhamentos) será perdida.')
        add(inv['tabelas'], f'{inv["tabelas"]} tabela(s) virarão texto corrido.')
        add(inv['imagens'] + inv['formas'] + inv['quadros'], 'Imagens, formas e caixas de texto serão perdidas.')
        add(inv['notas'], f'{inv["notas"]} nota(s) de rodapé/fim serão perdidas ou misturadas ao texto.')
        add(inv['comentarios'], f'{inv["comentarios"]} comentário(s) serão perdidos.')
        add(inv['alteracoes'], f'{inv["alteracoes"]} alteração(ões) controlada(s) serão perdidas.')
        add(inv['indices'], 'Sumários e índices virarão texto fixo.')
        r.append('Cabeçalhos, rodapés, numeração de páginas e seções serão perdidos.')
    elif filtro == 'Rich Text Format':
        add(inv['estilosPagina'] > 1 or inv['paisagem'], 'Quebras de seção com mudança de orientação ou de estilo de página podem ser perdidas (perda observada nos testes do AY).')
        add(inv['titulos'], f'Os níveis de tópico de {inv["titulos"]} título(s) não são mantidos: o sumário deixa de se atualizar (perda observada nos testes do AY).')
        add(inv['equacoes'] + inv['graficos'], 'Equações e gráficos podem virar imagens não editáveis.')
        add(inv['formas'] + inv['quadros'], 'Formas e caixas de texto podem mudar de posição.')
    elif filtro == 'MS Word 97':
        add(inv['equacoes'] + inv['graficos'], 'Equações e gráficos podem virar objetos ou imagens não editáveis no formato antigo.')
        add(inv['quadros'], 'Quadros de texto são convertidos (diferenças de posição observadas nos testes do AY).')
        add(inv['secoes'], 'Seções com colunas podem ser reorganizadas.')
        add(inv['alteracoes'], 'Alterações controladas de formatação podem não ser mantidas.')
    elif filtro == 'MS Word 2007 XML':
        add(inv['secoes'], f'{inv["secoes"]} seção(ões) com colunas: o texto pode refluir entre colunas e páginas (diferença observada nos testes do AY).')
        add(inv['quadros'], f'{inv["quadros"]} quadro(s) serão convertidos em caixas de texto do Word.')
    add(inv['macros'] and filtro != 'MS Word 97', 'Macros do documento não são salvas neste formato.')
    if not r:
        # Nenhuma perda específica conhecida: o aviso continua, sem prometer compatibilidade total
        nome = NOME_CURTO.get(filtro, filtro)
        r.append(f'Nenhuma perda específica foi encontrada neste documento, mas recursos sem equivalente em {nome} '
                 'podem ser convertidos ou mudar de aparência em outros programas.')
    return r


# ---------------------------------------------------------------------------------------------
# Diálogos
# ---------------------------------------------------------------------------------------------
class _Botao(unohelper.Base, XActionListener):
    def __init__(self, dialogo, codigo):
        self.dialogo, self.codigo = dialogo, codigo

    def actionPerformed(self, ev):
        self.dialogo.endDialog(self.codigo)

    def disposing(self, ev):
        pass


def dialogo_perdas(ctx, frame, filtro, lista, salvar_como):
    """Retorna ('formato'|'odt'|'cancelar', copia_odt: bool)."""
    nome = NOME_CURTO.get(canonico(filtro), filtro)
    texto = (f'O documento será salvo em {nome}. O formato nativo do AY ESCREVA é ODT, que guarda tudo.\n\n'
             f'Possíveis perdas encontradas neste documento:\n' + '\n'.join('•  ' + i for i in lista) +
             '\n\nVocê pode salvar assim mesmo, salvar em ODT, ou salvar no formato escolhido e guardar também uma cópia completa em ODT.')
    linhas = sum(max(1, len(l) // 70 + 1) for l in texto.split('\n'))
    altura_texto = 9 * linhas + 6
    dm = _servico(ctx, 'com.sun.star.awt.UnoControlDialogModel')
    dm.Width, dm.Height = 300, altura_texto + 58
    dm.Title = f'Salvar em {nome}: possíveis perdas'

    def add(tipo, nomec, **pr):
        m = dm.createInstance('com.sun.star.awt.UnoControl' + tipo + 'Model')
        for k, v in pr.items():
            setattr(m, k, v)
        dm.insertByName(nomec, m)
        return m
    add('FixedText', 'texto', PositionX=8, PositionY=8, Width=284, Height=altura_texto, MultiLine=True, Label=texto)
    add('CheckBox', 'copia', PositionX=8, PositionY=altura_texto + 12, Width=284, Height=12, State=1,
        Label='Guardar também uma cópia completa em ODT na mesma pasta (recomendado)')
    add('Button', 'formato', PositionX=8, PositionY=altura_texto + 34, Width=90, Height=16, Label=f'Salvar em {nome}', DefaultButton=True)
    add('Button', 'odt', PositionX=104, PositionY=altura_texto + 34, Width=90, Height=16, Label='Salvar em ODT')
    add('Button', 'cancelar', PositionX=212, PositionY=altura_texto + 34, Width=80, Height=16, Label='Cancelar')
    dlg = _servico(ctx, 'com.sun.star.awt.UnoControlDialog')
    dlg.setModel(dm)
    dlg.getControl('formato').addActionListener(_Botao(dlg, 10))
    dlg.getControl('odt').addActionListener(_Botao(dlg, 20))
    dlg.getControl('cancelar').addActionListener(_Botao(dlg, 0))
    tk = _servico(ctx, 'com.sun.star.awt.Toolkit')
    dlg.createPeer(tk, frame.getContainerWindow() if frame else None)
    r = dlg.execute()
    copia = dlg.getControl('copia').getState() == 1
    dlg.dispose()
    return {10: 'formato', 20: 'odt'}.get(r, 'cancelar'), copia


def escolher_arquivo(ctx, doc, filtro_atual, copia=False):
    """Diálogo Salvar como do AY: devolve (url, filtro) ou (None, None)."""
    from com.sun.star.ui.dialogs.TemplateDescription import FILESAVE_AUTOEXTENSION
    fp = _servico(ctx, 'com.sun.star.ui.dialogs.FilePicker', uno.Any('short', FILESAVE_AUTOEXTENSION))
    fp.setTitle('Salvar uma cópia' if copia else 'Salvar como')
    for filtro, (rotulo, ext, _n) in FORMATOS.items():
        fp.appendFilter(rotulo, f'*.{ext}')
    padrao = canonico(filtro_atual) if canonico(filtro_atual) in FORMATOS else 'writer8'
    fp.setCurrentFilter(FORMATOS[padrao][0])
    url = doc.getURL()
    if url:
        pasta, _, arquivo = url.rpartition('/')
        fp.setDisplayDirectory(pasta)
        fp.setDefaultName(arquivo.rsplit('.', 1)[0])
    else:
        fp.setDefaultName(doc.getDocumentProperties().Title or 'Documento')
    if fp.execute() != 1:
        return None, None
    destino = fp.getSelectedFiles()[0]
    rotulo = fp.getCurrentFilter()
    filtro = next((f for f, (r, _e, _n) in FORMATOS.items() if r == rotulo), 'writer8')
    ext = FORMATOS[filtro][1]
    if not destino.lower().endswith('.' + ext):
        destino += '.' + ext
    return destino, filtro


def _guardar(doc, url, filtro, como=True):
    extra = {'FilterOptions': 'UTF8,CRLF,,'} if filtro == 'Text (encoded)' else {}
    args = _props(FilterName=filtro, Overwrite=True, **extra)
    if como:
        doc.storeAsURL(url, args)
    else:
        doc.storeToURL(url, args)


def _url_copia_odt(url):
    base = url.rsplit('.', 1)[0]
    return base + '.odt' if not url.lower().endswith('.odt') else base + ' (cópia).odt'


def _infobar(doc, ident, titulo, texto, tipo='INFO', botoes=()):
    try:
        ctrl = doc.getCurrentController()
        if ctrl.hasInfobar(ident):
            ctrl.removeInfobar(ident)
        pares = []
        for rot, cmd in botoes:
            sp = StringPair()
            sp.First, sp.Second = rot, cmd
            pares.append(sp)
        ctrl.appendInfobar(ident, titulo, texto, uno.getConstantByName('com.sun.star.frame.InfobarType.' + tipo), tuple(pares), True)
    except Exception:
        _log('infobar: ' + traceback.format_exc())


# ---------------------------------------------------------------------------------------------
# Interceptação de Salvar / Salvar como / Salvar uma cópia
# ---------------------------------------------------------------------------------------------
_ACEITOS = []   # (modelo, filtro) já confirmados nesta sessão; compara-se por identidade UNO, não por id()


def _aceito(doc, filtro):
    return any(d == doc and f == filtro for d, f in _ACEITOS)


def _aceitar(doc, filtro):
    _esquecer(doc)
    _ACEITOS.append((doc, filtro))


def _esquecer(doc):
    _ACEITOS[:] = [(d, f) for d, f in _ACEITOS if d != doc]


def filtro_do(doc):
    for p in doc.getArgs():
        if p.Name == 'FilterName':
            return p.Value
    return ''


class _Adiado(unohelper.Base, XCallback):
    def __init__(self, f):
        self.f = f

    def notify(self, dados):
        try:
            self.f()
        except Exception:
            _log('adiado: ' + traceback.format_exc())


def _adiar(ctx, f):
    """Executa f no próximo ciclo da interface (thread principal), depois que o comando atual retornar."""
    _servico(ctx, 'com.sun.star.awt.AsyncCallback').addCallback(_Adiado(f), uno.Any('void', None))


class _DespachoSalvar(unohelper.Base, XNotifyingDispatch):
    """Salvar / Salvar como / Salvar uma cópia com os avisos do AY.

    dispatch(): pelos botões, menus e atalhos; os diálogos abrem de forma assíncrona, como os da base.
    dispatchWithNotification(): usado pelo motor quando precisa do resultado (ex.: "Salvar" na pergunta ao
    fechar o documento, que só fecha se o salvamento terminar com SUCCESS); roda de forma síncrona.
    """
    REPASSADO = 'repassado'   # o despachante da base cuidou da notificação

    def __init__(self, ctx, frame, escravo, url):
        self.ctx, self.frame, self.escravo, self.url = ctx, frame, escravo, url

    def addStatusListener(self, ouvinte, url):
        if self.escravo:
            self.escravo.addStatusListener(ouvinte, url)

    def removeStatusListener(self, ouvinte, url):
        if self.escravo:
            self.escravo.removeStatusListener(ouvinte, url)

    def _repassar(self, url, args, ouvinte=None):
        if not self.escravo:
            return False
        if ouvinte is not None and hasattr(self.escravo, 'dispatchWithNotification'):
            self.escravo.dispatchWithNotification(url, args, ouvinte)
            return self.REPASSADO
        self.escravo.dispatch(url, args)
        return None

    def dispatch(self, url, args):
        _log('salvar interceptado: ' + url.Complete + ' [' + ','.join(a.Name for a in (args or ())) + ']')
        if any(a.Name == 'SynchronMode' and a.Value for a in (args or ())):
            self._executar(url, args)
            return
        # Como os diálogos da base, que abrem de forma assíncrona: o comando retorna logo e os diálogos do AY
        # (perdas, Salvar como) abrem no ciclo seguinte da interface.
        _adiar(self.ctx, lambda: self._executar(url, args))

    def dispatchWithNotification(self, url, args, ouvinte):
        _log('salvar interceptado (com resultado): ' + url.Complete)
        r = self._executar(url, args, ouvinte)
        if r == self.REPASSADO or ouvinte is None:
            return
        nome = {True: 'SUCCESS', False: 'FAILURE'}.get(r, 'DONTKNOW')
        ev = uno.createUnoStruct('com.sun.star.frame.DispatchResultEvent')
        ev.Source = self
        ev.State = uno.getConstantByName('com.sun.star.frame.DispatchResultState.' + nome)
        _log('salvar: resultado ' + nome)
        ouvinte.dispatchFinished(ev)

    def _executar(self, url, args, ouvinte=None):
        """True = salvo pelo AY; False = cancelado ou falhou; None/REPASSADO = feito pela base."""
        try:
            doc = self.frame.getController().getModel()
            if not doc.supportsService('com.sun.star.text.TextDocument') or doc.isReadonly():
                _log('salvar: documento não é de texto ou é somente leitura')
                return self._repassar(url, args, ouvinte)
            cmd = url.Complete.split('?')[0]
            if cmd == '.uno:Save' and doc.hasLocation():
                return self._salvar(doc, url, args, ouvinte)
            return self._salvar_como(doc, copia=(cmd == '.uno:SaveACopy'))
        except Exception:
            _log('dispatch salvar: ' + traceback.format_exc())
            return self._repassar(url, args, ouvinte)

    def _salvar(self, doc, url, args, ouvinte=None):
        filtro = filtro_do(doc)
        if not filtro or filtro in NATIVOS:
            return self._repassar(url, args, ouvinte)   # ODT: comportamento da base
        lista = riscos(doc, filtro)
        _log(f'salvar: filtro {filtro!r}, {len(lista)} possível(is) perda(s)')
        if lista and not _aceito(doc, filtro):
            escolha, copia = dialogo_perdas(self.ctx, self.frame, filtro, lista, False)
            _log(f'salvar: escolha {escolha}, cópia ODT {copia}')
            if escolha == 'cancelar':
                return False
            if escolha == 'odt':
                destino = _url_copia_odt(doc.getURL())
                _guardar(doc, destino, 'writer8', como=True)
                _infobar(doc, 'ay-salvo', 'Salvo em ODT.', 'O documento agora está em ' + uno.fileUrlToSystemPath(destino))
                return True
            _aceitar(doc, filtro)
            if copia:
                destino = _url_copia_odt(doc.getURL())
                _guardar(doc, destino, 'writer8', como=False)
                _infobar(doc, 'ay-copia', 'Cópia completa em ODT guardada.', uno.fileUrlToSystemPath(destino))
        doc.store()
        return True

    def _salvar_como(self, doc, copia):
        destino, filtro = escolher_arquivo(self.ctx, doc, filtro_do(doc), copia)
        if not destino:
            return False
        lista = riscos(doc, filtro)
        guardar_odt = False
        if lista:
            escolha, guardar_odt = dialogo_perdas(self.ctx, self.frame, filtro, lista, True)
            if escolha == 'cancelar':
                return False
            if escolha == 'odt':
                destino, filtro, guardar_odt = destino.rsplit('.', 1)[0] + '.odt', 'writer8', False
            else:
                _aceitar(doc, filtro)
        _guardar(doc, destino, filtro, como=not copia)
        if guardar_odt:
            odt = _url_copia_odt(destino)
            _guardar(doc, odt, 'writer8', como=False)
            _infobar(doc, 'ay-copia', 'Cópia completa em ODT guardada.', uno.fileUrlToSystemPath(odt))
        return True


class Interceptador(unohelper.Base, XDispatchProviderInterceptor, XInterceptorInfo):
    URLS = ('.uno:Save', '.uno:SaveAs', '.uno:SaveACopy')

    def __init__(self, ctx, frame):
        self.ctx, self.frame = ctx, frame
        self.escravo = self.mestre = None

    def getInterceptedURLs(self):
        return self.URLS

    def getSlaveDispatchProvider(self):
        return self.escravo

    def setSlaveDispatchProvider(self, p):
        self.escravo = p

    def getMasterDispatchProvider(self):
        return self.mestre

    def setMasterDispatchProvider(self, p):
        self.mestre = p

    def queryDispatch(self, url, alvo, flags):
        if url.Complete.split('?')[0] in self.URLS:
            escravo = self.escravo.queryDispatch(url, alvo, flags) if self.escravo else None
            return _DespachoSalvar(self.ctx, self.frame, escravo, url)
        return self.escravo.queryDispatch(url, alvo, flags) if self.escravo else None

    def queryDispatches(self, pedidos):
        return tuple(self.queryDispatch(p.FeatureURL, p.FrameName, p.SearchFlags) for p in pedidos)


# ---------------------------------------------------------------------------------------------
# Tarefa de início e ouvinte de documentos
# ---------------------------------------------------------------------------------------------
_QUADROS = []   # quadros já interceptados (id() de um proxy UNO não é estável; compara-se por identidade UNO)


class _FimDoQuadro(unohelper.Base, XEventListener):
    def __init__(self, frame):
        self.frame = frame

    def disposing(self, ev):
        _QUADROS[:] = [f for f in _QUADROS if f != self.frame]


class OuvinteDocumentos(unohelper.Base, XDocumentEventListener):
    def __init__(self, ctx):
        self.ctx = ctx

    def documentEventOccured(self, ev):
        try:
            doc = ev.Source
            if not doc or not doc.supportsService('com.sun.star.text.TextDocument'):
                return
            if ev.EventName in ('OnViewCreated', 'OnNew', 'OnLoad'):
                ctrl = ev.ViewController or doc.getCurrentController()
                if ctrl:
                    preparar_quadro(self.ctx, ctrl.getFrame())
            if ev.EventName == 'OnLoad':
                avisar_fontes(self.ctx, doc)
            if ev.EventName == 'OnUnload':
                _esquecer(doc)
        except Exception:
            _log('evento: ' + traceback.format_exc())

    def disposing(self, ev):
        pass


def preparar_quadro(ctx, frame):
    if frame is None:
        return
    if any(f == frame for f in _QUADROS):
        return
    _QUADROS.append(frame)
    frame.addEventListener(_FimDoQuadro(frame))
    frame.registerDispatchProviderInterceptor(Interceptador(ctx, frame))
    _log(f'interceptador registrado ({len(_QUADROS)} quadro(s))')


def avisar_fontes(ctx, doc):
    ausentes = fontes_ausentes(ctx, doc)
    if not ausentes:
        return
    lista = ', '.join(f'“{a}”' for a in ausentes[:4]) + (f' e mais {len(ausentes) - 4}' if len(ausentes) > 4 else '')
    verbo = 'não está instalada' if len(ausentes) == 1 else 'não estão instaladas'
    _infobar(doc, 'ay-fontes', 'Fontes substituídas:',
             f'{lista} {verbo}. O AY mostra fontes parecidas no lugar; quebras de linha e de página podem mudar. Ao salvar, o nome original é mantido.',
             'WARNING', (('Detalhes', 'ayescreva:DetalhesFontes'),))


class Inicio(unohelper.Base, XJob, XServiceInfo):
    def __init__(self, ctx, *args):
        self.ctx = ctx

    def execute(self, args):
        try:
            difusor = self.ctx.getValueByName('/singletons/com.sun.star.frame.theGlobalEventBroadcaster')
            difusor.addDocumentEventListener(OuvinteDocumentos(self.ctx))
            desktop = _servico(self.ctx, 'com.sun.star.frame.Desktop')
            comps = desktop.getComponents().createEnumeration()
            while comps.hasMoreElements():
                c = comps.nextElement()
                if c.supportsService('com.sun.star.text.TextDocument') and c.getCurrentController():
                    preparar_quadro(self.ctx, c.getCurrentController().getFrame())
            _log('extensão iniciada')
        except Exception:
            _log('inicio: ' + traceback.format_exc())
        return None

    def getImplementationName(self):
        return 'br.ayescreva.Inicio'

    def supportsService(self, nome):
        return nome in self.getSupportedServiceNames()

    def getSupportedServiceNames(self):
        return ('com.sun.star.task.Job',)


# ---------------------------------------------------------------------------------------------
# Comandos "ayescreva:"
# ---------------------------------------------------------------------------------------------
class Comandos(unohelper.Base, XDispatchProvider, XDispatch, XInitialization, XServiceInfo):
    ACOES = ('PaginaEmBranco', 'Recuperacao', 'Guia', 'Atalhos', 'Limitacoes', 'Diagnostico', 'DetalhesFontes')

    def __init__(self, ctx, *args):
        self.ctx = ctx
        self.frame = None

    def initialize(self, args):
        if args:
            self.frame = args[0]

    def queryDispatch(self, url, alvo, flags):
        return self if url.Protocol == 'ayescreva:' and url.Path in self.ACOES else None

    def queryDispatches(self, pedidos):
        return tuple(self.queryDispatch(p.FeatureURL, p.FrameName, p.SearchFlags) for p in pedidos)

    def addStatusListener(self, ouvinte, url):
        ev = FeatureStateEvent()
        ev.Source, ev.FeatureURL, ev.IsEnabled, ev.Requery = self, url, True, False
        ouvinte.statusChanged(ev)

    def removeStatusListener(self, ouvinte, url):
        pass

    def dispatch(self, url, args):
        try:
            getattr(self, '_' + url.Path)()
        except Exception:
            _log('comando ' + url.Path + ': ' + traceback.format_exc())
            _mensagem(self.ctx, self.frame, 'AY ESCREVA', 'Não foi possível executar este comando. Detalhes foram gravados em ayescreva-extensao.log na pasta temporária.', 'aviso')

    def _executar(self, cmd):
        desp = _servico(self.ctx, 'com.sun.star.frame.DispatchHelper')
        desp.executeDispatch(self.frame, cmd, '', 0, ())

    def _PaginaEmBranco(self):
        # Página vazia no ponto do cursor: quebra, parágrafo vazio, quebra; o cursor fica na página nova
        self._executar('.uno:InsertPagebreak')
        self._executar('.uno:InsertPagebreak')
        self._executar('.uno:GoUp')

    def _Recuperacao(self):
        subst = _servico(self.ctx, 'com.sun.star.util.PathSubstitution')
        backup = subst.substituteVariables('$(user)/backup', True)
        caminho = uno.fileUrlToSystemPath(backup)
        os.makedirs(caminho, exist_ok=True)
        _abrir_no_sistema(self.ctx, caminho)

    def _abrir_ajuda(self, nome):
        _abrir_no_sistema(self.ctx, os.path.join(_pasta_extensao(self.ctx), 'ajuda', nome))

    def _Guia(self):
        self._abrir_ajuda('guia.html')

    def _Atalhos(self):
        self._abrir_ajuda('atalhos.html')

    def _Limitacoes(self):
        self._abrir_ajuda('limitacoes.html')

    def _Diagnostico(self):
        cfg = _servico(self.ctx, 'com.sun.star.configuration.ConfigurationProvider')
        def ler(no, prop):
            try:
                a = cfg.createInstanceWithArguments('com.sun.star.configuration.ConfigurationAccess', _props(nodepath=no))
                return a.getPropertyValue(prop)
            except Exception as e:
                return f'(indisponível: {e})'
        subst = _servico(self.ctx, 'com.sun.star.util.PathSubstitution')
        perfil = uno.fileUrlToSystemPath(subst.substituteVariables('$(user)', True))
        programa = uno.fileUrlToSystemPath(subst.substituteVariables('$(prog)', True))
        manifesto = os.path.join(os.path.dirname(programa), 'ay-escreva.json')
        versao_ay = open(manifesto, encoding='utf-8-sig').read() if os.path.exists(manifesto) else '(sem manifesto)'
        linhas = [
            'AY ESCREVA - relatório de diagnóstico',
            f'Gerado em: {time.strftime("%Y-%m-%d %H:%M:%S")}',
            'Este arquivo NÃO contém conteúdo de documentos e não é enviado a lugar nenhum.',
            '',
            '[Versão]', versao_ay.strip(),
            f'Base: {ler("/org.openoffice.Setup/Product", "ooName")} sobre motor {ler("/org.openoffice.Setup/Product", "ooSetupVersionAboutBox")}',
            '',
            '[Sistema]', f'{platform.platform()} | {platform.machine()} | Python {platform.python_version()}',
            '',
            '[Configuração]',
            f'Idioma da interface: {ler("/org.openoffice.Setup/L10N", "ooLocale")}',
            f'Idioma padrão dos documentos: {ler("/org.openoffice.Office.Linguistic/General", "DefaultLocale")}',
            f'Interface (Writer): {ler("/org.openoffice.Office.UI.ToolbarMode/Applications/Writer", "Active")}',
            f'Segurança de macros (nível): {ler("/org.openoffice.Office.Common/Security/Scripting", "MacroSecurityLevel")}',
            f'Bloqueio de vínculos externos: {ler("/org.openoffice.Office.Common/Security/Scripting", "BlockUntrustedRefererLinks")}',
            f'Recuperação automática ativa: {ler("/org.openoffice.Office.Recovery/AutoSave", "Enabled")} (a cada {ler("/org.openoffice.Office.Recovery/AutoSave", "TimeIntervall")} min)',
            f'Cópia de segurança ao salvar: {ler("/org.openoffice.Office.Common/Save/Document", "CreateBackup")}',
            '',
            '[Pastas]', f'Programa: {programa}', f'Perfil: {perfil}',
            '',
            '[Fontes instaladas visíveis ao AY]', str(len(fontes_disponiveis(self.ctx))),
        ]
        destino = os.path.join(perfil, 'diagnostico-ay-escreva.txt')
        with open(destino, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(linhas) + '\n')
        _abrir_no_sistema(self.ctx, destino)

    def _DetalhesFontes(self):
        doc = self.frame.getController().getModel()
        ausentes = fontes_ausentes(self.ctx, doc)
        texto = ('Fontes usadas no documento que não estão instaladas neste computador:\n\n' +
                 '\n'.join('•  ' + descrever_substituta(a) for a in ausentes) +
                 '\n\nO documento continua guardando o nome da fonte original: em um computador que tenha a fonte, '
                 'ele aparece como foi criado. Para evitar diferenças, instale a fonte ou troque-a no documento.')
        _mensagem(self.ctx, self.frame, 'Substituição de fontes', texto)

    def getImplementationName(self):
        return 'br.ayescreva.Comandos'

    def supportsService(self, nome):
        return nome in self.getSupportedServiceNames()

    def getSupportedServiceNames(self):
        return ('com.sun.star.frame.ProtocolHandler',)


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(Comandos, 'br.ayescreva.Comandos', ('com.sun.star.frame.ProtocolHandler',))
g_ImplementationHelper.addImplementation(Inicio, 'br.ayescreva.Inicio', ('com.sun.star.task.Job',))
