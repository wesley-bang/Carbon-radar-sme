# Deployment

## Target

The deployment target is Streamlit Community Cloud.

## Entry Point

Use `app/streamlit_app.py` as the app entry point.

## Required Files

- `requirements.txt`
- `app/streamlit_app.py`
- `data/sample/*.csv`
- `data/demand_evidence/*.csv`
- `carbonradar/` package

Generated output files under `data/outputs/` are not required for the dashboard to run. The dashboard loads committed demo CSV files directly.

## Deployment Steps

1. Push the repository to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Select branch: `main`.
5. Set main file path: `app/streamlit_app.py`.
6. Deploy.

## Runtime Notes

- No secrets are required.
- The dashboard uses committed demo CSV files only.
- The deployed app is a read-only demo.
- The deployed app does not use authentication, OCR, live APIs, scraping, database storage, or file upload.
- The deployed app is not legal, tax, certification, or regulatory advice.
