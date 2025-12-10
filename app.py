import os
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

# Get correct SQL placeholder for current database
def get_placeholder():
    return '%s' if DATABASE_URL else '?'

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
        cursor.execute("SELECT COUNT(*) as count FROM doctors")
        count = cursor.fetchone()['count']
    else:
        # SQLite syntax
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
        
        cursor.execute("SELECT COUNT(*) as count FROM doctors")
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

# Initialize database on app startup
with app.app_context():
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

# API Routes

@app.route('/sanity', methods=['GET'])
def get_sanity():
    return jsonify({'sanity_check': True})

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

@app.route('/appointments', methods=['GET'])
def get_appointments():
    patient_phone = request.args.get('patient_phone')
    placeholder = get_placeholder()
    
    conn = get_db()
    cursor = conn.cursor()
    
    if patient_phone:
        cursor.execute(f"""
            SELECT a.id, d.name as doctor_name, a.datetime, a.status
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN patients p ON a.patient_id = p.id
            WHERE p.phone = {placeholder} AND a.status = 'scheduled'
            ORDER BY a.datetime
        """, (patient_phone,))
    else:
        cursor.execute("SELECT * FROM appointments")
    
    appointments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(appointments)

@app.route('/appointments/available', methods=['GET'])
def get_available_appointments():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    placeholder = get_placeholder()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT datetime FROM appointments 
        WHERE doctor_id = {placeholder} AND date(datetime) = {placeholder} AND status = 'scheduled'
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
    placeholder = get_placeholder()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get or create patient
    cursor.execute(f"SELECT id FROM patients WHERE phone = {placeholder}", (patient_phone,))
    patient = cursor.fetchone()
    
    if patient:
        patient_id = patient['id']
    else:
        if DATABASE_URL:
            cursor.execute(f"INSERT INTO patients (name, phone) VALUES ({placeholder}, {placeholder}) RETURNING id", (patient_name, patient_phone))
            patient_id = cursor.fetchone()['id']
        else:
            cursor.execute(f"INSERT INTO patients (name, phone) VALUES ({placeholder}, {placeholder})", (patient_name, patient_phone))
            patient_id = cursor.lastrowid
    
    # Book appointment
    if DATABASE_URL:
        cursor.execute(f"""
            INSERT INTO appointments (doctor_id, patient_id, datetime, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, 'scheduled')
            RETURNING id
        """, (doctor_id, patient_id, datetime_str))
        appointment_id = cursor.fetchone()['id']
    else:
        cursor.execute(f"""
            INSERT INTO appointments (doctor_id, patient_id, datetime, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, 'scheduled')
        """, (doctor_id, patient_id, datetime_str))
        appointment_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return jsonify({'appointment_id': appointment_id, 'status': 'scheduled'}), 201

@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    data = request.json
    new_datetime = data.get('datetime')
    new_status = data.get('status')
    placeholder = get_placeholder()
    
    conn = get_db()
    cursor = conn.cursor()
    
    if new_datetime:
        cursor.execute(f"UPDATE appointments SET datetime = {placeholder} WHERE id = {placeholder}", (new_datetime, appointment_id))
    if new_status:
        cursor.execute(f"UPDATE appointments SET status = {placeholder} WHERE id = {placeholder}", (new_status, appointment_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'appointment_id': appointment_id, 'updated': True})

# webhook for caller context
@app.route('/webhook/caller-context', methods=['POST'])
def get_caller_context():
    """Webhook endpoint for Telnyx to get caller context via Dynamic Webhook Variables"""
    data = request.json
    
    # Telnyx sends caller phone number as 'from'
    caller_phone = data.get('from', '')
    
    # Clean phone number - remove all non-digits
    cleaned = ''.join(filter(str.isdigit, caller_phone))
    
    # Format to match database: 1-XXX-XXX-XXXX
    if len(cleaned) == 11 and cleaned.startswith('1'):
        formatted_phone = f"1-{cleaned[1:4]}-{cleaned[4:7]}-{cleaned[7:]}"
    elif len(cleaned) == 10:
        formatted_phone = f"1-{cleaned[0:3]}-{cleaned[3:6]}-{cleaned[6:]}"
    else:
        return jsonify({
            'is_existing_patient': False,
            'patient_name': 'caller',
            'debug_cleaned': cleaned,
            'debug_original': caller_phone
        })
    
    conn = get_db()
    cursor = conn.cursor()
    placeholder = get_placeholder()
    
    try:
        cursor.execute(f"SELECT * FROM patients WHERE phone = {placeholder}", (formatted_phone,))
        patient = cursor.fetchone()
        
        if patient:
            patient_dict = dict(patient)
            
            # Get their next upcoming appointment
            cursor.execute(f"""
                SELECT a.id, d.name as doctor_name, a.datetime, a.status
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.patient_id = {placeholder} 
                AND a.status = 'scheduled'
                ORDER BY a.datetime
                LIMIT 1
            """, (patient_dict['id'],))
            
            next_appt = cursor.fetchone()
            
            response_data = {
                'is_existing_patient': True,
                'patient_name': patient_dict['name'],
                'patient_phone': patient_dict['phone']
            }
            
            if next_appt:
                appt_dict = dict(next_appt)
                response_data['has_upcoming_appointment'] = True
                response_data['next_appointment_doctor'] = appt_dict['doctor_name']
                response_data['next_appointment_datetime'] = appt_dict['datetime']
            else:
                response_data['has_upcoming_appointment'] = False
            
            conn.close()
            return jsonify(response_data)
        else:
            conn.close()
            return jsonify({
                'is_existing_patient': False,
                'patient_name': 'caller',
                'debug_formatted': formatted_phone,
                'debug_cleaned': cleaned
            })
            
    except Exception as e:
        conn.close()
        return jsonify({
            'is_existing_patient': False,
            'patient_name': 'caller',
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)