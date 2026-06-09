import pandas as pd
from config import (SALAS, SESSOES_POR_DIA, META_RECEITA_MENSAL,
                   GRUPO_DRE, EXCLUIR_DRE, SEGMENTOS, PLANO_CONTAS_RECEITA)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _parse_valor(v):
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.replace("(", "").replace(")", "")
    last_comma = s.rfind(",")
    last_period = s.rfind(".")
    if last_comma > last_period:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        result = float(s)
        return -abs(result) if neg else result
    except ValueError:
        return 0.0


# ── KPIs do DRE (funciona para DRE do xlsx OU gerado do extrato) ─────────────
def calcular_kpis_dre(df_dre: pd.DataFrame, periodo: str) -> dict:
    if df_dre.empty:
        return {}
    receitas = df_dre[df_dre["valor"] > 0]["valor"].sum()
    despesas = abs(df_dre[df_dre["valor"] < 0]["valor"].sum())
    resultado = receitas - despesas
    margem = (resultado / receitas * 100) if receitas > 0 else 0

    pessoal_cats = ["Pro Labore", "Pessoal", "Imposto sobre pessoal (INSS, FGTS)"]
    pessoal = abs(df_dre[df_dre["plano_contas"].isin(pessoal_cats)]["valor"].sum())
    aluguel = abs(df_dre[df_dre["plano_contas"] == "Aluguel"]["valor"].sum())
    marketing = abs(df_dre[df_dre["plano_contas"] == "Marketing e publicidade"]["valor"].sum())

    return {
        "periodo": periodo,
        "receita_bruta": receitas,
        "total_despesas": despesas,
        "resultado_liquido": resultado,
        "margem_liquida": margem,
        "pessoal": pessoal,
        "aluguel": aluguel,
        "marketing": marketing,
        "pct_pessoal": (pessoal / receitas * 100) if receitas > 0 else 0,
        "pct_aluguel": (aluguel / receitas * 100) if receitas > 0 else 0,
        "pct_marketing": (marketing / receitas * 100) if receitas > 0 else 0,
        "atingimento_meta": (receitas / META_RECEITA_MENSAL * 100) if META_RECEITA_MENSAL > 0 else 0,
        "break_even": META_RECEITA_MENSAL,
    }


# ── Gerar DRE a partir do extrato categorizado ───────────────────────────────
def gerar_dre_do_extrato(df_extrato: pd.DataFrame) -> pd.DataFrame:
    """
    Converte o extrato categorizado em um DataFrame no formato do DRE:
    colunas: plano_contas, valor, tipo (Receita/Despesa)
    Exclui transferências internas e agrega por plano_contas.
    """
    if df_extrato.empty or "plano_contas" not in df_extrato.columns:
        return pd.DataFrame()

    df = df_extrato.copy()

    # Excluir transferências internas do DRE
    df = df[~df["plano_contas"].isin(EXCLUIR_DRE)]

    # Garantir valor_num
    if "valor_num" not in df.columns:
        df["valor_num"] = df.get("valor", pd.Series(dtype=float)).apply(_parse_valor)

    # Receitas: valor positivo → mantém positivo
    # Despesas: valor negativo → mantém negativo
    # Corrigir sinal com base no tipo se divergir
    if "tipo" in df.columns:
        mask_rec = df["tipo"] == "Receita"
        mask_des = df["tipo"] == "Despesa"
        df.loc[mask_rec, "valor_num"] = df.loc[mask_rec, "valor_num"].abs()
        df.loc[mask_des, "valor_num"] = -df.loc[mask_des, "valor_num"].abs()

    # Agregar por plano_contas
    agregado = df.groupby("plano_contas")["valor_num"].sum().reset_index()
    agregado.columns = ["plano_contas", "valor"]
    agregado["tipo"] = agregado["valor"].apply(lambda v: "Receita" if v > 0 else "Despesa")
    agregado["grupo_dre"] = agregado["plano_contas"].map(GRUPO_DRE).fillna("1.1 Despesas administrativas e comerciais")
    agregado["classificacao"] = agregado["plano_contas"]
    agregado["justificativa"] = ""

    return agregado.sort_values(["tipo", "plano_contas"], ascending=[False, True]).reset_index(drop=True)


