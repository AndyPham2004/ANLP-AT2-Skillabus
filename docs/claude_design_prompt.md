# Prompt for Claude Design — MDSI Skills Map poster

Attach first: `poster/figures/block3_sources.png`, `block4_pipeline.png`, `block5_top_skills.png`, `block6_gap_chart.png`, `block7_course_table.png`, `uts_logo.png`. Then paste everything below the line.

---

Design an A0 landscape research poster (1189 x 841 mm) for a university NLP course. It will be judged as a digital PDF by markers who read it without us present, so it has to explain itself.

You have creative freedom over layout, typography, colour and hierarchy. The five attached PNG figures are ours and already use teal for "have / market" and copper for "missing / gap"; feel free to pick up those two colours or to restyle the figures natively from the numbers given below, whichever gives a more coherent poster.

## Principles we care about, not rules

A stranger gets 3 seconds to stop and 30 seconds to understand. Build the poster around one dominant element, the skill-gap chart (block 6), placed left of and slightly above centre, and let everything else support it. Readers move from the title across the top, to the upper left, down each column to the lower right; let position carry that order without arrows. Keep roughly 40 percent of the sheet empty and separate sections with space rather than boxes or lines. Two typefaces at most, sentence case throughout, body text readable from 3 metres (24 pt or larger at true size), title around 120 pt. Two or three related colours on a neutral pale background with one accent used sparingly; keep warm reds and yellows to a minimum. Make a third of the area visual, label charts directly with no legends and no vertical text, and caption every figure with its source and sample size. Total words under 550. When in doubt, edit out.

## The one sentence a viewer should remember

We put subject outlines, job ads and resumes into one skills vocabulary, so a student can see exactly which skills a role needs that they lack, and which subject fills each gap.

## Content

**Title:** Skills Map: closing the gap between your degree and the job ad
**Authors:** Quan Pham, Van Thong, Phuong Nhi, Hoai Thuong
**Affiliation:** Master of Data Science and Innovation, University of Technology Sydney
**Course:** 36118 Applied NLP, Assessment 2A, Spring 2026
Place the attached uts_logo.png small in the title band, about 40 mm wide; it is black on transparent, so it sits on the paper colour without a box.

**1. The problem**
Subject outlines speak academic. Job ads speak industry. Nothing maps one to the other, so students guess which electives to take and what to put on a resume.
Two quotes side by side, same skill, different words:
- "Implement and evaluate advanced machine learning techniques to real-world problems." (UTS Handbook, 36120 Advanced Machine Learning Application, learning outcome)
- "Experience in building and deploying AI models and solutions. In-depth knowledge of deep learning, Generative AI and other advanced AI technologies." (Robert Walters, Data Scientist, Sydney CBD, September 2026)
Only the ad asks for generative AI, a phrase ESCO has no concept for yet. The app makes that difference visible, taking the teaching team's study-planner idea from the timetable to the job market.

**2. Users and goals**
Three users, one question each: Elective chooser, which subject moves me closest to the role I want? Job seeker, what does my resume lack for this ad? Career switcher, how far is my profile from a new role?
Five features: upload a resume or tick the subjects you have taken; pick a target role and city; see your skill gap ranked by demand; get electives ranked by how much gap they close; ask a chat that answers from real ads.

**3. Data: six sources, one vocabulary** (figure: block3_sources.png)
3,204 Seek Australia Data Scientist ads, 2019–2022, full text, the demand side. 13,960 ESCO v1.2.1 skill concepts with alt-labels, the shared vocabulary. 8,753 O*NET 31.0 tool names ESCO omits. 70 UTS Handbook subjects across six courses, scraped with learning outcomes. 1,355 LinkedIn US data roles, 2023–24, full text, the cross-market check. 2,484 resumes to build the student profile.
Caption: every count read from the downloaded file, not a dataset description page.

**4. Pipeline** (figure: block4_pipeline.png)
Input → Clean → Extract skills → Normalise → Match → Output. Extraction uses the ESCO dictionary now, with spaCy NER and an LLM compared in Part B. Matching uses TF-IDF cosine now, versus sentence embeddings in Part B. Output is the gap chart, ranked subjects and a RAG chat over ads. The two copper stages are where a traditional and a newer method run side by side and are scored (block 8).

