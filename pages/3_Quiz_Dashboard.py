"""
Quiz Dashboard — Escape Time Brasil
Visualização consolidada de resultados de treinamento.
"""

import streamlit as st
import json
import pathlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Quiz Dashboard — Escape Time Brasil",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

RESULTS_FILE = pathlib.Path(__file__).parent.parent / "quiz_results.json"

# ── Paleta Escape Time ────────────────────────────────────────────────────────
COR_VERMELHO = "#e63946"
COR_LARANJA  = "#f4a261"
COR_FUNDO    = "#0f0f1a"
COR_CARD     = "#1a1a2e"

st.markdown(f"""
<style>
.stApp {{ background-color: {COR_FUNDO}; }}
h1 {{ color: {COR_VERMELHO} !important; }}
h2, h3 {{ color: {COR_LARANJA} !important; }}
.metric-card {{
    background: {COR_CARD};
    border: 1px solid {COR_VERMELHO}66;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}}
.metric-value {{ font-size: 2.5rem; font-weight: bold; color: {COR_VERMELHO}; }}
.metric-label {{ font-size: 0.9rem; color: #888; margin-top: 4px; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ background-color: {COR_VERMELHO} !important; color: white !important; padding: 10px; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #2d2d5e; color: #e0e0e0; }}
tr:hover td {{ background-color: {COR_CARD}; }}
</style>
""", unsafe_allow_html=True)

# ── Carregar dados ────────────────────────────────────────────────────────────

def load_results() -> list:
    if RESULTS_FILE.exists():
        try:
            return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def reset_results():
    RESULTS_FILE.write_text("[]", encoding="utf-8")

# ── Cabeçalho ────────────────────────────────────────────────────────────────

st.markdown("# 📊 Quiz Dashboard — Escape Time Brasil")
st.markdown("*Resultados consolidados de treinamento corporativo*")
st.markdown("---")

results = load_results()

col_reload, col_reset, _ = st.columns([1, 1, 6])
with col_reload:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()
with col_reset:
    if st.button("🗑️ Apagar tudo", type="secondary", use_container_width=True):
        st.session_state["confirm_reset"] = True

if st.session_state.get("confirm_reset"):
    st.warning("⚠️ **Confirmar exclusão de todos os resultados?**")
    c1, c2, _ = st.columns([1, 1, 6])
    with c1:
        if st.button("✅ Confirmar", type="primary"):
            reset_results()
            st.session_state["confirm_reset"] = False
            st.success("Resultados apagados com sucesso.")
            st.rerun()
    with c2:
        if st.button("❌ Cancelar"):
            st.session_state["confirm_reset"] = False
            st.rerun()

if not results:
    st.info("ℹ️ Nenhum resultado registrado ainda. Os dados aparecerão aqui após os participantes concluírem o quiz.")
    st.stop()

# ── Preparar DataFrame ────────────────────────────────────────────────────────

df = pd.DataFrame(results)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["score"] = pd.to_numeric(df["score"], errors="coerce")
df["acertos"] = pd.to_numeric(df["acertos"], errors="coerce")
df["total"] = pd.to_numeric(df["total"], errors="coerce")

df_warmup = df[df["tipo"] == "warmup"]
df_pos    = df[df["tipo"] == "pos"]

# ── KPIs principais ───────────────────────────────────────────────────────────

st.markdown("## 📈 Visão Geral")
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(df)}</div>
        <div class="metric-label">Respostas totais</div>
    </div>""", unsafe_allow_html=True)

with k2:
    participantes = df["email"].nunique() if "email" in df.columns else len(df)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{participantes}</div>
        <div class="metric-label">Participantes únicos</div>
    </div>""", unsafe_allow_html=True)

with k3:
    empresas = df["empresa"].nunique() if "empresa" in df.columns else "-"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{empresas}</div>
        <div class="metric-label">Empresas</div>
    </div>""", unsafe_allow_html=True)

with k4:
    media_geral = df["score"].mean()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{media_geral:.1f}%</div>
        <div class="metric-label">Score médio geral</div>
    </div>""", unsafe_allow_html=True)

with k5:
    conceito_a = len(df[df["conceito"] == "A"])
    pct_a = (conceito_a / len(df) * 100) if len(df) > 0 else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{pct_a:.0f}%</div>
        <div class="metric-label">Conceito A</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Comparativo Warm-up vs Pós ────────────────────────────────────────────────

if len(df_warmup) > 0 and len(df_pos) > 0:
    st.markdown("## 🔄 Comparativo: Warm-up × Pós-treinamento")
    cw1, cw2, cw3 = st.columns(3)
    with cw1:
        delta = df_pos["score"].mean() - df_warmup["score"].mean()
        st.metric("Média Warm-up", f"{df_warmup['score'].mean():.1f}%")
        st.metric("Média Pós-treinamento", f"{df_pos['score'].mean():.1f}%",
                  delta=f"{delta:+.1f}%")
    with cw2, cw3:
        # Gráfico de evolução por participante (se houver nomes comuns)
        if "nome" in df.columns:
            pivot = df.pivot_table(index="nome", columns="tipo", values="score", aggfunc="mean").reset_index()
            if "warmup" in pivot.columns and "pos" in pivot.columns:
                pivot = pivot.dropna()
                if not pivot.empty:
                    fig = go.Figure()
                    for _, row in pivot.iterrows():
                        fig.add_trace(go.Scatter(
                            x=["Warm-up", "Pós"],
                            y=[row["warmup"], row["pos"]],
                            mode="lines+markers",
                            name=row["nome"],
                            line=dict(width=2),
                        ))
                    fig.update_layout(
                        title="Evolução por participante",
                        paper_bgcolor=COR_FUNDO,
                        plot_bgcolor=COR_CARD,
                        font=dict(color="#e0e0e0"),
                        yaxis=dict(range=[0, 100], title="Score (%)"),
                        height=300,
                    )
                    with cw2:
                        st.plotly_chart(fig, use_container_width=True)

