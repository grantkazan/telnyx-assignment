import os

# Database configuration - use Postgres in production, SQLite locally
from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = 'appointments.db'

DATABASE_URL = os.getenv('DATABASE_URL')

# Helper function to get database connection
def get_db():
    if DATABASE_URL:
        # Production - use PostgreSQL
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return conn
    else:
        # Local development - use SQLite
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

# Initialize database with tables
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                specialty TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                datetime TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')
        
        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM doctors")
        count = cursor.fetchone()['count'] if DATABASE_URL else cursor.fetchone()[0]
    else:
        # SQLite syntax (your existing code)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialty TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                datetime TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM doctors")
        count = cursor.fetchone()[0]
    
    # Seed data only if empty
    if count == 0:
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES ('Dr. Smith', 'General Practice')")
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES ('Dr. Jones', 'Cardiology')")
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES ('Dr. Williams', 'Pediatrics')")
        
        cursor.execute("INSERT INTO patients (name, phone) VALUES ('Alice', '1-555-0101')")
        cursor.execute("INSERT INTO patients (name, phone) VALUES ('Bobby', '1-555-0102')")
        cursor.execute("INSERT INTO patients (name, phone) VALUES ('Charlie', '1-555-0103')")
        
        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, datetime, status) VALUES (1, 1, '2025-12-08 13:00:00', 'scheduled')")
        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, datetime, status) VALUES (1, 2, '2025-12-08 14:00:00', 'scheduled')")
        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, datetime, status) VALUES (3, 3, '2025-12-08 15:00:00', 'scheduled')")
    
    conn.commit()
    conn.close()
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            datetime TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')
    
    # Seed data
    
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES ('Dr. Smith', 'General Practice')")
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES ('Dr. Jones', 'Cardiology')")
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES ('Dr. Williams', 'Pediatrics')")
        # the plus sign in phone numbers caused a formatting issue
        cursor.execute("INSERT INTO patients (name, phone) VALUES ('Alice', '+1-555-0101')")
        cursor.execute("INSERT INTO patients (name, phone) VALUES ('Bobby', '+1-555-0102')")
        cursor.execute("INSERT INTO patients (name, phone) VALUES ('Charlie', '+1-555-0103')")
        
        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, datetime, status) VALUES (1, 1, '2025-12-08 13:00:00', 'scheduled')")
        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, datetime, status) VALUES (1, 2, '2025-12-08 14:00:00', 'scheduled')")
        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, datetime, status) VALUES (3, 3, '2025-12-08 15:00:00', 'scheduled')")
    
    conn.commit()
    conn.close()

# API Routes

@app.route('/doctors', methods=['GET'])
def get_doctors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(doctors)

@app.route('/patients', methods=['GET'])
def get_patients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
    patients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(patients)

@app.route('/sanity', methods=['GET'])
def get_sanity():
    return jsonify({'sanity check': True})

@app.route('/appointments', methods=['GET'])
def get_appointments():
    patient_phone = request.args.get('patient_phone')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # If patient_phone is provided, filter by patient
    if patient_phone:
        # print(f"Looking for patient with phone: '{patient_phone}'")
        
        # First, check if patient exists
        cursor.execute("SELECT * FROM patients WHERE phone = ?", (patient_phone,))
        patient = cursor.fetchone()
        # print(f"Found patient: {dict(patient) if patient else None}")
        

        cursor.execute("""
            SELECT a.id, d.name as doctor_name, a.datetime, a.status
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN patients p ON a.patient_id = p.id
            WHERE p.phone = ? AND a.status = 'scheduled'
            ORDER BY a.datetime
        """, (patient_phone,))
    else:
        # Return all appointments
        # print("no phone provided")
        cursor.execute("SELECT * FROM appointments")
    
    appointments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(appointments)

@app.route('/appointments/available', methods=['GET'])
def get_available_appointments():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')  # Format: YYYY-MM-DD
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all appointments for this doctor on this date
    cursor.execute("""
        SELECT datetime FROM appointments 
        WHERE doctor_id = ? AND date(datetime) = ? AND status = 'scheduled'
    """, (doctor_id, date))
    
    booked_times = [row['datetime'] for row in cursor.fetchall()]
    conn.close()
    
    # Generate available time slots (9 AM to 5 PM, hourly)
    available_slots = []
    for hour in range(9, 17):
        time_slot = f"{date} {hour:02d}:00:00"
        if time_slot not in booked_times:
            available_slots.append(time_slot)
    
    return jsonify({'available_slots': available_slots})

@app.route('/appointments', methods=['POST'])
def book_appointment():
    data = request.json
    doctor_id = data.get('doctor_id')
    patient_phone = data.get('patient_phone')
    patient_name = data.get('patient_name')
    datetime_str = data.get('datetime')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get or create patient
    cursor.execute("SELECT id FROM patients WHERE phone = ?", (patient_phone,))
    patient = cursor.fetchone()
    
    if patient:
        patient_id = patient['id']
    else:
        cursor.execute("INSERT INTO patients (name, phone) VALUES (?, ?)", (patient_name, patient_phone))
        patient_id = cursor.lastrowid
    
    # Book appointment
    #DOESN'T CHECK IF DOCTOR IS AVAILABLE YET!!
    # CAN SCHEDULE DUP APPTS
    cursor.execute("""
        INSERT INTO appointments (doctor_id, patient_id, datetime, status)
        VALUES (?, ?, ?, 'scheduled')
    """, (doctor_id, patient_id, datetime_str))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'appointment_id': appointment_id, 'status': 'scheduled'}), 201

@app.route('/appointments/<int:appointment_id>', methods=['PUT']) # modify existing appointment to a different time
def update_appointment(appointment_id):
    data = request.json
    new_datetime = data.get('datetime')
    new_status = data.get('status')  # 'cancelled', 'rescheduled', etc.
    
    conn = get_db()
    cursor = conn.cursor()
    
    if new_datetime:
        cursor.execute("UPDATE appointments SET datetime = ? WHERE id = ?", (new_datetime, appointment_id))
    if new_status:
        cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, appointment_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'appointment_id': appointment_id, 'updated': True})

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)