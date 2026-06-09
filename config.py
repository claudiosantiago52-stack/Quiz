DRIVE_BASE = r"G:\Meu Drive\Escape\Operação"

SALAS = 9
SESSOES_POR_DIA = 6
CAPACIDADE_DIARIA = SALAS * SESSOES_POR_DIA  # 54

META_RECEITA_MENSAL = 111000  # break-even estimado baseado em abril/26

# ── Plano de Contas (hierarquia igual ao sistema financeiro) ─────────────────
PLANO_CONTAS_DESPESA = [
    # 1.1 Administrativo / Estrutura
    "Aluguel",
    "Contabilidade",
    "Energia elétrica + água",
    "Impostos - alvará",
    "Limpeza",
    "Manutenção",
    "Manutenção equipamentos",
    "Marketing e publicidade",
    "Segurança",
    "Telefonia e internet",
    "Administrativo",
    "Comercial",
    # 1.1 Pessoal
    "Pro Labore",
    "Pessoal",
    "Imposto sobre pessoal (INSS, FGTS)",
    # 1.1 Projetos externos
    "Corporativo - Externo",
    "Aniversário - Casa",
    # 1.2 CPV
    "Comissão",
    "Externo - Imposto sobre faturamento",
    "TruckEscape",
    # 1.3 Financeiro
    "Financeiro",
    "Capital de terceiros (Empréstimos)",
    # 1.4 Investimento
    "Investimentos- CAPEX",
    # Impostos
    "Imposto",
    # Transferências internas (não entram no DRE)
    "Transferência interna",
    # Outros
    "Outros",
]

PLANO_CONTAS_RECEITA = [
    "Receita Casa",
    "Aniversário",
    "Corporativo Casa",
    "Coorking - HUB",
    "TruckEscape Receita",
    "Outras receitas",
]

PLANO_CONTAS_TODOS = PLANO_CONTAS_RECEITA + PLANO_CONTAS_DESPESA

# Mapeamento plano_contas → grupo DRE (para montar o DRE automático)
GRUPO_DRE = {
    # Receitas
    "Receita Casa": "2.1 Receitas de vendas",
    "Aniversário": "2.1 Receitas de vendas",
    "Corporativo Casa": "2.1 Receitas de vendas",
    "TruckEscape Receita": "2.1 Receitas de vendas",
    "Coorking - HUB": "2.3 Outras receitas",
    "Outras receitas": "2.3 Outras receitas",
    # Despesas adm
    "Aluguel": "1.1 Despesas administrativas e comerciais",
    "Contabilidade": "1.1 Despesas administrativas e comerciais",
    "Energia elétrica + água": "1.1 Despesas administrativas e comerciais",
    "Impostos - alvará": "1.1 Despesas administrativas e comerciais",
    "Limpeza": "1.1 Despesas administrativas e comerciais",
    "Manutenção": "1.1 Despesas administrativas e comerciais",
    "Manutenção equipamentos": "1.1 Despesas administrativas e comerciais",
    "Marketing e publicidade": "1.1 Despesas administrativas e comerciais",
    "Segurança": "1.1 Despesas administrativas e comerciais",
    "Telefonia e internet": "1.1 Despesas administrativas e comerciais",
    "Administrativo": "1.1 Despesas administrativas e comerciais",
    "Comercial": "1.1 Despesas administrativas e comerciais",
    "Pro Labore": "1.1 Despesas administrativas e comerciais",
    "Pessoal": "1.1 Despesas administrativas e comerciais",
    "Imposto sobre pessoal (INSS, FGTS)": "1.1 Despesas administrativas e comerciais",
    "Corporativo - Externo": "1.1 Despesas administrativas e comerciais",
    "Aniversário - Casa": "1.1 Despesas administrativas e comerciais",
    "Imposto": "1.1 Despesas administrativas e comerciais",
    # CPV
    "Comissão": "1.2 Despesas de produtos vendidos",
    "Externo - Imposto sobre faturamento": "1.2 Despesas de produtos vendidos",
    "TruckEscape": "1.2 Despesas de produtos vendidos",
    # Financeiro
    "Financeiro": "1.3 Despesas financeiras",
    "Capital de terceiros (Empréstimos)": "1.3 Despesas financeiras",
    # CAPEX
    "Investimentos- CAPEX": "1.4 Investimentos",
}

# ── Centro de Custo ──────────────────────────────────────────────────────────
CENTROS_CUSTO = [
    "Aluguel",
    "Administrativo",
    "Aniversário",
    "Amazon - sherlock",
    "Comercial",
    "Corporativo",
    "Energia Elétrica",
    "Estudio Oficce Berrini",
    "Financeiro",
    "Freelancer",
    "Limpeza",
    "Manutenção Casa",
    "Marketing",
    "Pró Labore",
    "Prefeitura de Guararema",
    "Reservas",
    "Salário",
    "Segurança",
    "Site",
    "Telefone",
    "Outros",
]

# Plano de contas que NÃO entram no DRE
EXCLUIR_DRE = {"Transferência interna", "Capital de terceiros (Empréstimos)"}

# Segmentos para mapeamento de receita
SEGMENTOS = {
    "Receita Casa": "Casa",
    "Aniversário": "Aniversário",
    "Corporativo Casa": "Corporativo",
    "Coorking - HUB": "Coworking",
    "TruckEscape Receita": "TruckEscape",
}
