from __future__ import print_function

from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import re
import os
from io import BytesIO
from PyPDF2 import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
import requests

#Events Libraries
# from __future__ import print_function
import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import socket



load_dotenv()
credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
GEMINI_API = os.getenv('GEMINI_API')


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./testdb.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    __tablename__='users'

    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, email,password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def checkPassword(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
class UserDetails(db.Model):
    __tablename__ = 'user_details'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)  # Link to `users` table
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    umail = db.Column(db.String(100), unique=True)
    phNo = db.Column(db.String(10))
    altphNo = db.Column(db.String(10))
    backlogs = db.Column(db.String(100))
    currentState = db.Column(db.String(100))
    x = db.Column(db.String(10))
    xii = db.Column(db.String(10))
    university = db.Column(db.String(100))
    zone = db.Column(db.String(50))
    file_data = db.Column(db.LargeBinary)  # Store uploaded file path
    student_description = db.Column(db.Text)

    user = db.relationship('User', backref=db.backref('details', lazy=True))  # Relationship with `User`

    def __init__(self, uid, name, email, umail, x, xii, university, zone, file_data, phNo, altphNo, currentState, backlogs, student_description):
        self.uid = uid
        self.name = name
        self.email = email
        self.umail = umail
        self.phNo = phNo
        self.altphNo = altphNo
        self.currentState = currentState
        self.backlogs = backlogs
        self.x = x
        self.xii = xii
        self.university = university
        self.zone = zone
        self.file_data = file_data
        self.student_description = student_description


# class EventDetails(db.Model):
#     __tablename__='event_details'

#     id = db.Column(db.Integer, primary_key=True)
#     start = db.Column(db.String(50), nullable=False)   # better as string/datetime
#     title = db.Column(db.String(100), nullable=False)
    

#     def __init__(self, start, title):
#         self.start = start
#         self.title = title
        

    
with app.app_context():
    db.create_all()



def aiParser(pdf_binary_data):

    pdf_stream = BytesIO(pdf_binary_data)
    pdf_reader= PdfReader(pdf_stream)

    pdf_text=""
    for page in pdf_reader.pages:
        text = page.extract_text()

        if text:
            pdf_text += text+"\n"
   # Prepare and send request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Analyze the following text and create a structured description:\n\n{pdf_text}"}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)
    response_data = response.json()

    return response_data["candidates"][0]["content"]["parts"][0]["text"]

    

    


@app.route('/')
def index():
    return 'hi'

# Password validation function
def is_valid_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'
    return re.match(pattern, password)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method =="POST":
        #handle resistration
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if name and email and password:

            if is_valid_password(password):

                new_user= User(email=email, name=name,  password=password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('registerDetails')) 
            else:
                return render_template('register.html', errorReg=
                                    "Password must be at least 6 characters long and include at least one uppercase letter, one lowercase letter, one number, and one special character (@, $, !, %, *, ?, &).")
            
        else:
            return render_template('register.html', errorMissingValuesReg="Fields cannot be empty")

    return render_template('register.html')



@app.route('/registerDetails', methods=['GET', 'POST'])
def registerDetails():
    if request.method == 'GET':
        return render_template('registerDetails.html')
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        uid = request.form.get('uid').strip()
        umail = request.form.get('umail')
        phNo = request.form.get('phNo')
        altphNo = request.form.get('altphNo')
        currentState = request.form.get('currentState')
        backlogs = request.form.get('backlogs')
        x = request.form.get('x')
        xii = request.form.get('xii')
        university = request.form.get('university')
        zone = request.form.get('zone')
        file = request.files.get('file')
        

        #UID duplication error resolve
        existing_user = UserDetails.query.filter_by(uid=uid).first()
        if existing_user:
            return "UID already registered", 400
        
        if backlogs == "other":
            backlogs = request.form.get("otherbacklogs")

        if file:
            filename = f"{uid}.pdf"  # Rename file with UID
            file_data = file.read()  # Read file data BEFORE saving
            file_path = os.path.join('/Users/macbookair/Desktop/python/CU PLACEMENT ASSISTANT/Auth/uploads', filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_data)

            #AI ka time ho gya student information lene ka 
            
            pdf_binary_data = file_data 

            student_description = aiParser(pdf_binary_data)


        user_details = UserDetails(
            uid=uid,
            name=name,
            email=email,
            umail=umail,
            phNo= phNo,
            altphNo= altphNo,
            currentState= currentState,
            backlogs=backlogs,
            x=x,
            xii=xii,
            university=university,
            zone=zone,
            file_data=file_data,
            student_description=student_description
            
        )
        db.session.add(user_details)
        db.session.commit()



        return redirect(url_for('login'))


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method== "POST":
        email= request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.checkPassword(password):
            session['name'] = user.name
            session['email'] = user.email

            return redirect(url_for('homepage'))
        else:
            return render_template('login.html', error= 'invalid user')


    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/homepage')
