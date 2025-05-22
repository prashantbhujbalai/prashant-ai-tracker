
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Prashant AI Tracker", layout="wide")
st.title("🤖 Prashant AI Tracker")
st.markdown("AI-powered tool to track tax compliance and send smart reminders.")

# Initialize session state
if 'clients' not in st.session_state:
    st.session_state.clients = []

# Helper to get fixed due dates per tax type
def get_due_date(tax_type):
    today = datetime.date.today()
    year = today.year
    if tax_type == "GST":
        return datetime.date(year, today.month % 12 + 1, 20)
    elif tax_type == "TDS":
        return datetime.date(year, today.month % 12 + 1, 7)
    elif tax_type == "ROC":
        return datetime.date(year, 9, 30)
    elif tax_type == "ITR":
        return datetime.date(year, 7, 31)
    else:
        return today + datetime.timedelta(days=30)

# --- Sidebar: Add Client ---
st.sidebar.header("➕ Add New Client")
with st.sidebar.form(key="add_client_form"):
    name = st.text_input("Client Name")
    email = st.text_input("Email")
    pan = st.text_input("PAN Number (optional)")
    gstin = st.text_input("GSTIN (optional)")
    tax_types = st.multiselect("Select Tax Types", ["GST", "TDS", "ROC", "ITR"])
    freq = st.selectbox("Filing Frequency", ["Monthly", "Quarterly", "Annually"])
    submit = st.form_submit_button("Add Client")

    if submit and name and email:
        due_dates = {tax: get_due_date(tax).strftime('%d %b %Y') for tax in tax_types}
        st.session_state.clients.append({
            "name": name,
            "email": email,
            "pan": pan,
            "gstin": gstin,
            "tax_types": tax_types,
            "frequency": freq,
            "due_dates": due_dates
        })
        st.success(f"Client '{name}' added successfully!")

# --- Dashboard ---
st.header("📊 Client Dashboard")
if st.session_state.clients:
    for client in st.session_state.clients:
        with st.expander(f"Client: {client['name']}"):
            st.write(f"📧 **Email:** {client['email']}")
            if client['pan']:
                st.write(f"🆔 **PAN:** {client['pan']}")
            if client['gstin']:
                st.write(f"🔢 **GSTIN:** {client['gstin']}")
            st.write(f"📅 **Filing Frequency:** {client['frequency']}")
            st.write("🗓️ **Due Dates:**")
            for tax, due in client['due_dates'].items():
                st.write(f"- {tax}: **{due}**")
            st.write("💬 **WhatsApp Reminder Preview:**")
            for tax, due in client['due_dates'].items():
                st.info(f"Reminder: Your {tax} filing is due on {due}. – Prashant AI Tracker")
else:
    st.info("No clients added yet. Use the sidebar to add one.")

# --- Chatbot Simulation ---
st.header("💬 Chat with AI Tracker")
user_query = st.text_input("Ask something like: 'What’s due this week?'")

if user_query:
    today = datetime.date.today()
    this_week = today + datetime.timedelta(days=7)
    found = False
    for client in st.session_state.clients:
        for tax, due in client['due_dates'].items():
            due_date = datetime.datetime.strptime(due, '%d %b %Y').date()
            if today <= due_date <= this_week:
                st.success(f"{client['name']} – {tax} is due on {due}")
                found = True
    if not found:
        st.warning("No due items in the next 7 days.")
