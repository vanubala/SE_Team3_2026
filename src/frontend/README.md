# Frontend (`src/frontend`)

React + TypeScript + Vite presentation layer for the **Smart Parcel Locker System (SPLS)**.

---

## Tech Stack
* **Framework:** React 19 + TypeScript + Vite
* **Routing:** `react-router-dom`
* **UI & Styling:** Material UI (`@mui/material`, `@emotion/react`, `@emotion/styled`) with centralized theme tokens (`src/theme.ts`)
* **Backend Integration:** REST JSON API over HTTPS (`VITE_API_URL`)

---

## Getting Started

### 1. Navigate to the Frontend Directory
```bash
cd src/frontend
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Run the Development Server
```bash
npm run dev
```
Open `http://localhost:5173` in your browser to view the Locker Terminal UI.


---

**Routes:**
* `/terminal` — Kiosk welcome & action selection (`Pick Up` / `Drop Off`)
* `/terminal/pickup` — Guest recipient 6-digit PIN entry (UC4)
* `/terminal/deposit` — Courier Parcel-ID entry (UC3)
* `/terminal/door-open` — Unlocked compartment display & door-closure confirmation