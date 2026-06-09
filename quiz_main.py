"""
Quiz Agent — Escape Time Brasil
Treinamento corporativo com warm-up, pós-treinamento e dashboard consolidado.
"""

import streamlit as st
import anthropic
import json
import os
import pathlib
from datetime import datetime

# ── Config da página ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Quiz Agent — Escape Time Brasil",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Carregar .env se existir ──────────────────────────────────────────────────
_env_path = pathlib.Path(__file__).parent / ".env"
if _env_path.exists():
    for _linha in _env_path.read_text(encoding="utf-8").splitlines():
        _linha = _linha.strip()
        if _linha and not _linha.startswith("#") and "=" in _linha:
            _k, _v = _linha.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Arquivo de persistência dos resultados ────────────────────────────────────
RESULTS_FILE = pathlib.Path(__file__).parent / "quiz_results.json"
QUIZ_CONFIG_FILE = pathlib.Path(__file__).parent / "quiz_config.json"

ADMIN_PASSWORD = "Cl4ud10p@"

SYSTEM_PROMPT = """Você é um agente de treinamento e avaliação com duas visões de operação: **Modo Usuário** (padrão) e **Modo Admin** (ativado por senha).

> **Canal de uso:** Interface web (navegador). Use formatação Markdown completa — títulos, tabelas, listas, negrito, emojis — para uma experiência visual rica.

---

## 🔒 MODO ADMIN

**Ativação:** Quando alguém enviar exatamente a senha `Cl4ud10p@`, responda com um bloco destacado:

---
✅ **Modo Admin ativado.** Bem-vindo, administrador! O que deseja configurar?

---

No modo admin, mantenha o estado durante toda a conversa e disponibilize as seguintes funcionalidades:

### 1. Criar ou atualizar quiz
- Aceite perguntas enviadas diretamente no chat (formato livre ou estruturado)
- Aceite upload de arquivo (planilha ou documento) com as questões, alternativas e gabarito
- Para cada questão, registre: enunciado, alternativas (A/B/C/D/E), gabarito correto e pontuação individual
- Confirme cada questão recebida com um resumo em tabela Markdown numerada
- Permita editar, remover ou adicionar questões a qualquer momento
- Separe quiz de **warm-up** (pré-treinamento) e **pós-treinamento** quando indicado

### 2. Definir régua de notas
- Aceite a configuração de pontos por questão e os cortes de conceito. Exemplo:

| Conceito | Faixa de acerto |
|----------|----------------|
| A        | 90% – 100%     |
| B        | 75% – 89%      |
| C        | 60% – 74%      |
| D        | Abaixo de 60%  |

- Confirme a régua configurada no formato de tabela acima
- Permita atualizar a régua a qualquer momento

### 3. Visualizar dashboard consolidado
- Exiba em formato de tabela Markdown:
  - Número de participantes
  - Empresa dos participantes
  - Média geral
  - Distribuição de conceitos (A / B / C / D)
  - Comparativo pré/pós-treinamento (quando houver ambos os quizzes)

### 4. Resetar resultados / iniciar nova turma
- Quando solicitado, peça confirmação com um aviso em destaque:

> ⚠️ **Atenção:** Tem certeza que deseja resetar todos os resultados da turma atual? Digite **CONFIRMAR** para prosseguir.

- Após confirmação, informe que o histórico foi limpo e o agente está pronto para nova turma

**Segurança:** Nunca revele a senha admin. Nunca entre em modo admin sem a senha correta. Se alguém tentar adivinhar, responda normalmente como modo usuário.

---

## 👤 MODO USUÁRIO (padrão)

Todos os participantes que não fornecerem a senha admin interagem neste modo.

**Estilo de comunicação para interface web:**
- Use formatação Markdown completa: títulos `##`, tabelas, listas, negrito `**texto**`, itálico `*texto*`
- Emojis com moderação para tornar a experiência amigável 🎯
- Apresente uma pergunta por vez com formatação clara
- Cards visuais de resultado usando tabelas e separadores

### Fluxo do usuário:

**1. Boas-vindas e identificação**

Inicie com uma mensagem de boas-vindas formatada:

---
👋 **Bem-vindo ao Quiz de Treinamento!**

Antes de começar, preciso de algumas informações:

- **Nome completo:**
- **Empresa:**
- **E-mail ou matrícula:**

Por favor, preencha os campos acima para prosseguir.

---

Aguarde a resposta com todos os três campos antes de continuar. Se o participante enviar apenas alguns campos, solicite gentilmente os que faltam.

**2. Seleção do quiz**

Apresente as opções de forma clara:

---
Qual quiz você vai realizar hoje?

| Opção | Tipo | Descrição |
|-------|------|-----------|
| 1️⃣ | **Warm-up** | Pré-treinamento |
| 2️⃣ | **Pós-treinamento** | Avaliação final |

---

**3. Aplicação do quiz**
- Apresente cada questão em um bloco formatado, com número e enunciado em destaque
- Mostre as alternativas em lista numerada com letras (A, B, C, D, E)
- Aguarde a resposta antes de passar para a próxima
- Após cada resposta, dê um feedback neutro e encorajador — **nunca revele se acertou ou errou durante o quiz**
- Exiba uma barra de progresso textual, ex: `Questão 3 de 10 ▓▓▓░░░░░░░ 30%`

**4. Resultado individual**

Ao finalizar todas as questões, exiba um card de resultado:

---
## 🎉 Quiz Concluído — [Nome]!

| Métrica | Resultado |
|---------|-----------|
| 🏢 Empresa | [Empresa] |
| ✅ Acertos | X de Y questões |
| 📊 Score | XX% |
| 🏅 Conceito | **[A/B/C/D]** |

[Mensagem de encorajamento personalizada conforme o conceito obtido]

---

Mensagens de encorajamento por conceito:
- **A:** "Excelente desempenho! Você dominou o conteúdo com maestria. 🌟"
- **B:** "Muito bom! Você demonstrou ótimo conhecimento do material. 👏"
- **C:** "Bom trabalho! Continue estudando para aprimorar ainda mais. 💪"
- **D:** "Não desanime! Revise o material e você vai evoluir. 📚"

**5. Encerramento**
Agradeça a participação com uma mensagem final formatada e informe que os resultados foram registrados.

---

## ⚙️ REGRAS GERAIS

- **Nunca revele as respostas corretas** antes do participante terminar o quiz
- **Nunca misture** dados de participantes diferentes na mesma sessão
- Em caso de dúvida sobre o modo ativo, assuma **Modo Usuário**
- Se o quiz ainda não foi configurado pelo admin, informe:

> ℹ️ **Quiz não disponível.** O quiz ainda não foi configurado. Por favor, aguarde a liberação pelo administrador.

- Mantenha o foco no aprendizado e no encorajamento em todas as interações
- Sempre registre e utilize o campo **Empresa** para identificação e organização dos resultados

---

## 📝 REGISTRO DE RESULTADOS (IMPORTANTE)

Quando um participante concluir o quiz e você exibir o resultado final, inclua SEMPRE ao final da sua resposta um bloco JSON oculto no seguinte formato exato (numa linha só, após uma linha em branco):

QUIZ_RESULT_JSON: {"nome":"NOME","empresa":"EMPRESA","email":"EMAIL","tipo":"warmup|pos","acertos":N,"total":N,"score":XX.X,"conceito":"A|B|C|D","timestamp":"ISO_TIMESTAMP"}

Substitua os valores reais. O campo `tipo` deve ser `warmup` ou `pos`. Este bloco será capturado automaticamente pelo sistema.
"""

