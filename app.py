import os
import cv2
import base64
import numpy as np
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from face_auth import FaceAuthenticator
from gmail_lib import send_gmail, get_latest_emails
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "infosys_secure_key"

# ================= TOKENS =================
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

client = Client(TWILIO_SID, TWILIO_AUTH)

# ================= SYSTEM INIT =================
face_system = FaceAuthenticator()

# ================= GLOBAL STATS =================
stats = {
    "emails_sent": 0,
    "emails_received": 0,
    "whatsapp_sent": 0,
    "telegram_sent": 0,
    "summaries": 0,
    "voice_commands": 0
}

# ================= CONTACT MAP =================
CONTACT_MAP = {
    "teja": "+918341161719",
    "myself": "6247647941",
    "keerthi": "keerthisri66444@gmail.com",
    "shiny": "kuntamshiny@gmail.com"
}

# ================= HELPERS =================
def reset_flow():
    session.pop("flow", None)
    session.pop("step", None)
    session.pop("draft_to", None)
    session.pop("draft_sub", None)
    session.pop("draft_body", None)

# ================= ROUTES =================

@app.route('/')
def index():
    return redirect(url_for('face_auth_screen'))

@app.route('/face_auth_page')
def face_auth_screen():
    return render_template('face_recognition.html')

@app.route('/verify_face', methods=['POST'])
def verify_face():
    data = request.json['image']
    encoded = data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if face_system.verify_frame(frame):
        session['verified'] = True
        return jsonify({"status": "success"})

    return jsonify({"status": "fail"})

@app.route('/dashboard')
def dashboard():
    if not session.get('verified'):
        return redirect(url_for('face_auth_screen'))
    return render_template('dashboard.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("face_auth_screen"))

# ================= DYNAMIC LOAD =================

@app.route('/load/<section>')
def load_section(section):
    if not session.get('verified'):
        return "Unauthorized"

    if section == "home":
        return render_template("home.html")

    if section in ["inbox", "sent", "trash"]:
        emails = get_latest_emails(10, section.upper())
        session["last_loaded_emails"] = emails

        if section == "inbox":
            stats["emails_received"] = len(emails)

        return render_template("folder.html",
                               title=section.capitalize(),
                               emails=emails)

    if section == "compose":
        platform = request.args.get("platform", "email")
        return render_template("compose.html", platform=platform)

    if section == "analytics":
        return render_template("analytics.html", stats=stats)

    return "<h3>Section Not Found</h3>"

# ================= VOICE ENGINE =================

@app.route('/voice_action', methods=['POST'])
def voice_action():
    if not session.get("verified"):
        return jsonify({"status": "fail"})

    text = request.json.get("text", "").lower().strip()

    if not text:
        return jsonify({"status": "retry"})

    print("Heard:", text)
    stats["voice_commands"] += 1

    # ================= NAVIGATION =================

    if "open home" in text or text == "home":
        reset_flow()
        return jsonify({"status": "navigate", "url": "/load/home", "speak": "Returning to dashboard."})

    if "open analytics" in text or text == "analytics":
        return jsonify({"status": "navigate", "url": "/load/analytics", "speak": "Opening analytics dashboard."})

    if "open inbox" in text or text == "inbox":
        return jsonify({"status": "navigate", "url": "/load/inbox", "speak": "Opening inbox."})

    if "open sent" in text or text == "sent":
        return jsonify({"status": "navigate", "url": "/load/sent", "speak": "Opening sent mails."})

    if "open trash" in text or text == "trash":
        return jsonify({"status": "navigate", "url": "/load/trash", "speak": "Opening trash folder."})

    if "return to dashboard" in text or "go back" in text:
        reset_flow()
        return jsonify({"status": "navigate", "url": "/load/home", "speak": "Returning to dashboard."})

    if "logout" in text:
        return jsonify({"status": "navigate", "url": "/logout", "speak": "Logging out."})

    # ================= START FLOWS =================

    if "open telegram" in text or text == "telegram":
        reset_flow()
        session["flow"] = "telegram"
        session["step"] = "recipient"
        return jsonify({
            "status": "navigate",
            "url": "/load/compose?platform=telegram",
            "speak": "Opening Telegram. Please tell me the chat ID."
        })

    if "open whatsapp" in text or text == "whatsapp":
        reset_flow()
        session["flow"] = "whatsapp"
        session["step"] = "recipient"
        return jsonify({
            "status": "navigate",
            "url": "/load/compose?platform=whatsapp",
            "speak": "Opening WhatsApp. Please tell me the phone number."
        })

    if "compose email" in text or "open email" in text:
        reset_flow()
        session["flow"] = "email"
        session["step"] = "recipient"
        return jsonify({
            "status": "navigate",
            "url": "/load/compose?platform=email",
            "speak": "Opening email compose. Please tell me the recipient email."
        })

    # ================= FLOW HANDLER =================

    if "flow" in session:
        flow = session["flow"]
        step = session["step"]

        if step == "recipient":
            target = CONTACT_MAP.get(text.replace(" ", ""), text)
            session["draft_to"] = target
            session["step"] = "subject" if flow == "email" else "content"

            speak_text = "Please tell me the subject." if flow == "email" else "Please tell me the message."
            return jsonify({
                "status": "navigate",
                "url": f"/load/compose?platform={flow}",
                "speak": speak_text
            })

        if step == "subject":
            session["draft_sub"] = text
            session["step"] = "content"
            return jsonify({
                "status": "navigate",
                "url": "/load/compose?platform=email",
                "speak": "Subject noted. Please tell me the content."
            })

        if step == "content":
            session["draft_body"] = text
            session["step"] = "confirm"
            return jsonify({
                "status": "navigate",
                "url": f"/load/compose?platform={flow}",
                "speak": "Content noted. Say send to confirm or cancel to abort."
            })

        if step == "confirm":

            if "send" in text:
                try:
                    if flow == "email":
                        send_gmail(session["draft_to"],
                                   session.get("draft_sub", "NovaVoice"),
                                   session["draft_body"])
                        stats["emails_sent"] += 1

                    elif flow == "whatsapp":
                        msg = client.messages.create(
                            from_='whatsapp:+14155238886',
                            body=session["draft_body"],
                            to=f'whatsapp:{session["draft_to"]}'
                        )
                        if msg.sid:
                            stats["whatsapp_sent"] += 1

                    elif flow == "telegram":
                        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                        res = requests.post(url, json={
                            "chat_id": session["draft_to"],
                            "text": session["draft_body"]
                        }).json()

                        if res.get("ok"):
                            stats["telegram_sent"] += 1

                    reset_flow()

                    return jsonify({
                        "status": "navigate",
                        "url": "/load/home",
                        "speak": "Message sent successfully."
                    })

                except Exception as e:
                    print("Error:", e)
                    return jsonify({"status": "speak", "message": "Failed to send message."})

            if "cancel" in text:
                reset_flow()
                return jsonify({
                    "status": "navigate",
                    "url": "/load/home",
                    "speak": "Operation cancelled."
                })

    return jsonify({"status": "retry"})

@app.route("/api/stats")
def api_stats():
    return jsonify(stats)

if __name__ == "__main__":
    app.run(use_reloader=False)