# Review Intelligence — Frontend

React + Vite dashboard for the AI-powered customer review analyzer.

## Tech Stack

- React 19
- Vite 8
- Tailwind CSS v4
- Recharts (charts)
- Lucide React (icons)

## Pages

| Page | Description |
|---|---|
| Upload & Analyze | CSV upload, column mapping, live AI pipeline stepper |
| Executive Dashboard | KPI cards, Emerging Issue Radar, emotion & timeline charts |
| Issue Detail | Explainable diagnostic, evidence chain, occurrence timeline |
| PM Brief | Executive brief with copy/print, investigation hypotheses |

## Setup

```bash
npm install
npm run dev
```

Dev server runs on **http://localhost:5173**

The `vite.config.js` proxies all `/api` requests to the FastAPI backend at `http://127.0.0.1:8000`.

## Environment

No environment variables required for the frontend. Backend URL is proxied via Vite config.
