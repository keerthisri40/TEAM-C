import os
import cv2
import base64
import numpy as np
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from face_auth import FaceAuthenticator
from gmail_lib import send_gmail

app = Flask(__name__)
app.secret_key = "infosys_secure_key"

USER_CREDENTIALS = {"email": "keerthisri66444@gmail.com", "password": "password123"}
EMAIL_MAP = {
    "mail1": "keerthisri66444@gmail.com", 
    "mailone": "keerthisri66444@gmail.com",
    "mail2": "kuntamshiny@gmail.com",
    "mailtwo": "kuntamshiny@gmail.com"
}

face_system = FaceAuthenticator()
recognizer = sr.Recognizer()

# --- AUTH ROUTES ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/login_check', methods=['POST'])
def login_check():
    data = request.json
    if data.get('email') == USER_CREDENTIALS['email'] and data.get('password') == USER_CREDENTIALS['password']:
        session['step1'] = True 
        return jsonify({"status": "success"})
    return jsonify({"status": "fail", "message": "Wrong Credentials"})

@app.route('/face_auth_page')
def face_auth_screen():
    if not session.get('step1'): return redirect(url_for('login_page'))
    return render_template('face_recognition.html')

@app.route('/verify_face', methods=['POST'])
def verify_face_logic():
    data = request.json['image']
    encoded_data = data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if face_system.verify_frame(frame):
        session['step2'] = True 
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

@app.route('/dashboard')
def dashboard_view():
    if not session.get('step2'): return redirect(url_for('login_page'))
    return render_template('dashboard.html')

# --- ADD THESE NEW ROUTES TO YOUR app.py ---

@app.route('/inbox')
def inbox_page():
    return "<h1>Inbox Section</h1><p>Voice-enabled navigation successful!</p>"

@app.route('/sent')
def sent_page():
    return "<h1>Sent Section</h1>"

@app.route('/trash')
def trash_page():
    return "<h1>Trash Section</h1>"

@app.route('/voice_action', methods=['POST'])
def voice_action():
    """Phase 1: Identify the recipient"""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)
        try:
            raw_text = recognizer.recognize_google(audio).lower()
            processed_text = raw_text.replace("one", "1").replace("two", "2").replace(" ", "")
            
            if "open" in processed_text:
                alias = processed_text.replace("open", "").strip()
                recipient = EMAIL_MAP.get(alias)
                if recipient:
                    # Instead of sending immediately, ask for content
                    return jsonify({
                        "status": "ask_content", 
                        "message": f"Found {alias}. Please speak your message.",
                        "recipient": recipient
                    })
                return jsonify({"status": "error", "message": f"Contact '{alias}' not found"})
            return jsonify({"status": "heard", "text": raw_text})
        except:
            return jsonify({"status": "error", "message": "Listening failed"})

@app.route('/send_dictated_mail', methods=['POST'])
def send_dictated_mail():
    """Phase 2: Listen for the full message body with extended time."""
    recipient = request.json.get('recipient')
    with sr.Microphone() as source:
        # Crucial for noisy environments
        recognizer.adjust_for_ambient_noise(source, duration=0.8) 
        try:
            # Increased timeout and phrase_limit for dictating content
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=15)
            content = recognizer.recognize_google(audio)
            
            # Use Gmail API to send the actual dictated text
            if send_gmail(recipient, "Voice Dictated Message", content):
                return jsonify({"status": "success", "message": content})
            return jsonify({"status": "error", "message": "Failed to send via Gmail"})
        except sr.UnknownValueError:
            return jsonify({"status": "error", "message": "Could not understand your message."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
if __name__ == '__main__':
    app.run(debug=True, threaded=True)