import sqlite3
import os
import uuid
import html
import re
import time
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, make_response

# Try importing pymongo for MongoDB Atlas support
try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

app = Flask(__name__)

# --- SECURITY: Max payload limit ---
# Limit request body sizes to 1MB to prevent Denial of Service (DoS) attacks
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

# Database Configuration
MONGO_URI = os.environ.get('MONGO_URI')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'portfolio.db')

# Detect if we should use MongoDB Atlas or fallback to SQLite
USE_MONGODB = HAS_PYMONGO and MONGO_URI is not None

# --- Fallback SQLite Database Initializer with directory safety ---
def init_sqlite_db():
    global DATABASE_PATH
    try:
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    except Exception as e:
        # Handles Render container permission errors (e.g., trying to write to root /data without mounted disk)
        print(f"Warning: Failed to create database directory {db_dir}: {e}. Falling back to local directory.")
        DATABASE_PATH = 'portfolio.db'

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_uuid TEXT UNIQUE,
                user_agent TEXT,
                ip_address TEXT,
                first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visit_count INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_uuid TEXT,
                name TEXT,
                email TEXT,
                subject TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as sq_err:
        print(f"Critical error initializing SQLite database: {sq_err}")

# Safe connection getter for SQLite
def get_sqlite_conn():
    global DATABASE_PATH
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Failed to open SQLite database: {e}. Attempting local fallback.")
        DATABASE_PATH = 'portfolio.db'
        return sqlite3.connect(DATABASE_PATH)

mongo_client = None
db = None

if USE_MONGODB:
    try:
        # Connect to MongoDB Atlas (database: portfolio_db)
        # Timeout connection attempt quickly (5 seconds) to prevent hanging the server during startup
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client['portfolio_db']
        
        # Perform a quick Ping command to check if connection string/credentials and network match
        mongo_client.admin.command('ping')
        print("Connected successfully to MongoDB Atlas!")
    except Exception as e:
        # Fallback to local SQLite if MongoDB credentials are incorrect or if IP access is blocked
        print(f"Failed to connect to MongoDB Atlas, falling back to SQLite: {e}")
        USE_MONGODB = False
        init_sqlite_db()
else:
    init_sqlite_db()

# --- SECURITY: In-memory Rate Limiter ---
submission_tracker = defaultdict(list)
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
MAX_SUBMISSIONS = 5      # Max 5 submissions allowed per window