# ── Contas a Pagar do extrato ─────────────────────────────────────────────────
def gerar_contas_pagar_do_extrato(df_extrato: pd.DataFrame) -> pd.DataFrame:
    if df_extrato.empty or "valor_num" not in df_extrato.columns:
        return pd.DataFrame()
    df = df_extrato.copy()
    # Saídas = negativo; excluir transferências internas
    saidas = df[(df["valor_num"] < 0) & ~df.get("plano_contas", pd.Series()).isin(EXCLUIR_DRE)]
    if saidas.empty:
        return pd.DataFrame()

    saidas = saidas.copy()
    saidas["valor_abs"] = saidas["valor_num"].abs()

    # Renomear para padrão do sistema
    col_map = {
        "data": "data_confirmacao",
        "descricao": "descricao",
        "historico": "historico",
        "plano_contas": "plano_contas",
        "centro_custo": "centro_custo",
        "valor_abs": "valor_num",
        "confianca": "confianca",
        "precisa_revisao": "precisa_revisao",
    }
    cols_ok = {k: v for k, v in col_map.items() if k in saidas.columns}
    resultado = saidas.rename(columns=cols_ok)[list(cols_ok.values())].copy()

    if "data_confirmacao" in resultado.columns:
        resultado["data_confirmacao"] = pd.to_datetime(resultado["data_confirmacao"], errors="coerce").dt.strftime("%d/%m/%Y")

    resultado["situacao"] = "Confirmado"
    resultado["destinado"] = resultado.get("descricao", pd.Series())
    return resultado.reset_index(drop=True)


# ── Contas a Receber do extrato ───────────────────────────────────────────────
def gerar_contas_receber_do_extrato(df_extrato: pd.DataFrame) -> pd.DataFrame:
    if df_extrato.empty or "valor_num" not in df_extrato.columns:
        return pd.DataFrame()
    df = df_extrato.copy()
    entradas = df[(df["valor_num"] > 0) & ~df.get("plano_contas", pd.Series()).isin(EXCLUIR_DRE)]
    if entradas.empty:
        return pd.DataFrame()

    entradas = entradas.copy()
    col_map = {
        "data": "data_confirmacao",
        "descricao": "descricao",
        "historico": "historico",
        "plano_contas": "plano_contas",
        "centro_custo": "centro_custo",
        "valor_num": "valor_num",
        "confianca": "confianca",
        "precisa_revisao": "precisa_revisao",
    }
    cols_ok = {k: v for k, v in col_map.items() if k in entradas.columns}
    resultado = entradas.rename(columns=cols_ok)[list(cols_ok.values())].copy()

    if "data_confirmacao" in resultado.columns:
        resultado["data_confirmacao"] = pd.to_datetime(resultado["data_confirmacao"], errors="coerce").dt.strftime("%d/%m/%Y")

    resultado["situacao"] = "Confirmado"
    resultado["destinado"] = resultado.get("descricao", pd.Series())
    return resultado.reset_index(drop=True)


# ── Receita por segmento ──────────────────────────────────────────────────────
def calcular_receita_por_segmento(df_dre: pd.DataFrame) -> pd.DataFrame:
    if df_dre.empty:
        return pd.DataFrame()
    receitas = df_dre[df_dre["valor"] > 0].copy()
    receitas["segmento"] = receitas["plano_contas"].map(SEGMENTOS).fillna("Outros")
    return receitas.groupby("segmento")["valor"].sum().reset_index().sort_values("valor", ascending=False)


# ── Despesas por grupo ────────────────────────────────────────────────────────
def calcular_despesas_por_grupo(df_dre: pd.DataFrame) -> pd.DataFrame:
    if df_dre.empty:
        return pd.DataFrame()
    desp = df_dre[df_dre["valor"] < 0].copy()
    desp["grupo"] = desp["plano_contas"].map(GRUPO_DRE).fillna("Outros").str.replace(r"^\d+\.\d+ ", "", regex=True)
    desp["valor_abs"] = desp["valor"].abs()
    return desp.groupby("grupo")["valor_abs"].sum().reset_index().sort_values("valor_abs", ascending=False)