# ── Distribuição de conceitos ─────────────────────────────────────────────────

st.markdown("## 🏅 Distribuição de Conceitos")
gc1, gc2 = st.columns(2)

conceito_counts = df["conceito"].value_counts().reindex(["A", "B", "C", "D"], fill_value=0)
cores_conceito = {"A": "#2dc653", "B": "#f4a261", "C": "#f7b731", "D": "#e63946"}

with gc1:
    fig_pie = px.pie(
        names=conceito_counts.index,
        values=conceito_counts.values,
        color=conceito_counts.index,
        color_discrete_map=cores_conceito,
        title="Distribuição geral",
    )
    fig_pie.update_layout(
        paper_bgcolor=COR_FUNDO,
        font=dict(color="#e0e0e0"),
        height=320,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with gc2:
    fig_bar = px.bar(
        x=conceito_counts.index,
        y=conceito_counts.values,
        color=conceito_counts.index,
        color_discrete_map=cores_conceito,
        labels={"x": "Conceito", "y": "Participantes"},
        title="Quantidade por conceito",
    )
    fig_bar.update_layout(
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_CARD,
        font=dict(color="#e0e0e0"),
        showlegend=False,
        height=320,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Score por empresa ─────────────────────────────────────────────────────────

if "empresa" in df.columns and df["empresa"].nunique() > 1:
    st.markdown("## 🏢 Score por Empresa")
    empresa_stats = (
        df.groupby("empresa")
        .agg(participantes=("nome", "count"), media_score=("score", "mean"))
        .reset_index()
        .sort_values("media_score", ascending=False)
    )
    fig_emp = px.bar(
        empresa_stats,
        x="empresa",
        y="media_score",
        color="media_score",
        color_continuous_scale=[[0, COR_VERMELHO], [0.5, COR_LARANJA], [1, "#2dc653"]],
        text="media_score",
        labels={"empresa": "Empresa", "media_score": "Score médio (%)"},
    )
    fig_emp.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_emp.update_layout(
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_CARD,
        font=dict(color="#e0e0e0"),
        coloraxis_showscale=False,
        height=350,
    )
    st.plotly_chart(fig_emp, use_container_width=True)

# ── Tabela completa de participantes ─────────────────────────────────────────

st.markdown("## 📋 Tabela de Resultados")

# Filtros
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    tipo_filter = st.selectbox("Tipo de quiz", ["Todos", "Warm-up", "Pós-treinamento"])
with col_f2:
    conceito_filter = st.multiselect("Conceito", ["A", "B", "C", "D"], default=["A", "B", "C", "D"])
with col_f3:
    if "empresa" in df.columns:
        empresas_list = ["Todas"] + sorted(df["empresa"].dropna().unique().tolist())
        empresa_filter = st.selectbox("Empresa", empresas_list)
    else:
        empresa_filter = "Todas"

df_filtered = df.copy()
if tipo_filter == "Warm-up":
    df_filtered = df_filtered[df_filtered["tipo"] == "warmup"]
elif tipo_filter == "Pós-treinamento":
    df_filtered = df_filtered[df_filtered["tipo"] == "pos"]
if conceito_filter:
    df_filtered = df_filtered[df_filtered["conceito"].isin(conceito_filter)]
if empresa_filter != "Todas" and "empresa" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["empresa"] == empresa_filter]

# Colunas para exibição
display_cols = []
col_map = {
    "nome": "Nome",
    "empresa": "Empresa",
    "email": "E-mail / Matrícula",
    "tipo": "Quiz",
    "acertos": "Acertos",
    "total": "Total",
    "score": "Score (%)",
    "conceito": "Conceito",
    "timestamp": "Data/Hora",
}
for c in col_map:
    if c in df_filtered.columns:
        display_cols.append(c)

df_show = df_filtered[display_cols].rename(columns=col_map).copy()
if "Score (%)" in df_show.columns:
    df_show["Score (%)"] = df_show["Score (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
if "Quiz" in df_show.columns:
    df_show["Quiz"] = df_show["Quiz"].map({"warmup": "Warm-up", "pos": "Pós-treinamento"})
if "Data/Hora" in df_show.columns:
    df_show["Data/Hora"] = pd.to_datetime(df_show["Data/Hora"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")

st.dataframe(df_show, use_container_width=True, hide_index=True)

# Exportar CSV
csv = df_show.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Exportar CSV",
    data=csv,
    file_name=f"quiz_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption("📊 Escape Time Brasil — Quiz Dashboard v1.0")