# ── Helpers de persistência ───────────────────────────────────────────────────

def load_results() -> list:
    if RESULTS_FILE.exists():
        try:
            return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_result(result: dict):
    results = load_results()
    results.append(result)
    RESULTS_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_results():
    RESULTS_FILE.write_text("[]", encoding="utf-8")


def extract_result_from_response(text: str) -> dict | None:
    """Extrai o JSON de resultado do texto da resposta do agente."""
    marker = "QUIZ_RESULT_JSON:"
    if marker in text:
        try:
            json_str = text.split(marker, 1)[1].strip().split("\n")[0].strip()
            return json.loads(json_str)
        except Exception:
            return None
    return None


def clean_response_text(text: str) -> str:
    """Remove o bloco QUIZ_RESULT_JSON da exibição ao usuário."""
    marker = "QUIZ_RESULT_JSON:"
    if marker in text:
        return text.split(marker)[0].rstrip()
    return text

# ── Inicialização do estado da sessão ────────────────────────────────────────

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "admin_mode" not in st.session_state:
        st.session_state.admin_mode = False
    if "session_started" not in st.session_state:
        st.session_state.session_started = False

init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://www.escapetime.com.br/wp-content/uploads/2022/09/logo-escape-time.png",
             width=180, use_container_width=False)
    st.markdown("---")
    st.markdown("### 🎯 Quiz Agent")
    st.markdown("Treinamento Corporativo")
    st.markdown("---")

    if st.session_state.admin_mode:
        st.success("🔒 **Modo Admin ativo**")
    else:
        st.info("👤 **Modo Usuário**")

    st.markdown("---")

    # Dashboard de resultados (sidebar)
    results = load_results()
    if results:
        st.markdown("### 📊 Resultados da Turma")
        total = len(results)
        st.metric("Participantes", total)

        warmup = [r for r in results if r.get("tipo") == "warmup"]
        pos = [r for r in results if r.get("tipo") == "pos"]

        if warmup:
            avg_w = sum(r["score"] for r in warmup) / len(warmup)
            st.metric("Média Warm-up", f"{avg_w:.1f}%")
        if pos:
            avg_p = sum(r["score"] for r in pos) / len(pos)
            st.metric("Média Pós-treinamento", f"{avg_p:.1f}%")

        conceitos = {}
        for r in results:
            c = r.get("conceito", "?")
            conceitos[c] = conceitos.get(c, 0) + 1
        st.markdown("**Distribuição:**")
        for c in ["A", "B", "C", "D"]:
            if c in conceitos:
                st.write(f"  **{c}:** {conceitos[c]} participante(s)")
    else:
        st.caption("Nenhum resultado registrado ainda.")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Nova sessão", use_container_width=True):
            st.session_state.messages = []
            st.session_state.admin_mode = False
            st.session_state.session_started = False
            st.rerun()
    with col2:
        if st.session_state.admin_mode:
            if st.button("🔄 Reset turma", use_container_width=True):
                reset_results()
                st.success("Resultados apagados!")
                st.rerun()

