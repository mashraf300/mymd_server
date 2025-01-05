from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sql7755566:2DrRzlViLm@sql7.freemysqlhosting.net:3306/sql7755566'
CORS(app, resources={r"/api/*": {"origins": "*"}})

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 

    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username 
    

class Doctors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class DoctorSchedules(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    doctors = db.relationship('Doctors', backref='schedules')

class Appointments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum('pending', 'confirmed', 'cancelled'), default='pending')

    patient = db.relationship('User', backref='appointments') 
    doctor = db.relationship('Doctors', backref='appointments')

class MedicalRecords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    patient = db.relationship('User', backref='medical_records')

class MedicalRecordAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    record = db.relationship('MedicalRecords', backref='access_list')
    doctor = db.relationship('Doctors', backref='accessible_records')
    
class Pharmacy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    
class MentalHealthArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255))
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
class Diagnoses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    record = db.relationship('MedicalRecords', backref='diagnoses')
    doctor = db.relationship('Doctors', backref='diagnoses_given')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400


    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400

    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit() 


    return jsonify({'message': 'User created successfully', 'id': new_user.id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return jsonify({'message': 'Login successful', 'user_id': user.id, 'role': 'user'}), 200

    doctor = Doctors.query.filter_by(email=username).first() 
    if doctor and doctor.password == password:
        return jsonify({'message': 'Login successful', 'user_id': doctor.id, 'role': 'doctor'}), 200
    
    admin = Admin.query.filter_by(username=username).first()
    if admin and admin.password == password:
        return jsonify({'message': 'Login successful', 'user_id': admin.id, 'role': 'admin'}), 200

    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    search_query = request.args.get('search', '')
    specialty = request.args.get('specialty', '')

    query = Doctors.query
    if search_query:
        query = query.filter(
            Doctors.name.ilike(f'%{search_query}%') | 
            Doctors.specialty.ilike(f'%{search_query}%')
        )
    if specialty:
        query = query.filter_by(specialty=specialty)

    doctors = query.all()
    doctor_list = []
    for doctor in doctors:
        doctor_list.append({
            'id': doctor.id,
            'name': doctor.name,
            'specialty': doctor.specialty,
            'location': doctor.location,
            'phone': doctor.phone,
            'email': doctor.email,
            'bio': doctor.bio,
            'image_url': doctor.image_url,
        })

    return jsonify(doctor_list)

@app.route('/api/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    print("Doctor ID: ", doctor_id)

    doctor = Doctors.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    timeslots = get_available_timeslots(doctor_id)

    doctor_data = {
        'id': doctor.id,
        'name': doctor.name,
        'specialty': doctor.specialty,
        'location': doctor.location,
        'phone': doctor.phone,
        'email': doctor.email,
        'bio': doctor.bio,
        'image_url': doctor.image_url,
        'timeslots': timeslots
    }
    return jsonify(doctor_data)

def get_available_timeslots(doctor_id):
    schedules = DoctorSchedules.query.filter_by(doctor_id=doctor_id).all()
    timeslots = []
    for schedule in schedules:
        print("Got schedult")
        start_hour = schedule.start_time.hour
        end_hour = schedule.end_time.hour
        for hour in range(start_hour, end_hour):
            timeslots.append({
                'day': schedule.day_of_week, 
                'time': f'{hour:02d}:00',    
                'available': True
            })
    return timeslots

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.get_json()
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    date_str = data.get('date')
    time_str = data.get('time')

    if not all([patient_id, doctor_id, date_str, time_str]):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'message': 'Invalid date or time format'}), 400

    if not is_timeslot_available(doctor_id, date, time):
        return jsonify({'message': 'Timeslot not available'}), 400

    appointment = Appointments(
        patient_id=patient_id, 
        doctor_id=doctor_id, 
        date=date, 
        time=time
    )
    db.session.add(appointment)
    db.session.commit()

    return jsonify({'message': 'Appointment created successfully', 'appointment_id': appointment.id}), 201

def is_timeslot_available(doctor_id, date, time):
    return True


@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    appointments = Appointments.query.filter_by(patient_id=user_id).all()

    appointment_list = []
    for appointment in appointments:
        appointment_list.append({
            'id': appointment.id,
            'doctor': {
                'name': appointment.doctor.name,
                'specialty': appointment.doctor.specialty
            },
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M'),
            'status': appointment.status
        })

    return jsonify(appointment_list)

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    appointment = Appointments.query.get(appointment_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    db.session.delete(appointment)
    db.session.commit()

    return jsonify({'message': 'Appointment cancelled successfully'}), 200


@app.route('/api/medical_records', methods=['POST'])
def add_medical_record():
    data = request.get_json()
    patient_id = data.get('patient_id')
    image_url = data.get('image_url')
    description = data.get('description')
    doctor_ids = data.get('doctor_ids', [])

    if not patient_id or not image_url:
        return jsonify({'message': 'Missing required fields'}), 400

    record = MedicalRecords(
        patient_id=patient_id,
        image_url=image_url,
        description=description
    )
    db.session.add(record)
    db.session.flush()

    for doctor_id in doctor_ids:
        access = MedicalRecordAccess(record_id=record.id, doctor_id=doctor_id)
        db.session.add(access)

    db.session.commit()

    return jsonify({'message': 'Medical record added successfully', 'record_id': record.id}), 201


@app.route('/api/medical_records', methods=['GET'])
def get_medical_records():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    records = (
        MedicalRecords.query
        .filter_by(patient_id=user_id)
        .outerjoin(MedicalRecordAccess)
        .outerjoin(Doctors)
        .all()
    )

    record_list = []
    for record in records:
        diagnoses_list = []
        doctor_list = []
        
        for diagnosis in record.diagnoses:
            diagnoses_list.append({
                'id': diagnosis.id,
                'diagnosis': diagnosis.diagnosis,
                'doctor': {
                    'id': diagnosis.doctor.id,
                    'name': diagnosis.doctor.name
                },
                'created_at': diagnosis.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        for access in record.access_list:
            doctor_list.append({
                'id': access.doctor.id,
                'name': access.doctor.name
            })

        record_list.append({
            'id': record.id,
            'image_url': record.image_url,
            'description': record.description,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'doctors': doctor_list,
            'diagnoses': diagnoses_list
        })

    return jsonify(record_list)

@app.route('/api/doctor_appointments', methods=['GET'])
def get_doctor_appointments():
    doctor_id = request.args.get('doctor_id')

    if not doctor_id:
        return jsonify({'message': 'Doctor ID is required'}), 400

    appointments = Appointments.query.filter_by(doctor_id=doctor_id).all()

    appointment_list = []
    for appointment in appointments:
        appointment_list.append({
            'id': appointment.id,
            'patient': {
                'id': appointment.patient.id,
                'name': appointment.patient.username
            },
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M'),
            'status': appointment.status
        })

    return jsonify(appointment_list)

@app.route('/api/doctor_schedule', methods=['GET'])
def get_doctor_schedule():
    doctor_id = request.args.get('doctor_id')

    if not doctor_id:
        return jsonify({'message': 'Doctor ID is required'}), 400

    schedules = DoctorSchedules.query.filter_by(doctor_id=doctor_id).all()

    schedule_list = []
    for schedule in schedules:
        schedule_list.append({
            'day': schedule.day_of_week,
            'start_time': schedule.start_time.strftime('%H:%M'), 
            'end_time': schedule.end_time.strftime('%H:%M')
        })

    return jsonify(schedule_list)


@app.route('/api/doctor_schedule', methods=['PUT'])
def update_doctor_schedule():
    doctor_id = request.args.get('doctor_id')
    data = request.get_json()

    if not doctor_id:
        return jsonify({'message': 'Doctor ID is required'}), 400

    if not data or not isinstance(data, dict): 
        return jsonify({'message': 'Invalid schedule data'}), 400

    DoctorSchedules.query.filter_by(doctor_id=doctor_id).delete()

    for day_of_week, time_data in data.items():
        start_time = time_data.get('startTime')
        end_time = time_data.get('endTime')

        if not start_time or not end_time:
            return jsonify({'message': 'Invalid schedule item'}), 400

        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            return jsonify({'message': 'Invalid time format'}), 400

        schedule = DoctorSchedules(
            doctor_id=doctor_id,
            day_of_week=int(day_of_week),
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(schedule)

    db.session.commit()

    return jsonify({'message': 'Schedule updated successfully'}), 200

@app.route('/api/pharmacies', methods=['POST'])
def add_pharmacy():
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    phone_number = data.get('phone_number')

    if not name or not address or not phone_number:
        return jsonify({'message': 'Missing required fields'}), 400

    pharmacy = Pharmacy(name=name, address=address, phone_number=phone_number)
    db.session.add(pharmacy)
    db.session.commit()

    return jsonify({'message': 'Pharmacy added successfully', 'pharmacy_id': pharmacy.id}), 201

@app.route('/api/pharmacies', methods=['GET'])
def get_pharmacies():
    pharmacies = Pharmacy.query.all()

    pharmacy_list = []
    for pharmacy in pharmacies:
        pharmacy_list.append({
            'id': pharmacy.id,
            'name': pharmacy.name,
            'address': pharmacy.address,
            'phone_number': pharmacy.phone_number
        })

    return jsonify(pharmacy_list)

@app.route('/api/pharmacies/<int:pharmacy_id>', methods=['PUT'])
def edit_pharmacy(pharmacy_id):
    pharmacy = Pharmacy.query.get(pharmacy_id)
    if not pharmacy:
        return jsonify({'message': 'Pharmacy not found'}), 404

    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    phone_number = data.get('phone_number')

    if name:
        pharmacy.name = name
    if address:
        pharmacy.address = address
    if phone_number:
        pharmacy.phone_number = phone_number

    db.session.commit()

    return jsonify({'message': 'Pharmacy updated successfully'}), 200

@app.route('/api/pharmacies/<int:pharmacy_id>', methods=['GET'])
def get_pharmacy(pharmacy_id):
    pharmacy = Pharmacy.query.get(pharmacy_id)
    if not pharmacy:
        return jsonify({'message': 'Pharmacy not found'}), 404

    pharmacy_data = {
        'id': pharmacy.id,
        'name': pharmacy.name,
        'address': pharmacy.address,
        'phone_number': pharmacy.phone_number
    }
    return jsonify(pharmacy_data)


@app.route('/api/mental_health_articles', methods=['POST'])
def add_mental_health_article():
    data = request.get_json()
    image_url = data.get('image_url')
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'message': 'Missing required fields'}), 400

    article = MentalHealthArticle(image_url=image_url, title=title, content=content)
    db.session.add(article)
    db.session.commit()

    return jsonify({'message': 'Mental health article added successfully', 'article_id': article.id}), 201

@app.route('/api/mental_health_articles', methods=['GET'])
def get_mental_health_articles():
    articles = MentalHealthArticle.query.all()

    article_list = []
    for article in articles:
        article_list.append({
            'id': article.id,
            'image_url': article.image_url,
            'title': article.title,
            'content': article.content
        })

    return jsonify(article_list)

@app.route('/api/mental_health_articles/<int:article_id>', methods=['GET'])
def get_mental_health_article(article_id):
    article = MentalHealthArticle.query.get(article_id)
    if not article:
        return jsonify({'message': 'Article not found'}), 404

    article_data = {
        'id': article.id,
        'image_url': article.image_url,
        'title': article.title,
        'content': article.content
    }
    return jsonify(article_data)

@app.route('/api/mental_health_articles/<int:article_id>', methods=['PUT'])
def edit_mental_health_article(article_id):
    article = MentalHealthArticle.query.get(article_id)
    if not article:
        return jsonify({'message': 'Article not found'}), 404

    data = request.get_json()
    image_url = data.get('image_url')
    title = data.get('title')
    content = data.get('content')

    if image_url:
        article.image_url = image_url
    if title:
        article.title = title
    if content:
        article.content = content

    db.session.commit()

    return jsonify({'message': 'Mental health article updated successfully'}), 200

@app.route('/api/diagnoses', methods=['POST'])
def add_diagnosis():
    data = request.get_json()
    record_id = data.get('record_id')
    doctor_id = data.get('doctor_id')
    diagnosis_text = data.get('diagnosis')

    if not record_id or not doctor_id or not diagnosis_text:
        return jsonify({'message': 'Missing required fields'}), 400

    diagnosis = Diagnoses(record_id=record_id, doctor_id=doctor_id, diagnosis=diagnosis_text)
    db.session.add(diagnosis)
    db.session.commit()

    return jsonify({'message': 'Diagnosis added successfully', 'diagnosis_id': diagnosis.id}), 201


if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)