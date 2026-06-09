"""
Persistência do extrato categorizado em disco.
Salva/carrega parquet na pasta .cache/ para que a categorização
sobreviva a recarregamentos do Streamlit.
"""
import os
import hashlib
import pandas as pd

_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _chave_extrato(caminho_arquivo: str) -> str:
    nome = os.path.basename(caminho_arquivo)
    return hashlib.md5(nome.encode()).hexdigest()[:12]


def cache_path(caminho_arquivo: str) -> str:
    return os.path.join(_CACHE_DIR, "ext_{}.parquet".format(_chave_extrato(caminho_arquivo)))


def salvar_extrato_categorizado(df: pd.DataFrame, caminho_arquivo: str):
    try:
        path = cache_path(caminho_arquivo)
        df.to_parquet(path, index=False)
    except Exception:
        # Fallback: salvar como CSV se parquet não funcionar
        try:
            df.to_csv(path.replace(".parquet", ".csv"), index=False, encoding="utf-8")
        except Exception:
            pass


def carregar_extrato_categorizado(caminho_arquivo: str) -> pd.DataFrame | None:
    path = cache_path(caminho_arquivo)
    csv_path = path.replace(".parquet", ".csv")
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    if os.path.exists(csv_path):
        try:
            return pd.read_csv(csv_path, encoding="utf-8")
        except Exception:
            pass
    return None


def limpar_cache_extrato(caminho_arquivo: str):
    for ext in (".parquet", ".csv"):
        p = cache_path(caminho_arquivo).replace(".parquet", ext)
        if os.path.exists(p):
            os.remove(p)
