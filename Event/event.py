from __future__ import print_function
import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from google.auth.transport.requests import Request

# Scopes for accessing calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_api():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def schedule_event(service, title, description, date, start_time, end_time):
    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': f'{date}T{start_time}:00',
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': f'{date}T{end_time}:00',
            'timeZone': 'UTC',
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")

def main():
    service = authenticate_google_api()

    title = input("Enter Event Title: ")
    description = input("Enter Event Description: ")
    date = input("Enter Event Date (YYYY-MM-DD): ")
    start_time = input("Enter Start Time (HH:MM in 24hr): ")
    end_time = input("Enter End Time (HH:MM in 24hr): ")

    schedule_event(service, title, description, date, start_time, end_time)

if __name__ == '__main__':
    main()
