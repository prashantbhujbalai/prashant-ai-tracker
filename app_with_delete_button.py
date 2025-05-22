
import streamlit as st
import pandas as pd
import datetime
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Prashant AI Tracker", layout="wide")
st.title("🤖 Prashant AI Tracker")
st.markdown("AI-powered tool to track tax compliance and send smart reminders.")

# Set your email credentials here
SENDER_EMAIL = "casbassociate@gmail.com"
SENDER_PASSWORD = "hytm flxs ecou zarp"

def send_reminder_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return str(e)

# Connect to DB
conn = sqlite3.connect("tracker.db")
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, pan TEXT, gstin TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS compliances (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, type TEXT, frequency TEXT, due_date TEXT, status TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, compliance_id INTEGER, date_sent TEXT, channel TEXT, message TEXT)")
conn.commit()

# Add client form
st.sidebar.header("➕ Add New Client")
with st.sidebar.form("client_form"):
    name = st.text_input("Client Name")
    email = st.text_input("Email")
    pan = st.text_input("PAN")
    gstin = st.text_input("GSTIN")
    tax_types = st.multiselect("Compliance Types", ["GST", "TDS", "ROC", "ITR"])
    freq = st.selectbox("Filing Frequency", ["Monthly", "Quarterly", "Annually"])
    submit = st.form_submit_button("Add Client")

    if submit and name and email:
        c.execute("INSERT INTO clients (name, email, pan, gstin) VALUES (?, ?, ?, ?)", (name, email, pan, gstin))
        client_id = c.lastrowid
        today = datetime.date.today()
        for tax in tax_types:
            if tax == "GST":
                due = datetime.date(today.year, today.month % 12 + 1, 20)
            elif tax == "TDS":
                due = datetime.date(today.year, today.month % 12 + 1, 7)
            elif tax == "ROC":
                due = datetime.date(today.year, 9, 30)
            elif tax == "ITR":
                due = datetime.date(today.year, 7, 31)
            else:
                due = today + datetime.timedelta(days=30)
            c.execute("INSERT INTO compliances (client_id, type, frequency, due_date, status) VALUES (?, ?, ?, ?, ?)",
                      (client_id, tax, freq, due.strftime('%Y-%m-%d'), "Pending"))
        conn.commit()
        st.success(f"Client {name} added.")

# Dashboard display
st.header("📊 Client Dashboard")
c.execute("SELECT * FROM clients")
clients = c.fetchall()
for client in clients:
    client_id, name, email, pan, gstin = client
    with st.expander(f"{name} ({email})"):
        st.write(f"PAN: {pan}, GSTIN: {gstin}")
        if st.button(f"🗑️ Delete Client: {name}", key=f"delete_{client_id}"):
            c.execute("DELETE FROM reminders WHERE compliance_id IN (SELECT id FROM compliances WHERE client_id = ?)", (client_id,))
            c.execute("DELETE FROM compliances WHERE client_id = ?", (client_id,))
            c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            st.warning(f"Client {name} and all associated data deleted.")
            st.rerun()
        c.execute("SELECT * FROM compliances WHERE client_id = ?", (client_id,))
        compliances = c.fetchall()
        for comp in compliances:
            comp_id, _, tax_type, freq, due_date, status = comp
            st.write(f"🗓 {tax_type} | Due: {due_date} | Status: {status}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📧 Email: {tax_type}", key=f"email_{comp_id}"):
                    subject = f"Reminder: {tax_type} filing due on {due_date}"
                    message = f"Dear {name},\n\nThis is a reminder that your {tax_type} filing is due on {due_date}."
                    result = send_reminder_email(email, subject, message)
                    if result == True:
                        st.success("✅ Email sent.")
                    else:
                        st.error(f"❌ Email error: {result}")
            with col2:
                if st.button(f"✅ Mark Filed: {tax_type}", key=f"filed_{comp_id}"):
                    c.execute("UPDATE compliances SET status = 'Filed' WHERE id = ?", (comp_id,))
                    conn.commit()
                    st.success(f"{tax_type} marked as Filed.")

# Chatbot
st.header("💬 Ask the Tracker")
query = st.text_input("Try: 'What’s due this week?'")
if query:
    today = datetime.date.today()
    week = today + datetime.timedelta(days=7)
    found = False
    c.execute("SELECT clients.name, compliances.type, compliances.due_date FROM compliances JOIN clients ON clients.id = compliances.client_id WHERE compliances.status != 'Filed'")
    for row in c.fetchall():
        cname, ctype, cdate = row
        due = datetime.datetime.strptime(cdate, "%Y-%m-%d").date()
        if today <= due <= week:
            st.success(f"{cname} - {ctype} due on {due.strftime('%d %b %Y')}")
            found = True
    if not found:
        st.warning("No filings due this week.")

conn.close()
