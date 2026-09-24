import html
import json
import os
import re
import uuid
from datetime import datetime

import streamlit as st
from streamlit_quill import st_quill


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Past Papers",
    page_icon="📝",
    layout="wide",
)

st.title("📝 Completed Past Papers")
st.caption("Track past papers, completion progress, and revision notes.")

DATA_FILE = "data/past_papers.json"

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def generate_id():
    """Create a unique ID."""
    return str(uuid.uuid4())


def clean_html_preview(content, length=70):
    """Convert Quill HTML into a clean text preview."""

    if not content:
        return ""

    text = re.sub(r"<[^>]+>", " ", content)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return ""

    if len(text) > length:
        return text[:length] + "..."

    return text


def sort_papers(papers):
    """Sort papers newest year first."""

    def year_value(paper):
        try:
            return int(paper.get("year", 0))
        except (ValueError, TypeError):
            return 0

    return sorted(
        papers,
        key=year_value,
        reverse=True,
    )


def find_exam(exam_id):
    """Find an exam using its unique ID."""

    for exam in st.session_state.past_papers_data["exams"]:
        if exam["id"] == exam_id:
            return exam

    return None


def find_paper(exam, paper_id):
    """Find a paper inside an exam."""

    for paper in exam["papers"]:
        if paper["id"] == paper_id:
            return paper

    return None


# =========================================================
# DATA MIGRATION / LOADING
# =========================================================


def normalize_new_data(data):
    """
    Ensure all exams and papers have IDs.

    This also repairs malformed or partially migrated data.
    """

    data.setdefault("exams", [])

    used_exam_ids = set()
    used_paper_ids = set()

    for exam in data["exams"]:
        exam_id = str(exam.get("id", ""))

        if not exam_id or exam_id in used_exam_ids:
            exam["id"] = generate_id()

        used_exam_ids.add(exam["id"])

        exam.setdefault("name", "Untitled Exam")
        exam.setdefault("papers", [])

        for paper in exam["papers"]:
            paper_id = str(paper.get("id", ""))

            if not paper_id or paper_id in used_paper_ids:
                paper["id"] = generate_id()

            used_paper_ids.add(paper["id"])

            paper.setdefault("year", "")
            paper.setdefault("done", False)
            paper.setdefault("notes", "")

    return data


def load_data():

    if not os.path.exists(DATA_FILE):
        return {"exams": []}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        # -----------------------------------------
        # NEW FORMAT
        # -----------------------------------------

        if isinstance(data, dict) and "exams" in data:
            return normalize_new_data(data)

        # -----------------------------------------
        # OLD FORMAT
        # -----------------------------------------

        if isinstance(data, dict):
            return migrate_old_data(data)

    except (json.JSONDecodeError, OSError):
        st.error("Could not read your past papers file.")

    return {"exams": []}


def save_data():

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            st.session_state.past_papers_data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# SESSION STATE
# =========================================================

if "past_papers_data" not in st.session_state:
    st.session_state.past_papers_data = load_data()

    # Save once so old data is permanently migrated
    save_data()


# =========================================================
# DIALOGS
# =========================================================


@st.dialog(
    "📝 Edit Paper Notes",
    width="large",
)
def open_notes_editor(exam_id, paper_id):

    exam = find_exam(exam_id)

    if not exam:
        st.error("Exam could not be found.")
        return

    paper = find_paper(exam, paper_id)

    if not paper:
        st.error("Past paper could not be found.")
        return

    st.caption(f"{exam['name']} • {paper['year']}")

    content = st_quill(
        value=paper.get("notes", ""),
        html=True,
        key=f"quill_{exam_id}_{paper_id}",
    )

    save_col, cancel_col = st.columns(2)

    if save_col.button(
        "💾 Save & Close",
        type="primary",
        use_container_width=True,
    ):
        paper["notes"] = content or ""

        save_data()

        st.rerun()

    if cancel_col.button(
        "Cancel",
        use_container_width=True,
    ):
        st.rerun()


