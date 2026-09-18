import streamlit as st

todo_page = st.Page("pages/todo.py", title="Todo")
past_papers_page = st.Page("pages/past_papers.py", title="Past papers")
notes_page = st.Page("pages/notes.py", title="Notes")

pg = st.navigation(
    {
        "": [todo_page, past_papers_page, notes_page],
    }
)

pg.run()

# --- FOOTER SECTION ---
st.write("---")  # Adds a subtle horizontal divider line above the footer

# Custom CSS to center the text and give it a clean, muted look
st.markdown(
    """
    <style>
        .footer {
            position: relative;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: transparent;
            color: #888888; /* Muted gray text color */
            text-align: center;
            padding: 10px;
            font-size: 14px;
        }
    </style>
    <div class="footer">
        Made with streamlit by G.A.P. Vidunitha | © 2026 All Rights Reserved
    </div>
    """,
    unsafe_allow_html=True,
)
