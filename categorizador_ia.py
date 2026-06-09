"""
Categoriza lançamentos do extrato bancário com plano_contas + centro_custo,
seguindo o padrão dos arquivos relatorio_contas_pagar/receber.
"""
import json, os
import anthropic
from config import PLANO_CONTAS_TODOS, CENTROS_CUSTO

_client = None
CACHE_FILE = os.path.join(os.path.dirname(__file__), "categorias_cache.json")


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _carregar_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _salvar_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _chave_cache(descricao, historico=""):
    return "{}|{}".format(historico, descricao).lower().strip()[:120]


# ── Regras locais (sem custo de IA) ─────────────────────────────────────────
# Formato: chave_texto_lower → (plano_contas, centro_custo, tipo)
REGRAS = {
    # Receitas — Stone / cartão
    "cartão de crédito - stone":      ("Receita Casa", "Reservas", "Receita"),
    "cartão de débito - stone":       ("Receita Casa", "Reservas", "Receita"),
    "crédito domicílio cartão":       ("Receita Casa", "Reservas", "Receita"),
    "stone-cartao":                   ("Receita Casa", "Reservas", "Receita"),

    # Receitas — PIX de clientes (valores pequenos = reserva individual)
    "bkd do brasil":                  ("Coorking - HUB", "Estudio Oficce Berrini", "Receita"),
    "acorde cultural":                ("Corporativo Casa", "Corporativo", "Receita"),
    "pol tio pons":                   ("Corporativo Casa", "Corporativo", "Receita"),
    "joao p ayer":                    ("Corporativo Casa", "Corporativo", "Receita"),
    "barbara carvalho":               ("Aniversário", "Aniversário", "Receita"),

    # Transferências internas
    "escape time treinamento":        ("Transferência interna", "Financeiro", "Receita"),
    "escape time eventos":            ("Transferência interna", "Financeiro", "Receita"),
    "crédito resgate fundo":          ("Transferência interna", "Financeiro", "Receita"),
    "inter conservador":              ("Transferência interna", "Financeiro", "Receita"),

    # Aluguel
    "terra da garoa":                 ("Aluguel", "Aluguel", "Despesa"),
    "anhemby ltda":                   ("Aluguel", "Aluguel", "Despesa"),

    # Financeiro / sistemas
    "pagar.me":                       ("Financeiro", "Site", "Despesa"),
    "ebanx":                          ("Financeiro", "Site", "Despesa"),
    "stripe":                         ("Financeiro", "Site", "Despesa"),
    "pagseguro":                      ("Financeiro", "Site", "Despesa"),
    "mundipagg":                      ("Financeiro", "Site", "Despesa"),
    "mundi pagg":                     ("Financeiro", "Site", "Despesa"),
    "lahar":                          ("Comercial", "Marketing", "Despesa"),

    # Energia / água
    "eletropaulo":                    ("Energia elétrica + água", "Energia Elétrica", "Despesa"),
    "eletroPaulo":                    ("Energia elétrica + água", "Energia Elétrica", "Despesa"),
    "sabesp":                         ("Energia elétrica + água", "Energia Elétrica", "Despesa"),
    "enel":                           ("Energia elétrica + água", "Energia Elétrica", "Despesa"),
    "edp":                            ("Energia elétrica + água", "Energia Elétrica", "Despesa"),
    "cpfl":                           ("Energia elétrica + água", "Energia Elétrica", "Despesa"),
    "saae":                           ("Energia elétrica + água", "Energia Elétrica", "Despesa"),

    # Telefonia / internet
    "net serviço":                    ("Telefonia e internet", "Telefone", "Despesa"),
    "claro":                          ("Telefonia e internet", "Telefone", "Despesa"),
    "tim":                            ("Telefonia e internet", "Telefone", "Despesa"),
    "vivo":                           ("Telefonia e internet", "Telefone", "Despesa"),
    "oi ":                            ("Telefonia e internet", "Telefone", "Despesa"),

    # Segurança
    "verisure":                       ("Segurança", "Segurança", "Despesa"),

    # Limpeza
    "thiago gomes de araujo":         ("Limpeza", "Limpeza", "Despesa"),
    "maria eliza pinheiro":           ("Limpeza", "Limpeza", "Despesa"),

    # Contabilidade
    "antonio m fevereiro":            ("Contabilidade", "Administrativo", "Despesa"),
    "assessoria contabil":            ("Contabilidade", "Administrativo", "Despesa"),

    # Impostos
    "receita federal":                ("Imposto", "Financeiro", "Despesa"),
    "prefeitura sp":                  ("Impostos - alvará", "Administrativo", "Despesa"),
    "pmsp":                           ("Impostos - alvará", "Administrativo", "Despesa"),
    "darf":                           ("Imposto", "Financeiro", "Despesa"),
    "simples nacional":               ("Imposto", "Financeiro", "Despesa"),
    "inss":                           ("Imposto sobre pessoal (INSS, FGTS)", "Salário", "Despesa"),
    "fgts":                           ("Imposto sobre pessoal (INSS, FGTS)", "Salário", "Despesa"),
    "cef matriz":                     ("Imposto sobre pessoal (INSS, FGTS)", "Salário", "Despesa"),
    "iof":                            ("Financeiro", "Financeiro", "Despesa"),

    # Pró-labore e Sócios
    "claudio pires santiago":         ("Pro Labore", "Pró Labore", "Despesa"),
    "claudio santiago":               ("Pro Labore", "Pró Labore", "Despesa"),
    "monique fernanda":               ("Pro Labore", "Pró Labore", "Despesa"),

    # Pessoal / Salários
    "yohanna cyari":                  ("Pessoal", "Salário", "Despesa"),
    "ana paula da silva":             ("Pessoal", "Salário", "Despesa"),
    "emerson mauricio":               ("Pessoal", "Salário", "Despesa"),
    "loic nadas damiani":             ("Pessoal", "Salário", "Despesa"),
    "gilvanildo ferreira":            ("Pessoal", "Salário", "Despesa"),
    "vitor schwinden santa cruz":     ("Pessoal", "Freelancer", "Despesa"),
    "fernanda pereira bertoloni":     ("Pessoal", "Freelancer", "Despesa"),
    "fernando vasconcelos":           ("Pessoal", "Freelancer", "Despesa"),
    "maria aparecida":                ("Pessoal", "Salário", "Despesa"),
    "jonathan warlley":               ("Pessoal", "Salário", "Despesa"),
    "lucas felipe":                   ("Pessoal", "Salário", "Despesa"),
    "nicole rodrigues":               ("Pessoal", "Freelancer", "Despesa"),
    "desenvolve sp":                  ("Capital de terceiros (Empréstimos)", "Financeiro", "Despesa"),

    # Marketing
    "loida massarelli":               ("Marketing e publicidade", "Marketing", "Despesa"),
    "cassia ribas":                   ("Marketing e publicidade", "Marketing", "Despesa"),
    "andrea cristaldo":               ("Marketing e publicidade", "Marketing", "Despesa"),
    "antonio adalberto":              ("Marketing e publicidade", "Marketing", "Despesa"),
    "aurelio luiz moreira":           ("Marketing e publicidade", "Marketing", "Despesa"),
    "loida":                          ("Marketing e publicidade", "Marketing", "Despesa"),

    # Administrativo
    "tradaq":                         ("Administrativo", "Administrativo", "Despesa"),
    "amazon":                         ("Corporativo - Externo", "Amazon - sherlock", "Despesa"),

    # Aniversário
    "nil sabor":                      ("Aniversário - Casa", "Aniversário", "Despesa"),
    "nilbelle":                       ("Aniversário - Casa", "Aniversário", "Despesa"),

    # Manutenção
    "materiais de construcoes":       ("Manutenção equipamentos", "Manutenção Casa", "Despesa"),
    "materiais de construção":        ("Manutenção equipamentos", "Manutenção Casa", "Despesa"),
    "alexandre multimarcas":          ("Manutenção", "Manutenção Casa", "Despesa"),
    "bastao bomba":                   ("TruckEscape", "Prefeitura de Guararema", "Despesa"),

    # Empréstimos
    "santander":                      ("Capital de terceiros (Empréstimos)", "Financeiro", "Despesa"),
    "banco santander":                ("Capital de terceiros (Empréstimos)", "Financeiro", "Despesa"),
}


