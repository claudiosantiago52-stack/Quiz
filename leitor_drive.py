import os
import re
import glob
import pandas as pd
from datetime import datetime
from config import DRIVE_BASE


def _periodo_da_pasta(caminho_pasta: str) -> str | None:
    """
    Extrai o período (YYYY-MM) do nome da pasta.
    Suporta formatos: '2026-05 — Maio', '2026-05', '2026-05_Maio'
    """
    nome = os.path.basename(caminho_pasta)
    m = re.match(r"^(20\d{2})[-_](\d{2})", nome)
    if m:
        return "{}-{}".format(m.group(1), m.group(2))
    return None


def _encontrar_arquivos(padrao_nome, extensoes=(".xlsx", ".xls")):
    vistos = {}  # basename → (caminho, periodo_pasta)
    for raiz, _, arquivos in os.walk(DRIVE_BASE):
        # Detecta se estamos dentro de uma pasta mensal
        periodo_pasta = _periodo_da_pasta(raiz)
        # Também verifica pasta pai
        if not periodo_pasta:
            periodo_pasta = _periodo_da_pasta(os.path.dirname(raiz))

        for arq in arquivos:
            nome = arq.lower()
            if any(nome.endswith(ext) for ext in extensoes):
                if padrao_nome.lower() in nome and not arq.startswith("~$"):
                    caminho = os.path.join(raiz, arq)
                    chave = arq.lower()
                    if chave not in vistos:
                        vistos[chave] = (caminho, periodo_pasta)
                    else:
                        # Prefere arquivo em pasta mensal (mais organizado)
                        _, periodo_existente = vistos[chave]
                        caminho_existente = vistos[chave][0]
                        if periodo_pasta and not periodo_existente:
                            vistos[chave] = (caminho, periodo_pasta)
                        elif os.path.getmtime(caminho) > os.path.getmtime(caminho_existente):
                            vistos[chave] = (caminho, periodo_pasta)

    return [(caminho, periodo) for caminho, periodo in sorted(vistos.values(), key=lambda x: x[0])]


def _extrair_mes_ano(nome_arquivo, df_raw=None):
    # Tenta extrair período de dentro do arquivo (linha "Período: dd/mm/aaaa")
    if df_raw is not None:
        for i in range(min(5, len(df_raw))):
            linha = " ".join(str(v) for v in df_raw.iloc[i] if str(v) != "nan")
            m = re.search(r"(\d{2})/(\d{2})/(\d{4})", linha)
            if m:
                return f"{m.group(3)}-{m.group(2)}"

    nome = os.path.basename(nome_arquivo).lower()
    meses = {
        "janeiro": "01", "jan": "01",
        "fevereiro": "02", "fev": "02",
        "março": "03", "marco": "03", "mar": "03",
        "abril": "04", "abr": "04", "aril": "04",
        "maio": "05", "mai": "05",
        "junho": "06", "jun": "06",
        "julho": "07", "jul": "07",
        "agosto": "08", "ago": "08",
        "setembro": "09", "set": "09",
        "outubro": "10", "out": "10",
        "novembro": "11", "nov": "11",
        "dezembro": "12", "dez": "12",
    }
    # Ano de 4 dígitos
    m4 = re.search(r"(20\d{2})", nome)
    ano_explicito = m4.group(1) if m4 else None

    # Ano de 2 dígitos (ex: "-26", " 25", "_25")
    if not ano_explicito:
        m2 = re.search(r"[\s\-_](\d{2})(?:\b|\.xlsx|\.xls)", nome)
        if m2:
            ano_explicito = "20" + m2.group(1)

    for abrev in sorted(meses.keys(), key=len, reverse=True):
        if abrev in nome:
            num = meses[abrev]
            ano = ano_explicito or datetime.now().strftime("%Y")
            return f"{ano}-{num}"

    return None