# ── Ticket médio ──────────────────────────────────────────────────────────────
def calcular_ticket_medio(df_receber: pd.DataFrame) -> dict:
    if df_receber.empty or "valor_num" not in df_receber.columns:
        return {}
    if "plano_contas" not in df_receber.columns:
        return {}
    excluir = {"Transferência interna", "Coorking - HUB"}
    df = df_receber[~df_receber["plano_contas"].isin(excluir)].copy()
    resultado = {}
    for seg, grupo in df.groupby("plano_contas"):
        if seg not in PLANO_CONTAS_RECEITA:
            continue
        vals = grupo["valor_num"][grupo["valor_num"] > 10]
        if len(vals) > 0:
            resultado[SEGMENTOS.get(seg, seg)] = {
                "ticket_medio": round(vals.mean(), 2),
                "total_transacoes": len(vals),
                "receita_total": round(vals.sum(), 2),
            }
    return resultado


# ── Ocupação das salas ────────────────────────────────────────────────────────
def calcular_ocupacao(df_pedidos: pd.DataFrame, dias_no_mes: int = 30,
                      periodo: str = None, data_inicio=None, data_fim=None) -> dict:
    if df_pedidos.empty:
        return {"ocupacao_pct": None, "sessoes_realizadas": None, "capacidade_total": None}

    df = df_pedidos.copy()

    # Status aprovados
    if "status_norm" in df.columns:
        df = df[df["status_norm"].isin(["aprovado", "confirmado", "realizado", "concluído", "ok"])]
    else:
        col_s = next((c for c in df.columns if "status" in c.lower()), None)
        if col_s:
            df = df[df[col_s].astype(str).str.lower().isin(["aprovado", "confirmado", "realizado"])]

    # Filtrar por período (mês/ano)
    if "data_reserva_parsed" in df.columns:
        if data_inicio and data_fim:
            df = df[(df["data_reserva_parsed"] >= pd.Timestamp(data_inicio)) &
                    (df["data_reserva_parsed"] <= pd.Timestamp(data_fim))]
        elif periodo:
            ano, mes = int(periodo[:4]), int(periodo[5:])
            df = df[(df["data_reserva_parsed"].dt.year == ano) &
                    (df["data_reserva_parsed"].dt.month == mes)]

    sessoes = len(df)
    capacidade = SALAS * SESSOES_POR_DIA * dias_no_mes
    ocupacao = (sessoes / capacidade * 100) if capacidade > 0 else 0

    ticket_medio = None
    if "valor_num" in df.columns and sessoes > 0:
        vals = df["valor_num"][df["valor_num"] > 0]
        if not vals.empty:
            ticket_medio = round(vals.mean(), 2)

    por_sala = {}
    if "sala_nome" in df.columns:
        por_sala = df.groupby("sala_nome").size().to_dict()

    por_dia = {}
    if "data_reserva_parsed" in df.columns and not df.empty:
        por_dia = df.groupby(df["data_reserva_parsed"].dt.date).size().to_dict()

    return {
        "ocupacao_pct": round(ocupacao, 1),
        "sessoes_realizadas": sessoes,
        "capacidade_total": capacidade,
        "sessoes_por_dia_media": round(sessoes / dias_no_mes, 1) if dias_no_mes > 0 else 0,
        "ticket_medio_pedidos": ticket_medio,
        "por_sala": por_sala,
        "por_dia": por_dia,
    }


