# eCTD PDF Validator with Oracle JET Frontend

## 🧰 Prerequisites
- Python 3.8+
- pip
- Internet access (for Oracle JET CDN)

## 📦 Setup Instructions

### 1. Backend (Flask API)
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 2. Frontend (Oracle JET)
Open `frontend/index.html` in a web browser.

> ⚠️ Ensure the backend is running at `http://localhost:5000`.

## 📂 Project Structure
```
ectd_gui_project/
├── backend/
│   ├── app.py
│   ├── ectd_pdf_validator.py
│   └── requirements.txt
└── frontend/
    └── index.html
```

## ✅ What It Does
- Upload a PDF
- Validates structure, keywords, and eCTD compliance
- Returns a JSON report in the browser
