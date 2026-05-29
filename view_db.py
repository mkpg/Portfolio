import os
import sqlite3

MONGO_URI = os.environ.get('MONGO_URI')

try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

USE_MONGODB = HAS_PYMONGO and MONGO_URI is not None
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'portfolio.db')

def view_database():
    if USE_MONGODB:
        print("Connecting to MongoDB Atlas...")
        try:
            client = MongoClient(MONGO_URI)
            db = client['portfolio_db']
            
            print("==================================================")
            print("         👥 PORTFOLIO VISITORS (MongoDB)          ")
            print("==================================================")
            visitors = list(db.visitors.find().sort('last_visit', -1))
            if not visitors:
                print("No visitors tracked yet.")
            for v in visitors:
                print(f"UUID: {v.get('visitor_uuid')}")
                print(f"  IP: {v.get('ip_address')} | Visits: {v.get('visit_count')}")
                print(f"  First: {v.get('first_visit')} | Last: {v.get('last_visit')}")
                print(f"  User Agent: {v.get('user_agent', '')[:80]}...")
                print("-" * 50)

            print("\n==================================================")
            print("          📬 CONTACT MESSAGES (MongoDB)           ")
            print("==================================================")
            messages = list(db.messages.find().sort('timestamp', -1))
            if not messages:
                print("No messages received yet.")
            for m in messages:
                print(f"Name: {m.get('name')} | Email: {m.get('email')}")
                print(f"  Subject: {m.get('subject')}")
                print(f"  Date: {m.get('timestamp')}")
                print(f"  Message: {m.get('message')}")
                print(f"  Visitor UUID: {m.get('visitor_uuid')}")
                print("-" * 50)
                
            client.close()
        except Exception as e:
            print(f"MongoDB connection error: {e}")
    else:
        print(f"Using local SQLite database fallback ({DATABASE_PATH})...")
        if not os.path.exists(DATABASE_PATH):
            print(f"Error: Database file '{DATABASE_PATH}' does not exist yet. Run the server and visit the site first!")
            return

        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("==================================================")
        print("          👥 PORTFOLIO VISITORS (SQLite)          ")
        print("==================================================")
        try:
            cursor.execute("SELECT * FROM visitors ORDER BY last_visit DESC")
            visitors = cursor.fetchall()
            if not visitors:
                print("No visitors tracked yet.")
            for v in visitors:
                print(f"ID: {v['id']} | UUID: {v['visitor_uuid']}")
                print(f"  IP: {v['ip_address']} | Visits: {v['visit_count']}")
                print(f"  First: {v['first_visit']} | Last: {v['last_visit']}")
                print(f"  User Agent: {v['user_agent'][:80]}...")
                print("-" * 50)
        except sqlite3.OperationalError:
            print("Table 'visitors' does not exist yet.")

        print("\n==================================================")
        print("          📬 CONTACT MESSAGES (SQLite)           ")
        print("==================================================")
        try:
            cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC")
            messages = cursor.fetchall()
            if not messages:
                print("No messages received yet.")
            for m in messages:
                print(f"ID: {m['id']} | Name: {m['name']} | Email: {m['email']}")
                print(f"  Subject: {m['subject']}")
                print(f"  Date: {m['timestamp']}")
                print(f"  Message: {m['message']}")
                print(f"  Visitor UUID: {m['visitor_uuid']}")
                print("-" * 50)
        except sqlite3.OperationalError:
            print("Table 'messages' does not exist yet.")

        conn.close()

if __name__ == '__main__':
    view_database()
