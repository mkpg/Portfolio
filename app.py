import sqlite3
import os
import uuid
import html
import re
import time
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, make_response

app = Flask(__name__)

# --- SECURITY: Max payload limit ---
# Limit request body sizes to 1MB to prevent Denial of Service (DoS) attacks
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

# Configurable SQLite database path
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'portfolio.db')

# --- SECURITY: In-memory Rate Limiter ---
# Tracks client requests to prevent spamming the contact form
# Structure: {ip_address: [timestamp1, timestamp2, ...]}
submission_tracker = defaultdict(list)
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
MAX_SUBMISSIONS = 5      # Max 5 submissions allowed per window

def is_rate_limited(ip):
    now = time.time()
    # Retain only timestamps within the current active window
    submission_tracker[ip] = [t for t in submission_tracker[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(submission_tracker[ip]) >= MAX_SUBMISSIONS:
        return True
    submission_tracker[ip].append(now)
    return False

def get_db():
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Table for tracking visitor actions and sessions
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
    
    # Table for storing contact form messages
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

# Initialize tables at startup
init_db()

# --- SECURITY: HTTP Headers Middleware ---
@app.after_request
def add_security_headers(response):
    # Prevent stylesheet/script MIME sniffing attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent site from being embedded in iframes (prevents Clickjacking)
    response.headers['X-Frame-Options'] = 'DENY'
    # Enable browser-level cross-site scripting (XSS) filter
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Control how much referrer information is passed to external sites
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Strict Content Security Policy (CSP) - limits assets to self, google fonts, etc.
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
    
    # --- SECURITY: Validate visitor cookie format to prevent tampering ---
    uuid_regex = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    if visitor_uuid and not re.match(uuid_regex, visitor_uuid):
        visitor_uuid = None  # Reset tampered cookie
        
    if not visitor_uuid:
        visitor_uuid = str(uuid.uuid4())
        is_new = True
        
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr
    
    # Extract proxy forwarding headers safely
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
    conn = get_db()
    cursor = conn.cursor()
    try:
        if is_new:
            # Safe parameterized injection
            cursor.execute('''
                INSERT INTO visitors (visitor_uuid, user_agent, ip_address)
                VALUES (?, ?, ?)
            ''', (visitor_uuid, user_agent, ip_address))
        else:
            # Check if this uuid is in db (in case database was reset but cookie remained)
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
        print(f"Database error tracking visitor: {e}")
    finally:
        conn.close()
        
    response = make_response(send_from_directory('.', 'index.html'))
    
    # Determine if request is HTTPS to set Secure flag
    is_https = request.is_secure or request.headers.get('X-Forwarded-Proto', '').lower() == 'https'
    
    # --- SECURITY: Set secure HTTP-only cookies ---
    response.set_cookie(
        'visitor_uuid',
        visitor_uuid,
        max_age=31536000,
        httponly=True,  # Restricts client-side JS from reading cookie
        secure=is_https, # Transmit only over HTTPS in production
        samesite='Lax'   # Defends against Cross-Site Request Forgery (CSRF)
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
    # Fetch client IP safely
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()

    # --- SECURITY: Rate Limiting validation ---
    if is_rate_limited(ip_address):
        return jsonify({
            'success': False, 
            'error': 'Too many submissions. Please wait 15 minutes.'
        }), 429

    visitor_uuid = request.cookies.get('visitor_uuid')
    
    # --- SECURITY: Validate visitor cookie format ---
    uuid_regex = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    if visitor_uuid and not re.match(uuid_regex, visitor_uuid):
        visitor_uuid = "tampered-cookie-blocked"

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    # --- SECURITY: Input Sanitization (protects against XSS) ---
    name = html.escape(data.get('name', '').strip())
    email = html.escape(data.get('email', '').strip())
    subject = html.escape(data.get('subject', '').strip())
    message = html.escape(data.get('message', '').strip())
    
    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'Name, Email, and Message are required'}), 400

    # --- SECURITY: Validate Email Format ---
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({'success': False, 'error': 'Invalid email address format'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    success = False
    error = None
    
    try:
        # --- SECURITY: Parameterized Query protects against SQL Injection ---
        cursor.execute('''
            INSERT INTO messages (visitor_uuid, name, email, subject, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (visitor_uuid, name, email, subject, message))
        conn.commit()
        success = True
    except sqlite3.Error as e:
        error = str(e)
        print(f"Database error saving message: {e}")
    finally:
        conn.close()
        
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
            # Timeout set to 8 seconds to prevent hanging the request
            with urllib.request.urlopen(req, timeout=8) as f_res:
                print(f"Backend email forward status: {f_res.status}")
        except Exception as e:
            # We don't return an error to the frontend if email forwarding fails (e.g. timeout),
            # since the message has been securely saved in the SQLite database and can be retrieved!
            print(f"Warning: Failed to forward message to FormSubmit.co: {e}")

    if success:
        return jsonify({'success': True, 'message': 'Message saved successfully!'})
    else:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # production hosting on Render disables debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
