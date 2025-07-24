
# 🩺 HealthMate

**HealthMate** is a smart health monitoring web app built with Flask. It allows users to **predict diseases based on symptoms**, **add and track health logs**, **view and download health reports**, and access several other health-related tools like a **BMI calculator**, **medicine expiry tracker**, and **health charts**.

## 🌟 Features
- 🧠 Disease Prediction using ML based on symptoms
- 📊 Health Logs: Sleep, water intake, glucose, BP, etc.
- 🧾 Download Health Report as PDF
- ⚖️ BMI Calculator
- 📈 Symptom History Graphs using Chart.js
- 👤 User Profile with image upload and avatar selection
- 💊 Medicine Expiry Tracker with 5-day prior alerts
- 🌐 Clean, modern dashboard UI

## 🚀 Tech Stack
- Backend: Python, Flask  
- Frontend: HTML5, CSS3, JavaScript  
- Database: MySQL    

## 🛠️ How to Run Locally

### 1. Clone the Repo
```

git clone [https://github.com/shreyaa-naik/HealthMate.git](https://github.com/shreyaa-naik/HealthMate.git)
cd HealthMate

```

### 2. Create Virtual Environment
```

python -m venv venv
venv\Scripts\activate  # Windows

# OR

source venv/bin/activate  # Mac/Linux

```

### 3. Install Dependencies
```

pip install -r requirements.txt

```

### 4. Configure MySQL
Create a MySQL database named `healthmate_db`  
Update `app.py` with your MySQL credentials

### 5. Run the Flask App
```

python app.py

```
App runs at: http://127.0.0.1:5001/

## 📁 Folder Structure
HealthMate/  
├── app.py  
├── requirements.txt  
├── /templates  
│   ├── login.html  
│   ├── register.html  
│   ├── dashboard.html  
│   ├── view_reminders.html  
│   ├── profile.html  
│   └── ...  
├── /static  
│   ├── style.css  
│   └── alarm.mp3  
├── /venv  
├── README.md

## 🌍 Deployment Options
- ✅ Render  
- ✅ Replit  
- ✅ Ngrok

## 👨‍💻 About the Project

**HealthMate** is a Flask-based web application designed to assist users in managing their daily health activities and tracking overall wellness. The project focuses on providing a smart health assistant that can predict possible diseases based on symptoms, maintain daily health logs, and give visual insights using health charts.

It also includes:
- A **BMI calculator** to help users track their fitness.
- A **medicine expiry tracker** to alert users before their medicines expire.
- The ability to **download health logs as a PDF report**.
- Interactive and responsive UI built with HTML, CSS, and JavaScript.

This project is especially useful for:
- Individuals managing chronic conditions
- Elderly people who need regular health tracking
- Students or professionals interested in preventive healthcare

HealthMate aims to make health monitoring easy, accessible, and personalized for everyone.

## 📧 Contact
GitHub: https://github.com/shreyaa-naik 
Email: shreyaa4950@gmail.com



