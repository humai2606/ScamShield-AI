# ScamShield AI – AI-Powered Scam Message Investigator
APP LINK:=https://scamshield-ai-hf9tsrppjpjbfvguha6epg.streamlit.app/
## Project Overview

ScamShield AI is an AI-powered web application that analyzes suspicious messages and helps users identify potential scams, phishing attempts, and fraudulent activities.

The application uses AI analysis and rule-based risk detection to generate an investigation report with risk scores, warning signs, suspicious phrases, and recommended safety actions.

## Features

- **AI-Based Message Analysis:** Analyzes suspicious messages using Groq Cloud AI.
- **Risk Score:** Generates a risk score out of 100.
- **Risk Classification:** Classifies messages into Low, Medium, and High Concern.
- **Warning Sign Detection:** Identifies suspicious patterns and scam indicators.
- **Suspicious Phrase Detection:** Highlights potentially dangerous words and phrases.
- **Safety Recommendations:** Provides practical steps to stay safe.
- **Investigation History:** Maintains a history of analyzed messages.
- **Investigation Statistics:** Displays total investigations and high-risk messages.

## Technologies Used

- Python
- Streamlit
- Groq API
- Requests
- Regular Expressions
- JSON

## How It Works

1. User enters a suspicious message.
2. ScamShield AI analyzes the message.
3. AI identifies possible scam indicators.
4. The application calculates a risk score.
5. An investigation report is generated.
6. The user receives safety recommendations.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/humai2606/ScamShield-AI.git
```

### 2. Open the Project Folder

```bash
cd ScamShield-AI
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Groq API Key

Create a `.streamlit/secrets.toml` file:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Replace the placeholder with your own Groq API key. Never upload your API key to GitHub.

### 5. Run the Application

```bash
python -m streamlit run app.py
```

## Example Use Case

**Input Message:**

"URGENT! Your bank account will be blocked today. Click this link immediately to update your KYC. Share your OTP to avoid account suspension."

**Expected Result:**

- Risk Score: 95/100
- Risk Level: High Concern
- Message Type: Suspicious SMS (Phishing Attempt)

## Project Objective

The main objective of ScamShield AI is to help users recognize suspicious messages, understand potential online threats, and make safer decisions before responding to unknown messages or links.

## Disclaimer

ScamShield AI is an educational project. Its risk score and AI analysis are indicative assessments, not guarantees that a message is genuine or fraudulent. Always verify important requests through official channels.

## Author

**Humairul Jashira M.**

B.Sc. Computer Science with Artificial Intelligence
