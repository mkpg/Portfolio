import sqlite3
import os

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'portfolio.db')

def view_database():
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file '{DATABASE_PATH}' does not exist yet. Run the server and visit the site first!")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("==================================================")
    print("               👥 PORTFOLIO VISITORS               ")
    print("==================================================")
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

    print("\n==================================================")
    print("               📬 CONTACT MESSAGES                ")
    print("==================================================")
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

    conn.close()

if __name__ == '__main__':
    view_database()
