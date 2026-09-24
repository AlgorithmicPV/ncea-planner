import datetime
import json
import os
import uuid

import streamlit as st
from streamlit_calendar import calendar


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "data/tasks.json"

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

today = datetime.date.today()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 18px;
        border-radius: 14px;
    }

    div[data-testid="stMetric"] label {
        font-size: 0.9rem;
    }

    .stButton > button {
        border-radius: 9px;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.15);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATA FUNCTIONS
# =========================================================


def default_data():
    return {
        "tasks": [],
        "calendar_end_date": today + datetime.timedelta(days=30),
    }


def normalize_task(task):
    """
    Makes old saved tasks compatible with this version.
    """

    task.setdefault("id", str(uuid.uuid4()))
    task.setdefault("title", "Untitled Task")
    task.setdefault("start", str(today))
    task.setdefault("allDay", True)
    task.setdefault("completed", False)
    task.setdefault("notes", "")

    # Remove old subject/priority data if present
    task.pop("subject", None)
    task.pop("priority", None)

    return task


def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        exam_date = data.get("calendar_end_date")

        if exam_date:
            exam_date = datetime.datetime.strptime(
                exam_date,
                "%Y-%m-%d",
            ).date()
        else:
            exam_date = today + datetime.timedelta(days=30)

        tasks = [normalize_task(task) for task in data.get("tasks", [])]

        return {
            "tasks": tasks,
            "calendar_end_date": exam_date,
        }

    except (json.JSONDecodeError, OSError, ValueError):
        st.warning("Could not read the saved task file. Starting with a new planner.")

        return default_data()


def save_data():
    data_to_save = {
        "tasks": st.session_state.tasks,
        "calendar_end_date": st.session_state.calendar_end_date.strftime("%Y-%m-%d"),
    }

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data_to_save,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# SESSION STATE
# =========================================================

