import datetime
import json
import os
import streamlit as st
from streamlit_calendar import calendar

st.title("To-Do")

# Filepath for saving data permanently on your computer
DATA_FILE = "data/tasks.json"

# Ensure the data directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


def load_data():
    """Load tasks and settings from a JSON file if it exists."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if "calendar_end_date" in data:
                    data["calendar_end_date"] = datetime.datetime.strptime(
                        data["calendar_end_date"], "%Y-%m-%d"
                    ).date()
                return data
        except Exception:
            pass
    # Fallback default values if the file doesn't exist yet
    return {
        "tasks": [],
        "calendar_end_date": datetime.date.today() + datetime.timedelta(days=30),
    }


def save_data():
    """Save tasks and settings to a JSON file."""
    data_to_save = {
        "tasks": st.session_state.tasks,
        "calendar_end_date": st.session_state.calendar_end_date.strftime("%Y-%m-%d"),
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data_to_save, f, indent=4)


# Initialize session state with your saved data when the app first loads
if "data_loaded" not in st.session_state:
    saved_data = load_data()
    st.session_state.tasks = saved_data["tasks"]
    st.session_state.calendar_end_date = saved_data["calendar_end_date"]
    st.session_state.data_loaded = True

# Track today's date dynamically
today = datetime.date.today()

# Sidebar for Configuration
st.sidebar.header("Exams start on")
new_end_date = st.sidebar.date_input(
    "Your Exams start on",
    value=st.session_state.calendar_end_date,
    min_value=today,  # Prevents selecting an exam start date in the past
)

if new_end_date != st.session_state.calendar_end_date:
    st.session_state.calendar_end_date = new_end_date
    save_data()

st.sidebar.write("---")
st.sidebar.header("Add Task")
task_title = st.sidebar.text_input("Task Title")
task_date = st.sidebar.date_input(
    "Due Date",
    value=today,
    min_value=today,  # Prevents picking past dates in the picker interface
    max_value=st.session_state.calendar_end_date,
)

if st.sidebar.button("Add Task"):
    if task_title:
        if task_date < today:
            st.sidebar.error("Cannot add tasks to past dates!")
        elif task_date > st.session_state.calendar_end_date:
            st.sidebar.error(
                f"Cannot add task! Date exceeds the calendar limit ({st.session_state.calendar_end_date})."
            )
        else:
            new_task = {
                "id": str(len(st.session_state.tasks) + 1),
                "title": task_title,
                "start": str(task_date),
                "allDay": True,
                "completed": False,
            }
            st.session_state.tasks.append(new_task)
            save_data()
            st.success("Task added!")
            st.rerun()

# Display Calendar View
st.subheader("Calendar View")
calendar_events = [
    {
        "title": f"[{'X' if t['completed'] else ' '}] {t['title']}",
        "start": t["start"],
        "allDay": t["allDay"],
    }
    for t in st.session_state.tasks
]

calendar_options = {
    "initialView": "dayGridMonth",
    "height": "auto",  # Helps prevent full-height container layout overflow
    "firstDay": 1,  # CHANGED: Sets the first day of the week to 1 (Monday)
    "validRange": {
        "start": today.strftime("%Y-%m-%d"),  # Hides/greys out past dates automatically
        "end": (
            st.session_state.calendar_end_date + datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d"),
    },
}

# Wrapper style frame preventing container resizing issue
st.markdown(
    """
    <style>
        .calendar-container iframe {
            max-height: 600px !important;
            width: 100% !important;
        }
    </style>
    <div class="calendar-container">
    """,
    unsafe_allow_html=True,
)

calendar(events=calendar_events, options=calendar_options)

st.markdown("</div>", unsafe_allow_html=True)

# List View for Check, Edit, Delete
st.subheader("Task List")
if not st.session_state.tasks:
    st.write("No tasks yet.")
else:
    for i, task in enumerate(st.session_state.tasks):
        col1, col2, col3, col4 = st.columns([0.1, 0.5, 0.2, 0.2])

        completed = col1.checkbox("", value=task["completed"], key=f"check_{i}")
        if completed != task["completed"]:
            st.session_state.tasks[i]["completed"] = completed
            save_data()
            st.rerun()

        if task["completed"]:
            col2.markdown(f"~~{task['title']}~~ ({task['start']})")
        else:
            col2.write(f"{task['title']} ({task['start']})")

        if col3.button("Edit", key=f"edit_{i}"):
            st.session_state.editing = i

        if col4.button("Delete", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_data()
            st.rerun()

    # Edit form if edit is clicked
    if "editing" in st.session_state:
        idx = st.session_state.editing
        st.write("---")
        st.subheader("Edit Task")
        new_title = st.text_input(
            "New Title", value=st.session_state.tasks[idx]["title"]
        )
        current_task_date = datetime.datetime.strptime(
            st.session_state.tasks[idx]["start"], "%Y-%m-%d"
        ).date()

        # Safely defaults to today if the existing task date has slipped into the past
        edit_default_date = max(current_task_date, today)

        new_date = st.date_input(
            "New Date",
            value=edit_default_date,
            min_value=today,
            max_value=st.session_state.calendar_end_date,
        )

        if st.button("Save Changes"):
            if new_date > st.session_state.calendar_end_date:
                st.error("Cannot update task! New date exceeds the calendar limit.")
            elif new_date < today:
                st.error("Cannot shift tasks back into past dates.")
            else:
                st.session_state.tasks[idx]["title"] = new_title
                st.session_state.tasks[idx]["start"] = str(new_date)
                del st.session_state.editing
                save_data()
                st.success("Task updated!")
                st.rerun()
