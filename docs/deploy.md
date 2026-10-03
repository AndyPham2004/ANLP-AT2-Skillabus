# Deploying the app (issue #8)

Streamlit Community Cloud, free, deploys from the private GitHub repo. About 10 minutes, once.

1. Merge the app pull requests into `main` (#35, #36, #37, this one).
2. Go to https://share.streamlit.io and sign in with the GitHub account that owns the repo
   (AndyPham2004). Allow access to private repos when asked.
3. **Create app** → *Deploy a public app from GitHub*:
   - Repository: `AndyPham2004/ANLP-AT2-Skillabus`
   - Branch: `main`
   - Main file path: `app/Home.py`
   - App URL: pick a name, e.g. `skillabus`
4. **Advanced settings** → Python version **3.12** → Secrets (TOML):
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
   Lightcast keys are not needed on the cloud: without the raw ESCO files the app uses the
   dictionary baseline plus GPT-4o-mini, and normalisation falls back to Lightcast/emerging.
5. Deploy. The app installs from `app/requirements.txt` (no PyTorch), so the first build takes
   a minute or two.
6. Make the QR code for the report:
   ```powershell
   python src/make_qr.py https://skillabus.streamlit.app
   ```
   It writes `docs/report/figures/qr_app.png`.

## Before user testing (12 Oct)

- Set a spending limit on the OpenAI key (Settings → Limits). GPT-4o-mini costs a fraction of a
  cent per analysis; a limit of USD 10 is plenty.
- Votes go to `data/processed/feedback.csv` on the cloud machine, which is wiped on every
  redeploy. Download it from the app's machine before redeploying, or ask testers to vote in one
  session. (A shared store is a later improvement.)
- The app is public by link. Tell testers to use the sample resume or their own without contact
  details; resumes are never stored, but there is no reason to upload a phone number.
