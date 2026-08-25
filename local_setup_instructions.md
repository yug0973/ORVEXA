# ORVEXA: Local Setup & Running Instructions

Follow these step-by-step instructions to configure, seed, and run ORVEXA locally on your system.

---

## 📋 Prerequisites
Ensure you have the following installed on your machine:
1. **Python** (v3.10 or v3.11 recommended)
2. **Node.js** (v18 or higher recommended)
3. **npm** (comes bundled with Node.js)
4. **Git** (optional)

---

## 🛠️ Step 1: Backend Environment Setup

1. **Open a terminal** in the project's root folder (`c:\Users\jaymi\Documents\ORVEXA`).
2. **Create a virtual environment:**
   ```powershell
   python -m venv .venv
   ```
3. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```
4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Configure environment variables:**
   - Copy the template file [`.env.template`](file:///c:/Users/jaymi/Documents/ORVEXA/.env.template) to a new file named `.env`:
     ```powershell
     Copy-Item .env.template .env
     ```
   - Under local testing, it defaults to using an SQLite database file (`ORVEXA.db`).

---

## 🗄️ Step 2: Database Initialization & Seeding

Before running the app, you need to populate the database with orbital trajectories, conjunction events, and space weather logs.

1. **Set the python path** in your terminal so it recognizes local directories:
   - **Windows (PowerShell):**
     ```powershell
     $env:PYTHONPATH="."
     ```
   - **Windows (Command Prompt):**
     ```cmd
     set PYTHONPATH=.
     ```
   - **Linux / macOS:**
     ```bash
     export PYTHONPATH=.
     ```
2. **Run the database seed scripts:**
   ```bash
   python backend/seed_db.py
   python backend/seed_reentry.py
   ```
   *This initializes the database (`ORVEXA.db`) and seeds 100+ active satellites with correct operators (SpaceX, ISRO, NASA, etc.), SGP4 trajectories, and collision events.*

---

## ⚡ Step 3: Run the Backend API Server

With the virtual environment active and database seeded, start the FastAPI server:
```bash
python -m backend.main
```
* **Host Address:** `http://127.0.0.1:8000`
* **Interactive API Docs:** `http://127.0.0.1:8000/docs` (Swagger UI)

---

## 🎨 Step 4: Frontend Dashboard Setup

1. **Open a new terminal window** (keep the backend server terminal running).
2. **Navigate into the frontend folder:**
   ```bash
   cd ORVEXA-frontend
   ```
3. **Install npm packages:**
   ```bash
   npm install
   ```
4. **Start the Vite dev server:**
   ```bash
   npm run dev
   ```
* **Host Address:** `http://localhost:5173`
* Open this URL in your web browser to access the full ORVEXA dashboard!

---

## 🐳 Optional: Run via Docker Compose (Production Mode)

If you have **Docker** and **Docker Compose** installed, you can boot the entire system (including PostgreSQL and PostGIS spatial indexing) with a single command:

1. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```
2. **Access the application:**
   - **Frontend Dashboard:** `http://localhost` (Port 80)
   - **Backend API Docs:** `http://localhost/api/docs`
