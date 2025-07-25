# 🏏 CRICKET_DBMS

A full-stack **Cricket Player Management System** built using **Flask** and **PostgreSQL**. This project helps manage players, teams, match records, injuries, and awards in a structured and efficient way.

---

## 🚀 Features

- 🔐 **User Authentication** (Register/Login)
- 👥 **Player Management** (Add, View, and Update Players)
- 🏆 **Awards Tracking** (MOMs, POS, World Cups)
- 📊 **Match Records** (ODI, T20, Test Stats)
- 🩺 **Injury Records** (Injury history per player)
- 🏏 **Team Assignments** (National & Domestic Teams)
- 📂 Organized Flask App with HTML Templates and Static Assets

---

## 🖼️ Screenshots

> *(Add your app screenshots or GIFs here)*  
> Example:  
> ![Home Page](static/screenshots/home.png)

---

## 🛠️ Tech Stack

| Layer         | Technology       |
|---------------|------------------|
| Backend       | Python (Flask)   |
| Database      | PostgreSQL       |
| Frontend      | HTML, CSS, JS    |
| Template Eng. | Jinja2 (Flask)   |
| Deployment    | Localhost        |

---

## 📁 Project Structure

CRICKET_MANAGEMENT_SYSTEM/
├── app.py
├── templates/
│ ├── base.html
│ ├── home.html
│ ├── players/
│ ├── teams/
│ ├── awards/
│ ├── injuries/
│ └── auth/
├── static/
│ ├── styles.css
│ └── app.js
├── .gitignore
└── requirements.txt


---

## 🔧 Setup Instructions

1. **Clone this repo**  
   git clone https://github.com/SIVA-CEG/CRICKET_DBMS.git
   cd CRICKET_DBMS
2.Create & activate virtual environment

python -m venv venv
venv\Scripts\activate     # On Windows
Install dependencies

3.
  pip install -r requirements.txt

4.Configure database
  Make sure PostgreSQL is installed and update DB credentials in app.py.

5. Run the app

  flask run or (python app.py)
