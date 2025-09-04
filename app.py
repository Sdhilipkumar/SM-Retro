import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

# ----------------------
# DB Setup
# ----------------------
DB_PATH = Path(__file__).parent / "feedback.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint TEXT NOT NULL,
            team_name TEXT NOT NULL,
            member_name TEXT NOT NULL,
            q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT,
            q6 TEXT, q7 TEXT, q8 TEXT, q9 TEXT, q10 TEXT,
            submitted_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def save_feedback(sprint, team_name, member_name, responses):
    if len(responses) != 10:
        raise ValueError("Expected 10 responses")
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO feedback
        (sprint, team_name, member_name, q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,submitted_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (sprint, team_name, member_name, *responses, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

# Ensure DB exists before UI renders
init_db()

# ----------------------
# Streamlit UI
# ----------------------
st.title("Sprint Feedback (10 Questions)")

# Sprint dropdown
sprint_options = ["Sprint-1", "Sprint-2", "Sprint-3", "Sprint-4"]
sprint = st.selectbox("Select Sprint", sprint_options)

# Team dropdown
team_options = ["Vindhya", "Sahyadri", "Darwin", "CIS","NSS","Tejas","Ekalavya","iPrint-Constructor"]
team_name = st.selectbox("Select Team", team_options)

# Member name free text
member_name = st.text_input("Your Name")

st.write("### Please answer all questions")

questions = [
    "How clear were the sprint goals?",
    "How well did the team collaborate?",
    "How satisfied are you with communication?",
    "How manageable was the workload?",
    "How well were blockers resolved?",
    "How useful were sprint ceremonies?",
    "How confident are you in delivering sprint commitments?",
    "How do you rate code quality this sprint?",
    "How effective was testing & QA?",
    "How satisfied are you overall with this sprint?",
]

options = ["Poor", "Average", "Good", "Excellent"]

# render radios
responses = []
for i, q in enumerate(questions, start=1):
    response = st.radio(
        f"Q{i}. {q}",
        options,
        key=f"q{i}",
        index=0,  # default = "Poor"
    )
    responses.append(response)

# Submit button
if st.button("Submit Feedback"):
    if not member_name.strip():
        st.error("Please enter Your name.")
    else:
        try:
            save_feedback(sprint, team_name, member_name.strip(), responses)
            st.success("✅ Feedback submitted successfully!")
            # Clear state and reset form
            for i in range(1, 11):
                if f"q{i}" in st.session_state:
                    del st.session_state[f"q{i}"]
            st.rerun()
        except Exception as e:
            st.error(f"Database error: {e}")

st.write("---")

# ----------------------
# Admin / Viewer section
# ----------------------
with st.expander("Admin: View / Download Feedback"):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM feedback ORDER BY submitted_at DESC", conn)
    conn.close()

    if df.empty:
        st.info("No feedback entries yet.")
    else:
        sprint_list = ["All"] + sorted(df["sprint"].dropna().unique().tolist())
        selected_sprint = st.selectbox("Filter by Sprint", sprint_list)

        team_list = ["All"] + sorted(df["team_name"].dropna().unique().tolist())
        selected_team = st.selectbox("Filter by Team", team_list)

        view_df = df.copy()
        if selected_sprint != "All":
            view_df = view_df[view_df["sprint"] == selected_sprint]
        if selected_team != "All":
            view_df = view_df[view_df["team_name"] == selected_team]

        st.dataframe(view_df, use_container_width=True)

        csv = view_df.to_csv(index=False)
        st.download_button(
            "Download CSV for these results",
            csv,
            file_name=f"feedback_{selected_sprint}_{selected_team}.csv",
            mime="text/csv",
        )

        if st.checkbox("Show per-question counts (summary)"):
            cols = [f"q{i}" for i in range(1, 11)]
            for col, q in zip(cols, questions):
                st.markdown(f"**{q}**")
                counts = view_df[col].value_counts().reindex(options, fill_value=0)
                st.table(pd.DataFrame({"option": counts.index, "count": counts.values}))
