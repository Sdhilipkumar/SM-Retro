import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

firebase_creds = dict(st.secrets["firebase"])  # ✅ convert to dict

# --- Firestore Setup ---
# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)

db = firestore.client()
collection = db.collection("feedback")

# --- Function to save feedback ---
def save_feedback(sprint, team, member_name, responses):
    doc = {
        "sprint": sprint,
        "team": team,
        "member_name": member_name,
        "responses": responses,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    collection.add(doc)

# --- Streamlit UI ---
st.title("Sprint Feedback Survey")

sprint = st.selectbox("Select Sprint", ["Sprint 1", "Sprint 2", "Sprint 3","Sprint 4"])
team = st.selectbox("Select Team", ["Vindhya", "CIS", "Darwin"])
member_name = st.text_input("Your Name")

questions = [
    "How clear were sprint goals?",
    "How was collaboration?",
    "Was work fairly distributed?",
    "Were blockers resolved quickly?",
    "Was code review effective?",
    "Was sprint planning useful?",
    "Was daily standup effective?",
    "Was testing sufficient?",
    "How was team morale?",
    "How satisfied overall?"
]

responses = []
for i, q in enumerate(questions, start=1):
    responses.append(st.radio(q, ["Poor", "Average", "Good", "Excellent"], key=f"q{i}"))

if st.button("Submit Feedback"):
    if member_name:
        save_feedback(sprint, team, member_name, responses)
        st.success("✅ Thank you! Your feedback has been saved.")
    else:
        st.error("Please enter your name.")

# --- Admin view ---
if st.checkbox("Show All Feedback Results"):
    docs = collection.stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        row = {
            "sprint": d["sprint"],
            "team": d["team"],
            "member_name": d["member_name"],
            "submitted_at": d["submitted_at"],
        }
        # Flatten responses
        for i, r in enumerate(d["responses"], start=1):
            row[f"q{i}"] = r
        data.append(row)

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.info("No feedback submitted yet.")
