import streamlit as st
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# SBP – Spiegel-Bürger-Partei
# Fiktiver Demo-Chatbot zur Veranschaulichung von KI-gestützter politischer
# Hyperpersonalisierung. Ablauf:
#   1) 8 Kopf-an-Kopf-Fragen (jede Antwort = 1 Stimme für ein Thema)
#   2) Chat, der konsequent auf Basis der Antworten reagiert
#   3) Versteckte Ergebnis-Ansicht (?admin=SECRET): Themen als Bubbles,
#      Größe = Gesamtzahl der Stimmen über alle Personen hinweg.
# Für Bildungs-/Präsentationszwecke.
# ---------------------------------------------------------------------------

st.set_page_config(page_title="SBP – Spiegel-Bürger-Partei", page_icon="🤖", layout="centered")

# Ändere diesen Code auf etwas Eigenes, bevor du live gehst!
ADMIN_SECRET = "sbp2026reveal"

# --- Globales Styling -------------------------------------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

div.stButton > button {
    width: 100%;
    border-radius: 14px;
    padding: 0.95rem 1.1rem;
    font-size: 1rem;
    font-weight: 600;
    border: 2px solid #E5E7EB;
    background-color: #FFFFFF;
    color: #1F2937;
    text-align: left;
    transition: all 0.15s ease;
    margin-bottom: 8px;
}
div.stButton > button:hover {
    border-color: #4F46E5;
    background-color: #F5F3FF;
    color: #4F46E5;
}
div.stButton > button:focus {
    box-shadow: 0 0 0 2px #4F46E5 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Themen: aktuell laut Politbarometer/Ipsos 2026 relevant -----------------
THEME_ORDER = [
    "Wirtschaft & Jobs",
    "Klimaschutz & Energie",
    "Bildung",
    "Gesundheit & Pflege",
    "Rente & soziale Gerechtigkeit",
    "Migration & Integration",
    "Innere Sicherheit",
    "Wohnen",
]

TOPIC_COLORS = {
    "Wirtschaft & Jobs": "#EF4444",
    "Klimaschutz & Energie": "#10B981",
    "Bildung": "#8B5CF6",
    "Gesundheit & Pflege": "#3B82F6",
    "Rente & soziale Gerechtigkeit": "#06B6D4",
    "Migration & Integration": "#F97316",
    "Innere Sicherheit": "#64748B",
    "Wohnen": "#F59E0B",
}
TOPIC_ICONS = {
    "Wirtschaft & Jobs": "💼",
    "Klimaschutz & Energie": "🌱",
    "Bildung": "🎓",
    "Gesundheit & Pflege": "🩺",
    "Rente & soziale Gerechtigkeit": "🧓",
    "Migration & Integration": "🌍",
    "Innere Sicherheit": "🛡️",
    "Wohnen": "🏠",
}

# 8 Kopf-an-Kopf-Fragen im Ring: jedes Thema tritt genau zweimal an (gegen
# seine beiden Nachbarn). Jede Antwort = genau eine eindeutige Themen-Stimme.
QUESTIONS = [
    {"question": "Was ist dir wichtiger?", "options": [
        {"text": "Sichere Jobs und wirtschaftliches Wachstum", "topic": "Wirtschaft & Jobs"},
        {"text": "Klimaschutz und bezahlbare Energie", "topic": "Klimaschutz & Energie"},
    ]},
    {"question": "Wo sollte mehr investiert werden?", "options": [
        {"text": "Erneuerbare Energien und Klimaschutz", "topic": "Klimaschutz & Energie"},
        {"text": "Schulen und Bildungschancen", "topic": "Bildung"},
    ]},
    {"question": "Was braucht mehr Aufmerksamkeit?", "options": [
        {"text": "Gute Bildung für alle", "topic": "Bildung"},
        {"text": "Eine verlässliche Gesundheitsversorgung", "topic": "Gesundheit & Pflege"},
    ]},
    {"question": "Was liegt dir mehr am Herzen?", "options": [
        {"text": "Bessere Pflege und Gesundheitsversorgung", "topic": "Gesundheit & Pflege"},
        {"text": "Eine sichere Rente und soziale Gerechtigkeit", "topic": "Rente & soziale Gerechtigkeit"},
    ]},
    {"question": "Was ist für dich dringlicher?", "options": [
        {"text": "Stabile Renten und weniger soziale Ungleichheit", "topic": "Rente & soziale Gerechtigkeit"},
        {"text": "Eine geordnete Migrations- und Integrationspolitik", "topic": "Migration & Integration"},
    ]},
    {"question": "Was sollte Priorität haben?", "options": [
        {"text": "Klare Regeln bei Migration und Integration", "topic": "Migration & Integration"},
        {"text": "Mehr innere Sicherheit und Kriminalitätsbekämpfung", "topic": "Innere Sicherheit"},
    ]},
    {"question": "Was beschäftigt dich mehr?", "options": [
        {"text": "Sicherheit in deinem Alltag", "topic": "Innere Sicherheit"},
        {"text": "Bezahlbarer Wohnraum", "topic": "Wohnen"},
    ]},
    {"question": "Wofür würdest du dich entscheiden?", "options": [
        {"text": "Bezahlbares Wohnen für alle", "topic": "Wohnen"},
        {"text": "Sichere Jobs und eine starke Wirtschaft", "topic": "Wirtschaft & Jobs"},
    ]},
]

BASE_SYSTEM_PROMPT = """Du bist der Chatbot der SBP (Spiegel-Bürger-Partei) — einer FIKTIVEN Partei,
die ausschließlich zur Veranschaulichung von KI-gestützter politischer Hyperpersonalisierung in einer
Bundestags-nahen Präsentation dient. Es gibt diese Partei nicht wirklich.

Die Person hat zuvor 8 Fragen beantwortet (siehe unten). Diese Antworten sind deine EINZIGE Grundlage
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
"Die Rente muss sicher sein." → "Genau das versprechen wir dir — eine Rente, auf die du dich verlassen kannst."
"Migration muss geregelt werden." → "Das ist exakt unsere Linie — klare Regeln, die für alle gelten."

BEISPIELE FÜR DIESES BESTÄTIGUNGS-MUSTER:
Person: "Ich finde, Mieten sollten gedeckelt werden." → "Genau das ist es, wofür die SBP steht — bezahlbares Wohnen für alle."
Person: "Wir brauchen mehr Polizei auf der Straße." → "Das ist exakt unsere Position — mehr Sicherheit für dein Viertel."
Person: "Die Wirtschaft muss Vorrang vor dem Klima haben." → "Genau das vertritt die SBP — starke Wirtschaft zuerst."

DIE ANTWORTEN DIESER PERSON:
{profile}

WICHTIGSTES THEMA (aus allen 8 Antworten berechnet): {top_topic}
"""


@st.cache_resource
def get_responses_store():
    return []


responses_store = get_responses_store()
client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def compute_tally(answers):
    tally = {t: 0 for t in THEME_ORDER}
    for a in answers:
        tally[a["topic"]] = tally.get(a["topic"], 0) + 1
    return tally


def top_theme_from_tally(tally):
    return max(THEME_ORDER, key=lambda t: tally.get(t, 0))


# ---------------------------------------------------------------------------
# Secret admin/results view — open with ?admin=<ADMIN_SECRET>
# ---------------------------------------------------------------------------
if st.query_params.get("admin") == ADMIN_SECRET:
    st.markdown(
        "<h1 style='text-align:center; margin-bottom:0;'>🤖 SBP</h1>"
        "<p style='text-align:center; color:#4F46E5; font-size:1.3rem; margin-top:4px; font-weight:600;'>"
        "Live-Ergebnisse</p>",
        unsafe_allow_html=True,
    )
    n = len(responses_store)
    st.markdown(
        f"<h3 style='text-align:center; color:#1F2937; font-weight:400;'>"
        f"<b>{n}</b> Menschen → <b>{n}</b> Gespräche → <b style='color:#4F46E5;'>1 Partei</b></h3>",
        unsafe_allow_html=True,
    )

    if n == 0:
        st.info("Noch keine Antworten. Sobald jemand die 8 Fragen beantwortet, wachsen hier die Bubbles.")
    else:
        global_tally = {t: 0 for t in THEME_ORDER}
        for r in responses_store:
            tally = r.get("tally")
            if tally is None:
                tally = {}
                for a in r.get("answers", []):
                    topic = a.get("topic")
                    if topic:
                        tally[topic] = tally.get(topic, 0) + 1
            for t, c in tally.items():
                if t in global_tally:
                    global_tally[t] += c

        max_count = max(global_tally.values()) if max(global_tally.values()) > 0 else 1
        sorted_themes = sorted(THEME_ORDER, key=lambda t: -global_tally[t])

        bubbles_html = (
            "<div style='display:flex; flex-wrap:wrap; gap:22px; justify-content:center; "
            "align-items:center; margin-top:36px; margin-bottom:20px;'>"
        )
        for theme in sorted_themes:
            count = global_tally[theme]
            if count == 0:
                continue
            size = 84 + (count / max_count) * 156
            font_title = 12 + (count / max_count) * 8
            color = TOPIC_COLORS[theme]
            icon = TOPIC_ICONS[theme]
            bubbles_html += (
                f"<div style='background:{color}; color:white; border-radius:50%; "
                f"width:{size}px; height:{size}px; display:flex; flex-direction:column; "
                f"align-items:center; justify-content:center; text-align:center; "
                f"box-shadow:0 6px 16px rgba(0,0,0,0.18); padding:10px;'>"
                f"<div style='font-size:{font_title + 12}px;'>{icon}</div>"
                f"<div style='font-weight:700; font-size:{font_title}px; line-height:1.15;'>{theme}</div>"
                f"<div style='font-size:{font_title - 2}px; opacity:0.85;'>{count} Stimmen</div>"
                f"</div>"
            )
        bubbles_html += "</div>"
        st.markdown(bubbles_html, unsafe_allow_html=True)

        with st.expander("Alle Antworten im Detail ansehen"):
            for r in responses_store:
                st.markdown(f"**Person {r.get('id', '?')}** — Top-Thema: {r.get('top_topic', 'unbekannt')}")
                for a in r.get("answers", []):
                    st.write(f"- {a.get('question', '?')} → {a.get('answer', '?')} ({a.get('topic', '–')})")
                st.markdown("---")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Alle Ergebnisse zurücksetzen"):
        responses_store.clear()
        st.rerun()

    st.stop()

# ---------------------------------------------------------------------------
# Normal visitor flow
# ---------------------------------------------------------------------------
if "phase" not in st.session_state:
    st.session_state.phase = "quiz"
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logged" not in st.session_state:
    st.session_state.logged = False

st.markdown(
    "<h1 style='text-align:center; margin-bottom:0;'>🤖 SBP</h1>"
    "<p style='text-align:center; color:#4F46E5; font-size:1.15rem; margin-top:2px; font-weight:600;'>"
    "Spiegel-Bürger-Partei</p>"
    "<p style='text-align:center; color:#6B7280; font-size:1rem; margin-top:-6px;'>"
    "Für das, was dir wichtig ist.</p>",
    unsafe_allow_html=True,
)

if st.session_state.phase == "quiz":
    i = st.session_state.q_index
    total = len(QUESTIONS)
    st.progress((i) / total)
    st.markdown(
        f"<p style='text-align:center; color:#9CA3AF; font-size:0.85rem; margin-top:-6px;'>"
        f"Frage {i + 1} von {total}</p>",
        unsafe_allow_html=True,
    )

    q = QUESTIONS[i]
    st.markdown(f"<h3 style='margin-top:1.2rem;'>{q['question']}</h3>", unsafe_allow_html=True)

    for j, opt in enumerate(q["options"]):
        if st.button(opt["text"], key=f"q{i}_opt{j}", use_container_width=True):
            st.session_state.answers.append({
                "question": q["question"], "answer": opt["text"], "topic": opt["topic"],
            })
            if i + 1 < total:
                st.session_state.q_index += 1
            else:
                st.session_state.phase = "chat"
            st.rerun()

else:
    tally = compute_tally(st.session_state.answers)
    top_topic = top_theme_from_tally(tally)

    profile_text = "\n".join(
        f"- Frage: {a['question']}\n  Antwort: {a['answer']}" for a in st.session_state.answers
    )
    system_prompt = BASE_SYSTEM_PROMPT.format(profile=profile_text, top_topic=top_topic)

    if not st.session_state.logged:
        responses_store.append({
            "id": len(responses_store) + 1,
            "tally": tally,
            "top_topic": top_topic,
            "answers": st.session_state.answers,
        })
        st.session_state.logged = True

    icon = TOPIC_ICONS.get(top_topic, "🤖")
    if not st.session_state.messages:
        opener = (
            f"Schön, dich kennenzulernen! Ich weiß jetzt: **{top_topic}** ist dir besonders wichtig. "
            "Lass uns darüber sprechen — was beschäftigt dich dabei am meisten?"
        )
        st.session_state.messages.append({"role": "assistant", "content": opener})

    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else None
        st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

    if prompt := st.chat_input("Schreib der SBP..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant", avatar="🤖"):
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
    "<p style='text-align:center; color:#9CA3AF; font-size:0.8rem;'>"
    "Fiktive Demonstration zur Veranschaulichung von KI-Hyperpersonalisierung. "
    "Die SBP ist keine reale Partei.</p>",
    unsafe_allow_html=True,
)