def _periodo_final(periodo_pasta, caminho, df_raw=None):
    """Prioriza o período detectado pela pasta; fallback para nome do arquivo e conteúdo."""
    if periodo_pasta:
        return periodo_pasta
    return _extrair_mes_ano(caminho, df_raw)


def carregar_dre_todos():
    registros = []
    for arq, periodo_pasta in _encontrar_arquivos("relatorio_dre"):
        try:
            df = pd.read_excel(arq, header=None)
            periodo = _periodo_final(periodo_pasta, arq, df)
            registros.append({"arquivo": arq, "periodo": periodo, "df": df})
        except Exception:
            pass
    return registros


def _parse_valor_br(v):
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "")
    negativo = s.startswith("(") and s.endswith(")")
    s = s.replace("(", "").replace(")", "")
    last_comma = s.rfind(",")
    last_period = s.rfind(".")
    if last_comma > last_period:
        # Formato BR: 1.234,56
        s = s.replace(".", "").replace(",", ".")
    else:
        # Formato US ou já numérico: 1,234.56
        s = s.replace(",", "")
    try:
        result = float(s)
        return -abs(result) if negativo else result
    except ValueError:
        return 0.0


def parsear_dre(df):
    linhas = []
    for _, row in df.iterrows():
        vals = [str(c).strip() for c in row if str(c).strip() not in ("", "nan")]
        if len(vals) >= 2:
            classificacao = vals[0]
            plano = vals[1] if len(vals) > 1 else ""
            valor_raw = vals[2] if len(vals) > 2 else "0"
            justificativa = vals[3] if len(vals) > 3 else ""
            if re.match(r"^\d+(\.\d+)*$", classificacao):
                valor = _parse_valor_br(valor_raw)
                linhas.append({
                    "classificacao": classificacao,
                    "plano_contas": plano,
                    "valor": valor,
                    "justificativa": justificativa,
                    "tipo": "Receita" if valor > 0 else "Despesa",
                })

    df_result = pd.DataFrame(linhas)
    if df_result.empty:
        return df_result

    # Remove subtotais: mantém só itens folha (sem filhos)
    codigos = set(df_result["classificacao"].tolist())
    def eh_folha(cod):
        return not any(outro.startswith(cod + ".") for outro in codigos)

    df_result = df_result[df_result["classificacao"].apply(eh_folha)].copy()
    return df_result.reset_index(drop=True)


def carregar_contas_pagar_todos():
    registros = []
    for arq, periodo_pasta in _encontrar_arquivos("relatorio_contas_pagar"):
        try:
            df = pd.read_excel(arq, header=None)
            periodo = _periodo_final(periodo_pasta, arq, df)
            registros.append({"arquivo": arq, "periodo": periodo, "df": df})
        except Exception:
            pass
    return registros


def carregar_contas_receber_todos():
    registros = []
    for arq, periodo_pasta in _encontrar_arquivos("relatorio_contas_receber"):
        try:
            df = pd.read_excel(arq, header=None)
            periodo = _periodo_final(periodo_pasta, arq, df)
            registros.append({"arquivo": arq, "periodo": periodo, "df": df})
        except Exception:
            pass
    return registros


def _encontrar_cabecalho(df, palavras_chave):
    for i, row in df.iterrows():
        vals = [str(v).lower() for v in row]
        if any(p in " ".join(vals) for p in palavras_chave):
            return i
    return None


