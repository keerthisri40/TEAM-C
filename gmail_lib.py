import os
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# (Keep imports and get_gmail_service as they are)

def send_gmail(to_email, subject, body):
    try:
        service = get_gmail_service()
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['From'] = 'me'
        message['Subject'] = subject # Uses the passed subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        service.users().messages().send(userId="me", body=create_message).execute()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# (Keep get_latest_emails as it is)

# --- UPDATED: Accepts label_id to fetch specific folders ---
def get_latest_emails(count=1, label_id='INBOX'):
    try:
        service = get_gmail_service()
        # labelIds filter allows us to pick Inbox, Sent, or Trash
        results = service.users().messages().list(userId='me', maxResults=count, labelIds=[label_id]).execute()
        messages = results.get('messages', [])

        if not messages: return []

        mail_list = []
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            headers = msg['payload']['headers']
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            
            mail_list.append({
                "sender": sender,
                "snippet": msg['snippet']
            })
        return mail_list
    except Exception as e:
        print(f"Error fetching {label_id}: {e}")
        return []