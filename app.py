# app.py - Flask backend
import os
import sqlite3
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import joblib
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json

app = Flask(__name__)
app.secret_key = 'autism_detection_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create directories if not exist
os.makedirs('model', exist_ok=True)
os.makedirs('static/img', exist_ok=True)

# Create a mock ML model if not exists
if not os.path.exists('model/autism_model.pkl'):
    from sklearn.ensemble import RandomForestClassifier
    import joblib
    import numpy as np
    
    # Create a dummy model for demonstration
    model = RandomForestClassifier(n_estimators=100)
    X_dummy = np.random.rand(100, 17)  # 17 features
    y_dummy = np.random.randint(0, 2, 100)  # binary target
    model.fit(X_dummy, y_dummy)
    joblib.dump(model, 'model/autism_model.pkl')

# Load ML model
model = joblib.load('model/autism_model.pkl')

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            age INTEGER,
            gender TEXT,
            ethnicity TEXT,
            jaundice TEXT,
            autism_family TEXT,
            a1 INTEGER,
            a2 INTEGER,
            a3 INTEGER,
            a4 INTEGER,
            a5 INTEGER,
            a6 INTEGER,
            a7 INTEGER,
            a8 INTEGER,
            a9 INTEGER,
            a10 INTEGER,
            gaze_pattern TEXT,
            prediction REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Create admin user
def create_admin_user():
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin:
        conn.execute(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            ('admin', generate_password_hash('admin123'), 'admin')
        )
        conn.commit()
    conn.close()

create_admin_user()