@st.dialog("✏️ Rename Exam")
def rename_exam_dialog(exam_id):

    exam = find_exam(exam_id)

    if not exam:
        return

    new_name = st.text_input(
        "Exam name",
        value=exam["name"],
    )

    col1, col2 = st.columns(2)

    if col1.button(
        "Save",
        type="primary",
        use_container_width=True,
    ):
        clean_name = new_name.strip()

        if not clean_name:
            st.error("Exam name cannot be empty.")

        else:
            duplicate = any(
                other_exam["name"].lower() == clean_name.lower()
                and other_exam["id"] != exam_id
                for other_exam in st.session_state.past_papers_data["exams"]
            )

            if duplicate:
                st.error("An exam with this name already exists.")

            else:
                exam["name"] = clean_name

                save_data()

                st.rerun()

    if col2.button(
        "Cancel",
        use_container_width=True,
    ):
        st.rerun()


@st.dialog("🗑️ Delete Exam")
def delete_exam_dialog(exam_id):

    exam = find_exam(exam_id)

    if not exam:
        return

    st.warning(f"Delete **{exam['name']}** and all of its past-paper records?")

    st.write("This cannot be undone.")

    col1, col2 = st.columns(2)

    if col1.button(
        "Delete Exam",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.past_papers_data["exams"] = [
            item
            for item in st.session_state.past_papers_data["exams"]
            if item["id"] != exam_id
        ]

        save_data()

        st.rerun()

    if col2.button(
        "Cancel",
        use_container_width=True,
    ):
        st.rerun()


# =========================================================
# OVERALL STATISTICS
# =========================================================

all_exams = st.session_state.past_papers_data["exams"]

total_papers = sum(len(exam["papers"]) for exam in all_exams)

completed_papers = sum(
    1 for exam in all_exams for paper in exam["papers"] if paper["done"]
)

remaining_papers = total_papers - completed_papers

overall_progress = completed_papers / total_papers if total_papers else 0


metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "📚 Exams",
    len(all_exams),
)

metric2.metric(
    "📄 Past Papers",
    total_papers,
)

metric3.metric(
    "✅ Completed",
    completed_papers,
)

metric4.metric(
    "⏳ Remaining",
    remaining_papers,
)

st.write("**Overall Progress**")

st.progress(overall_progress)

st.caption(f"{overall_progress * 100:.0f}% complete")

st.divider()


# =========================================================
# ADD EXAM
# =========================================================

st.subheader("➕ Add Exam")

with st.form(
    "add_exam_form",
    clear_on_submit=True,
):
    col1, col2 = st.columns(
        [4, 1],
        vertical_alignment="bottom",
    )

    new_exam_name = col1.text_input(
        "Exam name",
        placeholder="e.g. Mechanics, Waves, Integration",
    )

    add_exam = col2.form_submit_button(
        "Add Exam",
        type="primary",
        use_container_width=True,
    )

    if add_exam:
        clean_name = new_exam_name.strip()

        if not clean_name:
            st.error("Please enter an exam name.")

        else:
            duplicate = any(
                exam["name"].lower() == clean_name.lower() for exam in all_exams
            )

            if duplicate:
                st.error("That exam already exists.")

            else:
                st.session_state.past_papers_data["exams"].append(
                    {
                        "id": generate_id(),
                        "name": clean_name,
                        "papers": [],
                    }
                )

                save_data()

                st.rerun()


st.divider()


# =========================================================
# EMPTY STATE
# =========================================================

if not all_exams:
    st.info("No exams added yet. Add your first exam above.")


# =========================================================
# EXAMS
# =========================================================

