# Deploying the app (issue #8)

Streamlit Community Cloud, free, deploys from the private GitHub repo. About 10 minutes, once.
Every later push to the deployed branch redeploys the app by itself within a few minutes.

1. Deploy from `main` (the app Quan froze on 17 Oct is at `bb2f366` or later). To hold a stable demo
   while work continues, deploy from a branch such as `release` instead and merge into it only when sure:
   whatever reaches the deployed branch goes live.
2. Go to https://share.streamlit.io and sign in with the GitHub account that owns the repo
   (AndyPham2004). Allow access to private repos when asked.
3. **Create app** → *Deploy a public app from GitHub*:
   - Repository: `AndyPham2004/ANLP-AT2-Skillabus`
   - Branch: `main` (or `release`)
   - Main file path: `app/Home.py`
   - App URL: pick a name, e.g. `skillabus`
4. **Advanced settings** → Python version **3.12** → Secrets (TOML). The app reads these from
   `st.secrets` at start (`app/Home.py`); the names must match exactly:
   ```toml
   OPENAI_API_KEY = "sk-..."                        # the GPT-4o-mini tier and the Handbook chat
   JOBSPIPE_API_KEY = "..."                         # the 17 Oct (b) batch of JobsPipe ads
   JOBSPIPE_API_KEY_2026_10_17_A = "..."            # the 17 Oct (a) batch
   JOBSPIPE_API_KEY_OLD_2026_10_16 = "..."          # the 16 Oct batch
   ```
   The JobsPipe keys are the ones in Quan's `.env` (`app/ads.py`, `FETCH_KEYS`, says which batch each
   serves). With them, "Use this ad" on a JobsPipe ad fetches its full text from the API, one credit per
   ad, kept in memory only; without them the ad is analysed from the skills found at fetch time (#188),
   which works but misses anything the dictionary did not name. The 64 job-board ads carry their text in
   the repo. Lightcast keys are not needed.
5. Deploy. The app installs from `app/requirements.txt`, which leaves PyTorch and sentence-transformers
   out, so the build takes a minute or two and the app starts without the one-minute model load.
6. Make the QR code for the report:
   ```powershell
   python src/make_qr.py https://anlp-at2-skillabus-eippveupf3g9iimpi93dma.streamlit.app
   ```
   It writes `docs/report/figures/qr_app.png`.

## What differs on the cloud

- **Matching uses TF-IDF, not the embedding model** (`SKILLABUS_NO_EMBED` behaviour in
  `src/skillabus/normalise.py`): no PyTorch on the free tier. Skill statuses and subject rankings can differ
  a little from a laptop run with the model; the numbers in the report come from the laptop.
- **No `data/raw/`**: the JobsPipe ad texts are not in git (JobsPipe's terms), hence the keys above.
- **Votes** (👍 / 👎) go to `data/runtime/feedback.csv` on the cloud machine, which is wiped on every
  redeploy. Download it from the app's machine before redeploying, or ask testers to vote in one session.
- The first "See roles that fit me" compares all 11 roles and takes a few seconds; later ones are cached.

## Before user testing

- Set a spending limit on the OpenAI key (Settings → Limits). GPT-4o-mini costs a fraction of a cent per
  analysis; a limit of USD 10 is plenty. The JobsPipe free keys have a fixed credit balance (about 54 left
  on `JOBSPIPE_API_KEY` on 17 Oct); each "Use this ad" on a JobsPipe ad spends one.
- The app is public by link. Tell testers to use the sample resume or their own without contact details;
  resumes are never stored and never sent to the chat model, but there is no reason to upload a phone number.
