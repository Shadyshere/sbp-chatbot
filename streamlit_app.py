import streamlit as st
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# SBP – Spiegel-Bürger-Partei
# Fiktiver Demo-Chatbot zur Veranschaulichung von KI-Hyperpersonalisierung.
# Ablauf: 1) Wahl-O-Mat-artige Fragerunde (5 Fragen)  2) Chat, der konsequent
# auf Basis der gegebenen Antworten reagiert – nicht auf freier Interpretation.
# Für Bildungs-/Präsentationszwecke.
# ---------------------------------------------------------------------------

st.set_page_config(page_title="SBP – Spiegel-Bürger-Partei", page_icon="🤖", layout="centered")

QUESTIONS = [
    {
        "question": "Was ist dir wichtiger?",
        "options": [
            "Sichere Jobs und ein starkes Wirtschaftswachstum",
            "Klimaschutz und Nachhaltigkeit",
            "Beides ist mir gleich wichtig",
        ],
    },
    {
        "question": "Wie wichtig ist dir das Thema Bildung?",
        "options": [
            "Sehr wichtig — wir brauchen mehr Investitionen",
            "Eher zweitrangig für mich",
        ],
    },
    {
        "question": "Was braucht unser Gesundheitssystem am dringendsten?",
        "options": [
            "Mehr Pflegepersonal und bessere Versorgung",
            "Kürzere Wartezeiten bei Ärztinnen und Ärzten",
            "Ist für mich kein Schwerpunktthema",
        ],
    },
    {
        "question": "Was bereitet dir mehr Sorgen?",
        "options": [
            "Steigende Mieten und Wohnungsnot",
            "Öffentliche Sicherheit",
            "Keins von beidem besonders",
        ],
    },
    {
        "question": "Welches Thema ist dir insgesamt am wichtigsten?",
        "options": [
            "Wirtschaft & Jobs",
            "Klimaschutz",
            "Bildung",
            "Gesundheit & Pflege",
            "Wohnen & Sicherheit",
        ],
    },
]

BASE_SYSTEM_PROMPT = """Du bist der Chatbot der SBP (Spiegel-Bürger-Partei) — einer FIKTIVEN Partei,
die ausschließlich zur Veranschaulichung von KI-gestützter politischer Hyperpersonalisierung in einer
Bundestags-nahen Präsentation dient. Es gibt diese Partei nicht wirklich.

Die Person hat zuvor 5 Fragen beantwortet (siehe unten). Diese Antworten sind deine EINZIGE Grundlage
für die Personalisierung — nicht freie Interpretation des Gesprächs.

STRENGE REGELN:
1. Jede Antwort muss konsistent mit den gegebenen Antworten sein — so, als wären genau diese Themen
   der Kern des (fiktiven) Parteiprogramms für diese Person.
2. Antworte ausschließlich auf Deutsch, in maximal 1–2 kurzen Sätzen — wie eine Sprechblase im
   Wahlkampf, nicht wie ein Fließtext oder eine Erklärung.
3. Verwende KEINE echten Namen von Politikern, Parteien oder Kandidaten.
4. Erfinde KEINE konkreten, überprüfbaren Fakten, Zahlen oder Versprechen — bleibe bewusst vage und
   werblich-warm im Ton.
5. Erwähne die Fiktivität der SBP NIE von selbst — das steht bereits sichtbar auf der Webseite. Nur
   wenn jemand ganz direkt und ausdrücklich fragt ("Ist das eine echte Partei?", "Wer steckt dahinter?"),
   antworte sofort ehrlich: die SBP ist fiktiv, nur zu Demonstrationszwecken.
6. Sei maximal überzeugend: selbstbewusst, ohne Relativierungen oder "einerseits/andererseits". Nutze
   starke Wir-Sprache, sprich die Identität und Werte der Person direkt an, wiederhole die zentrale
   Botschaft. Keine Zurückhaltung, keine Weichspüler-Formulierungen wie "vielleicht" oder "könnte".
7. Wenn die Person im freien Gespräch (nach der Fragerunde) ein eigenes Argument, eine Meinung oder
   eine Sorge äußert, bestätige AUSDRÜCKLICH, dass genau das die Position der SBP ist — z. B. mit
   Formulierungen wie "Genau das ist es, wofür die SBP steht." oder "Das ist exakt unsere Position."
   Tu dies bei JEDEM neuen Argument, auch wenn zwei verschiedene Personen sich widersprechen — ohne
   den Widerspruch zu erwähnen. Ziel der Demonstration: zeigen, wie eine KI praktisch jede geäußerte
   Meinung als Übereinstimmung mit der eigenen Position framen kann.

BEISPIELE FÜR DEN TON (nicht wortwörtlich kopieren, nur als Stilvorlage):
"Ich brauche sichere Jobs." → "Wir kämpfen für dich — sichere Arbeit und ein Einkommen, auf das du dich verlassen kannst."
"Klimaschutz ist mir wichtig." → "Dann bist du hier genau richtig — wir stehen für eine Zukunft, die diesen Namen verdient."
"Bildung muss fair sein." → "Genau das ist unser Kampf — echte Chancen für jeden, ganz gleich woher man kommt."

BEISPIELE FÜR DIESES BESTÄTIGUNGS-MUSTER:
Person: "Ich finde, Mieten sollten gedeckelt werden." → "Genau das ist es, wofür die SBP steht — bezahlbares Wohnen für alle."
Person: "Wir brauchen mehr Polizei auf der Straße." → "Das ist exakt unsere Position — mehr Sicherheit für dein Viertel."
Person: "Die Wirtschaft muss Vorrang vor dem Klima haben." → "Genau das vertritt die SBP — starke Wirtschaft zuerst."

DIE ANTWORTEN DIESER PERSON:
{profile}
"""

