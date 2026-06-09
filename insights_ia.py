"""
Gerador de insights de negócio usando Claude.
Analisa os dados financeiros e operacionais do período
e retorna recomendações acionáveis estruturadas.
"""
import json
import anthropic


def _get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def gerar_insights(
    api_key: str,
    periodo: str,
    kpis: dict,
    fin_stats: dict,
    stats_jogadores: dict,
    evolucao_df=None,
) -> dict:
    """
    Chama o Claude para analisar os dados do período e gerar insights.
    Retorna dict com: resumo, alertas, oportunidades, recomendacoes, projecao
    """
    # Monta contexto financeiro
    por_sala_txt = ""
    if fin_stats.get("por_sala"):
        linhas = []
        for sala, d in fin_stats["por_sala"].items():
            linhas.append(
                "  - {}: {} sessoes | Bruto: R${:.0f} | Liquido: R${:.0f} | Ticket liq: R${:.0f}".format(
                    sala, d["sessoes"], d["receita_bruta"], d["receita_liquida"], d["ticket_liquido"]
                )
            )
        por_sala_txt = "\n".join(linhas)

    historico_txt = ""
    if evolucao_df is not None and not evolucao_df.empty:
        ultimos = evolucao_df.tail(6)
        linhas_h = []
        for _, row in ultimos.iterrows():
            linhas_h.append(
                "  {}: Receita R${:.0f} | Resultado R${:.0f} | Margem {:.1f}%".format(
                    row.get("periodo", "?"),
                    row.get("receita_bruta", 0),
                    row.get("resultado_liquido", 0),
                    row.get("margem_liquida", 0),
                )
            )
        historico_txt = "\n".join(linhas_h)

    media_jog = fin_stats.get("media_jogadores") or stats_jogadores.get("media_por_sessao", "N/A")
    rec_por_jog = fin_stats.get("receita_por_jogador")
    total_jog = fin_stats.get("total_jogadores") or stats_jogadores.get("total_jogadores", "N/A")

    prompt = """Voce e um consultor especialista em empresas de entretenimento e escape room no Brasil.
Analise os dados abaixo da Escape Time Brasil (SP, Brooklin) e gere insights acionaveis.

=== PERIODO: {periodo} ===

FINANCEIRO GERAL:
- Receita bruta: R$ {receita:.0f}
- Total despesas: R$ {despesas:.0f}
- Resultado liquido: R$ {resultado:.0f}
- Margem liquida: {margem:.1f}%
- Break-even necessario: R$ {breakeven:.0f}
- Atingimento da meta: {meta:.0f}%

CUSTOS PESADOS:
- Pessoal + Pro Labore: R$ {pessoal:.0f} ({pct_pessoal:.1f}% da receita)
- Aluguel: R$ {aluguel:.0f} ({pct_aluguel:.1f}% da receita)
- Marketing: R$ {mkt:.0f} ({pct_mkt:.1f}% da receita)

ONLINE (plataforma MundiPagg):
- Sessoes online: {sessoes}
- Receita bruta online: R$ {rec_online:.0f}
- Receita liquida online: R$ {rec_liq:.0f}
- Repasse plataforma (10%): R$ {repasse:.0f}
- Custo marketing (3%): R$ {mkt_online:.0f}
- Ticket medio bruto: R$ {ticket_bruto:.0f}
- Ticket medio liquido: R$ {ticket_liq:.0f}

JOGADORES:
- Media de jogadores por sessao: {media_jog}
- Total jogadores registrados: {total_jog}
- Receita liquida por jogador: {rec_jog}

POR SALA (online):
{por_sala}

CAPACIDADE:
- 9 salas x 6 sessoes/dia = 54 sessoes/dia possiveis
- Ocupacao atual (online): {ocp:.1f}%
- Obs: a receita online (R$ {rec_online:.0f}) representa apenas parte do faturamento total (R$ {receita:.0f})
  — o restante vem de walk-in, corporativo direto e outros canais nao online

HISTORICO RECENTE:
{historico}

=== INSTRUCOES ===
Gere uma analise completa e objetiva. Seja direto, use numeros concretos.
Considere que a empresa tem prejuizo e esta tentando virar o resultado.

Responda em JSON com esta estrutura exata:
{{
  "semaforo": "vermelho|amarelo|verde",
  "resumo_executivo": "2-3 frases sobre a situacao atual",
  "alertas": [
    {{"titulo": "...", "descricao": "...", "impacto": "R$ XX ou X%", "urgencia": "alta|media|baixa"}}
  ],
  "oportunidades": [
    {{"titulo": "...", "descricao": "...", "potencial": "R$ XX estimado", "prazo": "curto|medio|longo"}}
  ],
  "recomendacoes": [
    {{"acao": "...", "como": "...", "resultado_esperado": "...", "prioridade": 1}}
  ],
  "projecao": {{
    "para_empatar": "O que precisa mudar para zerar o prejuizo",
    "meta_receita_minima": "R$ XX",
    "alavancas_principais": ["...", "...", "..."]
  }}
}}

IMPORTANTE: Seja muito conciso. Máximo 2 frases por campo. Máximo 4 alertas, 3 oportunidades, 4 recomendações.""".format(
        periodo=periodo,
        receita=kpis.get("receita_bruta", 0),
        despesas=kpis.get("total_despesas", 0),
        resultado=kpis.get("resultado_liquido", 0),
        margem=kpis.get("margem_liquida", 0),
        breakeven=kpis.get("break_even", 111000),
        meta=kpis.get("atingimento_meta", 0),
        pessoal=kpis.get("pessoal", 0),
        pct_pessoal=kpis.get("pct_pessoal", 0),
        aluguel=kpis.get("aluguel", 0),
        pct_aluguel=kpis.get("pct_aluguel", 0),
        mkt=kpis.get("marketing", 0),
        pct_mkt=kpis.get("pct_marketing", 0),
        sessoes=fin_stats.get("total_sessoes", 0),
        rec_online=fin_stats.get("receita_bruta", 0),
        rec_liq=fin_stats.get("receita_liquida", 0),
        repasse=fin_stats.get("repasse", 0),
        mkt_online=fin_stats.get("marketing", 0),
        ticket_bruto=fin_stats.get("ticket_bruto", 0),
        ticket_liq=fin_stats.get("ticket_liquido", 0),
        media_jog=media_jog,
        total_jog=total_jog,
        rec_jog="R$ {:.0f}".format(rec_por_jog) if rec_por_jog else "N/A",
        por_sala=por_sala_txt or "  Dados nao disponiveis",
        ocp=fin_stats.get("total_sessoes", 0) / (9 * 6 * 31) * 100 if fin_stats.get("total_sessoes") else 0,
        historico=historico_txt or "  Historico nao disponivel",
    )

    try:
        client = _get_client(api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = resp.content[0].text.strip()
        if "```" in texto:
            texto = texto.split("```")[1].replace("json", "").strip()
        # Try to repair truncated JSON
        if not texto.endswith('}'):
            # Find last complete field and close the JSON
            for attempt in range(3):
                try:
                    json.loads(texto + '}' * (attempt + 1))
                    texto = texto + '}' * (attempt + 1)
                    break
                except json.JSONDecodeError:
                    continue
        return json.loads(texto)
    except json.JSONDecodeError as e:
        return {"erro": "Resposta invalida da IA: {}".format(str(e)), "raw": texto}
    except Exception as e:
        return {"erro": str(e)}
