import streamlit as st
import requests
import json
import re
from datetime import datetime

st.set_page_config(page_title="ScamShield AI", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.stApp {background:#0e1117;color:white}
.main-title {font-size:38px;font-weight:bold;color:white}
.subtitle {color:#b0b7c3;font-size:16px}
.section-title {font-size:23px;font-weight:bold;color:white}
.risk-high {color:#ff4b4b;font-size:25px;font-weight:bold}
.risk-medium {color:#ffa500;font-size:25px;font-weight:bold}
.risk-low {color:#00cc88;font-size:25px;font-weight:bold}
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:1b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are ScamShield AI, a digital message safety investigator.
Analyze the SMS, WhatsApp message, email or online offer.
Return ONLY valid JSON with these fields:
{
 "message_type":"Short message category",
 "ai_analysis":"Explain why it may be safe or suspicious",
 "warning_signs":["Warning sign"],
 "suspicious_phrases":["Suspicious phrase"],
 "recommended_actions":["Action"]
}
Never call a message definitely genuine without evidence. Identify OTP requests,
threats, urgency, suspicious links and payment requests. Do not invent details.
Give practical safety recommendations."""


def get_api_key():
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        return ""


def calculate_risk_score(message):
    checks = [
        (r"\b(otp|one time password)\b", 35, "Requests for OTP information"),
        (r"\b(password|pin|cvv|card details|bank details)\b", 25, "Requests for sensitive financial or account information"),
        (r"\b(urgent|immediately|right now|hurry|act now|today only)\b", 15, "Urgent language and pressure tactics"),
        (r"\b(blocked|suspended|suspension|closed|deactivated|terminated)\b", 20, "Threats of account suspension or closure"),
        (r"(https?://|www\.|\bclick (here|this link)|open this link|visit this link)", 15, "Suspicious link or link-related request"),
        (r"\bkyc\b", 10, "KYC-related verification request"),
        (r"\b(transfer money|send money|make payment|pay now)\b", 15, "Payment or money transfer request"),
        (r"\b(lottery|prize|winner|free gift|reward)\b", 15, "Unexpected prize or reward claim")
    ]

    score, indicators = 0, []

    for pattern, points, description in checks:
        if re.search(pattern, message.lower()):
            score += points
            indicators.append(description)

    return min(score, 100), indicators
def parse_ai_response(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)

        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    return {
        "message_type": "General Message",
        "ai_analysis": text,
        "warning_signs": [],
        "suspicious_phrases": [],
        "recommended_actions": [
            "Verify the sender through an official source.",
            "Do not share OTPs, passwords or PINs.",
            "Avoid clicking unknown links."
        ]
    }
def ask_ai(message, api_key):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]

    if api_key:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1200
            },
            timeout=90
        )

        if not response.ok:
            raise Exception(
                f"Groq API Error {response.status_code}: {response.text}"
            )

        result = response.json()
        return parse_ai_response(
            result["choices"][0]["message"]["content"]
        ), "Groq Cloud AI"

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()
    result = response.json()

    return parse_ai_response(
        result["message"]["content"]
    ), "Ollama + Gemma 3:1B"


def investigate_message(message):
    ai, service = ask_ai(message, get_api_key())
    score, indicators = calculate_risk_score(message)

    level = (
        "High Concern" if score >= 61
        else "Medium Concern" if score >= 31
        else "Low Concern"
    )

    warnings = ai.get("warning_signs", [])
    phrases = ai.get("suspicious_phrases", [])
    actions = ai.get("recommended_actions", [])

    warnings = warnings if isinstance(warnings, list) else []
    phrases = phrases if isinstance(phrases, list) else []
    actions = actions if isinstance(actions, list) else []

    warnings.extend(x for x in indicators if x not in warnings)

    if not actions:
        actions = [
            "Do not click unknown links.",
            "Never share OTP, PIN or passwords.",
            "Verify the sender through official channels."
        ]

    return {
        "risk_score": score,
        "risk_level": level,
        "message_type": ai.get("message_type", "General Message"),
        "ai_analysis": ai.get("ai_analysis", "No additional AI analysis available."),
        "warning_signs": warnings,
        "suspicious_phrases": phrases,
        "recommended_actions": actions,
        "service": service
    }
st.markdown(
    '<div class="main-title">🛡️ ScamShield AI</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">AI-Powered Scam Message Investigator</div>',
    unsafe_allow_html=True
)
st.write(
    "Analyze suspicious SMS, WhatsApp messages, emails, "
    "and online offers using Artificial Intelligence."
)
st.divider()
with st.sidebar:
    st.title("🛡️ ScamShield AI")
    st.subheader("Investigation Statistics")

    st.metric("Total Investigations", len(st.session_state.history))

    high_count = sum(
        x["risk_level"] == "High Concern"
        for x in st.session_state.history
    )
    st.metric("High Risk Messages", high_count)

    st.divider()
    st.subheader("Safety Tips")
    st.write(
        "• Never share OTP or PIN.\n\n"
        "• Avoid unknown links.\n\n"
        "• Verify payment requests.\n\n"
        "• Use official websites."
    )

    st.divider()

    if get_api_key():
        st.success("Cloud AI: Groq")
    else:
        st.info("Local AI: Ollama + Gemma 3:1B")

    if st.button("Clear Investigation History"):
        st.session_state.history = []
        st.session_state.pop("latest_report", None)
        st.rerun()
st.markdown(
    '<div class="section-title">🔍 Message Investigation</div>',
    unsafe_allow_html=True
)

st.write("Paste the message you want ScamShield AI to investigate.")

message = st.text_area(
    "Suspicious Message",
    height=170,
    placeholder="Paste your suspicious SMS, WhatsApp message, email or online offer here..."
)

st.caption(
    "Privacy note: Your message is sent to your locally running "
    "Ollama service or configured Groq Cloud service. "
    "Avoid entering real passwords, OTPs or banking details."
)

if st.button(
    "🔍 Investigate Message",
    type="primary",
    use_container_width=True
):
    if not message.strip():
        st.warning("Please enter a message before investigation.")

    else:
        with st.spinner("ScamShield AI is analyzing your message..."):
            try:
                report = investigate_message(message)
                report["message"] = message
                report["date"] = datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                )

                st.session_state.history.append(report)
                st.rerun()

                st.success("Investigation completed successfully!")

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the AI service. "
                    "Check whether Ollama is running or whether "
                    "your Groq API key is configured."
                )

            except requests.exceptions.Timeout:
                st.error(
                    "The AI service took too long to respond. "
                    "Please try again."
                )

            except Exception as error:
                st.error(f"Something went wrong: {error}")
if "latest_report" in st.session_state:
   report = st.session_state.latest_report
    st.divider()
    st.markdown(
        '<div class="section-title">📊 Investigation Report</div>',
        unsafe_allow_html=True
    )

    st.write("Investigated on:", report["date"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Risk Score", f'{report["risk_score"]}/100')
    c2.metric("Risk Level", report["risk_level"])
    c3.metric("Warning Signs", len(report["warning_signs"]))

    st.progress(report["risk_score"] / 100)

    level = report["risk_level"]

    if level == "High Concern":
        st.markdown(
            '<div class="risk-high">🚨 HIGH CONCERN</div>',
            unsafe_allow_html=True
        )
        st.error("Multiple potential scam indicators have been detected.")

    elif level == "Medium Concern":
        st.markdown(
            '<div class="risk-medium">⚠️ MEDIUM CONCERN</div>',
            unsafe_allow_html=True
        )
        st.warning(
            "Some suspicious indicators were detected. Verify carefully."
        )

    else:
        st.markdown(
            '<div class="risk-low">✅ LOW CONCERN</div>',
            unsafe_allow_html=True
        )
        st.success(
            "Few known scam indicators were detected. "
            "Still verify important messages."
        )

    st.subheader("📩 Message Type")
    st.write(report["message_type"])

    st.subheader("🧠 AI Analysis")
    st.write(report["ai_analysis"])

    st.subheader("🔎 Detected Risk Indicators")

    if report["warning_signs"]:
        for item in report["warning_signs"]:
            st.write(f"• {item}")
    else:
        st.write("No common risk indicators were detected.")

    st.subheader("⚠️ Suspicious Phrase Detection")

    if report["suspicious_phrases"]:
        for i, phrase in enumerate(report["suspicious_phrases"], 1):
            st.write(f"**Warning Sign {i}:** {phrase}")
    else:
        st.write("No specific suspicious phrases were returned by the AI.")

    st.subheader("🛡️ Recommended Safety Actions")

    for action in report["recommended_actions"]:
        st.write("• " + action)

    st.subheader("ℹ️ Investigation Limitations")
    st.info(
        "This is an AI-generated assessment based on the message text. "
        "It may make mistakes. A low-risk classification does not "
        "guarantee that a message is legitimate. Always verify "
        "important communications through official channels."
    )
    st.caption(f"AI Service Used: {report['service']}")
st.divider()
st.markdown(
    '<div class="section-title">📚 Investigation History</div>',
    unsafe_allow_html=True
)

st.write(
    f"Total analyzed messages: {len(st.session_state.history)}"
)

if st.session_state.history:
    for number, item in enumerate(
        reversed(st.session_state.history), 1
    ):
        with st.expander(
            f"Investigation {len(st.session_state.history) - number + 1} "
            f"| {item['risk_level']} | {item['date']}"
        ):
            st.write("**Message:**", item["message"])
            st.write(f"**Risk Score:** {item['risk_score']}/100")
            st.write("**Message Type:**", item["message_type"])
            st.write("**AI Analysis:**", item["ai_analysis"])

else:
    st.info("No investigations yet. Analyze a message to see its history.")
st.divider()
st.markdown(
    "<center><b>SCAMSHIELD AI | Stay Alert. Stay Protected.</b>"
    "<br>AI-Powered Digital Safety Assistant</center>",
    unsafe_allow_html=True
)
