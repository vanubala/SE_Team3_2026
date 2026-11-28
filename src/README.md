# Smart Parcel Locker System (SPLS) — Running Instructions

## Prerequisites
* **PostgreSQL 15+** (running locally on port `5432`)
* **Python 3.12** (with `pip` / virtual environment support)
* **Node.js 18+ & npm** (for the React + TypeScript + Vite frontend in `src/frontend`)

---

## 1. Database Setup (`PostgreSQL`)

1. **Install and start the local PostgreSQL service** (macOS Homebrew example):
   ```bash
   brew install postgresql@15
   brew services start postgresql@15
   ```
2. **Create the `smart_locker` database:**
   ```bash
   createdb smart_locker
   ```
   *(Verify with `psql -d smart_locker -c "SELECT 1;"`)*

---

## 2. Backend Setup & Run (`src/backend`)

1. **Navigate to the backend directory:**
   ```bash
   cd src/backend
   ```

2. **Create and activate a Python virtual environment, then install the required packages:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   *(Optional: if running the test suite, also run `pip install -r requirements-dev.txt`.)*

3. **Create your local `.env` from `.env.example`:**
   ```bash
   cp .env.example .env
   ```
   Update `src/backend/.env` with your local PostgreSQL connection string, a 32+ byte `JWT_SECRET`, and two distinct 12+ character demo passwords:
   ```env
   DATABASE_URL=postgresql+psycopg://<YOUR_LOCAL_DB_USER>@localhost:5432/smart_locker
   JWT_SECRET=replace_with_a_random_secret_at_least_32_bytes_long
   DEMO_COURIER_PASSWORD=CourierDemoPass123!
   DEMO_ADMIN_PASSWORD=AdminDemoPass123!
   ```

4. **Apply Alembic database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Seed the demo accounts, stations, and compartments:**
   ```bash
   PYTHONPATH=. python3 -m app.db.seed --demo
   ```
   This creates:
   * **Courier account:** `courier@example.test`
   * **Admin account:** `admin@example.test`
   * **Stations:** Demo Belval Station & Demo Kirchberg Station (with 12 compartments each)
   * **Sample parcel:** `DEMO-0001` (`REGISTERED`)

6. **Start the FastAPI server (port `8000`):**
   ```bash
   PYTHONPATH=. python3 -m uvicorn app.main:create_app --factory --reload --port 8000
   ```
   * API base URL: `http://localhost:8000/api`
   * Interactive OpenAPI docs: `http://localhost:8000/docs`

---

## 3. Frontend Setup & Run (`src/frontend`)

1. **Open a second terminal and navigate to the frontend directory:**
   ```bash
   cd src/frontend
   ```

2. **Install Node.js dependencies (`react`, `react-router-dom`, `@mui/material`, `@emotion/react`, `@emotion/styled`, etc.):**
   ```bash
   npm install
   ```

3. **Start the Vite development server (port `5173`):**
   ```bash
   npm run dev
   ```

---

## 4. Available Routes & Demo Credentials

Open `http://localhost:5173` in your browser:

* **`/login`** — Staff login (`COURIER` & `ADMIN`):
  * **Courier:** `courier@example.test` + your `DEMO_COURIER_PASSWORD`
  * **Admin:** `admin@example.test` + your `DEMO_ADMIN_PASSWORD`
* **`/terminal`** — Public Kiosk Terminal Simulator (UC3 Parcel-ID Drop-Off & UC4 Guest PIN Pick-Up)