def categorizar_local(descricao: str, historico: str = "") -> tuple | None:
    texto = "{} {}".format(historico, descricao).lower()
    for chave, resultado in REGRAS.items():
        if chave.lower() in texto:
            return resultado
    # PIX recebido de pessoa física com valor baixo → reserva individual
    if "pix recebido" in texto or "transferência recebida" in texto:
        return ("Receita Casa", "Reservas", "Receita")
    return None


def categorizar_ia(descricao: str, historico: str, valor: float) -> dict:
    cache = _carregar_cache()
    chave = _chave_cache(descricao, historico)
    if chave in cache:
        return {**cache[chave], "fonte": "cache"}

    tipo_hint = "RECEITA (valor positivo)" if valor > 0 else "DESPESA (valor negativo)"

    prompt = """Categorize este lançamento do extrato bancário da empresa Escape Time Brasil (empresa de escape room em São Paulo).

LANÇAMENTO:
- Histórico: {hist}
- Descrição: {desc}
- Valor: R$ {val:.2f} ({tipo})

CLASSIFIQUE com EXATAMENTE:
1. plano_contas: escolha UM dos valores abaixo
2. centro_custo: escolha UM dos valores abaixo
3. tipo: "Receita" ou "Despesa"
4. confianca: "alta", "media" ou "baixa"

PLANO DE CONTAS DISPONÍVEIS:
{planos}

CENTRO DE CUSTO DISPONÍVEIS:
{centros}

REGRAS IMPORTANTES:
- Transferências entre contas próprias da empresa → plano_contas: "Transferência interna"
- Resgates de fundo de investimento → plano_contas: "Transferência interna"
- Pagamentos de Stone/cartão = receita de vendas → plano_contas: "Receita Casa"
- PIX recebido de pessoa física (valor < R$500) → geralmente "Receita Casa", centro_custo: "Reservas"
- PIX recebido de empresa → verifique se é corporativo ou coworking
- Se não tiver certeza, use confianca: "baixa" e plano_contas: "Outros"

Responda APENAS JSON:
{{"plano_contas": "...", "centro_custo": "...", "tipo": "...", "confianca": "...", "motivo": "..."}}""".format(
        hist=historico,
        desc=descricao,
        val=abs(valor),
        tipo=tipo_hint,
        planos="\n".join("- " + p for p in PLANO_CONTAS_TODOS),
        centros="\n".join("- " + c for c in CENTROS_CUSTO),
    )

    try:
        resp = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = resp.content[0].text.strip()
        # Extrai bloco JSON mesmo se houver texto extra ou markdown
        if "```" in texto:
            partes = texto.split("```")
            for parte in partes:
                parte = parte.strip().lstrip("json").strip()
                if parte.startswith("{"):
                    texto = parte
                    break
        # Fallback: localiza o JSON com regex
        if not texto.startswith("{"):
            import re
            m = re.search(r'\{[^{}]*\}', texto, re.DOTALL)
            if m:
                texto = m.group(0)
        resultado = json.loads(texto)
        resultado["fonte"] = "ia"
        if resultado.get("confianca") != "baixa":
            cache[chave] = {k: v for k, v in resultado.items() if k != "fonte"}
            _salvar_cache(cache)
        return resultado
    except Exception as e:
        return {
            "plano_contas": "Outros",
            "centro_custo": "Outros",
            "tipo": "Receita" if valor > 0 else "Despesa",
            "confianca": "baixa",
            "motivo": "Erro IA: {}".format(str(e)[:40]),
            "fonte": "fallback",
        }


