from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import joblib
import pandas as pd
import numpy as np
import mysql.connector
import smtplib
import random
from datetime import timedelta, date, datetime, time as dt_time
import os
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import render_template, send_file, make_response
from xhtml2pdf import pisa
import io


app = Flask(__name__)
app.secret_key = 'your_key'
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['UPLOAD_FOLDER'] = 'static/uploads'



model = joblib.load("disease_model.pkl")
encoder = joblib.load("symptom_encoder.pkl")
all_symptoms = list(encoder.classes_)

description_df = pd.read_csv('symptom_description.csv')
description_df.columns = description_df.columns.str.strip().str.lower()
description_df['disease'] = description_df['disease'].str.strip().str.lower()

precaution_df = pd.read_csv('symptom_precaution.csv')
precaution_df.columns = precaution_df.columns.str.strip().str.lower()
precaution_df['disease'] = precaution_df['disease'].str.strip().str.lower()

severity_df = pd.read_csv('Symptom-severity.csv')
severity_df.columns = severity_df.columns.str.strip().str.lower()
severity_df['symptom'] = severity_df['symptom'].str.strip().str.lower()

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root123',
        database='healthmate'
    )



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s AND is_verified = TRUE", (email, password))
        user = cur.fetchone()
        con.close()

        if user:
            session.permanent = True
            session['user_id'] = user['id']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        caretaker_email = request.form.get('caretaker_email')  # NEW

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            flash("Invalid date format.")
            return render_template('register.html')

        otp = str(random.randint(100000, 999999))  # Generate OTP

        con = get_db()
        cur = con.cursor()
        try:
            cur.execute("""INSERT INTO users (name, email, password, gender, dob, age, is_verified, caretaker_email) VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s)""", (name, email, password, gender, dob, age, caretaker_email))
            con.commit()
            flash("Registration successful! You can now log in.")
            return redirect(url_for('login'))

        except mysql.connector.Error as e:
            flash('Email already exists or error occurred.')
        finally:
            con.close()

    return render_template('register.html')


@app.route('/medicine_expiry', methods=['GET', 'POST'])
def medicine_expiry():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        med_name = request.form['medicine_name']
        expiry_date = request.form['expiry_date']

        cursor.execute("""
            INSERT INTO medicine_expiry (user_id, medicine_name, expiry_date)
            VALUES (%s, %s, %s)
        """, (session['user_id'], med_name, expiry_date))
        db.commit()

    # Fetch medicines sorted by expiry
    cursor.execute("SELECT * FROM medicine_expiry WHERE user_id = %s ORDER BY expiry_date ASC", (session['user_id'],))
    medicines = cursor.fetchall()
    db.close()

    today = datetime.today().date()
    for med in medicines:
        expiry = med['expiry_date']
        med['days_left'] = (expiry - today).days
        med['is_urgent'] = med['days_left'] <= 5

    return render_template("medicine_expiry.html", medicines=medicines)