**5. What Australian employers ask for** (figure: block5_top_skills.png, top 15 skills)
Python leads at 83%, SQL 57%, statistics 56%, then a long tail where no tool passes 26%. The surprise sits off the chart: communication appears in 28% of ads, more often than Tableau, AWS or Hadoop.
Caption: Seek Australia, Data Scientist ads 2019–2022, n = 3,204; technical skills shown, professional skills discussed in text. No LLM skill appears because the ads predate 2023: large language models sit at 0% here and at 15.8% in 1,355 US ads from 2023–24.

**6. Preliminary result: one profile against one role** (KEY FIGURE: block6_gap_chart.png; teal bars = the resume has the skill, copper = missing; bar length = share of 3,204 Seek ads mentioning it)
Three big numbers: 14 skills the ad demands, 3 covered, 11 missing.
One real Data Scientist ad, Sydney CBD, against a sample early-career resume. The biggest gaps by market demand are machine learning (71% of ads), predictive models (25%) and AI principles (22%): modelling, not tooling. Six required skills are ESCO phrasings no ad uses, so they are counted but not drawn.
Caption: ESCO dictionary extraction plus TF-IDF fuzzy matching; demand from n = 3,204 Seek Australia ads; the resume is synthetic, not a real person.

**7. Which UTS subject fills each gap** (figure: block7_course_table.png, or rebuild as a table)
Predictive models → 36120 Advanced Machine Learning Application: implement and evaluate advanced machine learning techniques to real-world problems.
Cloud technologies → 42904 Cloud Computing and Software as a Service: articulate the need for cloud computing and its elements.
Data models → 94693 Big Data Engineering: data modelling, big data, distributed processing and streaming.
Analytical calculations → 36103 Statistical Thinking for Data Science: formulate precise inquiries and justify the statistical tools used.
Caption: keyword match between each missing ESCO skill and the learning outcomes of 70 UTS subjects; Part B replaces it with embedding similarity. 42904 sits outside MDSI but is open as an elective.

**8. How we will measure each stage: traditional vs. modern** (build as a table)
Skill extraction: ESCO dictionary → spaCy NER → LLM API; precision, recall, F1; 200 hand-labelled LinkedIn ads.
Skill matching: TF-IDF cosine → sentence embeddings; Precision@5 and MRR; 50 team-labelled CV–JD pairs.
Chat (RAG): keyword search → LLM with FAISS retrieval; LLM-as-judge on relevance and faithfulness, 1–5; 30 curated questions.
Each stage pits a traditional baseline against a modern method. A measured baseline already justifies the comparison: exact ESCO matching covers only 36% of our 133-skill dictionary, and 55%, including the whole LLM stack, have no ESCO concept at all.

**9. Three-week plan to 14 October, owners named** (build as a Gantt strip: W1 23–29 Sep, W2 30 Sep–6 Oct, W3 7–14 Oct)
Data collection and cleaning, Van Thong, W1 into W2. Skill extraction, Phuong Nhi, W1–W2. Matching, Phuong Nhi, W2–W3. Evaluation and benchmarking, Hoai Thuong, W2–W3. Streamlit app and RAG chat, Quan Pham, W2–W3. Report writing, all, W2–W3.
Milestones: 7 Oct pipeline end-to-end, feature freeze; 11 Oct app and evaluation done; 14 Oct Part B due.
Technical setup: GitHub AndyPham2004/ANLP-AT2-Skills-Map, branch per member; Python 3.11, venv, requirements.txt; spaCy, scikit-learn, sentence-transformers, FAISS; LLM API; Streamlit on Streamlit Cloud or Hugging Face Spaces; resumes processed in memory, PII masked before any API call.

**10. Ethics and references** (small, wherever it fits best)
Resumes stay in memory, never on disk. Names, emails and phone numbers are masked before any LLM call. Ads are used under the dataset licence. Results are labelled as suggestions, not career advice.
European Commission (2024), ESCO v1.2.1. Seek Australia Data Scientist ads 2019–2022, published dataset. Reimers and Gurevych (2019), Sentence-BERT, EMNLP. Lewis et al. (2020), Retrieval-augmented generation, NeurIPS.

## What I want back

First show me a layout with the reading order and the hero figure placed, so I can react before the type is polished. Then the full poster. Tell me the final word count, and if anything did not fit, tell me what you would cut rather than shrinking text below readable size. Export as a PDF at true A0 size, no margins, and keep the editable source.
