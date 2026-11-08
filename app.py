
import streamlit as st
import requests
import json
import re
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ScamShield AI",
    page_icon="🛡️",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #ffffff;
}
.main-title {
    font-size: 38px;
    font-weight: bold;
    color: #ffffff;
}
.subtitle {
    color: #b0b7c3;
    font-size: 16px;
}
.section-title {
    font-size: 23px;
    font-weight: bold;
    color: #ffffff;
}
.risk-high {
    color: #ff4b4b;
    font-size: 25px;
    font-weight: bold;
}
.risk-medium {
    color: #ffa500;
    font-size: 25px;
    font-weight: bold;
}
.risk-low {
    color: #00cc88;
    font-size: 25px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

# --------------------------------------------------
# AI CONFIGURATION
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:1b"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """
You are ScamShield AI, a digital message safety investigator.

Analyze the given SMS, WhatsApp message, email, or online offer.

Return ONLY a valid JSON object with these fields:

{
    "message_type": "Short message category",
    "ai_analysis": "Explain why the message may be safe or suspicious.",
    "warning_signs": ["Warning sign 1", "Warning sign 2"],
    "suspicious_phrases": ["Suspicious phrase 1", "Suspicious phrase 2"],
    "recommended_actions": ["Action 1", "Action 2"]
}

Rules:
- Never say a message is definitely genuine without evidence.
- Identify OTP requests, threats, urgency, suspicious links and payment requests.
- If the message looks suspicious, explain why.
- Give practical safety recommendations.
- Do not invent details that are not in the message.
"""

# --------------------------------------------------
# GET GROQ API KEY
# --------------------------------------------------

def get_groq_api_key():
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        return ""

# --------------------------------------------------
# RISK SCORE CALCULATION
# --------------------------------------------------

def calculate_risk_score(message):
    text = message.lower()

    score = 0
    indicators = []

    checks = [
        (
            r"\b(otp|one time password)\b",
            35,
            "Requests for OTP information"
        ),
        (
            r"\b(password|pin|cvv|card details|bank details)\b",
            25,
            "Requests for sensitive financial or account information"
        ),
        (
            r"\b(urgent|immediately|right now|hurry|act now|today only)\b",
            15,
            "Urgent language and pressure tactics"
        ),
        (
            r"\b(blocked|suspended|suspension|closed|deactivated|terminated)\b",
            20,
            "Threats of account suspension or closure"
        ),
        (
            r"(https?://|www\.|\bclick (here|this link)|open this link|visit this link)",
            15,
            "Suspicious link or link-related request"
        ),
        (
            r"\bkyc\b",
            10,
            "KYC-related verification request"
        ),
        (
            r"\b(transfer money|send money|make payment|pay now)\b",
            15,
            "Payment or money transfer request"
        ),
        (
            r"\b(lottery|prize|winner|free gift|reward)\b",
            15,
            "Unexpected prize or reward claim"
        )
    ]

    for pattern, points, description in checks:
        if re.search(pattern, text):
            score += points
            indicators.append(description)

    return min(score, 100), indicators

# --------------------------------------------------
# AI RESPONSE PARSING
# --------------------------------------------------

def parse_ai_response(response_text):
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1

        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
    except json.JSONDecodeError:
        pass

    return {
        "message_type": "General Message",
        "ai_analysis": response_text,
        "warning_signs": [],
        "suspicious_phrases": [],
        "recommended_actions": [
            "Verify the sender through an official source.",
            "Do not share OTPs, passwords or PINs.",
            "Avoid clicking unknown links."
        ]
    }

# --------------------------------------------------
# OLLAMA AI
# --------------------------------------------------

def analyze_with_ollama(message):

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    result = response.json()
    ai_text = result["message"]["content"]

    return parse_ai_response(ai_text)

# --------------------------------------------------
# GROQ AI
# --------------------------------------------------

def analyze_with_groq(message, api_key):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }

    response = requests.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        timeout=90
    )

    response.raise_for_status()

    result = response.json()
    ai_text = result["choices"][0]["message"]["content"]

    return parse_ai_response(ai_text)

# --------------------------------------------------
# SELECT AI SERVICE AUTOMATICALLY
# --------------------------------------------------

def investigate_message(message):

    api_key = get_groq_api_key()

    if api_key:
        ai_result = analyze_with_groq(message, api_key)
        service_name = "Groq Cloud AI"
    else:
        ai_result = analyze_with_ollama(message)
        service_name = "Ollama + Gemma 3:1B"

    risk_score, local_indicators = calculate_risk_score(message)

    warning_signs = ai_result.get("warning_signs", [])
    suspicious_phrases = ai_result.get("suspicious_phrases", [])
    recommended_actions = ai_result.get("recommended_actions", [])

    if not isinstance(warning_signs, list):
        warning_signs = []

    if not isinstance(suspicious_phrases, list):
        suspicious_phrases = []

    if not isinstance(recommended_actions, list):
        recommended_actions = []

    # Add locally detected indicators
    for indicator in local_indicators:
        if indicator not in warning_signs:
            warning_signs.append(indicator)

    # Final risk classification
    if risk_score >= 61:
        risk_level = "High Concern"
    elif risk_score >= 31:
        risk_level = "Medium Concern"
    else:
        risk_level = "Low Concern"

    # Default safety actions
    if not recommended_actions:
        recommended_actions = [
            "Do not click unknown links.",
            "Never share OTP, PIN or passwords.",
            "Verify the sender through official channels."
        ]

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "message_type": ai_result.get(
            "message_type", "General Message"
        ),
        "ai_analysis": ai_result.get(
            "ai_analysis", "No additional AI analysis available."
        ),
        "warning_signs": warning_signs,
        "suspicious_phrases": suspicious_phrases,
        "recommended_actions": recommended_actions,
        "service": service_name
    }

# --------------------------------------------------
# HEADER
# --------------------------------------------------

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

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("🛡️ ScamShield AI")

    st.subheader("Investigation Statistics")

    total_investigations = len(st.session_state.history)

    high_risk_count = sum(
        1 for item in st.session_state.history
        if item["risk_level"] == "High Concern"
    )

    st.metric("Total Investigations", total_investigations)
    st.metric("High Risk Messages", high_risk_count)

    st.divider()

    st.subheader("Safety Tips")

    st.write("• Never share OTP or PIN.")
    st.write("• Avoid unknown links.")
    st.write("• Verify payment requests.")
    st.write("• Use official websites.")

    st.divider()

    if get_groq_api_key():
        st.success("Cloud AI: Groq")
    else:
        st.info("Local AI: Ollama + Gemma 3:1B")

    if st.button("Clear Investigation History"):
        st.session_state.history = []
        st.rerun()

# --------------------------------------------------
# MESSAGE INVESTIGATION
# --------------------------------------------------

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

if st.button("🔍 Investigate Message", type="primary", use_container_width=True):

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
                st.session_state.latest_report = report

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

            except requests.exceptions.HTTPError as error:
                st.error(
                    f"AI service returned an error: {error}"
                )

            except Exception as error:
                st.error(f"Something went wrong: {error}")

# --------------------------------------------------
# INVESTIGATION REPORT
# --------------------------------------------------

if "latest_report" in st.session_state:

    report = st.session_state.latest_report

    st.divider()

    st.markdown(
        '<div class="section-title">📊 Investigation Report</div>',
        unsafe_allow_html=True
    )

    st.write("Investigated on:", report["date"])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Risk Score",
            f'{report["risk_score"]}/100'
        )

    with col2:
        st.metric(
            "Risk Level",
            report["risk_level"]
        )

    with col3:
        st.metric(
            "Warning Signs",
            len(report["warning_signs"])
        )

    st.progress(report["risk_score"] / 100)

    if report["risk_level"] == "High Concern":
        st.markdown(
            '<div class="risk-high">🚨 HIGH CONCERN</div>',
            unsafe_allow_html=True
        )
        st.error(
            "Multiple potential scam indicators have been detected."
        )

    elif report["risk_level"] == "Medium Concern":
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
        for index, phrase in enumerate(
            report["suspicious_phrases"], start=1
        ):
            st.write(f"**Warning Sign {index}:** {phrase}")
    else:
        st.write("No specific suspicious phrases were returned by the AI.")

    st.subheader("🛡️ Recommended Safety Actions")

    for action in report["recommended_actions"]:
        st.write(f"• {action}")

    st.subheader("ℹ️ Investigation Limitations")

    st.info(
        "This is an AI-generated assessment based on the message text. "
        "It may make mistakes. A low-risk classification does not "
        "guarantee that a message is legitimate. Always verify "
        "important communications through official channels."
    )

    st.caption(f"AI Service Used: {report['service']}")

# --------------------------------------------------
# INVESTIGATION HISTORY
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">📚 Investigation History</div>',
    unsafe_allow_html=True
)

st.write(
    f"Total analyzed messages: {len(st.session_state.history)}"
)

if st.session_state.history:

    for index, item in enumerate(
        reversed(st.session_state.history), start=1
    ):

        with st.expander(
            f"Investigation {len(st.session_state.history) - index + 1} "
            f"| {item['risk_level']} | {item['date']}"
        ):

            st.write("**Message:**")
            st.write(item["message"])

            st.write(
                f"**Risk Score:** {item['risk_score']}/100"
            )

            st.write(
                f"**Message Type:** {item['message_type']}"
            )

            st.write("**AI Analysis:**")
            st.write(item["ai_analysis"])

else:
    st.info("No investigations yet. Analyze a message to see its history.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    "<center><b>SCAMSHIELD AI | Stay Alert. Stay Protected.</b>"
    "<br>AI-Powered Digital Safety Assistant</center>",
    unsafe_allow_html=True
)