def homepage():
    print("Homepage route accessed") 
    if session['name']:
        user = User.query.filter_by(email=session['email']).first()

        placements_events = session.get('placements_events', [])
        print("Retrieved placements events from session:", placements_events)  

        return render_template('homepage.html', user= user, events=placements_events)
    
    




@app.route('/studentDetails', methods=['GET','POST'])
def studentDetails():
    
    
    if 'email' not in session:
        return redirect(url_for('login'))  

    userDetails = UserDetails.query.filter_by(email=session['email']).first()

    if not userDetails:
        return "User details not found", 404

    if request.method == 'POST':
        if 'name' in request.form and request.form['name'].strip():
            userDetails.name = request.form['name'].strip()

        if 'umail' in request.form and request.form['umail'].strip():
            userDetails.umail = request.form['umail'].strip()

        if 'phNo' in request.form and request.form['phNo'].strip():
            userDetails.phNo = request.form['phNo'].strip()

        if 'altphNo' in request.form and request.form['altphNo'].strip():
            userDetails.altphNo = request.form['altphNo'].strip()

        if 'backlogs' in request.form and request.form['backlogs'].strip():
            userDetails.backlogs = request.form['backlogs'].strip()

        db.session.commit()  
        return redirect(url_for('studentDetails'))  

    return render_template('studentDetails.html', userDetails=userDetails)


@app.route('/calendar', methods=['GET','POSt'])
def event_schedule():

    if request.method== 'POST':
        SCOPES = ['https://www.googleapis.com/auth/calendar']


        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('127.0.0.1', port)) == 0

        def authenticate_google_api():
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:

                    if is_port_in_use(8080):
                        print("Port 8080 is in use, attempting cleanup...")
                        os.system("lsof -t -i:8080 | xargs kill -9")

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

        
        service = authenticate_google_api()

        title = f"Placement:{request.form.get('title')}"
        description = request.form.get('description')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        schedule_event(service, title, description, date, start_time, end_time)

        

        if os.path.exists('token.json'):
            os.remove('token.json')
            print("token.json has been deleted.")

        return redirect(url_for('homepage'))
    
   




@app.route('/get_events')
def get_events():
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def cleanup_port(port):
        while is_port_in_use(port):
            print(f"Port {port} is in use. Attempting cleanup...")
            result = os.popen(f"lsof -t -i:{port}").read()
            if result:
                pids = result.strip().split('\n')
                print(f"Found PIDs: {pids}")
                for pid in pids:
                    os.system(f"kill -9 {pid}")
                print("Processes killed. Waiting for port release...")
                time.sleep(1)
            else:
                break
        print(f"Port {port} is now free.")

    def authenticate_google_api():
        creds = None
        if os.path.exists('eventcred.json'):
            creds = Credentials.from_authorized_user_file('eventcred.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                cleanup_port(8081)
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=8081)
            with open('eventcred.json', 'w') as token:
                token.write(creds.to_json())
        return build('calendar', 'v3', credentials=creds)

# Function to get all events from today up to 3 months later, filtering by title containing "Placements:"
    def get_upcoming_placements_events():
        service = authenticate_google_api()

        # Get the current date and the date 3 months later
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        three_months_later = (datetime.datetime.utcnow() + datetime.timedelta(days=90)).replace(microsecond=0).isoformat() + 'Z'


        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now, 
            timeMax=three_months_later, 
            maxResults=2500,  # Adjust as necessary
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # List to store events with 'Placements:' in the title
        placements_events = []

        if not events:
            print('No upcoming events found.')
        else:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start.rstrip('Z'))  # Remove 'Z' before parsing
                summary = event['summary']
                
                # Check if the event title contains "Placements:"
                if "placement:" in summary.lower():
                    placements_events.append({
                        'start': start.strftime('%Y-%m-%d %H:%M:%S UTC'),  # Display time in UTC format
                        'title': summary
                    })

        return placements_events

    
    placements_events = get_upcoming_placements_events()
    print(placements_events)

    # for i in placements_events:
    #     start = i['start']
    #     title = i['title']


    #     event_details = EventDetails(
    #             start=start,
    #             title=title,
    
    #         )
    #     db.session.add(event_details)
    #     db.session.commit()




    if session['name']:
        user = User.query.filter_by(email=session['email']).first()

    session['placements_events'] = placements_events

    if os.path.exists('eventcred.json'):
        os.remove('eventcred.json')
        print("Deleted eventcred.json")

    # events = EventDetails.query.all()


    return render_template('homepage.html', events=placements_events, user=user)




    

    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)