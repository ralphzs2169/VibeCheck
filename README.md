# VibeCheck

## Tech Stack (current)
- FastAPI
- SQLAlchemy
- SQLite
- Streamlit
- Transformers (DistilBERT)
- KeyBERT
- Scikit-learn

---

## 1. Clone Repository

```bash
git clone <your-repository-url>
cd VibeCheck
```

---

## 2. Create Virtual Environment

### Windows (PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\Activate
```

### Mac/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see:

```bash
(.venv)
```
in your terminal.

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run Database Seed Script (optional but recommended)

This populates the database with sample:
- users
- businesses
- reviews
- analytics-ready timestamps

```bash
python -m backend.app.scripts.seed
```

---

## 5. Run FastAPI Backend

```bash
fastapi dev backend/app/main.py
```

Backend runs at:

```bash
http://127.0.0.1:8000
```

API docs:

```bash
http://127.0.0.1:8000/docs
```

---

## 6. Run Streamlit Frontend

Open a **new terminal**.

Activate virtual environment again:

### Windows
```bash
.\.venv\Scripts\Activate
```

### Mac/Linux
```bash
source .venv/bin/activate
```

Run Streamlit:

```bash
streamlit run frontend/app.py
```

Frontend runs at:

```bash
http://localhost:8501
```

---

## 7. Run Tests

```bash
pytest -q
```

---

## Project Structure

```bash
VibeCheck/
├── backend/
│   ├── app/
│   │   ├── models/      # SQLAlchemy database models/tables (User, Review, Business, etc.)
│   │   ├── routers/     # FastAPI API endpoints/routes
│   │   ├── schemas/     # Pydantic request/response schemas (validation)
│   │   ├── services/    # Business logic, analytics, sentiment, vibe computation
│   │   └── scripts/     # Utility scripts such as database seeding
│   └── tests/           # Unit & Integration tests for backend services and API routes
├── frontend/
│   └── app.py           # Streamlit dashboard UI for analytics visualization
├── requirements.txt     # Project dependencies
├── README.md            # Project documentation/setup guide
└── .gitignore           # Ignored files/folders
```

---

## Notes

- Ensure backend is running before opening Streamlit frontend.
- First startup may take longer because HuggingFace models download automatically.

Models used:
- DistilBERT sentiment analysis
- KeyBERT keyword extraction

---