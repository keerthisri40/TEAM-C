import cv2
import base64
import numpy as np
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from face_auth import FaceAuthenticator
from gmail_lib import send_gmail, get_latest_emails

app = Flask(__name__)
app.secret_key = "infosys_secure_key"

face_system = FaceAuthenticator()
recognizer = sr.Recognizer()

# Stability Settings
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True

@app.route('/')
def index():
    return redirect(url_for('face_auth_screen'))

@app.route('/face_auth_page')
def face_auth_screen():
    return render_template('face_recognition.html')

@app.route('/verify_face', methods=['POST'])
def verify_face_logic():
    try:
        data = request.json['image']
        encoded_data = data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if face_system.verify_frame(frame):
            session['verified'] = True
            return jsonify({"status": "success"})
        return jsonify({"status": "fail"})
    except:
        return jsonify({"status": "fail"})

@app.route('/dashboard')
def dashboard_view():
    if not session.get('verified'):
        return redirect(url_for('face_auth_screen'))
    
    # greet=True triggers "Hi Keerthi, listening..." in the HTML JS
    return render_template('dashboard.html', greet=True)

@app.route('/compose')
def compose_view():
    if not session.get('verified'):
        return redirect(url_for('face_auth_screen'))
    return render_template('compose.html')

@app.route('/voice_action', methods=['POST'])
def voice_action():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=7)
            text = recognizer.recognize_google(audio).lower()
            print(f">>> Voice: {text}")

            # 1. NAVIGATION
            if any(word in text for word in ["dashboard", "home", "back", "return"]):
                return jsonify({"status": "navigate", "url": "/dashboard", "message": "Returning home."})
            
            if "inbox" in text:
                return jsonify({"status": "navigate", "url": "/inbox", "message": "Opening inbox."})
            
            if "sent" in text:
                return jsonify({"status": "navigate", "url": "/sent", "message": "Opening sent mails."})
            
            if "trash" in text or "bin" in text:
                return jsonify({"status": "navigate", "url": "/trash", "message": "Opening trash folder."})
            
            if "compose" in text:
                return jsonify({"status": "navigate", "url": "/compose", "message": "Opening compose window."})

            # 2. EMAIL ACTIONS
            if "send" in text:
                return jsonify({"status": "trigger_send", "message": "send"})
            
            if "cancel" in text:
                return jsonify({"status": "cancel_action", "message": "cancel"})

            # Inside @app.route('/voice_action', methods=['POST'])
# Update the logic under # 3. OPEN MAIL 1 & REPLY FLOW

            # 3. OPEN MAIL 1 & REPLY FLOW
            if "mail" in text and ("one" in text or "1" in text):
                mail_data = get_latest_emails(1, 'INBOX')
                if mail_data:
                    session['last_sender'] = mail_data[0]['sender']
                    # We also store a flag to let the frontend know we are waiting for a reply/cancel
                    session['awaiting_reply_confirmation'] = True
                    res = f"Email from {mail_data[0]['sender']}. Content: {mail_data[0]['snippet']}. Do you want to reply or cancel?"
                    return jsonify({"status": "ask_reply", "message": res})
                return jsonify({"status": "heard", "message": "No emails found."})

            # ADD THIS: Handling the response to "reply or cancel"
            if session.get('awaiting_reply_confirmation'):
                if "reply" in text:
                    session['awaiting_reply_confirmation'] = False
                    # Extract just the email if sender is "Name <email@gmail.com>"
                    raw_sender = session.get('last_sender', "")
                    clean_email = raw_sender.split('<')[-1].replace('>', '').strip()
                    session['reply_email'] = clean_email 
                    return jsonify({"status": "navigate", "url": "/compose", "message": "Opening reply window."})
                
                if "cancel" in text:
                    session['awaiting_reply_confirmation'] = False
                    return jsonify({"status": "heard", "message": "Action cancelled."})

            # 4. LOGOUT
            if "logout" in text:
                session.clear()
                return jsonify({"status": "logout", "url": "/face_auth_page", "message": "Logging out."})

            return jsonify({"status": "heard", "message": text})
    except:
        return jsonify({"status": "error", "message": ""})

@app.route('/send_dictated_mail', methods=['POST'])
def send_dictated_mail():
    data = request.json
    try:
        if send_gmail(data.get('recipient'), data.get('subject'), data.get('content')):
            return jsonify({"status": "success"})
        return jsonify({"status": "error"})
    except:
        return jsonify({"status": "error"})

@app.route('/reply_to_mail', methods=['POST'])
def reply_to_mail():
    data = request.json
    recipient = session.get('last_sender')
    try:
        if recipient and send_gmail(recipient, "Re: Your Email", data.get('content')):
            return jsonify({"status": "success"})
        return jsonify({"status": "error"})
    except:
        return jsonify({"status": "error"})

@app.route('/inbox')
def inbox_view():
    emails = get_latest_emails(count=5, label_id='INBOX')
    return render_template('folder.html', title="Inbox", emails=emails)

@app.route('/sent')
def sent_view():
    emails = get_latest_emails(count=5, label_id='SENT')
    return render_template('folder.html', title="Sent Mail", emails=emails)

@app.route('/trash')
def trash_view():
    emails = get_latest_emails(count=5, label_id='TRASH')
    return render_template('folder.html', title="Trash", emails=emails)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)