if "data_loaded" not in st.session_state:
    saved_data = load_data()

    st.session_state.tasks = saved_data["tasks"]

    st.session_state.calendar_end_date = saved_data["calendar_end_date"]

    st.session_state.data_loaded = True


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def task_date(task):
    try:
        return datetime.datetime.strptime(
            task["start"],
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return today


def sorted_tasks(tasks):
    """
    Order:
    1. Incomplete tasks first
    2. Earliest due date first
    3. Alphabetical
    """

    return sorted(
        tasks,
        key=lambda task: (
            task["completed"],
            task_date(task),
            task["title"].lower(),
        ),
    )


def days_until(date):
    return (date - today).days


def due_text(task):

    date = task_date(task)

    difference = days_until(date)

    if difference < 0:
        return f"⚠️ Overdue by {abs(difference)} day(s)"

    if difference == 0:
        return "📌 Due today"

    if difference == 1:
        return "Due tomorrow"

    return f"Due in {difference} days"


def delete_task(task_id):

    st.session_state.tasks = [
        task for task in st.session_state.tasks if task["id"] != task_id
    ]

    save_data()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("📚 Study Planner")

    st.caption("Plan your tasks and stay on track for exams.")

    st.divider()

    # -----------------------------------------------------
    # ADD TASK
    # -----------------------------------------------------

    st.subheader("➕ Add Task")

    task_title = st.text_input(
        "Task",
        placeholder="e.g. Complete projectile revision",
    )

    task_date_input = st.date_input(
        "Due Date",
        value=today,
        min_value=today,
        max_value=st.session_state.calendar_end_date,
    )

    task_notes = st.text_area(
        "Notes",
        placeholder="Optional notes...",
        height=90,
    )

    if st.button(
        "➕ Add Task",
        use_container_width=True,
        type="primary",
    ):
        clean_title = task_title.strip()

        if not clean_title:
            st.error("Please enter a task title.")

        else:
            new_task = {
                "id": str(uuid.uuid4()),
                "title": clean_title,
                "start": str(task_date_input),
                "allDay": True,
                "completed": False,
                "notes": task_notes.strip(),
            }

            st.session_state.tasks.append(new_task)

            save_data()

            st.success("Task added!")

            st.rerun()

    st.divider()

    # -----------------------------------------------------
    # EXAM SETTINGS
    # -----------------------------------------------------

    st.subheader("⚙️ Exam Settings")

    new_exam_date = st.date_input(
        "Exams start on",
        value=st.session_state.calendar_end_date,
        min_value=today,
    )

    if new_exam_date != st.session_state.calendar_end_date:
        st.session_state.calendar_end_date = new_exam_date

        save_data()

        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title("📚 Exam Study Planner")

st.caption("Organise your workload, track deadlines and stay prepared for your exams.")

exam_date = st.session_state.calendar_end_date

days_left = (exam_date - today).days

weeks_left = days_left / 7 if days_left > 0 else 0


# =========================================================
# STATISTICS
# =========================================================

total_tasks = len(st.session_state.tasks)

completed_tasks = sum(1 for task in st.session_state.tasks if task["completed"])

remaining_tasks = total_tasks - completed_tasks

today_tasks = sum(
    1
    for task in st.session_state.tasks
    if not task["completed"] and task_date(task) == today
)

completion_percentage = completed_tasks / total_tasks if total_tasks else 0


# =========================================================
# COUNTDOWN
# =========================================================

if days_left > 0:
    st.info(
        f"🎯 **Exams start on "
        f"{exam_date.strftime('%A, %d %B %Y')}** — "
        f"you have **{days_left} days** remaining."
    )

elif days_left == 0:
    st.warning("🎓 Your exams start today!")


# =========================================================
# METRICS
# =========================================================

metric1, metric2, metric3, metric4, metric5 = st.columns(5)

metric1.metric(
    "📅 Days Left",
    days_left,
)

metric2.metric(
    "🗓️ Weeks Left",
    f"{weeks_left:.1f}",
)

metric3.metric(
    "📚 Total Tasks",
    total_tasks,
)

metric4.metric(
    "⏳ Remaining",
    remaining_tasks,
)

metric5.metric(
    "📌 Due Today",
    today_tasks,
)


# =========================================================
# PROGRESS
# =========================================================

st.write("")

progress_col1, progress_col2 = st.columns([4, 1])

with progress_col1:
    st.write("**Overall Progress**")

    st.progress(completion_percentage)

with progress_col2:
    st.metric(
        "Completed",
        f"{completion_percentage * 100:.0f}%",
    )


# =========================================================
# TABS
# =========================================================

st.write("")

calendar_tab, tasks_tab = st.tabs(
    [
        "📅 Calendar",
        "📋 My Tasks",
    ]
)


# =========================================================
# CALENDAR TAB
# =========================================================

with calendar_tab:
    st.subheader("Study Calendar")

    calendar_events = []

    for task in st.session_state.tasks:
        prefix = "✓ " if task["completed"] else ""

        calendar_events.append(
            {
                "id": task["id"],
                "title": f"{prefix}{task['title']}",
                "start": task["start"],
                "allDay": True,
            }
        )

    calendar_options = {
        "initialView": "dayGridMonth",
        "height": 650,
        "firstDay": 1,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek",
        },
        "buttonText": {
            "today": "Today",
            "month": "Month",
            "week": "Week",
        },
        "validRange": {
            "end": (
                st.session_state.calendar_end_date + datetime.timedelta(days=1)
            ).strftime("%Y-%m-%d"),
        },
        "dayMaxEvents": True,
    }

    calendar(
        events=calendar_events,
        options=calendar_options,
        key="study_calendar",
    )


# =========================================================
# TASK TAB
# =========================================================

