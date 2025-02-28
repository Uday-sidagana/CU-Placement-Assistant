from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import re
import os
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
    x = db.Column(db.String(10))
    xii = db.Column(db.String(10))
    university = db.Column(db.String(100))
    zone = db.Column(db.String(50))
    file_data = db.Column(db.LargeBinary)  # Store uploaded file path

    user = db.relationship('User', backref=db.backref('details', lazy=True))  # Relationship with `User`

    def __init__(self, uid, name, email, umail, x, xii, university, zone, file_data):
        self.uid = uid
        self.name = name
        self.email = email
        self.umail = umail
        self.x = x
        self.xii = xii
        self.university = university
        self.zone = zone
        self.file_data = file_data

    
with app.app_context():
    db.create_all()





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
        x = request.form.get('x')
        xii = request.form.get('xii')
        university = request.form.get('university')
        zone = request.form.get('zone')
        file = request.files.get('file')

        #UID duplication error resolve
        existing_user = UserDetails.query.filter_by(uid=uid).first()
        if existing_user:
            return "UID already registered", 400

        if file:
            filename = f"{uid}.pdf"  # Rename file with UID
            file_data = file.read()  # Read file data BEFORE saving
            file_path = os.path.join('/Users/macbookair/Desktop/python/CU PLACEMENT ASSISTANT/Auth/uploads', filename)
          

        user_details = UserDetails(
            uid=uid,
            name=name,
            email=email,
            umail=umail,
            x=x,
            xii=xii,
            university=university,
            zone=zone,
            file_data=file_data
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
    if session['name']:
        user = User.query.filter_by(email=session['email']).first()

        return render_template('homepage.html', user= user)
    

    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)