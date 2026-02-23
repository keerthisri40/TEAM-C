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

def send_gmail(to_email, subject, body):
    try:
        service = get_gmail_service()
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['From'] = 'me'
        message['Subject'] = subject 
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        service.users().messages().send(userId="me", body=create_message).execute()
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def get_latest_emails(count=10, label_id='INBOX'):
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me', 
            maxResults=count, 
            labelIds=[label_id]
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            return []

        mail_list = []
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            date = next((h['value'] for h in headers if h['name'] == 'Date'), "")
            
            # IMPROVED BODY EXTRACTION
            # We try to get the snippet first as a reliable backup
            body_content = msg.get('snippet', '')
            
            # If there's parts, we try to find the actual plain text for better summarization
            parts = payload.get('parts', [])
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body_content = base64.urlsafe_b64decode(data).decode()
                        break

            mail_list.append({
                "id": m['id'],
                "sender": sender,
                "subject": subject,
                "date": date,
                "body": body_content # This is what the AI uses
            })
            
        return mail_list

    except Exception as e:
        print(f"❌ Error fetching {label_id}: {e}")
        return []