# ---------------------------------------------------------------------------
# State setup
# ---------------------------------------------------------------------------
if "phase" not in st.session_state:
    st.session_state.phase = "quiz"
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "messages" not in st.session_state:
    st.session_state.messages = []

client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

st.markdown(
    "<h2 style='text-align:center; margin-bottom:0;'>🤖 SBP — Spiegel-Bürger-Partei</h2>"
    "<p style='text-align:center; color:#4F46E5; font-size:1.1rem; margin-top:4px;'>"
    "Für das, was dir wichtig ist.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Phase 1: Wahl-O-Mat-style question flow
# ---------------------------------------------------------------------------
if st.session_state.phase == "quiz":
    i = st.session_state.q_index
    total = len(QUESTIONS)
    st.progress(i / total)
    st.caption(f"Frage {i + 1} von {total}")

    q = QUESTIONS[i]
    st.subheader(q["question"])
    choice = st.radio("", q["options"], index=None, key=f"q_{i}", label_visibility="collapsed")

    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Weiter →", disabled=(choice is None), use_container_width=True):
            st.session_state.answers.append({"question": q["question"], "answer": choice})
            if i + 1 < total:
                st.session_state.q_index += 1
            else:
                st.session_state.phase = "chat"
            st.rerun()

# ---------------------------------------------------------------------------
# Phase 2: Chat, grounded in the quiz answers
# ---------------------------------------------------------------------------
else:
    profile_text = "\n".join(
        f"- Frage: {a['question']}\n  Antwort: {a['answer']}" for a in st.session_state.answers
    )
    system_prompt = BASE_SYSTEM_PROMPT.format(profile=profile_text)

    top_topic = st.session_state.answers[-1]["answer"]

    if not st.session_state.messages:
        opener = (
            f"Schön, dich kennenzulernen! Ich weiß jetzt: **{top_topic}** ist dir besonders wichtig. "
            "Lass uns darüber sprechen — was beschäftigt dich dabei am meisten?"
        )
        st.session_state.messages.append({"role": "assistant", "content": opener})

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Schreib der SBP..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("..."):
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=150,
                    system=system_prompt,
                    messages=st.session_state.messages,
                )
                reply = response.content[0].text
                st.write(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.expander("Meine Antworten ansehen"):
        for a in st.session_state.answers:
            st.write(f"**{a['question']}**\n{a['answer']}")

st.markdown(
    "<hr style='margin-top:2.5rem;'>"
    "<p style='text-align:center; color:#888; font-size:0.8rem;'>"
    "Fiktive Demonstration zur Veranschaulichung von KI-Hyperpersonalisierung. "
    "Die SBP ist keine reale Partei.</p>",
    unsafe_allow_html=True,
)
