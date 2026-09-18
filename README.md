
# Streamlit Task and Project Planner

A web-based application built using Streamlit to track daily scheduling deadlines and manage rich-text project logs. It features a dynamically bounded calendar view, inline rich-text document editing, and single-click PDF report exportation.

---

## Key Features

### Dynamic To-Do Calendar
* **Moving Date Window:** Automatically hides and greys out past dates as days go by.
* **Monday Start:** Custom-configured week grid view starting explicitly on Mondays.
* **Exam/Event Ceiling Limit:** Define a custom global project deadline date in the sidebar that restricts tasks from being added past it.
* **CRUD Management:** Add, complete (strike-through), inline edit, or delete items instantly.

### Things and Notes Tracker
* **Relational Tables:** Organize custom categories with tabular records mapped by Year, Status, and Documentation Canvas.
* **API-Free Rich Text Editor:** Fully embedded, secure open-source Quill WYSIWYG editor supporting custom styles, tables, and pasted media.
* **Iframe Fix:** Embedded CSS constraints prevent the calendar framework from sizing up or breaking layout flow when switching browser pages.

### One-Click PDF Generation
* Compiles your rich-text entries, tables, and years into a cleanly styled standalone PDF layout using custom print CSS styling sheets.

---

## Installation and Setup

### Prerequisites
Ensure you have Python 3.8+ installed on your computer.

### 1. Clone or Download Project
```bash
cd your-workspace-directory
```

### 2. Install Required Dependencies
Run the following package command in your terminal to fetch the necessary interface wrappers, rich text editor, and document PDF engine:
```bash
pip install streamlit streamlit-calendar streamlit-quill xhtml2pdf
```

---

## How to Run the App

To launch the system inside your default web browser tab:
```bash
streamlit run app.py
```

---

## Data Storage Structure
All user metrics and tabular canvas modifications are saved locally to flat configuration files in real-time. No internet connection or remote cloud databases required:
* `data/tasks.json` — Calendar constraints and scheduling lists.
* `data/past_papers.json` — Text documents, matrices, and custom workspace headers.

---

License: Copyright 2026 All Rights Reserved.