def is_rate_limited(ip):
    now = time.time()
    submission_tracker[ip] = [t for t in submission_tracker[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(submission_tracker[ip]) >= MAX_SUBMISSIONS:
        return True
    submission_tracker[ip].append(now)
    return False

# --- Database Abstract Actions ---
def log_visitor(visitor_uuid, user_agent, ip_address):
    if USE_MONGODB:
        try:
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            visitor = db.visitors.find_one({'visitor_uuid': visitor_uuid})
            if visitor:
                db.visitors.update_one(
                    {'visitor_uuid': visitor_uuid},
                    {
                        '$set': {
                            'last_visit': now,
                            'ip_address': ip_address,
                            'user_agent': user_agent
                        },
                        '$inc': {'visit_count': 1}
                    }
                )
            else:
                db.visitors.insert_one({
                    'visitor_uuid': visitor_uuid,
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'first_visit': now,
                    'last_visit': now,
                    'visit_count': 1
                })
        except PyMongoError as e:
            print(f"MongoDB tracking error: {e}")
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM visitors WHERE visitor_uuid = ?', (visitor_uuid,))
            if cursor.fetchone():
                cursor.execute('''
                    UPDATE visitors
                    SET last_visit = CURRENT_TIMESTAMP, visit_count = visit_count + 1, ip_address = ?, user_agent = ?
                    WHERE visitor_uuid = ?
                ''', (ip_address, user_agent, visitor_uuid))
            else:
                cursor.execute('''
                    INSERT INTO visitors (visitor_uuid, user_agent, ip_address)
                    VALUES (?, ?, ?)
                ''', (visitor_uuid, user_agent, ip_address))
            conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite tracking error: {e}")
        finally:
            conn.close()

def save_message(visitor_uuid, name, email, subject, message):
    if USE_MONGODB:
        try:
            db.messages.insert_one({
                'visitor_uuid': visitor_uuid,
                'name': name,
                'email': email,
                'subject': subject,
                'message': message,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            return True, None
        except PyMongoError as e:
            return False, str(e)
    else:
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        success = False
        error = None
        try:
            cursor.execute('''
                INSERT INTO messages (visitor_uuid, name, email, subject, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (visitor_uuid, name, email, subject, message))
            conn.commit()
            success = True
        except sqlite3.Error as e:
            error = str(e)
        finally:
            conn.close()
        return success, error

# --- SECURITY: HTTP Headers Middleware ---
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response

@app.route('/')
def index():
    visitor_uuid = request.cookies.get('visitor_uuid')
    is_new = False
    
    uuid_regex = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    if visitor_uuid and not re.match(uuid_regex, visitor_uuid):
        visitor_uuid = None
        
    if not visitor_uuid:
        visitor_uuid = str(uuid.uuid4())
        is_new = True
        
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr
    
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
    log_visitor(visitor_uuid, user_agent, ip_address)
        
    response = make_response(send_from_directory('.', 'index.html'))
    is_https = request.is_secure or request.headers.get('X-Forwarded-Proto', '').lower() == 'https'
    
    response.set_cookie(
        'visitor_uuid',
        visitor_uuid,
        max_age=31536000,
        httponly=True,
        secure=is_https,
        samesite='Lax'
    )
    return response

@app.route('/styles.css')
def serve_css():
    return send_from_directory('.', 'styles.css', mimetype='text/css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('.', 'script.js', mimetype='application/javascript')

@app.route('/Manikandaprabu_VK_Resume N.pdf')
def serve_resume():
    return send_from_directory('.', 'Manikandaprabu_VK_Resume N.pdf', mimetype='application/pdf')

@app.route('/api/contact', methods=['POST'])
def contact():
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()

    if is_rate_limited(ip_address):
        return jsonify({
            'success': False, 
            'error': 'Too many submissions. Please wait 15 minutes.'
        }), 429

    visitor_uuid = request.cookies.get('visitor_uuid')
    
    uuid_regex = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    if visitor_uuid and not re.match(uuid_regex, visitor_uuid):
        visitor_uuid = "tampered-cookie-blocked"

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    name = html.escape(data.get('name', '').strip())
    email = html.escape(data.get('email', '').strip())
    subject = html.escape(data.get('subject', '').strip())
    message = html.escape(data.get('message', '').strip())
    
    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'Name, Email, and Message are required'}), 400

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({'success': False, 'error': 'Invalid email address format'}), 400
        
    success, error = save_message(visitor_uuid, name, email, subject, message)
        
    # --- Forward message to user's email via FormSubmit.co in the backend ---
    if success:
        try:
            import urllib.request
            import json
            forward_url = 'https://formsubmit.co/ajax/manikandaprabuvk@gmail.com'
            forward_data = json.dumps({
                'name': name,
                'email': email,
                '_subject': f"📬 Portfolio Message: {subject}",
                'message': message,
                '_captcha': 'false',
                '_template': 'table'
            }).encode('utf-8')
            
            req = urllib.request.Request(
                forward_url,
                data=forward_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0'
                }
            )
            with urllib.request.urlopen(req, timeout=8) as f_res:
                print(f"Backend email forward status: {f_res.status}")
        except Exception as e:
            print(f"Warning: Failed to forward message to FormSubmit.co: {e}")

    if success:
        return jsonify({'success': True, 'message': 'Message saved successfully!'})
    else:
        return jsonify({'success': False, 'error': 'Internal database error'}), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