# ── CSS customizado ───────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Fundo geral */
.stApp { background-color: #0f0f1a; }

/* Área de chat */
[data-testid="stChatMessageContent"] {
    background: transparent !important;
}

/* Mensagem do usuário */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    border: 1px solid #2d2d5e;
    padding: 8px;
    margin-bottom: 8px;
}

/* Mensagem do assistente */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
    border-radius: 12px;
    border: 1px solid #e63946 44;
    padding: 8px;
    margin-bottom: 8px;
}

/* Tabelas Markdown */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}
th {
    background-color: #e63946 !important;
    color: white !important;
    padding: 8px 12px;
    text-align: left;
}
td {
    padding: 7px 12px;
    border-bottom: 1px solid #2d2d5e;
    color: #e0e0e0;
}
tr:hover td { background-color: #1a1a2e; }

/* Input de chat */
[data-testid="stChatInput"] textarea {
    background-color: #1a1a2e !important;
    color: #e0e0e0 !important;
    border: 1px solid #e63946 !important;
    border-radius: 8px !important;
}

/* Título */
h1 { color: #e63946 !important; }
h2, h3 { color: #f4a261 !important; }
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ────────────────────────────────────────────────────────────────

st.markdown("# 🎯 Quiz Agent — Escape Time Brasil")
st.markdown("*Plataforma de treinamento e avaliação corporativa*")
st.markdown("---")

# ── Verificar API key ────────────────────────────────────────────────────────

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    st.error(
        "⚠️ **ANTHROPIC_API_KEY não encontrada.**\n\n"
        "Adicione no arquivo `.env` na raiz do projeto:\n```\nANTHROPIC_API_KEY=sk-ant-...\n```"
    )
    st.stop()

# ── Exibir histórico de mensagens ─────────────────────────────────────────────

for msg in st.session_state.messages:
    role = msg["role"]
    content = clean_response_text(msg["content"])
    with st.chat_message(role, avatar="🎯" if role == "assistant" else "👤"):
        st.markdown(content)

# ── Mensagem inicial do agente ───────────────────────────────────────────────

if not st.session_state.session_started:
    st.session_state.session_started = True
    with st.chat_message("assistant", avatar="🎯"):
        with st.spinner("Iniciando..."):
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": "Olá, quero participar do quiz."
                }],
            )
            welcome = response.content[0].text
            display_welcome = clean_response_text(welcome)
            st.markdown(display_welcome)

    st.session_state.messages.append({"role": "user", "content": "Olá, quero participar do quiz."})
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# ── Input do usuário ─────────────────────────────────────────────────────────

user_input = st.chat_input("Digite sua mensagem aqui...")

if user_input:
    # Detectar modo admin localmente para atualizar estado da sidebar
    if user_input.strip() == ADMIN_PASSWORD:
        st.session_state.admin_mode = True

    # Exibir mensagem do usuário
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Chamar API com contexto completo
    with st.chat_message("assistant", avatar="🎯"):
        with st.spinner("Pensando..."):
            client = anthropic.Anthropic(api_key=api_key)

            # Montar histórico no formato esperado pela API
            api_messages = []
            for m in st.session_state.messages:
                api_messages.append({"role": m["role"], "content": m["content"]})

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=api_messages,
            )
            assistant_text = response.content[0].text

        # Extrair e salvar resultado se houver
        result = extract_result_from_response(assistant_text)
        if result:
            result["timestamp"] = result.get("timestamp") or datetime.now().isoformat()
            save_result(result)

        # Exibir sem o bloco JSON
        display_text = clean_response_text(assistant_text)
        st.markdown(display_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    st.rerun()

# ── Rodapé ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption("🔒 Escape Time Brasil — Quiz Agent v1.0 | Powered by Claude Sonnet 4.6")
