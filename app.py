from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import sqlite3
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
import csv
import io
import pytz

app = Flask(__name__)
app.secret_key = "super_secure_key_vraj"  # for session management
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

ADMIN_PASSWORD = "admin123"  # 🔒 change this password if needed

# 📧 Email config
SENDER_EMAIL = "dept-clerk.etrx@somaiya.edu"
SENDER_PASSWORD = "lsrq bqxq fcqs lbsq"  # app password

scheduler = BackgroundScheduler()
scheduler.start()


# ---------------------- INIT DB ----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS professors (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS issued_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        professor_id TEXT,
        professor_name TEXT,
        department TEXT,
        item_code TEXT,
        item_name TEXT,
        action TEXT,
        issue_date TEXT
    )
    """)

    professors = [
        ("16000050", "Dinesh Auti", "Electronics", "dinesh.a@somaiya.edu"),
        ("160592", "Amrita Naiksatam", "Electronics", "aynaiksatam@somaiya.edu"),
        ("161006", "Ayesha Hakim", "Electronics", "ayesha.hakim@somaiya.edu"),
        ("16000022", "Ashwini Kumar", "Electronics", "ashwinikumar@somaiya.edu"),
        ("160028", "Arati Phadke", "Electronics", "aratiphadke@somaiya.edu"),
        ("161030", "Balwant Kumar Singh", "Electronics", "balwantkumar@somaiya.edu"),
        ("160706", "Bharati Khedkar", "Electronics", "bharatikhedkar@somaiya.edu"),
        ("160767", "Deepa Jain", "Electronics", "deepajain@somaiya.edu"),
        ("160111", "Jagannath Nirmal", "Electronics", "jhnirmal@somaiya.edu"),
        ("16011041", "Jasraj Bherwani", "Electronics", "jasraj@somaiya.edu"),
        ("161020", "Jayesh Rane", "Electronics", "jayesh.rane@somaiya.edu"),
        ("16000005", "Kiran Thale", "Electronics", "kiran.thale@somaiya.edu"),
        ("160035", "Kirti Sawlani", "Electronics", "kirtisawlani@somaiya.edu"),
        ("160039", "Makarand Kulkarni", "Electronics", "makarandkulkarni@somaiya.edu"),
        ("160865", "Megha Sharma", "Electronics", "meghasharma@somaiya.edu"),
        ("161007", "Midhya Mathew", "Electronics", "midhya@somaiya.edu"),
        ("160891", "Nilesh Lakade", "Electronics", "nilesh.lakade@somaiya.edu"),
        ("161001", "Ninad Mehendale", "Electronics", "ninad@somaiya.edu"),
        ("161008", "Om Prakash Goswami", "Electronics", "o.g@somaiya.edu"),
        ("161012", "Payal Varangaonkar", "Electronics", "payal.av@somaiya.edu"),
        ("160968", "Pragya Gupta", "Electronics", "pragya.g@somaiya.edu"),
        ("160048", "Rajashree Daryapurkar", "Electronics", "rajashreedaryapurkar@somaiya.edu"),
        ("160126", "Sandeep Hanumante", "Electronics", "sahanumante@somaiya.edu"),
        ("160132", "Seema Talmale", "Electronics", "seematalmale@somaiya.edu"),
        ("160652", "Shila Dhande", "Electronics", "shiladhande@somaiya.edu"),
        ("16000030", "Snehal Shinde", "Electronics", "snehal.shinde@somaiya.edu"),
        ("160866", "Sonia Joshi", "Electronics", "soniajoshi@somaiya.edu"),
        ("160155", "Sudha Gupta", "Electronics", "sudhagupta@somaiya.edu"),
        ("160157", "Sushma Kadge", "Electronics", "sushmakadge@somaiya.edu"),
        ("161028", "Tejashree Phatak", "Electronics", "tejashree@somaiya.edu"),
        ("161005", "Umang Patel", "Electronics", "umang@somaiya.edu")
    ]

    c.executemany("INSERT OR IGNORE INTO professors VALUES (?, ?, ?, ?)", professors)
    conn.commit()
    conn.close()


# ---------------------- EMAIL ALERT ----------------------
def send_email_alert(professor_email, professor_name, item_name, item_code, issued_time):
    subject = f"⚠️ Reminder: Please return the {item_name}"
    body = f"""
Dear {professor_name},

This is an automated reminder from the Item Issuer & Logger system.

The following item issued to you has not been returned:

Item Name: {item_name}
Item Code: {item_code}
Issued At: {issued_time}

Please return it to the office as soon as possible.

This is a system-generated mail. Do not reply to it.

Thank you,
Faculty Items Issuer & Logger
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = professor_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, professor_email, msg.as_string())
        print(f"✅ Email sent to {professor_email} for {item_code}")
    except Exception as e:
        print(f"❌ Email failed: {e}")


