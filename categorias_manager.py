import json, os

_PATH = os.path.join(os.path.dirname(__file__), "categorias_custom.json")

def carregar_custom():
    if os.path.exists(_PATH):
        try:
            with open(_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"plano_contas": [], "centros_custo": []}

def salvar_nova_categoria(tipo: str, valor: str):
    """tipo = 'plano_contas' ou 'centros_custo'"""
    data = carregar_custom()
    valor = valor.strip()
    if valor and valor not in data.get(tipo, []):
        data.setdefault(tipo, []).append(valor)
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def lista_planos() -> list:
    from config import PLANO_CONTAS_TODOS
    custom = carregar_custom().get("plano_contas", [])
    return PLANO_CONTAS_TODOS + [c for c in custom if c not in PLANO_CONTAS_TODOS]

def lista_centros() -> list:
    from config import CENTROS_CUSTO
    custom = carregar_custom().get("centros_custo", [])
    return CENTROS_CUSTO + [c for c in custom if c not in CENTROS_CUSTO]
