# Wireframes (issue #5)

Screens of the working app on the sample inputs (Robert Walters ad, synthetic resume), 4 Oct 2026.
They double as the wireframes: the layout is built, so what you see is what the user gets.
Run it yourself: `streamlit run app/Home.py`.

| Screen | File | What the user does |
|---|---|---|
| 1 Start | `01_start.png` | Picks one of the three users from the poster: elective chooser, job seeker, career switcher |
| 2 Inputs | `02_input.png` | Job seeker: pastes an ad (or the sample) and uploads a resume (or the sample). Elective chooser and career switcher pick the target role; the elective chooser also ticks subjects already taken |
| 3 Results | `03_results.png` | One number first ("6 of 8"), then the gap chart (bar = % of 3,204 Seek ads, blue = have, copper = missing), then the shortest path: the 2-3 subjects that close the most demand-weighted gaps |
| 4 Evidence | `04_evidence.png` | Picks a gap and sees the ad sentence next to the subject sentence, with the layer it came from (learning objective, topic, description). Votes "teaches it / not really", which feeds validation |
| 5 Chat | `05_chat.png` | Asks a question in the side panel; answers come only from Handbook text, with the subject and layer cited |

## Design decisions and the feedback they answer

| Decision | Why |
|---|---|
| Evidence panel: ad sentence beside subject sentence | Marker: recommendations must be checkable. The user sees why a subject is suggested instead of trusting a score |
| Layer label on every piece of subject evidence | Marker: Handbook learning objectives alone miss what is taught. Topics and (soon) assessments count too, and the label says how strong the evidence is |
| Shortest path, weighted by employer demand | The innovation: no existing tool turns a skill gap into a short list of specific subjects |
| "✦ new" tag on LLMs and generative AI, with the 2023-24 US figure in the caption | Marker: how are emerging skills handled? They are kept and flagged, not dropped because ESCO and the 2019-22 ads predate them |
| Thumbs up/down with "I've taken it" | Marker: validate the subject-skill mappings. Votes go to `data/runtime/feedback.csv` |
| One number first, few words, poster colours | Marker: the poster was text-dense. The app leads with the answer |
| "Engine: baseline / pipeline" line | Honest about which method produced the result while the pipeline is being built |
| Resume never stored or sent to the LLM | Ethics block on the poster |
