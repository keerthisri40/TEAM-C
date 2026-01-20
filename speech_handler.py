import speech_recognition as sr

# Your Registered Email Schema
EMAIL_MAP = {
    "mail1": "keerthisri66444@gmail.com",
    "mailone": "keerthisri66444@gmail.com", # Added for spoken word support
    "mail2": "kuntamshiny@gmail.com",
    "mailtwo": "kuntamshiny@gmail.com"   # Added for spoken word support
}

def get_voice_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command (e.g., 'open mail2')...")
        audio = recognizer.listen(source)
    
    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Instruction: {command}")
        return command
    except:
        return "Command not recognized"