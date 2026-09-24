import io
import json
import os
import re
import html

import streamlit as st
from streamlit_quill import st_quill
from xhtml2pdf import pisa


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Notes",
    page_icon="📝",
    layout="wide",
)

st.title("📝 Past Paper Notes")
st.caption("Review, edit and export your past-paper notes.")

DATA_FILE = "data/past_papers.json"


# =========================================================
# DATA FUNCTIONS
# =========================================================


def load_data():
    """Load the current past-paper records."""

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            return data

        except (json.JSONDecodeError, OSError):
            st.error("Could not read the past papers data file.")

    return {"exams": []}


def save_data():
    """Save records back to the JSON file."""

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            st.session_state.past_papers_data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def clean_filename(name):
    """Create a safe PDF filename."""

    cleaned = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        name.strip().lower(),
    )

    return cleaned.strip("_")


def sort_papers(papers):
    """Show newest past papers first."""

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


# =========================================================
# PDF GENERATION
# =========================================================


def generate_pdf(exam_name, papers):
    """Generate a PDF containing all notes for an exam."""

    safe_exam_name = html.escape(exam_name)

    html_content = f"""
    <html>
    <head>
        <style>

            body {{
                font-family: Helvetica, Arial, sans-serif;
                color: #333333;
                line-height: 1.5;
                padding: 20px;
            }}

            h1 {{
                color: #1E3A8A;
                border-bottom: 2px solid #1E3A8A;
                padding-bottom: 8px;
            }}

            h2 {{
                color: #2563EB;
                margin-top: 22px;
            }}

            .status {{
                color: #666666;
                font-size: 11px;
                margin-bottom: 10px;
            }}

            .divider {{
                border-top: 1px solid #cccccc;
                margin: 22px 0;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}

            th,
            td {{
                border: 1px solid #dddddd;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background-color: #f3f4f6;
            }}

            ul,
            ol {{
                margin-left: 20px;
            }}

            img {{
                max-width: 100%;
                height: auto;
            }}

        </style>
    </head>

    <body>

        <h1>{safe_exam_name} - Past Paper Notes</h1>
    """

    for paper in sort_papers(papers):
        year = html.escape(str(paper.get("year", "Unknown")))

        status = "Completed" if paper.get("done", False) else "Not Completed"

        html_content += f"""
        <h2>{year}</h2>

        <div class="status">
            Status: {status}
        </div>
        """

        notes = paper.get(
            "notes",
            "",
        )

        if notes and notes.strip() not in [
            "<p><br></p>",
            "<p></p>",
        ]:
            html_content += f"""
            <div>
                {notes}
            </div>
            """

        else:
            html_content += """
            <p style="color: #888888;">
                No notes added.
            </p>
            """

        html_content += """
        <div class="divider"></div>
        """

    html_content += """
    </body>
    </html>
    """

    pdf_buffer = io.BytesIO()

    pisa.CreatePDF(
        html_content,
        dest=pdf_buffer,
        encoding="UTF-8",
    )

    pdf_buffer.seek(0)

    return pdf_buffer


# =========================================================
# INITIALIZE DATA
# =========================================================

if "past_papers_data" not in st.session_state:
    st.session_state.past_papers_data = load_data()


data = st.session_state.past_papers_data

exams = data.get(
    "exams",
    [],
)


# =========================================================
# PAGE
# =========================================================

if not exams:
    st.info(
        "No past papers have been added yet. Add them from the Past Papers page first."
    )

else:
    # =====================================================
    # SUMMARY
    # =====================================================

    total_papers = sum(len(exam.get("papers", [])) for exam in exams)

    papers_with_notes = sum(
        1
        for exam in exams
        for paper in exam.get("papers", [])
        if paper.get("notes", "").strip() not in ["", "<p><br></p>", "<p></p>"]
    )

    summary1, summary2, summary3 = st.columns(3)

    summary1.metric(
        "📚 Exams",
        len(exams),
    )

    summary2.metric(
        "📄 Past Papers",
        total_papers,
    )

    summary3.metric(
        "📝 Papers with Notes",
        papers_with_notes,
    )

    st.divider()

    # =====================================================
    # EXAMS
    # =====================================================

    for exam in exams:
        exam_id = exam["id"]

        exam_name = exam.get(
            "name",
            "Untitled Exam",
        )

        papers = sort_papers(
            exam.get(
                "papers",
                [],
            )
        )

        note_count = sum(
            1
            for paper in papers
            if paper.get("notes", "").strip() not in ["", "<p><br></p>", "<p></p>"]
        )

        with st.expander(
            f"📘 {exam_name} • {note_count}/{len(papers)} with notes",
            expanded=False,
        ):
            # =================================================
            # EXPORT
            # =================================================

            export_col1, export_col2 = st.columns(
                [3, 1],
                vertical_alignment="center",
            )

            export_col1.markdown("### 📄 Export Notes")

            if papers:
                pdf_data = generate_pdf(
                    exam_name,
                    papers,
                )

                export_col2.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=(f"{clean_filename(exam_name)}_notes.pdf"),
                    mime="application/pdf",
                    key=f"pdf_{exam_id}",
                    use_container_width=True,
                )

            st.divider()

            # =================================================
            # NO PAPERS
            # =================================================

            if not papers:
                st.info("No past papers have been added to this exam yet.")

                continue

            # =================================================
            # PAPER NOTES
            # =================================================

            for paper in papers:
                paper_id = paper["id"]

                year = paper.get(
                    "year",
                    "Unknown",
                )

                done = paper.get(
                    "done",
                    False,
                )

                if done:
                    status_text = "✅ Completed"
                else:
                    status_text = "⬜ Not Completed"

                with st.container(border=True):
                    header_col1, header_col2 = st.columns(
                        [4, 1],
                        vertical_alignment="center",
                    )

                    header_col1.subheader(f"📅 {year}")

                    header_col2.write(status_text)

                    current_notes = paper.get(
                        "notes",
                        "",
                    )

                    updated_notes = st_quill(
                        value=current_notes,
                        html=True,
                        key=(f"notes_{exam_id}_{paper_id}"),
                    )

                    if updated_notes != current_notes:
                        # Find the actual paper
                        # inside session state
                        for stored_exam in st.session_state.past_papers_data["exams"]:
                            if stored_exam["id"] != exam_id:
                                continue

                            for stored_paper in stored_exam["papers"]:
                                if stored_paper["id"] == paper_id:
                                    stored_paper["notes"] = updated_notes or ""

                                    save_data()

                                    break

                            break
