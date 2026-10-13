# LinkedIn Technical Post Collector

A free Streamlit proof-of-concept that discovers **publicly indexed LinkedIn post links** using Bing's public RSS search endpoint, deduplicates them, and exports search previews to Excel.

## Deploy to Streamlit Community Cloud

1. Upload `app.py`, `requirements.txt`, and `README.md` to your GitHub repository root.
2. Sign in to https://share.streamlit.io with GitHub.
3. Choose **Create app** → **Deploy a public app from GitHub** (labels may vary).
4. Select your repository, branch `main`, and main file path `app.py`.
5. Deploy, then open the provided URL on your iPad.

## Limitations

- Search-engine indexing is incomplete; results may be empty.
- Date selections are search hints, not strict LinkedIn post-date filters.
- Search snippets are **not full post text** and publication dates are unverified.
- Does not bypass login, CAPTCHA, or access controls.
- This prototype has no cross-session persistent storage. Download the Excel file before closing.
- No AI summarization is included; adding it may require a model/API or a separate summarization service.
- A public Streamlit app is publicly reachable; don't put credentials or private data in the repository.