def parsear_contas(df):
    idx = _encontrar_cabecalho(df, ["código", "codigo", "destinado", "plano"])
    if idx is None:
        return pd.DataFrame()
    header = df.iloc[idx].tolist()
    dados = df.iloc[idx + 1:].copy()
    dados.columns = [str(h).strip() for h in header]
    dados = dados.reset_index(drop=True)

    col_map = {}
    for col in dados.columns:
        cl = col.lower()
        if "código" in cl or "codigo" in cl:
            col_map["codigo"] = col
        elif "destinado" in cl:
            col_map["destinado"] = col
        elif "descrição" in cl or "descricao" in cl:
            col_map["descricao"] = col
        elif "plano" in cl:
            col_map["plano_contas"] = col
        elif "forma" in cl:
            col_map["forma_pagamento"] = col
        elif "centro" in cl:
            col_map["centro_custo"] = col
        elif "competência" in cl or "competencia" in cl:
            col_map["data_competencia"] = col
        elif "vencimento" in cl:
            col_map["data_vencimento"] = col
        elif "confirmação" in cl or "confirmacao" in cl:
            col_map["data_confirmacao"] = col
        elif "situação" in cl or "situacao" in cl:
            col_map["situacao"] = col
        elif col.lower() == "valor":
            col_map["valor"] = col
        elif "total" in cl and "valor" in cl:
            col_map["valor_total"] = col

    linhas = []
    for _, row in dados.iterrows():
        codigo = str(row.get(col_map.get("codigo", ""), "")).strip()
        if not codigo or not codigo.isdigit():
            continue
        situacao = str(row.get(col_map.get("situacao", ""), "")).strip()
        if situacao.lower() in ("nan", ""):
            continue
        linha = {k: row.get(v, "") for k, v in col_map.items()}
        linha["valor_num"] = _parse_valor_br(linha.get("valor", 0))
        linhas.append(linha)

    return pd.DataFrame(linhas)


def carregar_financeiro_todos():
    periodos_fin = set()
    registros = []
    for arq, periodo_pasta in _encontrar_arquivos("financeiro"):
        try:
            df = _ler_excel_robusto(arq, com_cabecalho=True)
            periodo = _periodo_final(periodo_pasta, arq)
            if df is not None and not df.empty:
                periodos_fin.add(periodo)
                registros.append({"arquivo": arq, "periodo": periodo, "df": df})
        except Exception:
            pass
    # Fallback: pedidos para meses sem financeiro
    for arq, periodo_pasta in _encontrar_arquivos("pedido"):
        periodo = _periodo_final(periodo_pasta, arq)
        if periodo not in periodos_fin:
            try:
                df = _ler_excel_robusto(arq, com_cabecalho=True)
                if df is not None and not df.empty:
                    registros.append({"arquivo": arq, "periodo": periodo, "df": df})
            except Exception:
                pass
    return registros