# ---------------------- HELPERS ----------------------
def get_item_name(code):
    code = code.upper().strip()
    mapping = {}
    for i in range(1, 11):
        mapping[f"HDMI{i:03}"] = "HDMI Cable"
        mapping[f"REM{i:03}"] = "Projector Remote"
    return mapping.get(code, "Unknown Item")


def get_last_issue(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT professor_id, professor_name, action FROM issued_items WHERE item_code=? ORDER BY id DESC LIMIT 1",
        (code,),
    )
    row = c.fetchone()
    conn.close()
    return row


# ---------------------- ROUTES ----------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/adminlogin", methods=["GET", "POST"])
def adminlogin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["adminlogged_in"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("adminlogin.html", error="Incorrect password.")
    return render_template("adminlogin.html")


@app.route("/admin")
def admin():
    if not session.get("adminlogged_in"):
        return redirect(url_for("adminlogin"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM issued_items ORDER BY id DESC")
    records = c.fetchall()
    conn.close()
    return render_template("admin.html", records=records)


@app.route("/logout")
def logout():
    session.pop("adminlogged_in", None)
    return redirect(url_for("adminlogin"))


@app.route("/get_professor/<prof_id>")
def get_professor(prof_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, department, email FROM professors WHERE id = ?", (prof_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({"found": True, "name": row[0], "department": row[1], "email": row[2]})
    return jsonify({"found": False})


@app.route("/get_item_name/<item_code>")
def get_item_name_route(item_code):
    return jsonify({"item_name": get_item_name(item_code)})


@app.route("/log_item", methods=["POST"])
def log_item():
    try:
        data = request.get_json()
        professor_id = data.get("professor_id")
        professor_name = data.get("professor_name")
        department = data.get("department")
        item_code = data.get("item_code")
        action = data.get("action")
        item_name = get_item_name(item_code)

        india = pytz.timezone("Asia/Kolkata")
        timestamp = datetime.datetime.now(india).strftime("%Y-%m-%d %H:%M:%S")

        if not all([professor_id, professor_name, department, item_code, action]):
            return jsonify({"status": "error", "message": "Missing required fields."})

        last_issue = get_last_issue(item_code)

        if action.lower() == "issue":
            if last_issue and last_issue[2].lower() == "issue":
                return jsonify({
                    "status": "error",
                    "message": f"⚠️ {item_name} ({item_code}) is already issued by {last_issue[1]} ({last_issue[0]}) and not yet returned!"
                })
        elif action.lower() == "return":
            if not last_issue:
                return jsonify({"status": "error", "message": f"{item_name} has not been issued yet."})
            if last_issue[2].lower() == "return":
                return jsonify({"status": "error", "message": f"{item_name} is already returned."})
            if last_issue[0] != professor_id:
                return jsonify({"status": "error", "message": f"This item was issued by {last_issue[1]} ({last_issue[0]}). Only they can return it."})

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO issued_items (professor_id, professor_name, department, item_code, item_name, action, issue_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (professor_id, professor_name, department, item_code, item_name, action.capitalize(), timestamp))
        conn.commit()
        conn.close()

        # Optional background reminder email
        def check_item_return():
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                    SELECT professor_name, item_name, item_code, professor_id, action
                    FROM issued_items WHERE item_code=? ORDER BY id DESC LIMIT 1
                """, (item_code,))
                last = c.fetchone()
                conn.close()

                if last and last[4].lower() == "issue":
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT email FROM professors WHERE id=?", (last[3],))
                    prof = c.fetchone()
                    conn.close()
                    if prof and prof[0]:
                        send_email_alert(prof[0], last[0], last[1], last[2], timestamp)
            except Exception as e:
                print("❌ Email scheduler error:", e)

        scheduler.add_job(func=check_item_return, trigger="date",
                          run_date=datetime.datetime.now() + datetime.timedelta(hours=2))

        return jsonify({"status": "success", "message": f"✅ {action.capitalize()} logged successfully!"})

    except Exception as e:
        print("❌ Error in /log_item:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/delete_entry/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    if not session.get("adminlogged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"})
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM issued_items WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Entry deleted successfully!"})


@app.route("/delete_all", methods=["DELETE"])
def delete_all_entries():
    if not session.get("adminlogged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"})
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM issued_items")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "All entries deleted successfully!"})


@app.route("/download_logs")
def download_logs():
    if not session.get("adminlogged_in"):
        return redirect(url_for("adminlogin"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM issued_items ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Faculty ID", "Faculty Name", "Department", "Item Code", "Item Name", "Action", "Date & Time"])
    for row in rows:
        writer.writerow(row)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="item_logs.csv")


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=10000)
