import os
import html
import re
import time
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, make_response

app = Flask(__name__)

# --- SECURITY: Max payload limit ---
# Limit request body sizes to 1MB to prevent Denial of Service (DoS) attacks
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

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
    return send_from_directory('.', 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory('.', 'styles.css', mimetype='text/css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('.', 'script.js', mimetype='application/javascript')

@app.route('/background.jpg')
def serve_background():
    return send_from_directory('.', 'background.jpg', mimetype='image/jpeg')

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
        
    # --- Forward message to user's email directly ---
    smtp_success = False
    sender_password = os.environ.get('SENDER_PASSWORD')
    
    # 1. Try sending directly via Gmail SMTP (Highly reliable, bypasses API blocks)
    if sender_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            sender_email = os.environ.get('SENDER_EMAIL', 'manikandaprabuvk@gmail.com')
            
            msg = MIMEMultipart()
            msg['From'] = f"Portfolio Contact <{sender_email}>"
            msg['To'] = sender_email
            msg['Subject'] = f"📬 Portfolio Message: {subject}"
            
            body_content = f"You received a new message from your portfolio contact form:\n\n" \
                           f"Name: {name}\n" \
                           f"Email: {email}\n" \
                           f"Subject: {subject}\n\n" \
                           f"Message:\n{message}"
                           
            msg.attach(MIMEText(body_content, 'plain'))
            
            # Connect to Gmail's secure SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, sender_email, msg.as_string())
            server.quit()
            print("Email sent successfully via Gmail SMTP!")
            smtp_success = True
        except Exception as smtp_err:
            print(f"Failed to send email via SMTP: {smtp_err}")
            
    # 2. Fallback to FormSubmit.co if SMTP is not configured or failed
    if not smtp_success:
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
            smtp_success = True
        except Exception as e:
            print(f"Warning: Failed to forward message to FormSubmit.co: {e}")

    if smtp_success:
        return jsonify({'success': True, 'message': 'Message sent successfully!'})
    else:
        return jsonify({
            'success': False, 
            'error': 'Failed to send message. Please try emailing directly to manikandaprabuvk@gmail.com.'
        }), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