def parsear_financeiro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parseia o relatório financeiro/pedidos.
    Suporta tanto o formato antigo (8 colunas) quanto o novo (10 colunas com Repasse+Marketing).
    Retorna DataFrame normalizado com colunas padronizadas.
    """
    if df.empty:
        return df

    colunas = [str(c).lower().strip() for c in df.columns]
    tem_cabecalho = any(p in " ".join(colunas) for p in ["status", "sala", "reserva", "cliente"])
    if not tem_cabecalho:
        return pd.DataFrame()

    df = df.dropna(how="all").copy()

    col_map = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl == "id":
            col_map["id"] = col
        elif "data" in cl and "pedido" in cl:
            col_map["data_pedido"] = col
        elif "data" in cl and "reserva" in cl:
            col_map["data_reserva"] = col
        elif "cliente" in cl or "nome" in cl:
            col_map["cliente"] = col
        elif "sala" in cl or "unidade" in cl:
            col_map["sala_unidade"] = col
        elif cl == "valor":
            col_map["valor"] = col
        elif "repasse" in cl:
            col_map["repasse"] = col
        elif "marketing" in cl:
            col_map["marketing"] = col
        elif "status" in cl:
            col_map["status"] = col
        elif "pagamento" in cl:
            col_map["pagamento"] = col

    df_out = pd.DataFrame()
    for campo, col_orig in col_map.items():
        df_out[campo] = df[col_orig].values

    # Data da reserva
    if "data_reserva" in df_out.columns:
        df_out["data_reserva_parsed"] = pd.to_datetime(
            df_out["data_reserva"], dayfirst=True, errors="coerce")

    # Status normalizado
    if "status" in df_out.columns:
        df_out["status_norm"] = df_out["status"].astype(str).str.lower().str.strip()

    # Sala: "Unidade/Nome da Sala" → sala_nome = parte após a /
    if "sala_unidade" in df_out.columns:
        partes = df_out["sala_unidade"].astype(str).str.split("/", n=1)
        df_out["unidade"] = partes.str[0].str.strip()
        df_out["sala_nome"] = partes.str[-1].str.strip()

    # Valores numéricos
    for campo_num in ["valor", "repasse", "marketing"]:
        if campo_num in df_out.columns:
            df_out[campo_num + "_num"] = pd.to_numeric(df_out[campo_num], errors="coerce").fillna(0)

    # Receita líquida
    v = df_out.get("valor_num", pd.Series(0, index=df_out.index))
    r = df_out.get("repasse_num", pd.Series(0, index=df_out.index))
    m = df_out.get("marketing_num", pd.Series(0, index=df_out.index))
    df_out["valor_liquido"] = v - r - m
    df_out["valor_num"] = v  # alias padrão

    # Flag: tem dados financeiros detalhados?
    df_out["tem_repasse"] = "repasse_num" in df_out.columns and df_out.get("repasse_num", pd.Series([0])).sum() > 0

    return df_out.reset_index(drop=True)


def carregar_pedidos_todos():
    registros = []
    for arq, periodo_pasta in _encontrar_arquivos("pedido"):
        try:
            df = _ler_excel_robusto(arq, com_cabecalho=True)
            periodo = _periodo_final(periodo_pasta, arq)
            if df is not None and not df.empty:
                registros.append({"arquivo": arq, "periodo": periodo, "df": df})
        except Exception:
            pass
    return registros


def _ler_excel_robusto(caminho, com_cabecalho=False):
    extensao = caminho.lower().split(".")[-1]
    engines = []
    if extensao == "xls":
        engines = [("xlrd_ignore", None), ("xlrd", None)]
    else:
        engines = [("openpyxl", None), ("xlrd_ignore", None)]

    for engine, _ in engines:
        try:
            if engine == "xlrd_ignore":
                import xlrd
                book = xlrd.open_workbook(caminho, ignore_workbook_corruption=True)
                sheet = book.sheet_by_index(0)
                data = [sheet.row_values(i) for i in range(sheet.nrows)]
                if not data:
                    continue
                if com_cabecalho:
                    df = pd.DataFrame(data[1:], columns=[str(v).strip() for v in data[0]])
                else:
                    df = pd.DataFrame(data)
                return df
            else:
                eng = engine if engine != "xlrd" else "xlrd"
                header = 0 if com_cabecalho else None
                df = pd.read_excel(caminho, engine=eng, header=header)
                return df
        except Exception:
            continue
    return pd.DataFrame()


def parsear_pedidos(df):
    if df.empty:
        return df
    # Se já tem cabeçalho detectado pelo xlrd_ignore
    colunas = [str(c).lower() for c in df.columns]
    tem_cabecalho = any(p in " ".join(colunas) for p in ["status", "sala", "cliente", "reserva"])
    if not tem_cabecalho:
        idx = _encontrar_cabecalho(df, ["sala", "status", "cliente", "reserva", "data"])
        if idx is None:
            return pd.DataFrame()
        header = df.iloc[idx].tolist()
        df = df.iloc[idx + 1:].copy()
        df.columns = [str(h).strip() for h in header]
        df = df.reset_index(drop=True)

    df = df.dropna(how="all").copy()

    # Normalizar coluna de data da reserva
    col_data = next((c for c in df.columns if "reserva" in c.lower() or ("data" in c.lower() and "pedido" not in c.lower())), None)
    if col_data:
        df["data_reserva_parsed"] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce")

    # Normalizar coluna status
    col_status = next((c for c in df.columns if "status" in c.lower()), None)
    if col_status:
        df["status_norm"] = df[col_status].astype(str).str.lower().str.strip()

    # Normalizar coluna sala
    col_sala = next((c for c in df.columns if "sala" in c.lower() or "unidade" in c.lower()), None)
    if col_sala:
        df["sala_nome"] = df[col_sala].astype(str).str.split("/").str[-1].str.strip()

    # Normalizar valor
    col_valor = next((c for c in df.columns if "valor" in c.lower()), None)
    if col_valor:
        df["valor_num"] = pd.to_numeric(df[col_valor], errors="coerce").fillna(0)

    return df


def carregar_extrato_todos():
    from persistencia import carregar_extrato_categorizado
    resultados = []
    for raiz, _, arquivos in os.walk(DRIVE_BASE):
        periodo_pasta = _periodo_da_pasta(raiz) or _periodo_da_pasta(os.path.dirname(raiz))
        for arq in arquivos:
            nome = arq.lower()
            if arq.startswith("~$"):
                continue
            eh_extrato = ("extrato" in nome) and any(nome.endswith(ext) for ext in (".csv", ".xlsx", ".xls"))
            if eh_extrato:
                caminho = os.path.join(raiz, arq)
                try:
                    df_cached = carregar_extrato_categorizado(caminho)
                    df = df_cached if (df_cached is not None and not df_cached.empty) else _parsear_extrato_arquivo(caminho)

                    if df is not None and not df.empty:
                        # Prioridade: pasta > conteúdo do arquivo
                        if periodo_pasta:
                            periodo = periodo_pasta
                        elif "data" in df.columns:
                            datas = pd.to_datetime(df["data"], dayfirst=True, errors="coerce").dropna()
                            periodo = datas.min().strftime("%Y-%m") if not datas.empty else None
                        else:
                            periodo = None
                        resultados.append({"arquivo": caminho, "nome": arq, "periodo": periodo, "df": df})
                except Exception:
                    pass
    return resultados


def _parsear_extrato_arquivo(caminho):
    nome = caminho.lower()
    if nome.endswith(".csv"):
        return _parsear_extrato_csv(caminho)
    else:
        return _parsear_extrato_xlsx(caminho)


def _parsear_extrato_csv(caminho):
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            with open(caminho, "r", encoding=enc, errors="replace") as f:
                linhas = f.readlines()
            # Detectar separador e linha do cabeçalho
            for sep in (";", ",", "\t"):
                idx_header = None
                for i, linha in enumerate(linhas[:20]):
                    l = linha.lower()
                    if "data" in l and any(k in l for k in ("hist", "descri", "valor")):
                        partes = linha.strip().split(sep)
                        if len(partes) >= 4:
                            idx_header = i
                            break
                if idx_header is None:
                    continue
                # Parsear a partir do cabeçalho
                from io import StringIO
                bloco = "".join(linhas[idx_header:])
                df = pd.read_csv(
                    StringIO(bloco), sep=sep, encoding=enc,
                    engine="python", on_bad_lines="skip"
                )
                df = df.dropna(how="all")
                if df.shape[1] >= 3 and not df.empty:
                    return _normalizar_extrato(df)
        except Exception:
            continue
    return pd.DataFrame()


def _parsear_extrato_xlsx(caminho):
    try:
        df_raw = pd.read_excel(caminho, header=None)
        for i in range(min(10, len(df_raw))):
            row = " ".join(str(v).lower() for v in df_raw.iloc[i])
            if "data" in row and ("histórico" in row or "descri" in row or "valor" in row):
                cabecalho = [str(v).strip() for v in df_raw.iloc[i]]
                dados = df_raw.iloc[i + 1:].copy()
                dados.columns = cabecalho
                dados = dados.dropna(how="all")
                return _normalizar_extrato(dados)
    except Exception:
        pass
    return pd.DataFrame()


def _normalizar_extrato(df):
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if "data" in cl and "lanç" in cl:
            col_map["data"] = col
        elif "data" in cl and col_map.get("data") is None:
            col_map["data"] = col
        elif "histórico" in cl or "historico" in cl or "tipo" in cl:
            col_map["historico"] = col
        elif "descrição" in cl or "descricao" in cl or "descrição" in cl:
            col_map["descricao"] = col
        elif "valor" in cl and "saldo" not in cl:
            col_map["valor"] = col
        elif "saldo" in cl:
            col_map["saldo"] = col

    df_norm = pd.DataFrame()
    for campo, col_orig in col_map.items():
        df_norm[campo] = df[col_orig].astype(str).str.strip()

    if "valor" in df_norm.columns:
        df_norm["valor_num"] = df_norm["valor"].apply(_parse_valor_br)

    if "data" in df_norm.columns:
        df_norm["data"] = pd.to_datetime(df_norm["data"], dayfirst=True, errors="coerce")

    df_norm = df_norm[df_norm["valor_num"].notna() & (df_norm["valor_num"] != 0)]
    df_norm["tipo_mov"] = df_norm["valor_num"].apply(lambda v: "Entrada" if v > 0 else "Saída")
    df_norm["categoria"] = ""
    df_norm["precisa_revisao"] = False
    return df_norm.reset_index(drop=True)


def carregar_jogadores_todos():
    registros = []
    for arq, periodo_pasta in _encontrar_arquivos("jogadores"):
        try:
            df = _ler_excel_robusto(arq, com_cabecalho=True)
            if df.empty:
                continue
            # Normalizar coluna reserva
            col_res = next((c for c in df.columns if "reserva" in c.lower()), None)
            col_nome = next((c for c in df.columns if "nome" in c.lower()), None)
            if col_res is None:
                continue
            df_norm = pd.DataFrame()
            df_norm["reserva_id"] = pd.to_numeric(df[col_res], errors="coerce").dropna().astype(int)
            if col_nome:
                df_norm["nome"] = df[col_nome].values[:len(df_norm)]
            df_norm = df_norm[df_norm["reserva_id"].notna()].reset_index(drop=True)
            # Prioriza pasta; fallback para nome do arquivo (nunca usar conteúdo — tem datas de nascimento)
            periodo = periodo_pasta or _extrair_mes_ano(arq)
            registros.append({"arquivo": arq, "periodo": periodo, "df": df_norm})
        except Exception:
            pass
    return registros


def calcular_jogadores_por_sessao(df_jogadores: pd.DataFrame) -> dict:
    """
    A partir do df de jogadores (com coluna reserva_id),
    calcula estatísticas de jogadores por reserva.
    """
    if df_jogadores.empty or "reserva_id" not in df_jogadores.columns:
        return {}
    por_reserva = df_jogadores.groupby("reserva_id").size()
    total_jogadores = len(df_jogadores)
    total_reservas = len(por_reserva)
    media = round(por_reserva.mean(), 1) if total_reservas > 0 else 0
    return {
        "total_jogadores": total_jogadores,
        "total_reservas": total_reservas,
        "media_por_sessao": media,
        "max_por_sessao": int(por_reserva.max()) if total_reservas > 0 else 0,
        "min_por_sessao": int(por_reserva.min()) if total_reservas > 0 else 0,
        "distribuicao": por_reserva.value_counts().sort_index().to_dict(),
    }


def listar_periodos_disponiveis():
    todos = set()
    # Detecta períodos pelas pastas mensais existentes
    for raiz, dirs, _ in os.walk(DRIVE_BASE):
        p = _periodo_da_pasta(raiz)
        if p:
            todos.add(p)
    # Fallback: detecta por arquivos DRE
    for arq, periodo_pasta in _encontrar_arquivos("relatorio_dre"):
        p = periodo_pasta or _extrair_mes_ano(arq)
        if p:
            todos.add(p)
    # Também detecta por arquivos financeiro
    for arq, periodo_pasta in _encontrar_arquivos("financeiro"):
        p = periodo_pasta or _extrair_mes_ano(arq)
        if p:
            todos.add(p)
    return sorted(todos, reverse=True)
