# 📖 Dear Diary — Personal Diary Web App

A beautiful, private diary web app for you and your friends. Each person has their own secure account and all entries are completely private.

---

## ✨ Features

- 🔐 **Secure login** — each user has their own private account
- 📅 **Interactive calendar** — click any date to see that day's entry
- 😊 **Mood tracker** — track how you felt each day with emoji moods
- ✍️ **Rich text editor** — bold, italic, underline, lists, headings
- 🔍 **Recent entries list** — quickly find past memories
- 💾 **Auto-updates** — saving the same day's entry updates it
- 🎨 **Beautiful design** — warm, paper-like aesthetic

---

## 🚀 How to Run

### 1. Install MongoDB
- Download from: https://www.mongodb.com/try/download/community
- Make sure MongoDB is running on `localhost:27017`

### 2. Install Python dependencies
```bash
cd diary-app
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
Go to: **http://localhost:5000**

---

## 🌐 Share with Friends

To let your friends access it on the same WiFi:

```bash
# Find your local IP (on Mac/Linux)
ifconfig | grep inet

# Then run with:
flask run --host=0.0.0.0 --port=5000
```

Your friends can access it at `http://YOUR_IP:5000`

---

## 🔒 For Production / Public Internet

Use these environment variables:

```bash
export SECRET_KEY="some-very-long-random-string-here"
export MONGO_URI="mongodb://localhost:27017/"
python app.py
```

For public deployment, use **gunicorn** + **nginx** + **MongoDB Atlas** (free tier).

---

## 📁 File Structure

```
diary-app/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── templates/
    ├── auth.html       # Login / Register page
    └── diary.html      # Main diary page
```

---

## 🛡️ Security

- Passwords are **hashed** (never stored in plain text)
- Sessions are server-side signed
- Each user can only see **their own entries** — fully private
- No one else, including other users, can read your diary

---

## 💡 Tips

- Press **Ctrl+S** (or **Cmd+S** on Mac) to quickly save an entry
- Click the same mood again to deselect it
- The calendar dots show which days have entries
- You can edit any past entry by selecting that date and clicking Edit