@app.route('/delete_medicine/<int:med_id>')
def delete_medicine(med_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM medicine_expiry WHERE id = %s AND user_id = %s", (med_id, session['user_id']))
    db.commit()
    db.close()
    return redirect(url_for('medicine_expiry'))



@app.route('/bmi', methods=['GET', 'POST'])
def bmi():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    result = None

    if request.method == 'POST':
        try:
            height = float(request.form['height'])
            weight = float(request.form['weight'])
            unit = request.form['unit']  # 'cm' or 'm'

            # Convert to meters if input is in cm
            height_m = height / 100 if unit == 'cm' else height

            bmi = round(weight / (height_m ** 2), 2)

            if bmi < 18.5:
                category = "Underweight"
                suggestion = "Try gaining weight through a healthy diet and exercise."
            elif 18.5 <= bmi < 25:
                category = "Normal"
                suggestion = "Maintain your current lifestyle!"
            elif 25 <= bmi < 30:
                category = "Overweight"
                suggestion = "Consider adopting healthier eating habits and more exercise."
            else:
                category = "Obese"
                suggestion = "You may need to consult a healthcare provider."

            result = {
                "bmi": bmi,
                "category": category,
                "suggestion": suggestion
            }

        except Exception as e:
            flash("Invalid input. Please enter numbers only.")

    return render_template('bmi.html', result=result)



@app.route('/health_stats')
def health_stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT date, blood_pressure, glucose_level, sleep_hours, water_intake
        FROM health_logs
        WHERE user_id = %s
        ORDER BY date
    """, (user_id,))
    logs = cursor.fetchall()

    labels = [log['date'].strftime('%Y-%m-%d') for log in logs]
    glucose = [
        float(log['glucose_level']) if log['glucose_level'] and log['glucose_level'].replace('.', '', 1).isdigit() else None
        for log in logs
    ]
    sleep = [log['sleep_hours'] for log in logs]
    water = [log['water_intake'] for log in logs]
    blood_pressure = [log['blood_pressure'] if log['blood_pressure'] else None for log in logs]

    db.close()

    return render_template(
        "health_graph.html",
        labels=labels,
        glucose=glucose,
        sleep=sleep,
        water=water,
        blood_pressure=[log['blood_pressure'] for log in logs],
    hide_navbar=True  
    )


from flask import send_file
import io
from xhtml2pdf import pisa

@app.route('/download_report')
def download_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM health_logs WHERE user_id = %s ORDER BY date DESC", (user_id,))
    logs = cursor.fetchall()
    db.close()

    # Render HTML template
    rendered = render_template('health_report.html', logs=logs)

    # Convert HTML to PDF
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(rendered, dest=result)

    if pisa_status.err:
        return "Error generating PDF"
    
    result.seek(0)
    return send_file(result, download_name="health_report.pdf", as_attachment=True)

        

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get user
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # Latest log
    cursor.execute("SELECT * FROM health_logs WHERE user_id = %s ORDER BY log_date DESC LIMIT 1", (user_id,))
    health_log = cursor.fetchone()

    # ✅ All logs for the chart
    cursor.execute("SELECT * FROM health_logs WHERE user_id = %s ORDER BY log_date ASC", (user_id,))
    health_logs = cursor.fetchall()

    profile_pic_path = os.path.join("static/profile_pics", f"{user_id}.jpg")
    profile_pic_url = f"/static/profile_pics/{user_id}.jpg" if os.path.exists(profile_pic_path) else None

    db.close()

    return render_template("dashboard.html",
                           user=user,
                           health_log=health_log,
                           health_logs=health_logs,
                           profile_pic_url=profile_pic_url)



@app.route('/about')
def about():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    con = get_db()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.execute("SELECT * FROM health_logs WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user_id,))
    health_log = cur.fetchone() or {}
    con.close()

    return render_template('about.html', user=user, health_log=health_log)





@app.route('/contact')
def contact():
    return render_template('contact.html')



from datetime import date, datetime
from werkzeug.utils import secure_filename

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    con = get_db()
    cur = con.cursor(dictionary=True)

    if request.method == 'POST':
        # Handle custom image upload
        file = request.files.get('profile_image')
        avatar_url = request.form.get('avatar_choice')
        gender = request.form.get('gender')

        # Case 1: User uploaded a file
        if file and file.filename != '':
            filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            cur.execute("UPDATE users SET profile_image = %s WHERE id = %s", (filename, session['user_id']))
            con.commit()
            flash('Profile image updated from upload.')

        # Case 2: User selected an avatar
        elif avatar_url:
            cur.execute("UPDATE users SET profile_image = %s WHERE id = %s", (avatar_url, session['user_id']))
            con.commit()
            flash('Profile image updated using default avatar.')

    # Get user info after update
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()

    # Calculate age from DOB if available
    def calculate_age(dob):
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    age = None
    if user.get('dob'):
        try:
            dob = user['dob']
            if isinstance(dob, str):
                dob = datetime.strptime(dob, "%Y-%m-%d").date()
            age = calculate_age(dob)
        except Exception as e:
            print("DOB parsing error:", e)

    # Get latest health log
    cur.execute("SELECT * FROM health_logs WHERE user_id = %s ORDER BY date DESC LIMIT 1", (session['user_id'],))
    health_log = cur.fetchone() or {}

    con.close()

    # Determine profile image (local file or avatar URL)
    if user['profile_image'] and (
        user['profile_image'].startswith('http://') or user['profile_image'].startswith('https://')
    ):
        profile_pic_url = user['profile_image']
    elif user['profile_image']:
        profile_pic_url = url_for('static', filename='uploads/' + user['profile_image'])
    else:
        profile_pic_url = url_for('static', filename='uploads/default_avatar.png')

    return render_template('profile.html', user=user, health_log=health_log, profile_pic_url=profile_pic_url, age=age)



@app.route('/add_health_log', methods=['GET', 'POST'])
def add_health_log():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        bp = request.form['blood_pressure']
        glucose = request.form['glucose_level']
        sleep = request.form['sleep_hours']
        water = request.form['water_intake']
        notes = request.form['exercise_notes']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO health_logs (user_id, date, blood_pressure, glucose_level, sleep_hours, water_intake, exercise_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], date.today(), bp, glucose, sleep, water, notes))
        conn.commit()
        conn.close()

        flash('Health log added successfully.')
        return redirect(url_for('dashboard'))

    return render_template('add_health_log.html')

@app.route('/view_health_log')
def view_health_log():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM health_logs WHERE user_id = %s ORDER BY date DESC", (session['user_id'],))
    logs = cursor.fetchall()
    conn.close()

    return render_template('view_health_log.html', logs=logs)

@app.route('/delete_health_log/<int:log_id>', methods=['POST'])
def delete_health_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM health_logs WHERE id = %s AND user_id = %s", (log_id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect(url_for('view_health_log'))


@app.route('/symptom-checker')
def symptom_checker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', symptoms=all_symptoms)

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    selected_symptoms = request.form.getlist('symptoms')
    input_vector = np.zeros(len(all_symptoms))
    for symptom in selected_symptoms:
        if symptom in all_symptoms:
            input_vector[all_symptoms.index(symptom)] = 1

    prediction = model.predict([input_vector])[0]
    prediction_lower = prediction.strip().lower()

    desc_row = description_df[description_df['disease'] == prediction_lower]
    description = desc_row['description'].values[0] if not desc_row.empty else "Description not available."

    prec_row = precaution_df[precaution_df['disease'] == prediction_lower]
    precautions = [p for p in prec_row.iloc[0, 1:].values if pd.notna(p)] if not prec_row.empty else ["No precautions available."]

    cleaned_symptoms = [s.strip().lower() for s in selected_symptoms]
    severity_values = severity_df[severity_df['symptom'].isin(cleaned_symptoms)]['weight']
    severity_score = round(severity_values.mean(), 2) if not severity_values.empty else "N/A"

    return render_template('result.html',
                           disease=prediction,
                           description=description,
                           precautions=precautions,
                           severity=severity_score)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')





if __name__ == '__main__':
    

    app.run(debug=True, port=5001)

