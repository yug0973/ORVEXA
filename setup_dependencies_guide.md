# ORVEXA: Dependency Setup & Configuration Guide

This guide details the step-by-step instructions to download, install, and configure external services required for the advanced features of ORVEXA: **PostgreSQL/PostGIS** (spatial database), **Ollama** (offline AI Copilot), and the **Aditya-L1** (solar weather simulation) pipeline.

---

## 🗺️ 1. PostgreSQL & PostGIS Spatial Database

PostgreSQL with the PostGIS extension is used in ORVEXA to store, index, and query 2D/3D geographic geometries (such as reentry landing hazard corridors).

### Option A: 1-Click Setup via Docker (Recommended)
If you have **Docker Desktop** installed, you do not need to install PostgreSQL or PostGIS locally.
1. Install **Docker Desktop** from [Docker's official site](https://www.docker.com/products/docker-desktop/).
2. Open a terminal in the project's root folder (`c:\Users\jaymi\Documents\ORVEXA`).
3. Run the database container in the background:
   ```bash
   docker-compose up -d db
   ```
4. **Verification:** Check if the container is running:
   ```bash
   docker ps
   ```
   You should see `ORVEXA-db` running on port `5432`. It automatically initializes the database schema using [init_db.sql](file:///c:/Users/jaymi/Documents/ORVEXA/db/migrations/init_db.sql).
5. Update your local backend [`.env`](file:///c:/Users/jaymi/Documents/ORVEXA/.env) database URL to:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ORVEXA
   ```

---

### Option B: Direct Local Setup (Windows Installer)
If you prefer running the database directly on your host operating system:
1. **Download PostgreSQL:** Download the Windows Installer (PostgreSQL v15 or v16) from [EnterpriseDB](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2. **Install PostgreSQL:** Run the installer. Set the password for the default `postgres` user (e.g., `postgres`) and keep the default port `5432`.
3. **Install PostGIS Extension:**
   * At the end of the installation wizard, check the box to launch **Application Stack Builder**.
   * Select your PostgreSQL installation from the dropdown.
   * Expand **Spatial Extensions** and check **PostGIS**.
   * Complete the installation download and wizard prompts.
4. **Create Database & Enable PostGIS:**
   * Open **pgAdmin** or a terminal and run `psql -U postgres`.
   * Create the database:
     ```sql
     CREATE DATABASE ORVEXA;
     ```
   * Connect to the database and enable the PostGIS spatial engine:
     ```sql
     \c ORVEXA;
     CREATE EXTENSION postgis;
     ```
5. **Verify Spatial Queries:** Run the following SQL query to verify PostGIS is active:
     ```sql
     SELECT postgis_full_version();
     ```
6. Update your local [`.env`](file:///c:/Users/jaymi/Documents/ORVEXA/.env) to point to the local database server.

---

## 🦙 2. Ollama & Llama 3.2 (Secure Offline AI Copilot)

The local copilot uses Retrieval-Augmented Generation (RAG) running an offline LLM to prevent sensitive satellite operational telemetry from leaking to cloud APIs.

### Setup Instructions
1. **Download Ollama:** Go to [Ollama's official website](https://ollama.com) and download the Windows installer.
2. **Install Ollama:** Run the installer and launch the Ollama tray application.
3. **Pull Llama 3.2 Model:** Open a command prompt or PowerShell and run:
   ```bash
   ollama run llama3.2
   ```
   *This automatically downloads the default 3-Billion parameter Llama 3.2 instruction model (approx. 2.0 GB) and starts an interactive prompt.*
4. **Keep API Server Running:** Ollama runs a background web server at `http://localhost:11434`. Ensure the Ollama app icon is running in your Windows task tray.
5. **Verify API Connection:**
   * Open a web browser or run in terminal:
     ```bash
     curl http://localhost:11434/api/tags
     ```
   * Verify that the response JSON lists `llama3.2:latest` (or `llama3.2:3b`).
6. **Integration / Fallback:** The backend is preconfigured to talk to this endpoint. If Ollama is offline or Llama 3.2 is not pulled, the copilot will automatically catch the connection timeout and fall back to the structured SQL database reporting generator without crashing.

---

## ☀️ 3. Aditya-L1 Solar Event Telemetry Pipeline

The Aditya-L1 simulation tracks solar flares, CME travel speed, and geomagnetic Ap storm indexes to scale thermospheric drag parameters.

### How it works
The backend reads space weather states from [`solar_weather_cache.json`](file:///c:/Users/jaymi/Documents/ORVEXA/solar_weather_cache.json). 
* When a flare is triggered, HEL1OS/SoLEXS simulated telemetry registers elevated flux.
* A CME ETA countdown starts. 
* Upon CME arrival, $F_{10.7}$ solar flux and $A_p$ geomagnetic indexes spike, accelerating satellite decay rates in LEO up to 3.5x.

### How to Trigger & Clear Events Manually
You can test the frontend reaction and the backend drag calculations by triggering simulated flare events using standard HTTP requests:

* **Trigger an X-Class Solar Flare (Geomagnetic Storm):**
  Open a terminal and run the following curl command:
  ```powershell
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/solar/trigger-flare/X"
  ```
  *(Or use standard `curl -X POST http://127.0.0.1:8000/api/solar/trigger-flare/X` on Cmd/Linux)*.

* **Trigger an M-Class Solar Flare (Moderate Activity):**
  ```powershell
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/solar/trigger-flare/M"
  ```

* **Clear Active Storm & Restore Quiet Sun Baselines:**
  ```powershell
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/solar/clear-flare"
  ```

### Verification Checks
1. When a flare is active, visit `http://127.0.0.1:8000/api/solar/aditya-l1` to see the simulated payload telemetry and count down.
2. In the frontend **Solar Weather** dashboard tab, observe the live solar flux charting spikes and the CME travel status updates.