for exam in all_exams:
    exam_id = exam["id"]

    papers = sort_papers(exam["papers"])

    total = len(papers)

    completed = sum(paper["done"] for paper in papers)

    progress = completed / total if total else 0

    # =====================================================
    # EXAM CONTAINER
    # =====================================================

    with st.container(border=True):
        header1, header2, header3 = st.columns(
            [6, 1, 1],
            vertical_alignment="center",
        )

        header1.subheader(f"📘 {exam['name']}")

        if header2.button(
            "✏️ Rename",
            key=f"rename_exam_{exam_id}",
            use_container_width=True,
        ):
            rename_exam_dialog(exam_id)

        if header3.button(
            "🗑️ Delete",
            key=f"delete_exam_{exam_id}",
            use_container_width=True,
        ):
            delete_exam_dialog(exam_id)

        # =================================================
        # EXAM PROGRESS
        # =================================================

        stat1, stat2, stat3 = st.columns(3)

        stat1.metric(
            "Papers",
            total,
        )

        stat2.metric(
            "Completed",
            completed,
        )

        stat3.metric(
            "Remaining",
            total - completed,
        )

        st.progress(progress)

        st.caption(f"{completed} of {total} papers completed ({progress * 100:.0f}%)")

        st.write("")

        # =================================================
        # TABLE HEADER
        # =================================================

        (
            year_header,
            done_header,
            notes_header,
            action_header,
        ) = st.columns(
            [1.3, 0.8, 4.5, 1],
            vertical_alignment="center",
        )

        year_header.markdown("**Year**")

        done_header.markdown("**Done**")

        notes_header.markdown("**Notes**")

        action_header.markdown("**Action**")

        # =================================================
        # TABLE ROWS
        # =================================================

        for paper in papers:
            paper_id = paper["id"]

            (
                year_col,
                done_col,
                notes_col,
                delete_col,
            ) = st.columns(
                [1.3, 0.8, 4.5, 1],
                vertical_alignment="center",
            )

            # ---------------------------------------------
            # YEAR
            # ---------------------------------------------

            new_year = year_col.text_input(
                "Year",
                value=str(paper.get("year", "")),
                key=f"year_{exam_id}_{paper_id}",
                label_visibility="collapsed",
            )

            if new_year != paper["year"]:
                clean_year = new_year.strip()

                duplicate_year = any(
                    other["year"] == clean_year and other["id"] != paper_id
                    for other in exam["papers"]
                )

                if not duplicate_year:
                    paper["year"] = clean_year

                    save_data()

            # ---------------------------------------------
            # COMPLETED
            # ---------------------------------------------

            is_done = done_col.checkbox(
                "Done",
                value=paper["done"],
                key=f"done_{exam_id}_{paper_id}",
                label_visibility="collapsed",
            )

            if is_done != paper["done"]:
                paper["done"] = is_done

                save_data()

                st.rerun()

            # ---------------------------------------------
            # NOTES
            # ---------------------------------------------

            preview = clean_html_preview(paper.get("notes", ""))

            if preview:
                note_label = f"📝 {preview}"

            else:
                note_label = "➕ Add notes"

            if notes_col.button(
                note_label,
                key=f"notes_{exam_id}_{paper_id}",
                use_container_width=True,
            ):
                open_notes_editor(
                    exam_id,
                    paper_id,
                )

            # ---------------------------------------------
            # DELETE PAPER
            # ---------------------------------------------

            if delete_col.button(
                "🗑️",
                key=f"delete_paper_{exam_id}_{paper_id}",
                use_container_width=True,
            ):
                exam["papers"] = [
                    existing_paper
                    for existing_paper in exam["papers"]
                    if existing_paper["id"] != paper_id
                ]

                save_data()

                st.rerun()

        # =================================================
        # ADD PAPER
        # =================================================

        st.write("")

        with st.form(
            f"add_paper_form_{exam_id}",
            clear_on_submit=True,
        ):
            add_col1, add_col2 = st.columns(
                [4, 1],
                vertical_alignment="bottom",
            )

            new_year = add_col1.text_input(
                "Add past paper year",
                value=str(datetime.now().year - 1),
                key=f"new_year_{exam_id}",
            )

            add_paper = add_col2.form_submit_button(
                "➕ Add Paper",
                use_container_width=True,
            )

            if add_paper:
                clean_year = new_year.strip()

                if not clean_year:
                    st.error("Please enter a year.")

                elif any(paper["year"] == clean_year for paper in exam["papers"]):
                    st.error(f"{clean_year} already exists under {exam['name']}.")

                else:
                    exam["papers"].append(
                        {
                            "id": generate_id(),
                            "year": clean_year,
                            "done": False,
                            "notes": "",
                        }
                    )

                    save_data()

                    st.rerun()

    st.write("")

