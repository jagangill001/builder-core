\# Builder Core



\## Live Services



\### Frontend

`https://builder-core-frontend-599596796788.us-central1.run.app`



\### Backend

`https://builder-core-599596796788.us-central1.run.app`



\---



\## Repo



GitHub repo:

`jagangill001/builder-core`



Main branch:

`main`



\---



\## Cloud Run Services



\### Backend service

\- Service name: `builder-core`

\- Region: `us-central1`

\- Build type: `Buildpacks`

\- Build directory: `backend`



\### Frontend service

\- Service name: `builder-core-frontend`

\- Region: `us-central1`

\- Build type: `Buildpacks`

\- Build directory: `frontend`



\---



\## Backend notes



\- Framework: FastAPI

\- Main app file: `backend/app/main.py`

\- Procfile path: `backend/Procfile`

\- Port: `8080`



Procfile:

```text

web: uvicorn app.main:app --host 0.0.0.0 --port 8080

