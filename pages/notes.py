import io
import json
import os
import streamlit as st
from streamlit_quill import st_quill
from xhtml2pdf import pisa

st.set_page_config(layout="wide")
st.title("Notes")

DATA_FILE = "data/past_papers.json"


def load_data():
    """Loads current project records."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_data():
    """Saves records back to local JSON file repository."""
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.things_data, f, indent=4)


def generate_pdf(thing_name, rows):
    """Converts the raw HTML from Quill directly into a stylized PDF document."""
    # Start building a clean HTML string with simple CSS rules for the PDF layout
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.5; }}
            h1 {{ color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 5px; }}
            h2 {{ color: #2563EB; margin-top: 20px; }}
            .divider {{ border-top: 1px solid #ccc; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f3f4f6; }}
            ul, ol {{ margin-left: 20px; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <h1>Report: {thing_name}</h1>
    """

    for row in rows:
        status = "Completed" if row["done"] else "In Progress"
        html_content += f"<h2>Year: {row['year']} ({status})</h2>"

        # Append the rich-text note HTML as it is directly from the text editor
        if row["notes"]:
            html_content += f"<div>{row['notes']}</div>"
        else:
            html_content += "<p style='color: #888;'>No notes provided.</p>"

        html_content += "<div class='divider'></div>"

    html_content += """
    </body>
    </html>
    """

    # Render the compiled HTML content into a PDF binary buffer stream
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

    pdf_buffer.seek(0)
    return pdf_buffer


# Initialize state engine context
if "things_data" not in st.session_state:
    st.session_state.things_data = load_data()

# Pull dynamic layout updates from disk
st.session_state.things_data = load_data()

if not st.session_state.things_data:
    st.info(
        "No things recorded yet. Please add data in your primary management tabs first."
    )
else:
    for thing_name, rows in st.session_state.things_data.items():
        with st.expander(f"{thing_name} ({len(rows)} entries)", expanded=False):
            # --- EXPORT INTERFACE ---
            st.markdown("### Export Options")
            pdf_data = generate_pdf(thing_name, rows)

            st.download_button(
                label=f"Download Entire PDF for {thing_name}",
                data=pdf_data,
                file_name=f"{thing_name.lower().replace(' ', '_')}_report.pdf",
                mime="application/pdf",
                key=f"dl_pdf_{thing_name}",
            )
            st.write("---")

            # --- LIVE EDIT INLINE VIEW ---
            if not rows:
                st.write("*No rows mapped to this thing.*")
            else:
                for i, row in enumerate(rows):
                    st.markdown(f"#### Year: **{row['year']}**")

                    # Live document tracking editor rendered directly in page flow
                    updated_notes = st_quill(
                        value=row["notes"],
                        html=True,
                        key=f"view_quill_{thing_name}_{i}",
                    )

                    # Update state instantly if modifications are recorded
                    if updated_notes != row["notes"]:
                        st.session_state.things_data[thing_name][i]["notes"] = (
                            updated_notes
                        )
                        save_data()

                    st.markdown("<br>", unsafe_allow_html=True)

