import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar

import os, pathlib
import leitor_drive as ld
import persistencia as pers
import calculos as calc
import categorizador_ia as cat_ia
import insights_ia as ins_ia
import categorias_manager as cat_mgr
from config import (META_RECEITA_MENSAL, SALAS, SESSOES_POR_DIA,
                    PLANO_CONTAS_TODOS, CENTROS_CUSTO, EXCLUIR_DRE)

# Carrega .env se existir
_env_path = pathlib.Path(__file__).parent / ".env"
if _env_path.exists():
    for _linha in _env_path.read_text(encoding="utf-8").splitlines():
        _linha = _linha.strip()
        if _linha and not _linha.startswith("#") and "=" in _linha:
            _k, _v = _linha.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

st.set_page_config(page_title="Escape Time Brasil — Dashboard", page_icon="⏱️",
                   layout="wide", initial_sidebar_state="expanded")

# ── Paleta Escape Time Brasil ────────────────────────────────────────────────
# Vermelho primário: #E31E24  |  Preto fundo: #0D0D0D  |  Card: #181818
# Cinza escuro: #242424       |  Texto: #F0F0F0         |  Muted: #888888
# Verde sucesso: #22C55E      |  Laranja alerta: #F97316

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700;800&family=Barlow+Condensed:wght@700;800&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
.stApp { background: #0D0D0D; }
.stSidebar { background: #111111 !important; border-right: 1px solid #1E1E1E; }
.stSidebar .stMarkdown { color: #B0B0B0; }

/* ── Esconde header padrão Streamlit ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: #111111;
  border-bottom: 2px solid #E31E24;
  gap: 2px;
  border-radius: 8px 8px 0 0;
  padding: 4px 4px 0;
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  color: #888888;
  font-family: 'Barlow', sans-serif;
  font-weight: 600;
  font-size: .85rem;
  letter-spacing: .03em;
  border-radius: 6px 6px 0 0;
  padding: 8px 16px;
  border: none;
  transition: all .2s;
}
.stTabs [aria-selected="true"] {
  background: #E31E24 !important;
  color: #FFFFFF !important;
}
.stTabs [data-baseweb="tab-panel"] { background: #111111; border-radius: 0 0 8px 8px; padding: 16px; }

/* ── Metric cards ── */
.metric-card {
  background: #181818;
  border-radius: 10px;
  padding: 14px 18px;
  border-left: 4px solid #E31E24;
  margin-bottom: 8px;
  border-top: 1px solid #252525;
}
.metric-card.green  { border-left-color: #22C55E; }
.metric-card.red    { border-left-color: #E31E24; }
.metric-card.orange { border-left-color: #F97316; }
.metric-card.blue   { border-left-color: #3B82F6; }
.metric-card.gray   { border-left-color: #555555; }
.metric-val { font-family:'Barlow Condensed',sans-serif; font-size:1.9rem; font-weight:800; color:#F0F0F0; margin:0; line-height:1.1; }
.metric-lbl { font-size:.7rem; color:#888888; margin:0 0 4px; text-transform:uppercase; letter-spacing:.08em; }
.metric-sub { font-size:.78rem; color:#555555; margin-top:3px; }

/* ── Alertas ── */
.alerta-red   { background:#1C0A0A; border:1px solid #E31E24; border-left:4px solid #E31E24; border-radius:8px; padding:10px 14px; color:#FCA5A5; margin-bottom:8px; }
.alerta-green { background:#062012; border:1px solid #22C55E; border-left:4px solid #22C55E; border-radius:8px; padding:10px 14px; color:#86EFAC; margin-bottom:8px; }
.alerta-org   { background:#1C0E04; border:1px solid #F97316; border-left:4px solid #F97316; border-radius:8px; padding:10px 14px; color:#FDBA74; margin-bottom:8px; }
.alerta-blue  { background:#050E1C; border:1px solid #3B82F6; border-left:4px solid #3B82F6; border-radius:8px; padding:10px 14px; color:#93C5FD; margin-bottom:8px; }

/* ── Fonte extrato badge ── */
.fonte-extrato { background:#1C0A0A; border:1px solid #E31E24; border-radius:20px; padding:3px 12px; font-size:.72rem; color:#FCA5A5; display:inline-block; margin-bottom:10px; letter-spacing:.05em; }

/* ── Títulos ── */
h1 { font-family:'Barlow Condensed',sans-serif !important; font-size:2.2rem !important; font-weight:800 !important; color:#F0F0F0 !important; letter-spacing:.02em; }
h2, h3 { font-family:'Barlow',sans-serif !important; font-weight:700 !important; color:#E0E0E0 !important; }
.stSubheader { color:#E0E0E0 !important; }

/* ── Separadores ── */
hr { border-color: #1E1E1E !important; margin: 16px 0; }

/* ── Botões ── */
.stButton > button {
  background: #E31E24 !important;
  color: #FFFFFF !important;
  font-family: 'Barlow', sans-serif;
  font-weight: 700;
  border: none !important;
  border-radius: 6px !important;
  letter-spacing: .04em;
  transition: all .2s;
}
.stButton > button:hover { background: #C01820 !important; transform: translateY(-1px); }
.stButton > button[kind="secondary"] { background: #242424 !important; color: #E0E0E0 !important; }

/* ── Selectbox / inputs ── */
.stSelectbox > div > div, .stTextInput > div > div, .stDateInput > div > div {
  background: #181818 !important;
  border: 1px solid #333333 !important;
  color: #F0F0F0 !important;
  border-radius: 6px !important;
}

/* ── DataFrames ── */
.stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #252525; }
iframe { border-radius: 8px; }

/* ── Radio ── */
.stRadio [data-baseweb="radio"] { color: #B0B0B0; }

/* ── Sidebar itens ── */
.stSidebar .stButton > button {
  background: #E31E24 !important;
  width: 100%;
}
.stSidebar .stTextInput > div > div { background: #1A1A1A !important; border-color: #333 !important; }

/* ── Logo no topo ── */
.et-logo-bar {
  display:flex; align-items:center; gap:12px;
  padding: 0 0 12px 0; border-bottom: 1px solid #1E1E1E; margin-bottom: 12px;
}
.et-periodo-badge {
  display:inline-block; background:#1C0A0A; border:1px solid #E31E24;
  border-radius:4px; padding:3px 10px; font-size:.72rem; color:#FCA5A5;
  font-family:'Barlow',sans-serif; font-weight:600; letter-spacing:.06em;
  text-transform: uppercase;
}
</style>""", unsafe_allow_html=True)


# ── Funções helper ────────────────────────────────────────────────────────────
def fmt_brl(v):
    if v is None: return "-"
    try:
        return "R$ {:,.2f}".format(float(v)).replace(",","X").replace(".",",").replace("X",".")
    except (TypeError, ValueError):
        return "-"

def card(label, val, cor="", sub=""):
    s = "<p class='metric-sub'>{}</p>".format(sub) if sub else ""
    st.markdown("<div class='metric-card {}'><p class='metric-lbl'>{}</p><p class='metric-val'>{}</p>{}</div>".format(
        cor, label, val, s), unsafe_allow_html=True)

def gauge_chart(val, maximo, titulo):
    val = val or 0
    cor = "#22C55E" if val >= 70 else ("#F97316" if val >= 40 else "#E31E24")
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val,
        title={"text": titulo, "font": {"size": 12, "color": "#888888", "family": "Barlow"}},
        number={"suffix": "%", "font": {"size": 28, "color": "#F0F0F0", "family": "Barlow Condensed"}},
        gauge={
            "axis": {"range": [0, maximo], "tickcolor": "#333333", "tickfont": {"color": "#555555"}},
            "bar": {"color": cor, "thickness": 0.25},
            "bgcolor": "#181818",
            "bordercolor": "#252525",
            "borderwidth": 1,
            "steps": [
                {"range": [0, 40],  "color": "#1A0808"},
                {"range": [40, 70], "color": "#1A1008"},
                {"range": [70, maximo], "color": "#081A0E"},
            ],
            "threshold": {"line": {"color": "#F0F0F0", "width": 2}, "value": 70},
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=210, margin=dict(t=45, b=5, l=10, r=10),
        font={"color": "#888888", "family": "Barlow"},
    )
    return fig

def badge_fonte(extrato=False):
    if extrato:
        st.markdown('<span class="fonte-extrato">⚡ Fonte: Extrato Bancário Categorizado</span>', unsafe_allow_html=True)

def selectbox_com_novo(label, opcoes, key, tipo_cat):
    """Selectbox que permite digitar nova opção e persiste no categorias_custom.json."""
    NOVO = "[ + Adicionar novo... ]"
    sel = st.selectbox(label, [NOVO] + list(opcoes), key=key)
    if sel == NOVO:
        novo_val = st.text_input(
            "Digite o novo {}".format(label.lower()),
            key=key + "_novo_txt",
            placeholder="ex: Estacionamento"
        )
        if novo_val.strip():
            cat_mgr.salvar_nova_categoria(tipo_cat, novo_val.strip())
            return novo_val.strip()
        return None
    return sel


def mostrar_tabela_com_revisao(df, key_prefix, filtros_col=None):
    if df.empty: return df
    c_busca = st.text_input("Buscar", key=key_prefix+"_busca", placeholder="Filtrar por qualquer campo...")
    if c_busca:
        mask = df.astype(str).apply(lambda c: c.str.contains(c_busca, case=False, na=False)).any(axis=1)
        df = df[mask]
    if filtros_col:
        n = len(filtros_col)
        cols = st.columns(n)
        for i, fc in enumerate(filtros_col):
            if fc in df.columns:
                ops = sorted(df[fc].dropna().astype(str).unique())
                sel = cols[i].multiselect(fc.replace("_", " ").title(), ops, key=key_prefix+"_f_"+fc)
                if sel:
                    df = df[df[fc].astype(str).isin(sel)]
    return df


# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def carregar_tudo():
    dre_raw = ld.carregar_dre_todos()
    for x in dre_raw: x["df_parsed"] = ld.parsear_dre(x["df"])

    pagar_raw = ld.carregar_contas_pagar_todos()
    for x in pagar_raw: x["df_parsed"] = ld.parsear_contas(x["df"])

    receber_raw = ld.carregar_contas_receber_todos()
    for x in receber_raw: x["df_parsed"] = ld.parsear_contas(x["df"])

    # Financeiro (novo padrão) — substitui pedidos
    fin_raw = ld.carregar_financeiro_todos()
    for x in fin_raw: x["df_parsed"] = ld.parsear_financeiro(x["df"])

    ext_raw = ld.carregar_extrato_todos()
    jog_raw = ld.carregar_jogadores_todos()

    return dre_raw, pagar_raw, receber_raw, fin_raw, ext_raw, jog_raw


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<img src="https://www.escapetime.com.br/public/images/logo.png" '
        'style="width:160px;margin-bottom:8px;filter:brightness(1.1)">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#888;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;'
        'margin:-4px 0 12px;font-family:Barlow,sans-serif;font-weight:600">Dashboard Financeiro</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    if st.button("Atualizar dados do Drive", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    periodos = ld.listar_periodos_disponiveis()
    if not periodos: periodos = ["2026-04"]

    fmt_periodo = lambda p: datetime.strptime(p, "%Y-%m").strftime("%b/%Y").capitalize()

    modo_periodo = st.radio("Modo de período", ["Mês único", "Vários meses", "Ano completo"],
                            horizontal=False, key="modo_periodo")

    if modo_periodo == "Mês único":
        periodo_sel = st.selectbox("Mês", periodos, format_func=fmt_periodo)
        periodos_sel = [periodo_sel]

    elif modo_periodo == "Vários meses":
        anos_disp = sorted(set(p[:4] for p in periodos), reverse=True)
        ano_filtro = st.selectbox("Ano", anos_disp)
        meses_ano = sorted([p for p in periodos if p.startswith(ano_filtro)], reverse=False)
        if meses_ano:
            col_de, col_ate = st.columns(2)
            with col_de:
                p_ini = st.selectbox("De", meses_ano, format_func=fmt_periodo, key="p_ini")
            with col_ate:
                p_fim = st.selectbox("Até", meses_ano,
                                     index=len(meses_ano)-1, format_func=fmt_periodo, key="p_fim")
            idx_ini = meses_ano.index(p_ini)
            idx_fim = meses_ano.index(p_fim)
            if idx_fim < idx_ini:
                p_ini, p_fim = p_fim, p_ini
                idx_ini, idx_fim = idx_fim, idx_ini
            periodos_sel = meses_ano[idx_ini:idx_fim+1]
        else:
            periodos_sel = periodos[:1]
        periodo_sel = periodos_sel[-1]  # mês mais recente como referência

    else:  # Ano completo
        anos_disp = sorted(set(p[:4] for p in periodos), reverse=True)
        ano_sel = st.selectbox("Ano", anos_disp)
        periodos_sel = sorted([p for p in periodos if p.startswith(ano_sel)])
        periodo_sel = periodos_sel[-1] if periodos_sel else periodos[0]

    # Rótulo do período selecionado
    if len(periodos_sel) == 1:
        mes_label_sidebar = fmt_periodo(periodos_sel[0])
    else:
        mes_label_sidebar = "{} a {}".format(fmt_periodo(periodos_sel[0]), fmt_periodo(periodos_sel[-1]))

    st.markdown("---")
    # ── Configuração da chave da IA ──────────────────────────────────────────
    api_key_env = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key_env:
        st.success("IA configurada ✓")
        api_key_ativo = api_key_env
        # Permite trocar a chave
        with st.expander("Trocar chave da IA"):
            nova_chave = st.text_input("Nova API Key", type="password",
                                       placeholder="sk-ant-...", key="api_key_troca")
            if nova_chave and nova_chave.startswith("sk-"):
                env_path = pathlib.Path(__file__).parent / ".env"
                env_path.write_text("ANTHROPIC_API_KEY={}\n".format(nova_chave), encoding="utf-8")
                os.environ["ANTHROPIC_API_KEY"] = nova_chave
                st.success("Chave atualizada!")
                st.rerun()
    else:
        st.markdown("**Chave da IA (Anthropic)**")
        api_key_input = st.text_input(
            "Cole sua API Key",
            type="password",
            placeholder="sk-ant-...",
            key="api_key_input",
            help="Obtenha em console.anthropic.com/settings/keys",
        )
        if api_key_input and api_key_input.startswith("sk-"):
            # Grava automaticamente no .env ao inserir
            env_path = pathlib.Path(__file__).parent / ".env"
            env_path.write_text("ANTHROPIC_API_KEY={}\n".format(api_key_input), encoding="utf-8")
            os.environ["ANTHROPIC_API_KEY"] = api_key_input
            st.success("Chave salva! Recarregando...")
            st.rerun()
        api_key_ativo = api_key_input or ""
        if not api_key_ativo:
            st.caption("Sem chave: categorização e insights desabilitados")

    st.markdown("---")
    st.caption("{} salas × {} sessoes/dia | Cap. {}".format(
        SALAS, SESSOES_POR_DIA, SALAS*SESSOES_POR_DIA*30))
    st.caption("Break-even: {}".format(fmt_brl(META_RECEITA_MENSAL)))
    st.caption("Atualizado: {}".format(datetime.now().strftime("%d/%m %H:%M")))


# ── Carrega dados ──────────────────────────────────────────────────────────────
dre_todos, pagar_todos, receber_todos, fin_todos, ext_todos, jog_todos = carregar_tudo()


def _agregar(lista_todos, periodos, campo="df_parsed"):
    frames = []
    for p in periodos:
        item = next((x for x in lista_todos if x.get("periodo") == p), None)
        if item and item.get(campo) is not None and not item[campo].empty:
            df_p = item[campo].copy()
            df_p["__periodo__"] = p
            frames.append(df_p)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    # Remove colunas duplicadas (mantém a primeira ocorrência)
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def _limpar_df(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas duplicadas e garante tipos serializáveis antes de exibir."""
    if df.empty:
        return df
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df


def _soma_coluna(df: pd.DataFrame, col: str) -> float:
    """Soma segura de coluna — retorna sempre um float escalar."""
    if col not in df.columns:
        return 0.0
    serie = df[col]
    # Se o resultado for DataFrame (colunas duplicadas), pega a primeira
    if isinstance(serie, pd.DataFrame):
        serie = serie.iloc[:, 0]
    return float(pd.to_numeric(serie, errors="coerce").fillna(0).sum())


# Extrato — pega todos os períodos selecionados e mantém referência por arquivo
ext_lista = [x for x in ext_todos if x.get("periodo") in periodos_sel]
df_extrato_raw = pd.concat([x["df"] for x in ext_lista], ignore_index=True) if ext_lista else pd.DataFrame()

extrato_categorizado = (not df_extrato_raw.empty and
                        "plano_contas" in df_extrato_raw.columns and
                        df_extrato_raw["plano_contas"].astype(str).str.strip().ne("").any())
usar_extrato = extrato_categorizado

if usar_extrato:
    df_dre     = calc.gerar_dre_do_extrato(df_extrato_raw)
    df_pagar   = calc.gerar_contas_pagar_do_extrato(df_extrato_raw)
    df_receber = calc.gerar_contas_receber_do_extrato(df_extrato_raw)
else:
    # Agrega DRE de múltiplos meses
    frames_dre = []
    for p in periodos_sel:
        item = next((x for x in dre_todos if x.get("periodo") == p), None)
        if item and item.get("df_parsed") is not None and not item["df_parsed"].empty:
            frames_dre.append(item["df_parsed"])
    if frames_dre:
        df_dre_raw = pd.concat(frames_dre, ignore_index=True)
        # Agregar por plano_contas para DRE consolidado
        df_dre = df_dre_raw.groupby("plano_contas", as_index=False).agg(
            valor=("valor","sum"), tipo=("tipo","first"),
            classificacao=("classificacao","first"), justificativa=("justificativa","first"))
    else:
        df_dre = pd.DataFrame()
    df_pagar   = _agregar(pagar_todos, periodos_sel)
    df_receber = _agregar(receber_todos, periodos_sel)

# Sanitizar TODOS os DataFrames na fonte — elimina duplicatas antes de qualquer uso
df_dre       = _limpar_df(df_dre)
df_pagar     = _limpar_df(df_pagar)
df_receber   = _limpar_df(df_receber)
df_financeiro = _limpar_df(_agregar(fin_todos, periodos_sel, campo="df_parsed"))
df_extrato_raw = _limpar_df(df_extrato_raw)

# Total de dias no período selecionado
dias_mes = sum(calendar.monthrange(int(p[:4]), int(p[5:]))[1] for p in periodos_sel)

jog_items = [x for x in jog_todos if x.get("periodo") in periodos_sel]
df_jogadores = pd.concat([x["df"] for x in jog_items], ignore_index=True) if jog_items else pd.DataFrame()
stats_jogadores = ld.calcular_jogadores_por_sessao(df_jogadores)

kpis           = calc.calcular_kpis_dre(df_dre, periodo_sel)
receita_seg    = calc.calcular_receita_por_segmento(df_dre)
despesas_grupo = calc.calcular_despesas_por_grupo(df_dre)
ocupacao       = calc.calcular_ocupacao(df_financeiro, dias_mes, periodo_sel if len(periodos_sel)==1 else None)
ticket_seg     = calc.calcular_ticket_medio(df_receber)
evolucao       = calc.calcular_evolucao_mensal(dre_todos)
mes_label      = mes_label_sidebar

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="et-logo-bar">
  <img src="https://www.escapetime.com.br/public/images/logo.png"
       style="height:40px;filter:brightness(1.1)">
  <div>
    <p style="margin:0;font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;
              font-weight:800;color:#F0F0F0;letter-spacing:.04em">DASHBOARD FINANCEIRO</p>
    <span class="et-periodo-badge">{}</span>
  </div>
</div>
""".format(mes_label.upper()), unsafe_allow_html=True)

if kpis:
    ca1, ca2 = st.columns(2)
    res = kpis.get("resultado_liquido", 0)
    with ca1:
        cls = "alerta-green" if res >= 0 else "alerta-red"
        st.markdown('<div class="{}">{}: <b>{}</b></div>'.format(
            cls, "Resultado positivo" if res >= 0 else "Prejuizo no periodo", fmt_brl(res)),
            unsafe_allow_html=True)
    with ca2:
        pp = kpis.get("pct_pessoal", 0)
        cls2 = "alerta-green" if pp <= 45 else "alerta-org"
        st.markdown('<div class="{}">Custo de pessoal: <b>{:.1f}%</b> da receita (meta &lt;40%)</div>'.format(
            cls2, pp), unsafe_allow_html=True)

if usar_extrato:
    n_rev = int(df_extrato_raw.get("precisa_revisao", pd.Series([False])).sum())
    if n_rev > 0:
        st.warning("{} lançamentos do extrato com baixa confiança — revise na aba Extrato.".format(n_rev))
    else:
        st.info("Dados gerados do extrato bancário categorizado.")
elif not df_extrato_raw.empty:
    st.warning("Extrato disponível mas ainda não categorizado. Vá à aba **Extrato** e clique em Categorizar.")

st.markdown("---")

def _inserir_lancamento_manual(df_extrato_raw, ext_lista):
    """Formulário de inserção manual de lançamento (receita ou despesa)."""
    with st.expander("➕ Inserir lançamento manual (receita ou despesa)"):
        st.caption("Preencha os campos e clique em Adicionar. O lançamento será salvo no extrato do período.")
        fm1, fm2, fm3 = st.columns([1, 2, 1])
        with fm1:
            man_data = st.date_input("Data", value=datetime.now().date(), key="man_data")
        with fm2:
            man_desc = st.text_input("Descrição", key="man_desc", placeholder="Ex: Aluguel extra sala")
        with fm3:
            man_valor = st.number_input("Valor (R$)", key="man_valor", step=0.01,
                                         help="Positivo = entrada / Negativo = saída")

        fm4, fm5, fm6 = st.columns([2, 2, 1])
        with fm4:
            man_plano = selectbox_com_novo("Plano de Contas", cat_mgr.lista_planos(),
                                           key="man_plano", tipo_cat="plano_contas")
            if man_plano is None:
                man_plano = cat_mgr.lista_planos()[0]
        with fm5:
            man_cc = selectbox_com_novo("Centro de Custo", cat_mgr.lista_centros(),
                                        key="man_cc", tipo_cat="centros_custo")
            if man_cc is None:
                man_cc = cat_mgr.lista_centros()[0]
        with fm6:
            man_tipo = st.selectbox("Tipo", ["Despesa", "Receita"], key="man_tipo")

        man_hist = st.text_input("Histórico (opcional)", key="man_hist",
                                  placeholder="Ex: Pix enviado, Pagamento efetuado...")

        if st.button("Adicionar lançamento", type="primary", key="btn_add_lanc"):
            if man_desc.strip() and man_valor != 0:
                novo_lanc = {
                    "data": pd.Timestamp(man_data),
                    "historico": man_hist or ("Pix recebido" if man_valor > 0 else "Pagamento efetuado"),
                    "descricao": man_desc.strip(),
                    "valor": str(man_valor).replace(".", ","),
                    "saldo": "",
                    "valor_num": float(man_valor),
                    "tipo_mov": "Entrada" if man_valor > 0 else "Saída",
                    "plano_contas": man_plano,
                    "centro_custo": man_cc,
                    "tipo": man_tipo,
                    "confianca": "alta",
                    "precisa_revisao": False,
                    "fonte": "manual",
                }
                # Garante que existe ao menos um arquivo de cache para persistir
                if not ext_lista:
                    _arq_manual = os.path.join(
                        os.path.dirname(__file__), ".cache",
                        "manual_{}.parquet".format(periodo_sel.replace("-", "")))
                    _ext_lista_salvo = [{"arquivo": _arq_manual}]
                else:
                    _ext_lista_salvo = ext_lista
                df_novo = pd.concat([df_extrato_raw, pd.DataFrame([novo_lanc])], ignore_index=True)
                for ext_item in _ext_lista_salvo:
                    pers.salvar_extrato_categorizado(df_novo, ext_item["arquivo"])
                st.cache_data.clear()
                st.success("Lançamento '{}' adicionado com sucesso!".format(man_desc))
                st.rerun()
            else:
                st.warning("Preencha a descrição e um valor diferente de zero.")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Visão Geral", "📈 DRE", "💸 Contas a Pagar", "💰 Contas a Receber",
    "🏦 Extrato", "🏠 Salas", "🤖 Insights IA"
])


# ════════════════════════════════════════════════════════════
# TAB 1 — VISÃO GERAL
# ════════════════════════════════════════════════════════════
with tab1:
    if kpis:
        ocp = ocupacao.get("ocupacao_pct")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cor = "green" if kpis["receita_bruta"] >= META_RECEITA_MENSAL else "red"
            card("Receita Bruta", fmt_brl(kpis["receita_bruta"]), cor,
                 "{:.0f}% da meta".format(kpis["atingimento_meta"]))
        with c2:
            card("Total Despesas", fmt_brl(kpis["total_despesas"]), "red")
        with c3:
            cor = "green" if kpis["resultado_liquido"] >= 0 else "red"
            card("Resultado Líquido", fmt_brl(kpis["resultado_liquido"]), cor,
                 "Margem {:.1f}%".format(kpis["margem_liquida"]))
        with c4:
            if ocp is not None:
                cor = "green" if ocp >= 70 else ("orange" if ocp >= 40 else "red")
                card("Ocupação Salas", "{}%".format(ocp), cor,
                     "{} sessões".format(ocupacao.get("sessoes_realizadas")))
            else:
                card("Ocupação Salas", "–", "blue", "Suba o rel. de pedidos")

        st.markdown("---")
        g1, g2, g3 = st.columns(3)
        with g1:
            st.plotly_chart(gauge_chart(kpis["atingimento_meta"], 150, "Meta de Receita"), use_container_width=True, key='chart_0')
        with g2:
            if ocp is not None:
                st.plotly_chart(gauge_chart(ocp, 100, "Ocupação das Salas"), use_container_width=True, key='chart_0b')
            else:
                st.info("Suba o relatório de pedidos.")
        with g3:
            pp = kpis.get("pct_pessoal", 0)
            cor_p = "#22C55E" if pp <= 40 else ("#F97316" if pp <= 55 else "#E31E24")
            fig_p = go.Figure(go.Indicator(
                mode="gauge+number", value=pp,
                title={"text": "Pessoal/Receita", "font": {"size": 13, "color": "#888888"}},
                number={"suffix": "%", "font": {"size": 26, "color": "#F0F0F0"}},
                gauge={"axis": {"range": [0, 80]}, "bar": {"color": cor_p},
                       "bgcolor": "#181818", "bordercolor": "#252525",
                       "threshold": {"line": {"color": "#F0F0F0", "width": 2}, "value": 40}},
            ))
            fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=200,
                                margin=dict(t=40, b=5, l=5, r=5), font_color="#888888")
            st.plotly_chart(fig_p, use_container_width=True, key='chart_1')

        st.markdown("---")
        cr, cd = st.columns(2)
        with cr:
            st.subheader("Receita por Segmento")
            if not receita_seg.empty:
                fig = px.pie(receita_seg, values="valor", names="segmento",
                             color_discrete_sequence=px.colors.qualitative.Vivid, hole=0.45)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", legend_font_color="#888888",
                                  font_color="#888888", margin=dict(t=10, b=10), height=300)
                fig.update_traces(textfont_color="white")
                st.plotly_chart(fig, use_container_width=True, key='chart_2')
        with cd:
            st.subheader("Despesas por Grupo")
            if not despesas_grupo.empty:
                fig = px.bar(despesas_grupo, x="valor_abs", y="grupo", orientation="h",
                             color="valor_abs", color_continuous_scale=["#181818", "#E31E24", "#E31E24"],
                             labels={"valor_abs": "R$", "grupo": ""})
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                  showlegend=False, coloraxis_showscale=False,
                                  margin=dict(t=10, b=10), height=300)
                st.plotly_chart(fig, use_container_width=True, key='chart_3')

        if ticket_seg:
            st.subheader("Ticket Médio por Segmento")
            tc = st.columns(len(ticket_seg))
            for i, (seg, d) in enumerate(ticket_seg.items()):
                with tc[i]:
                    card(seg, fmt_brl(d["ticket_medio"]), "blue",
                         "{} transações".format(d["total_transacoes"]))

        tk_p = ocupacao.get("ticket_medio_pedidos")
        if tk_p:
            st.info("**Ticket médio real (pedidos):** {}".format(fmt_brl(tk_p)))
    else:
        st.info("Sem dados para {}. Adicione os arquivos no Drive e clique Atualizar.".format(mes_label))

    if not evolucao.empty and len(evolucao) > 1:
        st.markdown("---")
        st.subheader("Evolução Mensal")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evolucao["periodo"], y=evolucao["receita_bruta"],
                             name="Receita", marker_color="#E31E24"))
        fig.add_trace(go.Bar(x=evolucao["periodo"], y=evolucao["total_despesas"],
                             name="Despesas", marker_color="#E31E24"))
        fig.add_trace(go.Scatter(x=evolucao["periodo"], y=evolucao["resultado_liquido"],
                                 name="Resultado", line=dict(color="#22C55E", width=3),
                                 mode="lines+markers"))
        fig.add_hline(y=0, line_dash="dot", line_color="#333333")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888", barmode="group",
                          legend=dict(bgcolor="rgba(0,0,0,0)"),
                          margin=dict(t=10, b=10), height=360)
        st.plotly_chart(fig, use_container_width=True, key='chart_4')


# ════════════════════════════════════════════════════════════
# TAB 2 — DRE
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("DRE — {}".format(mes_label))
    badge_fonte(usar_extrato)

    if df_dre.empty:
        st.info("Sem dados de DRE. Categorize o extrato ou adicione o relatório DRE no Drive.")
    else:
        d1, d2 = st.columns([2, 1])
        with d1:
            # Receitas
            rec_df = df_dre[df_dre["valor"] > 0][["plano_contas", "valor", "justificativa"]].copy()
            rec_df = rec_df.rename(columns={"plano_contas":"Plano de Contas","valor":"Valor (R$)","justificativa":"Obs."})
            rec_df["Valor (R$)"] = rec_df["Valor (R$)"].apply(fmt_brl)
            st.markdown("#### Receitas")
            st.dataframe(_limpar_df(rec_df), use_container_width=True, hide_index=True)

            # Despesas agrupadas por grupo DRE
            desp_df = df_dre[df_dre["valor"] < 0].copy()
            desp_df["valor_abs"] = desp_df["valor"].abs()
            desp_df["Grupo"] = desp_df["plano_contas"].map(
                {k: v.split(" ", 1)[1] if " " in v else v
                 for k, v in __import__("config").GRUPO_DRE.items()}
            ).fillna("Outros")
            desp_show = desp_df[["Grupo", "plano_contas", "valor_abs"]].copy()
            desp_show = desp_show.rename(columns={"Grupo":"Grupo","plano_contas":"Plano de Contas","valor_abs":"Valor (R$)"})
            desp_show["Valor (R$)"] = desp_show["Valor (R$)"].apply(fmt_brl)
            desp_show = desp_show.sort_values(["Grupo", "Plano de Contas"])
            st.markdown("#### Despesas")
            st.dataframe(_limpar_df(desp_show), use_container_width=True, hide_index=True)

        with d2:
            st.markdown("#### Resumo")
            rv = kpis.get("receita_bruta", 0)
            dv = kpis.get("total_despesas", 0)
            resv = kpis.get("resultado_liquido", 0)
            st.dataframe(pd.DataFrame({
                "Item": ["(+) Receita Bruta", "(-) Despesas Totais", "(=) Resultado"],
                "Valor": [fmt_brl(rv), "({})".format(fmt_brl(dv)), fmt_brl(resv)],
            }), use_container_width=True, hide_index=True)
            st.markdown("**Indicadores:**")
            card("Margem Líquida", "{:.1f}%".format(kpis.get("margem_liquida", 0)),
                 "green" if kpis.get("margem_liquida", 0) > 0 else "red")
            card("Pessoal / Receita", "{:.1f}%".format(kpis.get("pct_pessoal", 0)),
                 "green" if kpis.get("pct_pessoal", 0) <= 40 else "red")
            card("Aluguel / Receita", "{:.1f}%".format(kpis.get("pct_aluguel", 0)),
                 "green" if kpis.get("pct_aluguel", 0) <= 20 else "red")
            card("Marketing / Receita", "{:.1f}%".format(kpis.get("pct_marketing", 0)),
                 "green" if kpis.get("pct_marketing", 0) <= 15 else "orange")


# ════════════════════════════════════════════════════════════
# TAB 3 — CONTAS A PAGAR
# ════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Contas a Pagar — {}".format(mes_label))
    badge_fonte(usar_extrato)

    if df_pagar.empty:
        st.info("Sem dados de contas a pagar. Categorize o extrato ou adicione o relatório.")
    else:
        total = _soma_coluna(df_pagar, "valor_num")
        cp1, cp2, cp3 = st.columns(3)
        with cp1: card("Total Pago", fmt_brl(total), "red")
        with cp2: card("Nº Lançamentos", str(len(df_pagar)), "blue")
        with cp3:
            if "plano_contas" in df_pagar.columns:
                top = df_pagar.groupby("plano_contas")["valor_num"].sum().idxmax()
                card("Maior Despesa", top, "orange")

        st.markdown("---")

        filtros = [c for c in ["plano_contas", "centro_custo"] if c in df_pagar.columns]
        df_p = mostrar_tabela_com_revisao(df_pagar, "pagar", filtros)

        cols_vis = [c for c in ["data_confirmacao", "destinado", "descricao", "plano_contas",
                                "centro_custo", "situacao", "valor_num", "confianca", "precisa_revisao"]
                    if c in df_p.columns]
        df_show = df_p[cols_vis].copy()
        rename = {"data_confirmacao": "Data", "destinado": "Para", "descricao": "Descrição",
                  "plano_contas": "Plano de Contas", "centro_custo": "Centro de Custo",
                  "situacao": "Situação", "valor_num": "Valor (R$)",
                  "confianca": "Confiança", "precisa_revisao": "Revisar?"}
        df_show = df_show.rename(columns={k: v for k, v in rename.items() if k in df_show.columns})
        if "Valor (R$)" in df_show.columns:
            df_show["Valor (R$)"] = df_show["Valor (R$)"].apply(lambda v: fmt_brl(v) if isinstance(v, (int, float)) else v)
        st.dataframe(_limpar_df(df_show), use_container_width=True, hide_index=True)

        st.markdown("---")
        gc1, gc2 = st.columns(2)
        with gc1:
            if "plano_contas" in df_pagar.columns:
                st.subheader("Por Plano de Contas")
                pc = df_pagar.groupby("plano_contas")["valor_num"].sum().reset_index()
                pc = pc.rename(columns={"plano_contas":"Plano","valor_num":"Valor"})
                pc = pc.sort_values("Valor", ascending=True)
                fig = px.bar(pc, x="Valor", y="Plano", orientation="h",
                             color_discrete_sequence=["#E31E24"])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                  margin=dict(t=5, b=5), height=350)
                st.plotly_chart(fig, use_container_width=True, key='chart_5')
        with gc2:
            if "centro_custo" in df_pagar.columns:
                st.subheader("Por Centro de Custo")
                cc = df_pagar.groupby("centro_custo")["valor_num"].sum().reset_index()
                cc = cc.rename(columns={"centro_custo":"CC","valor_num":"Valor"})
                cc = cc.sort_values("Valor", ascending=False)
                fig2 = px.pie(cc, values="Valor", names="CC",
                              color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                   legend_font_color="#888888", margin=dict(t=5, b=5), height=350)
                st.plotly_chart(fig2, use_container_width=True, key='chart_6')


# ════════════════════════════════════════════════════════════
# TAB 4 — CONTAS A RECEBER
# ════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Contas a Receber — {}".format(mes_label))
    badge_fonte(usar_extrato)

    if df_receber.empty:
        st.info("Sem dados de contas a receber. Categorize o extrato ou adicione o relatório.")
    else:
        total_r = _soma_coluna(df_receber, "valor_num")
        nr = len(df_receber)
        cr1, cr2, cr3 = st.columns(3)
        with cr1: card("Total Recebido", fmt_brl(total_r), "green")
        with cr2: card("Nº Transações", str(nr), "blue")
        with cr3: card("Ticket Médio", fmt_brl(total_r / nr if nr else 0), "blue")

        st.markdown("---")

        filtros_r = [c for c in ["plano_contas", "centro_custo", "historico"] if c in df_receber.columns]
        df_r = mostrar_tabela_com_revisao(df_receber, "receber", filtros_r)

        cols_r = [c for c in ["data_confirmacao", "destinado", "descricao", "plano_contas",
                               "centro_custo", "situacao", "valor_num", "confianca", "precisa_revisao"]
                  if c in df_r.columns]
        df_show_r = df_r[cols_r].copy()
        rename_r = {"data_confirmacao": "Data", "destinado": "De", "descricao": "Descrição",
                    "plano_contas": "Plano de Contas", "centro_custo": "Centro de Custo",
                    "situacao": "Situação", "valor_num": "Valor (R$)",
                    "confianca": "Confiança", "precisa_revisao": "Revisar?"}
        df_show_r = df_show_r.rename(columns={k: v for k, v in rename_r.items() if k in df_show_r.columns})
        if "Valor (R$)" in df_show_r.columns:
            df_show_r["Valor (R$)"] = df_show_r["Valor (R$)"].apply(lambda v: fmt_brl(v) if isinstance(v, (int, float)) else v)
        st.dataframe(_limpar_df(df_show_r), use_container_width=True, hide_index=True)

        gr1, gr2, gr3 = st.columns(3)
        with gr1:
            if "plano_contas" in df_receber.columns:
                st.subheader("Por Segmento")
                ps = df_receber.groupby("plano_contas")["valor_num"].sum().reset_index()
                ps = ps.rename(columns={"plano_contas":"Segmento","valor_num":"Valor"})
                fig = px.pie(ps, values="Valor", names="Segmento",
                             color_discrete_sequence=px.colors.qualitative.Vivid, hole=0.4)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                  legend_font_color="#888888", margin=dict(t=5, b=5), height=280)
                st.plotly_chart(fig, use_container_width=True, key='chart_7')
        with gr2:
            if "historico" in df_receber.columns:
                st.subheader("Por Forma Pgto.")
                ph = df_receber.groupby("historico")["valor_num"].sum().reset_index()
                ph = ph.rename(columns={"historico":"Forma","valor_num":"Valor"})
                fig2 = px.pie(ph, values="Valor", names="Forma",
                              color_discrete_sequence=["#E31E24","#3B82F6","#22C55E","#F97316"], hole=0.4)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                   legend_font_color="#888888", margin=dict(t=5, b=5), height=280)
                st.plotly_chart(fig2, use_container_width=True, key='chart_8')
        with gr3:
            if "centro_custo" in df_receber.columns:
                st.subheader("Por Centro de Custo")
                pcc = df_receber.groupby("centro_custo")["valor_num"].sum().reset_index()
                pcc = cc.rename(columns={"centro_custo":"CC","valor_num":"Valor"})
                pcc = pcc.sort_values("Valor", ascending=True)
                fig3 = px.bar(pcc, x="Valor", y="CC", orientation="h",
                              color_discrete_sequence=["#22C55E"])
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                   margin=dict(t=5, b=5), height=280)
                st.plotly_chart(fig3, use_container_width=True, key='chart_9')


# ════════════════════════════════════════════════════════════
# TAB 5 — EXTRATO BANCÁRIO
# ════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Extrato Bancário — {}".format(mes_label))

    if df_extrato_raw.empty:
        st.info("Coloque o extrato do Inter (CSV ou XLSX) na pasta do Google Drive com 'extrato' no nome. Ex: Extrato-01-05-2026-a-31-05-2026-CSV.csv")
        _inserir_lancamento_manual(df_extrato_raw, ext_lista)
    else:
        ent = _soma_coluna(df_extrato_raw[df_extrato_raw["valor_num"] > 0], "valor_num") if "valor_num" in df_extrato_raw.columns else 0
        sai = _soma_coluna(df_extrato_raw[df_extrato_raw["valor_num"] < 0].assign(valor_num=lambda d: d["valor_num"].abs()), "valor_num") if "valor_num" in df_extrato_raw.columns else 0
        n_rev = int(df_extrato_raw.get("precisa_revisao", pd.Series([False])).sum())

        e1, e2, e3, e4 = st.columns(4)
        with e1: card("Entradas", fmt_brl(ent), "green")
        with e2: card("Saídas", fmt_brl(sai), "red")
        with e3: card("Saldo", fmt_brl(ent - sai), "green" if ent >= sai else "red")
        with e4:
            cor_rev = "orange" if n_rev > 0 else "green"
            card("Pendentes Revisão", str(n_rev), cor_rev)

        st.markdown("---")

        # Verificar se há chave configurada
        if not api_key_ativo:
            st.markdown('<div class="alerta-org">⚠️ Configure a chave Anthropic na barra lateral para usar a categorização por IA.</div>', unsafe_allow_html=True)

        col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
        with col_b1:
            btn_cat_label = "Categorizar com IA" if not extrato_categorizado else "Recategorizar"
            btn_cat = st.button(btn_cat_label, type="primary",
                                use_container_width=True, disabled=not api_key_ativo)
        with col_b2:
            btn_limpar = st.button("Limpar categorização", use_container_width=True,
                                   disabled=not extrato_categorizado)

        if btn_cat and api_key_ativo:
            n_lanc = len(df_extrato_raw)
            with st.spinner("IA categorizando {} lançamentos (plano de contas + centro de custo)...".format(n_lanc)):
                df_cat = cat_ia.categorizar_extrato(df_extrato_raw, max_ia=min(n_lanc, 100))
                # Persistir em disco para cada arquivo de extrato do período
                for ext_item in ext_lista:
                    pers.salvar_extrato_categorizado(df_cat, ext_item["arquivo"])
            st.cache_data.clear()
            st.success("Categorização salva! Recarregando...")
            st.rerun()

        if btn_limpar:
            for ext_item in ext_lista:
                pers.limpar_cache_extrato(ext_item["arquivo"])
            st.cache_data.clear()
            st.rerun()

        # Filtros do extrato
        tipo_sel = st.radio("Exibir", ["Todos", "Entradas", "Saídas"], horizontal=True, key="ext_tipo")
        df_ext = df_extrato_raw.copy()
        if tipo_sel == "Entradas":   df_ext = df_ext[df_ext["valor_num"] > 0]
        elif tipo_sel == "Saídas": df_ext = df_ext[df_ext["valor_num"] < 0]

        if "plano_contas" in df_ext.columns:
            cats = sorted(df_ext["plano_contas"].dropna().astype(str).unique())
            sel_cat = st.multiselect("Plano de Contas", cats, key="ext_plano")
            if sel_cat: df_ext = df_ext[df_ext["plano_contas"].isin(sel_cat)]
        if "centro_custo" in df_ext.columns:
            ccs = sorted(df_ext["centro_custo"].dropna().astype(str).unique())
            sel_cc = st.multiselect("Centro de Custo", ccs, key="ext_cc")
            if sel_cc: df_ext = df_ext[df_ext["centro_custo"].isin(sel_cc)]

        # Tabela principal
        cols_ext = [c for c in ["data", "historico", "descricao", "plano_contas", "centro_custo",
                                 "valor_num", "confianca", "precisa_revisao"] if c in df_ext.columns]
        df_et = df_ext[cols_ext].copy()
        rn_ext = {"data": "Data", "historico": "Tipo", "descricao": "Descrição",
                  "plano_contas": "Plano de Contas", "centro_custo": "Centro de Custo",
                  "valor_num": "Valor (R$)", "confianca": "Confiança", "precisa_revisao": "Revisar?"}
        df_et = df_et.rename(columns={k: v for k, v in rn_ext.items() if k in df_et.columns})
        if "Valor (R$)" in df_et.columns:
            df_et["Valor (R$)"] = df_et["Valor (R$)"].apply(fmt_brl)
        st.dataframe(_limpar_df(df_et), use_container_width=True, hide_index=True)

        # ── Edição manual de categorias ─────────────────────────────────────────
        if extrato_categorizado:
            st.markdown("---")
            n_rev = int(df_extrato_raw["precisa_revisao"].sum()) if "precisa_revisao" in df_extrato_raw.columns else 0

            st.subheader("Edição Manual de Categorias")
            if n_rev > 0:
                st.markdown('<div class="alerta-org">⚠️ {} lançamentos com baixa confiança</div>'.format(n_rev), unsafe_allow_html=True)

            mostrar_so_revisao = st.checkbox("Ver só pendentes de revisão", value=(n_rev > 0 and n_rev < 30), key="chk_revisao")
            st.caption("Edite **Plano de Contas**, **Centro de Custo** e **Tipo** diretamente na tabela. Clique em 💾 Salvar.")

            df_edit_src = df_extrato_raw.copy().reset_index(drop=False)
            if mostrar_so_revisao and "precisa_revisao" in df_edit_src.columns:
                df_edit_src = df_edit_src[df_edit_src["precisa_revisao"] == True]

            cols_ed = [c for c in ["index", "data", "descricao", "valor_num", "plano_contas", "centro_custo", "tipo", "confianca"] if c in df_edit_src.columns]
            df_edit_src = _limpar_df(df_edit_src[cols_ed])

            col_config = {
                "index":        st.column_config.NumberColumn("Idx", width="small"),
                "data":         st.column_config.DateColumn("Data", width="small"),
                "descricao":    st.column_config.TextColumn("Descrição", width="large"),
                "valor_num":    st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", width="small"),
                "plano_contas": st.column_config.SelectboxColumn("Plano de Contas", options=cat_mgr.lista_planos(), width="medium", required=True),
                "centro_custo": st.column_config.SelectboxColumn("Centro de Custo", options=cat_mgr.lista_centros(), width="medium", required=True),
                "tipo":         st.column_config.SelectboxColumn("Tipo", options=["Despesa","Receita"], width="small", required=True),
                "confianca":    st.column_config.TextColumn("Conf.", width="small"),
            }

            df_editado = st.data_editor(
                df_edit_src,
                column_config=col_config,
                disabled=["data", "descricao", "valor_num", "confianca"],
                hide_index=True,
                use_container_width=True,
                key="data_editor_ext_{}".format(periodo_sel),
            )

            if st.button("💾 Salvar edições", type="primary", key="btn_salvar_cat"):
                n_salvo = 0
                for _, row_ed in df_editado.iterrows():
                    idx_orig = row_ed.get("index")
                    if idx_orig is not None and idx_orig in df_extrato_raw.index:
                        desc = str(df_extrato_raw.at[idx_orig, "descricao"]) if "descricao" in df_extrato_raw.columns else ""
                        hist = str(df_extrato_raw.at[idx_orig, "historico"]) if "historico" in df_extrato_raw.columns else ""
                        plano = str(row_ed.get("plano_contas", "Outros"))
                        cc    = str(row_ed.get("centro_custo", "Outros"))
                        tipo  = str(row_ed.get("tipo", "Despesa"))
                        cat_ia.salvar_manual(desc, hist, plano, cc, tipo)
                        df_extrato_raw.at[idx_orig, "plano_contas"] = plano
                        if "centro_custo" in df_extrato_raw.columns:
                            df_extrato_raw.at[idx_orig, "centro_custo"] = cc
                        if "tipo" in df_extrato_raw.columns:
                            df_extrato_raw.at[idx_orig, "tipo"] = tipo
                        if "precisa_revisao" in df_extrato_raw.columns:
                            df_extrato_raw.at[idx_orig, "precisa_revisao"] = False
                        n_salvo += 1
                for ext_item in ext_lista:
                    pers.salvar_extrato_categorizado(df_extrato_raw, ext_item["arquivo"])
                st.cache_data.clear()
                st.success("✓ {} edição(ões) salva(s)!".format(n_salvo))
                st.rerun()

            # Adicionar nova categoria
            with st.expander("➕ Adicionar nova categoria ou centro de custo"):
                st.caption("Itens adicionados aqui aparecem nas listas de seleção em toda a aplicação.")
                col_nc1, col_nc2 = st.columns(2)
                with col_nc1:
                    novo_plano = st.text_input("Novo Plano de Contas", key="inp_novo_plano",
                                                placeholder="ex: Estacionamento")
                    if st.button("Adicionar Plano", key="btn_add_plano"):
                        if novo_plano.strip():
                            cat_mgr.salvar_nova_categoria("plano_contas", novo_plano.strip())
                            st.success("'{}' adicionado!".format(novo_plano))
                            st.rerun()
                with col_nc2:
                    novo_cc = st.text_input("Novo Centro de Custo", key="inp_novo_cc",
                                             placeholder="ex: TruckEscape")
                    if st.button("Adicionar Centro", key="btn_add_cc"):
                        if novo_cc.strip():
                            cat_mgr.salvar_nova_categoria("centros_custo", novo_cc.strip())
                            st.success("'{}' adicionado!".format(novo_cc))
                            st.rerun()

        # Gráficos do extrato categorizado
        if extrato_categorizado:
            st.markdown("---")
            eg1, eg2 = st.columns(2)
            with eg1:
                st.subheader("Saídas por Plano de Contas")
                s_df = df_extrato_raw[df_extrato_raw["valor_num"] < 0].copy()
                s_df = s_df[~s_df.get("plano_contas", pd.Series()).isin(EXCLUIR_DRE)]
                s_df["valor_abs"] = s_df["valor_num"].abs()
                sg = s_df.groupby("plano_contas")["valor_abs"].sum().reset_index()
                sg = sg.rename(columns={"plano_contas":"Plano","valor_abs":"Valor"})
                sg = sg.sort_values("Valor", ascending=True)
                fig_s = px.bar(sg, x="Valor", y="Plano", orientation="h",
                               color_discrete_sequence=["#E31E24"])
                fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                    margin=dict(t=5, b=5), height=380)
                st.plotly_chart(fig_s, use_container_width=True, key='chart_10')
            with eg2:
                st.subheader("Entradas por Plano de Contas")
                e_df = df_extrato_raw[df_extrato_raw["valor_num"] > 0].copy()
                e_df = e_df[~e_df.get("plano_contas", pd.Series()).isin(EXCLUIR_DRE)]
                eg = e_df.groupby("plano_contas")["valor_num"].sum().reset_index()
                eg = eg.rename(columns={"plano_contas":"Plano","valor_num":"Valor"})
                fig_e = px.pie(eg, values="Valor", names="Plano",
                               color_discrete_sequence=px.colors.qualitative.Vivid, hole=0.4)
                fig_e.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                    legend_font_color="#888888", margin=dict(t=5, b=5), height=380)
                st.plotly_chart(fig_e, use_container_width=True, key='chart_11')

        # ── Inserção manual de lançamento ────────────────────────────────────
        st.markdown("---")
        _inserir_lancamento_manual(df_extrato_raw, ext_lista)


# ════════════════════════════════════════════════════════════
# TAB 6 — SALAS
# ════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Salas e Ocupação — {}".format(mes_label))
    cap_mensal = SALAS * SESSOES_POR_DIA * dias_mes

    if df_financeiro.empty:
        s1, s2, s3 = st.columns(3)
        with s1: card("Salas Ativas", str(SALAS), "blue")
        with s2: card("Capacidade/Dia", str(SALAS * SESSOES_POR_DIA), "blue")
        with s3: card("Capacidade Mensal", str(cap_mensal), "blue")
        st.info("Adicione financeiro-mes-ano.xls na pasta do Drive.")
        st.dataframe(pd.DataFrame({
            "Cenário": ["Mínimo (40%)", "Meta (70%)", "Ótimo (90%)"],
            "Sessões/mês": [int(cap_mensal * p) for p in [0.4, 0.7, 0.9]],
            "Sessões/dia": [round(cap_mensal * p / dias_mes, 1) for p in [0.4, 0.7, 0.9]],
        }), use_container_width=True, hide_index=True)
    else:
        # ── Filtro de data ─────────────────────────────────────────────────────
        ano_p, mes_p = int(periodo_sel[:4]), int(periodo_sel[5:])
        data_ini_mes = date(ano_p, mes_p, 1)
        data_fim_mes = date(ano_p, mes_p, dias_mes)

        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            data_ini = st.date_input("De", value=data_ini_mes,
                                     min_value=data_ini_mes, max_value=data_fim_mes, key="sala_ini")
        with col_f2:
            data_fim = st.date_input("Até", value=data_fim_mes,
                                     min_value=data_ini_mes, max_value=data_fim_mes, key="sala_fim")
        with col_f3:
            if st.button("Mês todo", key="sala_reset"):
                data_ini, data_fim = data_ini_mes, data_fim_mes

        dias_filtro = max(1, (data_fim - data_ini).days + 1)
        usando_filtro = (data_ini != data_ini_mes or data_fim != data_fim_mes)

        # Calcula métricas do financeiro com filtro de data
        fin_stats = calc.calcular_financeiro_por_sala(
            df_financeiro, df_jogadores, periodo_sel,
            data_inicio=datetime.combine(data_ini, datetime.min.time()),
            data_fim=datetime.combine(data_fim, datetime.max.time().replace(microsecond=0)),
        )

        if usando_filtro:
            st.info("{} a {} ({} dias) | Capacidade: {} sessões".format(
                data_ini.strftime("%d/%m"), data_fim.strftime("%d/%m"),
                dias_filtro, SALAS * SESSOES_POR_DIA * dias_filtro))

        total_sessoes = fin_stats.get("total_sessoes", 0)
        cap_filtro    = SALAS * SESSOES_POR_DIA * dias_filtro
        ocp_v         = round(total_sessoes / cap_filtro * 100, 1) if cap_filtro > 0 else 0
        media_jog     = fin_stats.get("media_jogadores") or stats_jogadores.get("media_por_sessao")
        tem_repasse   = fin_stats.get("tem_repasse", False)

        # ── KPI Cards ───────────────────────────────────────────────────────────
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1:
            card("Salas Ativas", str(SALAS), "blue")
        with s2:
            cor = "green" if ocp_v >= 70 else ("orange" if ocp_v >= 40 else "red")
            card("Ocupação", "{}%".format(ocp_v), cor, "{} sessões".format(total_sessoes))
        with s3:
            card("Ticket Bruto", fmt_brl(fin_stats.get("ticket_bruto")), "blue")
        with s4:
            if tem_repasse:
                card("Ticket Líquido", fmt_brl(fin_stats.get("ticket_liquido")), "green",
                     "Após repasse (10%) e mkt (3%)")
            else:
                card("Ticket Líquido", "–", "blue", "Suba o financeiro-mes-ano")
        with s5:
            if media_jog:
                card("Média Jogadores", str(media_jog), "blue",
                     "{} total | {} reservas".format(
                         fin_stats.get("total_jogadores") or stats_jogadores.get("total_jogadores", "?"),
                         fin_stats.get("total_reservas") or stats_jogadores.get("total_reservas", "?")))
            else:
                card("Média Jogadores", "–", "blue", "Suba jogadores-mes-ano")
        with s6:
            rpj = fin_stats.get("receita_por_jogador")
            card("Receita/Jogador", fmt_brl(rpj) if rpj else "–",
                 "green" if rpj else "blue",
                 "Líquido ÷ jogadores" if rpj else "Precisa jogadores-mes-ano")

        # Repasse e marketing como alerta
        if tem_repasse:
            rep = fin_stats.get("repasse", 0)
            mkt = fin_stats.get("marketing", 0)
            st.markdown('<div class="alerta-org">Custos plataforma: Repasse <b>{}</b> ({:.0f}%) + Marketing <b>{}</b> ({:.0f}%) = <b>{}</b> descontados da receita bruta</div>'.format(
                fmt_brl(rep), fin_stats.get("pct_repasse", 0),
                fmt_brl(mkt), fin_stats.get("pct_mkt", 0),
                fmt_brl(rep + mkt)), unsafe_allow_html=True)

        st.markdown("---")

        # ── Gauge + Distribuição jogadores ─────────────────────────────────────
        g1, g2 = st.columns([1, 2])
        with g1:
            st.plotly_chart(gauge_chart(ocp_v, 100, "Ocupação das Salas"), use_container_width=True, key='chart_15')
            if stats_jogadores.get("distribuicao"):
                st.markdown("**Jogadores por sessão**")
                dist = stats_jogadores["distribuicao"]
                df_dist = pd.DataFrame(list(dist.items()), columns=["Jogadores", "Sessões"])
                df_dist = df_dist.sort_values("Jogadores")
                fig_dist = px.bar(df_dist, x="Jogadores", y="Sessões",
                                  color_discrete_sequence=["#E31E24"],
                                  text="Sessões")
                fig_dist.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                       margin=dict(t=5, b=5), height=200,
                                       xaxis=dict(tickmode="linear"))
                fig_dist.update_traces(textposition="outside")
                st.plotly_chart(fig_dist, use_container_width=True, key='chart_12')

        with g2:
            por_sala_dict = fin_stats.get("por_sala", {})
            if por_sala_dict:
                st.subheader("Por Sala — Receita e Sessões")
                rows_sala = []
                for sala, d in por_sala_dict.items():
                    cap_sala = SESSOES_POR_DIA * dias_filtro
                    rows_sala.append({
                        "Sala": sala,
                        "Sessões": d["sessoes"],
                        "Ocp%": round(d["sessoes"] / cap_sala * 100, 1),
                        "Bruto": d["receita_bruta"],
                        "Repasse": d["repasse"],
                        "Marketing": d["marketing"],
                        "Líquido": d["receita_liquida"],
                        "Ticket Bruto": d["ticket_bruto"],
                        "Ticket Líquido": d["ticket_liquido"],
                        "Jog. Est.": d["jogadores_estimados"],
                        "R$/Jogador": d["receita_por_jogador"],
                    })
                df_sala = pd.DataFrame(rows_sala).sort_values("Sessões", ascending=True)

                fig_s = px.bar(df_sala, x="Líquido", y="Sala", orientation="h",
                               color="Ocp%",
                               color_continuous_scale=["#E31E24", "#F97316", "#22C55E"],
                               range_color=[0, 100],
                               hover_data=["Sessões", "Ticket Líquido", "Jog. Est."],
                               labels={"Líquido": "Receita Líquida (R$)"})
                fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                    margin=dict(t=5, b=5), height=320)
                st.plotly_chart(fig_s, use_container_width=True, key='chart_13')

        # ── Tabela detalhada por sala ───────────────────────────────────────────
        if por_sala_dict:
            st.markdown("---")
            st.subheader("Tabela detalhada por sala")
            df_sala_show = df_sala.copy()
            cols_show = ["Sala", "Sessões", "Ocp%"]
            if tem_repasse:
                cols_show += ["Bruto", "Repasse", "Marketing", "Líquido", "Ticket Bruto", "Ticket Líquido"]
            else:
                cols_show += ["Bruto", "Ticket Bruto"]
            if media_jog:
                cols_show += ["Jog. Est.", "R$/Jogador"]

            df_sala_show = df_sala_show[cols_show].sort_values("Sessões", ascending=False)
            for col_brl in ["Bruto", "Repasse", "Marketing", "Líquido",
                            "Ticket Bruto", "Ticket Líquido", "R$/Jogador"]:
                if col_brl in df_sala_show.columns:
                    df_sala_show[col_brl] = df_sala_show[col_brl].apply(
                        lambda v: fmt_brl(v) if v is not None and not pd.isna(v) else "–")
            df_sala_show = df_sala_show.rename(columns={"Ocp%": "Ocupação (%)"})
            st.dataframe(_limpar_df(df_sala_show), use_container_width=True, hide_index=True)

        # ── Sessões por dia ─────────────────────────────────────────────────────
        por_dia = fin_stats.get("por_dia", {})
        if por_dia:
            st.markdown("---")
            st.subheader("Sessões por Dia")
            df_dia = pd.DataFrame(list(por_dia.items()), columns=["Data", "Sessões"])
            df_dia = df_dia.sort_values("Data")
            cap_diaria = SALAS * SESSOES_POR_DIA
            fig_d = px.bar(df_dia, x="Data", y="Sessões",
                           color_discrete_sequence=["#E31E24"])
            fig_d.add_hline(y=cap_diaria, line_dash="dot", line_color="#E31E24",
                            annotation_text="Cap. máx. ({})".format(cap_diaria),
                            annotation_font_color="#E31E24")
            fig_d.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#888888",
                                margin=dict(t=10, b=5), height=280)
            st.plotly_chart(fig_d, use_container_width=True, key='chart_14')

            df_dia["Ocp%"] = (df_dia["Sessões"] / cap_diaria * 100).round(1)
            dias_criticos = df_dia[df_dia["Ocp%"] < 30]
            if not dias_criticos.empty:
                st.warning("{} dia(s) com menos de 30% de ocupação:".format(len(dias_criticos)))
                st.dataframe(_limpar_df(dias_criticos).rename(columns={"Ocp%": "Ocupação (%)"}),
                             use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# TAB 7 — INSIGHTS IA
# ════════════════════════════════════════════════════════════
with tab7:
    st.subheader("Insights de Negócio — IA — {}".format(mes_label))

    if not api_key_ativo:
        st.warning("""
        **A chave da API Anthropic não está configurada.**

        Para usar os insights de IA:
        1. Acesse [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
        2. Crie uma conta e gere uma chave (começa com `sk-ant-...`)
        3. Cole a chave na barra lateral esquerda e clique em **Salvar chave no .env**
        4. Volte aqui e clique em **Gerar Análise**
        """)
    elif not kpis:
        st.info("Sem dados financeiros para o período. Selecione um período com dados.")
    else:
        st.markdown("""
        A IA analisa todos os dados do período — financeiro, ocupação, custos, histórico —
        e gera recomendações acionáveis específicas para o seu negócio.
        """)

        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            gerar = st.button("Gerar Análise", type="primary", use_container_width=True)
        with col_info:
            st.caption("Usa Claude Sonnet — leva ~15 segundos. Cada análise consome créditos da API.")

        # Cache da análise na sessão para não refazer sem necessidade
        cache_key = "insights_{}_{}".format(periodo_sel, hash(str(kpis.get("receita_bruta", 0))))
        if cache_key not in st.session_state:
            st.session_state[cache_key] = None

        if gerar:
            with st.spinner("Claude está analisando seus dados..."):
                resultado = ins_ia.gerar_insights(
                    api_key=api_key_ativo,
                    periodo=mes_label,
                    kpis=kpis,
                    fin_stats=fin_stats if "fin_stats" in dir() else {},
                    stats_jogadores=stats_jogadores,
                    evolucao_df=evolucao,
                )
                st.session_state[cache_key] = resultado

        resultado = st.session_state.get(cache_key)

        if resultado:
            if "erro" in resultado:
                st.error("Erro na análise: {}".format(resultado["erro"]))
            else:
                # ── Semáforo e resumo ─────────────────────────────────────────
                semaforo = resultado.get("semaforo", "amarelo")
                cores_sem = {"vermelho": "#E31E24", "amarelo": "#f59e0b", "verde": "#22C55E"}
                emoji_sem = {"vermelho": "🔴", "amarelo": "🟡", "verde": "🟢"}
                cor_sem = cores_sem.get(semaforo, "#f59e0b")
                em_sem = emoji_sem.get(semaforo, "🟡")

                st.markdown(
                    '<div style="background:{};border-radius:12px;padding:16px 20px;margin-bottom:16px;">'
                    '<p style="font-size:1.1rem;font-weight:700;color:white;margin:0">{} Situação: {}</p>'
                    '<p style="color:rgba(255,255,255,0.9);margin:8px 0 0 0">{}</p>'
                    '</div>'.format(
                        cor_sem, em_sem, semaforo.upper(),
                        resultado.get("resumo_executivo", "")),
                    unsafe_allow_html=True)

                # ── Alertas ───────────────────────────────────────────────────
                alertas = resultado.get("alertas", [])
                if alertas:
                    st.markdown("---")
                    st.subheader("⚠️ Alertas")
                    for al in alertas:
                        urg = al.get("urgencia", "media")
                        cor_urg = {"alta": "alerta-red", "media": "alerta-org", "baixa": "alerta-green"}.get(urg, "alerta-org")
                        st.markdown(
                            '<div class="{}">'
                            '<b>{}</b> <span style="float:right;font-size:.75rem">Impacto: {} | Urgência: {}</span><br>'
                            '<span style="color:#e2e8f0">{}</span>'
                            '</div>'.format(
                                cor_urg, al.get("titulo", ""),
                                al.get("impacto", ""), urg,
                                al.get("descricao", "")),
                            unsafe_allow_html=True)

                # ── Oportunidades ─────────────────────────────────────────────
                opps = resultado.get("oportunidades", [])
                if opps:
                    st.markdown("---")
                    st.subheader("💡 Oportunidades")
                    cols_op = st.columns(min(len(opps), 3))
                    for i, op in enumerate(opps):
                        with cols_op[i % 3]:
                            prazo = op.get("prazo", "medio")
                            cor_prazo = {"curto": "#22C55E", "medio": "#3B82F6", "longo": "#E31E24"}.get(prazo, "#3B82F6")
                            st.markdown(
                                '<div class="metric-card blue">'
                                '<p class="metric-lbl">{} prazo</p>'
                                '<p style="font-weight:700;color:#f1f5f9;margin:4px 0">{}</p>'
                                '<p style="color:#94a3b8;font-size:.82rem">{}</p>'
                                '<p style="color:{};font-size:.85rem;margin-top:6px"><b>{}</b></p>'
                                '</div>'.format(
                                    prazo.capitalize(), op.get("titulo", ""),
                                    op.get("descricao", ""),
                                    cor_prazo, op.get("potencial", "")),
                                unsafe_allow_html=True)

                # ── Recomendações ─────────────────────────────────────────────
                recs = resultado.get("recomendacoes", [])
                if recs:
                    st.markdown("---")
                    st.subheader("✅ Recomendações (por prioridade)")
                    recs_sorted = sorted(recs, key=lambda x: x.get("prioridade", 99))
                    for i, rec in enumerate(recs_sorted):
                        with st.expander("#{} — {}".format(i + 1, rec.get("acao", ""))):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown("**Como fazer:**")
                                st.markdown(rec.get("como", ""))
                            with c2:
                                st.markdown("**Resultado esperado:**")
                                st.markdown(rec.get("resultado_esperado", ""))

                # ── Projeção ──────────────────────────────────────────────────
                proj = resultado.get("projecao", {})
                if proj:
                    st.markdown("---")
                    st.subheader("📈 Para virar o resultado")
                    p1, p2, p3 = st.columns(3)
                    with p1:
                        card("Receita mínima necessária",
                             proj.get("meta_receita_minima", fmt_brl(META_RECEITA_MENSAL)),
                             "orange")
                    with p2:
                        st.markdown("**O que precisa mudar:**")
                        st.markdown(proj.get("para_empatar", ""))
                    with p3:
                        st.markdown("**Principais alavancas:**")
                        for alav in proj.get("alavancas_principais", []):
                            st.markdown("• {}".format(alav))

                st.caption("Análise gerada por Claude Sonnet em {}".format(
                    datetime.now().strftime("%d/%m/%Y %H:%M")))
