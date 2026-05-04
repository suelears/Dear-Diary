from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId
import os, re, base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'diary-secret-key-change-in-production')

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['personal_diary']
users_col   = db['users']
entries_col = db['entries']

users_col.create_index('username', unique=True)
entries_col.create_index([('user_id', 1), ('date', -1)])

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ─── Pages ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('diary'))
    return render_template('auth.html')

@app.route('/diary')
def diary():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('diary.html')

# ─── Auth ────────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data         = request.get_json()
    username     = data.get('username', '').strip().lower()
    password     = data.get('password', '')
    display_name = data.get('display_name', '').strip()

    if not username or not password or not display_name:
        return jsonify({'error': 'All fields are required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if not re.match(r'^[a-z0-9_]+$', username):
        return jsonify({'error': 'Username can only contain letters, numbers, underscores'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if users_col.find_one({'username': username}):
        return jsonify({'error': 'Username already taken'}), 409

    user = {
        'username':     username,
        'display_name': display_name,
        'password':     generate_password_hash(password),
        'avatar':       '',
        'created_at':   datetime.utcnow()
    }
    result = users_col.insert_one(user)
    session['user_id']      = str(result.inserted_id)
    session['username']     = username
    session['display_name'] = display_name
    return jsonify({'message': 'Account created!', 'display_name': display_name})

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')

    user = users_col.find_one({'username': username})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    session['user_id']      = str(user['_id'])
    session['username']     = user['username']
    session['display_name'] = user['display_name']
    return jsonify({'message': 'Welcome back!', 'display_name': user['display_name']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/me')
@login_required
def me():
    user = users_col.find_one({'_id': ObjectId(session['user_id'])}, {'password': 0})
    return jsonify({
        'username':     user['username'],
        'display_name': user['display_name'],
        'avatar':       user.get('avatar', ''),
        'member_since': user['created_at'].strftime('%B %Y') if user.get('created_at') else ''
    })

@app.route('/api/me/avatar', methods=['POST'])
@login_required
def upload_avatar():
    data   = request.get_json()
    avatar = data.get('avatar', '')          # base64 data-url
    if not avatar:
        return jsonify({'error': 'No image provided'}), 400
    # limit ~2 MB
    if len(avatar) > 2_800_000:
        return jsonify({'error': 'Image too large (max 2 MB)'}), 400
    users_col.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'avatar': avatar}}
    )
    return jsonify({'message': 'Avatar updated', 'avatar': avatar})

# ─── Entries ─────────────────────────────────────────────────────────────────

@app.route('/api/entries', methods=['POST'])
@login_required
def create_entry():
    data       = request.get_json()
    date_str   = data.get('date')
    title      = data.get('title', '').strip()
    content    = data.get('content', '').strip()
    mood       = data.get('mood', '')
    day_rating = data.get('day_rating', '')

    if not date_str or not content:
        return jsonify({'error': 'Date and content are required'}), 400
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    existing = entries_col.find_one({'user_id': session['user_id'], 'date_str': date_str})
    entry_data = {
        'user_id':    session['user_id'],
        'date_str':   date_str,
        'date':       date,
        'title':      title,
        'content':    content,
        'mood':       mood,
        'day_rating': day_rating,
        'updated_at': datetime.utcnow()
    }
    if existing:
        entries_col.update_one({'_id': existing['_id']}, {'$set': entry_data})
        entry_id = str(existing['_id'])
    else:
        entry_data['created_at'] = datetime.utcnow()
        result   = entries_col.insert_one(entry_data)
        entry_id = str(result.inserted_id)

    return jsonify({'message': 'Entry saved!', 'id': entry_id})

@app.route('/api/entries', methods=['GET'])
@login_required
def get_entries():
    entries = entries_col.find(
        {'user_id': session['user_id']},
        {'date_str': 1, 'mood': 1, 'title': 1, 'day_rating': 1}
    ).sort('date', -1)
    return jsonify([{
        'id':         str(e['_id']),
        'date':       e['date_str'],
        'mood':       e.get('mood', ''),
        'title':      e.get('title', ''),
        'day_rating': e.get('day_rating', '')
    } for e in entries])

@app.route('/api/entries/<date_str>', methods=['GET'])
@login_required
def get_entry_by_date(date_str):
    entry = entries_col.find_one({'user_id': session['user_id'], 'date_str': date_str})
    if not entry:
        return jsonify(None)
    return jsonify({
        'id':         str(entry['_id']),
        'date':       entry['date_str'],
        'title':      entry.get('title', ''),
        'content':    entry['content'],
        'mood':       entry.get('mood', ''),
        'day_rating': entry.get('day_rating', ''),
        'created_at': entry['created_at'].isoformat() if entry.get('created_at') else '',
        'updated_at': entry['updated_at'].isoformat() if entry.get('updated_at') else ''
    })

@app.route('/api/entries/<entry_id>', methods=['DELETE'])
@login_required
def delete_entry(entry_id):
    result = entries_col.delete_one({'_id': ObjectId(entry_id), 'user_id': session['user_id']})
    if result.deleted_count == 0:
        return jsonify({'error': 'Entry not found'}), 404
    return jsonify({'message': 'Entry deleted'})

@app.route('/api/stats')
@login_required
def stats():
    total  = entries_col.count_documents({'user_id': session['user_id']})
    green  = entries_col.count_documents({'user_id': session['user_id'], 'day_rating': 'green'})
    yellow = entries_col.count_documents({'user_id': session['user_id'], 'day_rating': 'yellow'})
    red    = entries_col.count_documents({'user_id': session['user_id'], 'day_rating': 'red'})
    return jsonify({'total': total, 'green': green, 'yellow': yellow, 'red': red})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
