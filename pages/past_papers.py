import json
import os
import streamlit as st
from streamlit_quill import st_quill

st.set_page_config(layout="wide")
st.title("Completed Past Papers")

DATA_FILE = "data/past_papers.json"


def load_data():
    """Loads all things and their tables from a JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_data():
    """Saves all things and their tables to a JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.things_data, f, indent=4)


# Initialize data structure in session state
if "things_data" not in st.session_state:
    st.session_state.things_data = load_data()


# --- FREE POPUP DIALOG USING QUILL ---
@st.dialog("Edit Document Notes", width="large")
def open_notes_editor(thing_name, row_index):
    """Opens a modal overlay containing a 100% free API-free Quill Document Editor."""
    current_notes = st.session_state.things_data[thing_name][row_index]["notes"]

    st.write(f"Editing notes for row {row_index + 1} under **{thing_name}**:")

    # Quill open-source document component
    content = st_quill(
        value=current_notes,
        html=True,  # Keeps rich-text format matching your data layout
        key=f"quill_{thing_name}_{row_index}",
    )

    # FIXED: Added explicit layout specification argument '2'
    col1, col2 = st.columns(2)
    if col1.button("Save & Close", type="primary"):
        st.session_state.things_data[thing_name][row_index]["notes"] = content
        save_data()
        st.rerun()


# --- UI AREA: ADD NEW THING ---
st.subheader("What is your Exam?")
with st.form("add_thing_form", clear_on_submit=True):
    col1, col2 = st.columns(2)  # FIXED: Added specification argument '2'
    new_thing = col1.text_input(
        "Enter your exam:", placeholder="e.g., Mechanics, Waves"
    )
    submit_thing = col2.form_submit_button("Add Exam")

    if submit_thing and new_thing:
        new_thing_cleaned = new_thing.strip()
        if new_thing_cleaned and new_thing_cleaned not in st.session_state.things_data:
            st.session_state.things_data[new_thing_cleaned] = []
            save_data()
            st.success(f"Added '{new_thing_cleaned}'!")
            st.rerun()
        elif new_thing_cleaned in st.session_state.things_data:
            st.error("This Thing already exists.")

st.write("---")

# --- UI AREA: RENDER TABLES FOR EACH THING ---
if not st.session_state.things_data:
    st.info("No things added yet. Use the form above to get started!")
else:
    for thing_name, rows in list(st.session_state.things_data.items()):
        header_col, del_thing_col = st.columns(
            2
        )  # FIXED: Added specification argument '2'
        header_col.subheader(f"{thing_name}")

        if del_thing_col.button("Delete Exam", key=f"del_thing_{thing_name}"):
            del st.session_state.things_data[thing_name]
            save_data()
            st.rerun()

        # Custom interactive table headers
        t_col1, t_col2, t_col3, t_col4 = st.columns([1.5, 1, 3.5, 1])
        t_col1.markdown("**Year**")
        t_col2.markdown("**Done?**")
        t_col3.markdown("**Notes Preview**")
        t_col4.markdown("**Actions**")
        st.write("---")

        # Table Rows
        for i, row in enumerate(rows):
            r_col1, r_col2, r_col3, r_col4 = st.columns([1.5, 1, 3.5, 1])

            # 1. Year Input
            new_year = r_col1.text_input(
                "Year",
                value=row["year"],
                key=f"year_{thing_name}_{i}",
                label_visibility="collapsed",
            )
            if new_year != row["year"]:
                st.session_state.things_data[thing_name][i]["year"] = new_year
                save_data()

            # 2. Done Checkbox
            is_done = r_col2.checkbox(
                "Done",
                value=row["done"],
                key=f"done_{thing_name}_{i}",
                label_visibility="collapsed",
            )
            if is_done != row["done"]:
                st.session_state.things_data[thing_name][i]["done"] = is_done
                save_data()

            # 3. Notes Action Button (Strips basic HTML elements for snippet display)
            clean_text_preview = ""
            if row["notes"]:
                clean_text_preview = (
                    row["notes"]
                    .replace("<p>", "")
                    .replace("</p>", "")
                    .replace("<br>", "")[:40]
                )

            btn_label = (
                f"📝 Edit Notes ({clean_text_preview}...)"
                if clean_text_preview
                else "➕ Add Notes (Empty)"
            )

            if r_col3.button(
                btn_label, key=f"note_btn_{thing_name}_{i}", use_container_width=True
            ):
                open_notes_editor(thing_name, i)

            # 4. Delete Row Button
            if r_col4.button("❌", key=f"del_row_{thing_name}_{i}"):
                st.session_state.things_data[thing_name].pop(i)
                save_data()
                st.rerun()

        # Add Row utility below individual tables
        if st.button(f"Add New Row to {thing_name}", key=f"add_row_btn_{thing_name}"):
            st.session_state.things_data[thing_name].append(
                {"year": "2026", "done": False, "notes": ""}
            )
            save_data()
            st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