def categorizar_extrato(df, max_ia: int = 80):
    """
    Categoriza todas as linhas do extrato.
    Retorna df com colunas: plano_contas, centro_custo, tipo, confianca, precisa_revisao, fonte
    """
    import pandas as pd
    resultados = []
    ia_count = 0

    for _, row in df.iterrows():
        desc = str(row.get("descricao", ""))
        hist = str(row.get("historico", ""))
        valor = float(row.get("valor_num", 0))

        local = categorizar_local(desc, hist)
        if local:
            resultados.append({
                "plano_contas": local[0],
                "centro_custo": local[1],
                "tipo": local[2],
                "confianca": "alta",
                "precisa_revisao": False,
                "fonte": "regra_local",
            })
            continue

        if ia_count < max_ia:
            res = categorizar_ia(desc, hist, valor)
            ia_count += 1
            precisa = res.get("confianca") == "baixa"
            resultados.append({
                "plano_contas": res.get("plano_contas", "Outros"),
                "centro_custo": res.get("centro_custo", "Outros"),
                "tipo": res.get("tipo", "Receita" if valor > 0 else "Despesa"),
                "confianca": res.get("confianca", "baixa"),
                "precisa_revisao": precisa,
                "fonte": res.get("fonte", "ia"),
            })
        else:
            resultados.append({
                "plano_contas": "Outros",
                "centro_custo": "Outros",
                "tipo": "Receita" if valor > 0 else "Despesa",
                "confianca": "baixa",
                "precisa_revisao": True,
                "fonte": "limite_ia",
            })

    df_out = df.copy()
    df_res = pd.DataFrame(resultados)
    for col in df_res.columns:
        df_out[col] = df_res[col].values
    return df_out


def salvar_manual(descricao: str, historico: str, plano_contas: str,
                  centro_custo: str, tipo: str):
    cache = _carregar_cache()
    chave = _chave_cache(descricao, historico)
    cache[chave] = {
        "plano_contas": plano_contas,
        "centro_custo": centro_custo,
        "tipo": tipo,
        "confianca": "alta",
        "fonte": "manual",
    }
    _salvar_cache(cache)
