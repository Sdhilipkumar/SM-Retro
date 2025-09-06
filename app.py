import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# Remove top padding & reduce margins
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📋 Retrospective Survey")

# --- Firebase Setup ---
firebase_creds = dict(st.secrets["firebase"])

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)

db = firestore.client()
collection = db.collection("feedback")

# --- Function to save feedback ---
def save_feedback(sprint, team, member_name, role, responses, comments):
    doc = {
        "sprint": sprint,
        "team": team,
        "member_name": member_name,
        "role": role,
        "responses": responses,
        "comments": comments,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    collection.add(doc)

# --- Streamlit UI ---
sprint = st.selectbox("Select Sprint", ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5"])
team = st.selectbox("Select Team", ["Sahyadri", "Vindhya", "Ekalavya", "Darwin", "Cheetahs", "Cumulus", "Tejas", "Constructors"])
role = st.selectbox("Select Role", ["Developer", "QA", "Scrum Master"])

# Show "Your Name" only for Devs & QA
member_name = None
if role in ["Developer", "QA"]:
    member_name = st.text_input("Your Name")

# Scrum Master password input
scrum_master_password_ok = False
if role == "Scrum Master":
    password = st.text_input("Enter Scrum Master Password", type="password")
    if password == "Scrum@123":   # <-- change to your secure password
        scrum_master_password_ok = True
    elif password:
        st.error("Invalid Scrum Master password")

# --- Feedback form (only for Devs & QA) ---
if role in ["Developer", "QA"]:
    questions = [
        "How clear were sprint goals?",
        "How was collaboration?",
        "Was work fairly distributed?",
        "Were blockers resolved quickly?",
        "Was code review effective?",
        "Was sprint planning useful?",
        "Was daily standup effective?",
        "How satisfied overall?"
    ]

    responses = []
    for i, q in enumerate(questions, start=1):
        responses.append(st.radio(q, ["Poor", "Average", "Good", "Excellent"], key=f"q{i}"))

    # --- Extra free-text comment box ---
    comments = st.text_area("Additional Comments (optional)")

    if st.button("Submit Feedback"):
        if member_name:
            save_feedback(sprint, team, member_name, role, responses, comments)
            st.success("✅ Thank you! Your feedback has been saved.")
        else:
            st.error("Please enter your name.")
    
# --- Admin view (only for Scrum Masters with correct password) ---
if role == "Scrum Master" and scrum_master_password_ok:
    if st.checkbox("Show My Team's Feedback"):
        docs = collection.stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            if d["team"] == team:  # Filter only SM's team
                row = {
                    "Sprint": d["sprint"],
                    "Team": d["team"],
                    "Member_name": d["member_name"],
                    "Role": d.get("role", "Unknown"),
                    "Submitted_at": d["submitted_at"],
                    "Comments": d.get("comments", "")
                }
                for i, r in enumerate(d["responses"], start=1):
                    row[f"Q{i}"] = r
                data.append(row)

        if data:
            df = pd.DataFrame(data)

            # Map questions for tooltips
            question_map = {
                "Q1": "How clear were sprint goals?",
                "Q2": "How was collaboration?",
                "Q3": "Was work fairly distributed?",
                "Q4": "Were blockers resolved quickly?",
                "Q5": "Was code review effective?",
                "Q6": "Was sprint planning useful?",
                "Q7": "Was daily standup effective?",
                "Q8": "How satisfied overall?"
            }

            st.dataframe(df, use_container_width=True)

            with st.expander("ℹ️ Show Question Legend"):
                for q, text in question_map.items():
                    st.markdown(f"- **{q}**: {text}")


        else:
            st.info("No feedback submitted yet for your team.")