# Behavioral assessment questions
QUESTIONS = [
    "Does your child look at you when you call his/her name?",
    "How easy is it for you to get eye contact with your child?",
    "Does your child point to indicate that s/he wants something?",
    "Does your child point to share interest with you?",
    "Does your child pretend?",
    "Does your child follow where you're looking?",
    "If you or someone else in the family is visibly upset, does your child show signs of wanting to comfort them?",
    "Would you describe your child's first words as:",
    "Does your child use simple gestures?",
    "Does your child stare at nothing with no apparent purpose?"
]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            error = 'Username already exists'
            return render_template('register.html', error=error)
        finally:
            conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        
        error = 'Invalid username or password'
        return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Get user's assessment history
    conn = get_db_connection()
    assessments = conn.execute(
        'SELECT * FROM assessments WHERE user_id = ? ORDER BY timestamp DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    return render_template('user_dashboard.html', assessments=assessments)

@app.route('/behavioral-assessment', methods=['GET', 'POST'])
def behavioral_assessment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Collect form data
        data = {
            'age': int(request.form['age']),
            'gender': request.form['gender'],
            'ethnicity': request.form['ethnicity'],
            'jaundice': request.form['jaundice'],
            'autism_family': request.form['autism_family'],
        }
        
        # Add question answers
        for i in range(1, 11):
            data[f'a{i}'] = int(request.form[f'a{i}'])
        
        # Store in session for eye tracking
        session['assessment_data'] = data
        return redirect(url_for('eye_tracking'))
    
    return render_template('behavioral_assessment.html', questions=QUESTIONS)

@app.route('/eye-tracking')
def eye_tracking():
    if 'user_id' not in session or 'assessment_data' not in session:
        return redirect(url_for('behavioral_assessment'))
    
    return render_template('eye_tracking.html')

@app.route('/simulate-eye-tracking', methods=['POST'])
def simulate_eye_tracking():
    # Generate simulated gaze data
    gaze_pattern = {
        'fixations': random.randint(5, 20),
        'saccades': random.randint(10, 30),
        'pupil_dilation': round(random.uniform(2.0, 5.0), 1),
        'attention_areas': {
            'eyes': random.randint(20, 80),
            'mouth': random.randint(10, 60),
            'objects': random.randint(5, 40)
        }
    }
    
    # Get behavioral data from session
    behavioral_data = session['assessment_data']
    
    # Prepare data for prediction
    input_data = pd.DataFrame({
        'A1_Score': [behavioral_data['a1']],
        'A2_Score': [behavioral_data['a2']],
        'A3_Score': [behavioral_data['a3']],
        'A4_Score': [behavioral_data['a4']],
        'A5_Score': [behavioral_data['a5']],
        'A6_Score': [behavioral_data['a6']],
        'A7_Score': [behavioral_data['a7']],
        'A8_Score': [behavioral_data['a8']],
        'A9_Score': [behavioral_data['a9']],
        'A10_Score': [behavioral_data['a10']],
        'age': [behavioral_data['age']],
        'gender': [1 if behavioral_data['gender'] == 'male' else 0],
        'jaundice': [1 if behavioral_data['jaundice'] == 'yes' else 0],
        'family_mem_with_ASD': [1 if behavioral_data['autism_family'] == 'yes' else 0],
        'gaze_fixations': [gaze_pattern['fixations']],
        'gaze_saccades': [gaze_pattern['saccades']],
        'pupil_dilation': [gaze_pattern['pupil_dilation']],
        'attention_eyes': [gaze_pattern['attention_areas']['eyes']],
        'attention_mouth': [gaze_pattern['attention_areas']['mouth']],
        'attention_objects': [gaze_pattern['attention_areas']['objects']]
    })
    
    # Make prediction
    prediction = model.predict_proba(input_data)[0][1]  # Probability of ASD
    
    # Store assessment in database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO assessments (
            user_id, age, gender, ethnicity, jaundice, autism_family,
            a1, a2, a3, a4, a5, a6, a7, a8, a9, a10,
            gaze_pattern, prediction
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        behavioral_data['age'],
        behavioral_data['gender'],
        behavioral_data['ethnicity'],
        behavioral_data['jaundice'],
        behavioral_data['autism_family'],
        behavioral_data['a1'],
        behavioral_data['a2'],
        behavioral_data['a3'],
        behavioral_data['a4'],
        behavioral_data['a5'],
        behavioral_data['a6'],
        behavioral_data['a7'],
        behavioral_data['a8'],
        behavioral_data['a9'],
        behavioral_data['a10'],
        json.dumps(gaze_pattern),
        prediction
    ))
    conn.commit()
    conn.close()
    
    # Clear session data
    session.pop('assessment_data', None)
    
    return jsonify({
        'prediction': prediction,
        'gaze_data': gaze_pattern
    })

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get latest assessment for user
    conn = get_db_connection()
    assessment = conn.execute(
        'SELECT * FROM assessments WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if not assessment:
        return redirect(url_for('behavioral_assessment'))
    
    # Parse gaze pattern
    gaze_pattern = json.loads(assessment['gaze_pattern'])
    
    return render_template('results.html', assessment=assessment, gaze_pattern=gaze_pattern)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get user counts
    users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    assessments = conn.execute('SELECT COUNT(*) FROM assessments').fetchone()[0]
    positive = conn.execute('SELECT COUNT(*) FROM assessments WHERE prediction >= 0.7').fetchone()[0]
    
    # Get recent assessments
    recent_assessments = conn.execute(
        'SELECT assessments.*, users.username FROM assessments '
        'JOIN users ON assessments.user_id = users.id '
        'ORDER BY timestamp DESC LIMIT 10'
    ).fetchall()
    
    # Get data for charts
    age_data = conn.execute(
        'SELECT age, COUNT(*) as count FROM assessments GROUP BY age'
    ).fetchall()
    
    gender_data = conn.execute(
        "SELECT gender, COUNT(*) as count FROM assessments GROUP BY gender"
    ).fetchall()
    
    prediction_data = conn.execute(
        'SELECT prediction FROM assessments'
    ).fetchall()
    
    conn.close()
    
    # Process data for charts
    ages = [row['age'] for row in age_data]
    age_counts = [row['count'] for row in age_data]
    
    genders = [row['gender'] for row in gender_data]
    gender_counts = [row['count'] for row in gender_data]
    
    predictions = [row['prediction'] for row in prediction_data]
    
    # Create prediction distribution chart
    plt.figure(figsize=(8, 4))
    plt.hist(predictions, bins=20, color='skyblue', edgecolor='black')
    plt.title('ASD Prediction Distribution')
    plt.xlabel('Prediction Probability')
    plt.ylabel('Count')
    plt.grid(axis='y', alpha=0.75)
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    prediction_chart = base64.b64encode(img_buf.read()).decode('utf-8')
    plt.close()
    
    return render_template('admin/dashboard.html', 
                          users=users, 
                          assessments=assessments,
                          positive=positive,
                          recent_assessments=recent_assessments,
                          ages=ages,
                          age_counts=age_counts,
                          genders=genders,
                          gender_counts=gender_counts,
                          prediction_chart=prediction_chart)

@app.route('/admin/assessments')
def admin_assessments():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    assessments = conn.execute(
        'SELECT assessments.*, users.username FROM assessments '
        'JOIN users ON assessments.user_id = users.id '
        'ORDER BY timestamp DESC'
    ).fetchall()
    conn.close()
    
    return render_template('admin/assessments.html', assessments=assessments)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/analytics')
def admin_analytics():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get data for charts
    ethnicity_data = conn.execute(
        'SELECT ethnicity, COUNT(*) as count FROM assessments GROUP BY ethnicity'
    ).fetchall()
    
    jaundice_data = conn.execute(
        "SELECT jaundice, COUNT(*) as count FROM assessments GROUP BY jaundice"
    ).fetchall()
    
    family_data = conn.execute(
        "SELECT autism_family, COUNT(*) as count FROM assessments GROUP BY autism_family"
    ).fetchall()
    
    scores_data = conn.execute(
        "SELECT a1, a2, a3, a4, a5, a6, a7, a8, a9, a10 FROM assessments"
    ).fetchall()
    
    conn.close()
    
    # Process data for charts
    ethnicities = [row['ethnicity'] for row in ethnicity_data]
    ethnicity_counts = [row['count'] for row in ethnicity_data]
    
    jaundice_labels = ['Jaundice: Yes' if row['jaundice'] == 'yes' else 'Jaundice: No' for row in jaundice_data]
    jaundice_counts = [row['count'] for row in jaundice_data]
    
    family_labels = ['Family History: Yes' if row['autism_family'] == 'yes' else 'Family History: No' for row in family_data]
    family_counts = [row['count'] for row in family_data]
    
    # Calculate average scores
    scores_df = pd.DataFrame(scores_data, columns=[f'a{i}' for i in range(1, 11)])
    avg_scores = scores_df.mean().tolist()
    
    return render_template('admin/analytics.html', 
                          ethnicities=ethnicities,
                          ethnicity_counts=ethnicity_counts,
                          jaundice_labels=jaundice_labels,
                          jaundice_counts=jaundice_counts,
                          family_labels=family_labels,
                          family_counts=family_counts,
                          avg_scores=avg_scores)

if __name__ == '__main__':
    app.run(debug=True)