# ── Análise financeira por sala ───────────────────────────────────────────────
def calcular_financeiro_por_sala(df_fin: pd.DataFrame,
                                  df_jog: pd.DataFrame | None = None,
                                  periodo: str = None,
                                  data_inicio=None, data_fim=None) -> dict:
    """
    Usa o relatório financeiro (com Repasse e Marketing) para calcular
    métricas por sala com maior acurácia.
    Retorna dict com DataFrames e KPIs.
    """
    if df_fin.empty:
        return {}

    df = df_fin.copy()

    # Filtrar aprovados
    if "status_norm" in df.columns:
        df = df[df["status_norm"].isin(["aprovado", "confirmado", "realizado"])]
    elif "status" in df.columns:
        df = df[df["status"].astype(str).str.lower().str.strip().isin(["aprovado", "confirmado"])]

    if df.empty:
        return {}

    # Filtro por data
    if "data_reserva_parsed" in df.columns:
        if data_inicio and data_fim:
            df = df[(df["data_reserva_parsed"] >= pd.Timestamp(data_inicio)) &
                    (df["data_reserva_parsed"] <= pd.Timestamp(data_fim))]
        elif periodo:
            ano, mes = int(periodo[:4]), int(periodo[5:])
            df = df[(df["data_reserva_parsed"].dt.year == ano) &
                    (df["data_reserva_parsed"].dt.month == mes)]

    if df.empty:
        return {}

    tem_repasse = "repasse_num" in df.columns and df["repasse_num"].sum() > 0

    # Média de jogadores por sessão do arquivo de jogadores
    media_jog = None
    total_jog = None
    if df_jog is not None and not df_jog.empty and "reserva_id" in df_jog.columns:
        por_res = df_jog.groupby("reserva_id").size()
        media_jog = round(por_res.mean(), 1)
        total_jog = len(df_jog)

    # Agregado por sala
    agg = {}
    col_sala = "sala_nome" if "sala_nome" in df.columns else "unidade" if "unidade" in df.columns else None

    if col_sala:
        for sala, g in df.groupby(col_sala):
            bruto   = g["valor_num"].sum() if "valor_num" in g.columns else 0
            repasse = g["repasse_num"].sum() if "repasse_num" in g.columns else 0
            mkt     = g["marketing_num"].sum() if "marketing_num" in g.columns else 0
            liquido = g["valor_liquido"].sum() if "valor_liquido" in g.columns else bruto
            sessoes = len(g)
            agg[sala] = {
                "sessoes": sessoes,
                "receita_bruta": round(bruto, 2),
                "repasse": round(repasse, 2),
                "marketing": round(mkt, 2),
                "receita_liquida": round(liquido, 2),
                "ticket_bruto": round(bruto / sessoes, 2) if sessoes > 0 else 0,
                "ticket_liquido": round(liquido / sessoes, 2) if sessoes > 0 else 0,
                "jogadores_estimados": round(sessoes * media_jog) if media_jog else None,
                "receita_por_jogador": round(liquido / (sessoes * media_jog), 2)
                    if media_jog and sessoes > 0 else None,
            }

    # Totais
    total_sessoes = len(df)
    receita_bruta_t = df["valor_num"].sum() if "valor_num" in df.columns else 0
    repasse_t  = df["repasse_num"].sum() if "repasse_num" in df.columns else 0
    mkt_t      = df["marketing_num"].sum() if "marketing_num" in df.columns else 0
    liquido_t  = df["valor_liquido"].sum() if "valor_liquido" in df.columns else receita_bruta_t

    # Sessões por dia
    por_dia = {}
    if "data_reserva_parsed" in df.columns:
        por_dia = df.groupby(df["data_reserva_parsed"].dt.date).size().to_dict()

    return {
        "por_sala": agg,
        "total_sessoes": total_sessoes,
        "receita_bruta": round(receita_bruta_t, 2),
        "repasse": round(repasse_t, 2),
        "marketing": round(mkt_t, 2),
        "receita_liquida": round(liquido_t, 2),
        "pct_repasse": round(repasse_t / receita_bruta_t * 100, 1) if receita_bruta_t > 0 else 0,
        "pct_mkt": round(mkt_t / receita_bruta_t * 100, 1) if receita_bruta_t > 0 else 0,
        "ticket_bruto": round(receita_bruta_t / total_sessoes, 2) if total_sessoes > 0 else 0,
        "ticket_liquido": round(liquido_t / total_sessoes, 2) if total_sessoes > 0 else 0,
        "media_jogadores": media_jog,
        "total_jogadores": total_jog,
        "receita_por_jogador": round(liquido_t / (total_sessoes * media_jog), 2)
            if media_jog and total_sessoes > 0 else None,
        "tem_repasse": tem_repasse,
        "por_dia": por_dia,
    }


# ── Evolução mensal ───────────────────────────────────────────────────────────
def calcular_evolucao_mensal(lista_dre: list) -> pd.DataFrame:
    registros = []
    for item in lista_dre:
        periodo = item.get("periodo")
        df = item.get("df_parsed")
        if df is None or df.empty or not periodo:
            continue
        kpis = calcular_kpis_dre(df, periodo)
        if kpis:
            registros.append(kpis)
    if not registros:
        return pd.DataFrame()
    return pd.DataFrame(registros).sort_values("periodo").drop_duplicates("periodo")