with tasks_tab:
    st.subheader("My Tasks")

    # -----------------------------------------------------
    # FILTER
    # -----------------------------------------------------

    filter_col1, filter_col2 = st.columns([1, 2])

    status_filter = filter_col1.selectbox(
        "Show",
        [
            "All Tasks",
            "Incomplete",
            "Completed",
        ],
    )

    search_text = filter_col2.text_input(
        "Search",
        placeholder="Search tasks...",
    )

    filtered_tasks = st.session_state.tasks.copy()

    if status_filter == "Incomplete":
        filtered_tasks = [task for task in filtered_tasks if not task["completed"]]

    elif status_filter == "Completed":
        filtered_tasks = [task for task in filtered_tasks if task["completed"]]

    if search_text:
        filtered_tasks = [
            task
            for task in filtered_tasks
            if search_text.lower() in task["title"].lower()
            or search_text.lower() in task.get("notes", "").lower()
        ]

    filtered_tasks = sorted_tasks(filtered_tasks)

    st.write("")

    # -----------------------------------------------------
    # TASK LIST
    # -----------------------------------------------------

    if not filtered_tasks:
        st.info("No tasks match your current filter.")

    else:
        for task in filtered_tasks:
            date = task_date(task)

            task_id = task["id"]

            is_overdue = date < today and not task["completed"]

            with st.container(border=True):
                (
                    col_check,
                    col_main,
                    col_date,
                    col_edit,
                    col_delete,
                ) = st.columns(
                    [0.07, 0.50, 0.20, 0.11, 0.12],
                    vertical_alignment="center",
                )

                # -----------------------------------------
                # COMPLETE
                # -----------------------------------------

                completed = col_check.checkbox(
                    "Done",
                    value=task["completed"],
                    key=f"check_{task_id}",
                    label_visibility="collapsed",
                )

                if completed != task["completed"]:
                    for stored_task in st.session_state.tasks:
                        if stored_task["id"] == task_id:
                            stored_task["completed"] = completed

                            break

                    save_data()

                    st.rerun()

                # -----------------------------------------
                # TASK INFO
                # -----------------------------------------

                if task["completed"]:
                    col_main.markdown(f"~~**{task['title']}**~~")

                else:
                    col_main.markdown(f"**{task['title']}**")

                if task.get("notes"):
                    col_main.caption(f"📝 {task['notes']}")

                # -----------------------------------------
                # DATE
                # -----------------------------------------

                col_date.write(f"📅 {date.strftime('%d %b %Y')}")

                if task["completed"]:
                    col_date.caption("✅ Completed")

                elif is_overdue:
                    col_date.error(due_text(task))

                else:
                    col_date.caption(due_text(task))

                # -----------------------------------------
                # EDIT
                # -----------------------------------------

                if col_edit.button(
                    "✏️ Edit",
                    key=f"edit_{task_id}",
                    use_container_width=True,
                ):
                    st.session_state.editing = task_id

                    st.rerun()

                # -----------------------------------------
                # DELETE
                # -----------------------------------------

                if col_delete.button(
                    "🗑️",
                    key=f"delete_{task_id}",
                    use_container_width=True,
                ):
                    st.session_state["delete_confirmation"] = task_id

                    st.rerun()


# =========================================================
# DELETE CONFIRMATION
# =========================================================

if "delete_confirmation" in st.session_state:
    task_id = st.session_state.delete_confirmation

    task_to_delete = next(
        (task for task in st.session_state.tasks if task["id"] == task_id),
        None,
    )

    if task_to_delete:
        st.divider()

        st.warning(f"Delete **{task_to_delete['title']}**?")

        delete_yes, delete_no, _ = st.columns([1, 1, 4])

        if delete_yes.button(
            "Yes, delete",
            type="primary",
        ):
            delete_task(task_id)

            del st.session_state.delete_confirmation

            st.rerun()

        if delete_no.button("Cancel"):
            del st.session_state.delete_confirmation

            st.rerun()


# =========================================================
# EDIT TASK
# =========================================================

if "editing" in st.session_state:
    editing_id = st.session_state.editing

    editing_task = next(
        (task for task in st.session_state.tasks if task["id"] == editing_id),
        None,
    )

    if editing_task:
        st.divider()

        st.subheader("✏️ Edit Task")

        with st.form("edit_task_form"):
            new_title = st.text_input(
                "Task",
                value=editing_task["title"],
            )

            existing_date = task_date(editing_task)

            safe_date = max(
                existing_date,
                today,
            )

            new_date = st.date_input(
                "Due Date",
                value=safe_date,
                min_value=today,
                max_value=st.session_state.calendar_end_date,
            )

            new_notes = st.text_area(
                "Notes",
                value=editing_task.get(
                    "notes",
                    "",
                ),
            )

            save_button, cancel_button = st.columns(2)

            save_changes = save_button.form_submit_button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True,
            )

            cancel_edit = cancel_button.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

            if save_changes:
                if not new_title.strip():
                    st.error("Task title cannot be empty.")

                else:
                    editing_task["title"] = new_title.strip()

                    editing_task["start"] = str(new_date)

                    editing_task["notes"] = new_notes.strip()

                    save_data()

                    del st.session_state.editing

                    st.rerun()

            if cancel_edit:
                del st.session_state.editing

                st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption("📚 Study Planner • Stay consistent and make every study day count.")

