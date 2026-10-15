"""Every path the code uses, in one place (layout of 15 Oct 2026; data/README.md is the map).

Only data/ holds data. Code, scripts, tests and notebooks import their paths from here instead of
building them by hand, so a file that moves is changed in one line:

    from skillabus import paths
    seed = pd.read_csv(paths.SKILLS_SEED, skiprows=1)

Scripts outside src/ (data-eda/src/*.py, notebooks/) first put src/ on sys.path, as tests/conftest.py does.

    data/1_knowledge/   what the app looks up: skills, taxonomies, UTS subjects, outside courses
    data/2_demand/      what employers ask for: counts, role profiles, cleaned ads, collection lists
    data/3_tuning/      README only: which threshold was set on which data
    data/4_evaluation/  test labels, the inputs they were made on, results, the committed GPT cache
    data/5_crosscheck/  other markets and platforms, ESCO coverage
    data/raw/           downloads (not in git)
    data/runtime/       written while the app and pipeline run: votes, caches, vector indexes (not in git)
    archive/            frozen: the AT2A poster and the first mock; read, never write
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
KNOWLEDGE = DATA / "1_knowledge"
DEMAND = DATA / "2_demand"
TUNING = DATA / "3_tuning"
EVALUATION = DATA / "4_evaluation"
CROSSCHECK = DATA / "5_crosscheck"
RAW = DATA / "raw"
RUNTIME = DATA / "runtime"
ARCHIVE = ROOT / "archive"

# ------------------------------------------------------------------ 1_knowledge
SKILLS = KNOWLEDGE / "skills"
SKILLS_SEED = SKILLS / "skills_seed_v2.csv"               # the one dictionary: 148 rows (starts with a # line)
SKILL_TO_ESCO = SKILLS / "skill_to_esco.csv"              # dictionary skill -> ESCO concept
SKILLS_SEED_V1 = SKILLS / "original" / "skills_seed.csv"  # Van Thong's 133-row original (poster, EDA)
SKILL_TO_ESCO_V1 = SKILLS / "original" / "skill_to_esco.csv"

TAXONOMIES = KNOWLEDGE / "taxonomies"
ESCO_SKILLS_CLEAN = TAXONOMIES / "esco_skills_clean.csv"
ESCO_LABEL_LOOKUP = TAXONOMIES / "esco_label_lookup.csv"

UTS = KNOWLEDGE / "uts"
SUBJECT_PROFILES = UTS / "subject_profiles.csv"
PREREQUISITES = UTS / "prerequisites.csv"
OFFERINGS = UTS / "offerings.csv"
ASSESSMENTS_SCRAPED = UTS / "assessments_scraped.csv"
SUBJECT_CONTENT = UTS / "subject_content.csv"             # hand-collected rows, optional (template next to it)
SUBJECTS_TEMPLATE = UTS / "subjects_template.csv"

LEARNING_RESOURCES = KNOWLEDGE / "learning_resources"
EXTERNAL_COURSES = LEARNING_RESOURCES / "external_courses.csv"
EXTERNAL_COURSES_MD = LEARNING_RESOURCES / "external_courses.md"

# ------------------------------------------------------------------ 2_demand
SKILL_COUNTS = DEMAND / "skill_counts_v2.csv"             # 3,204 Seek Data Scientist ads 2019-22
SKILL_COUNTS_2026 = DEMAND / "skill_counts_2026.csv"
TOP_SKILLS = DEMAND / "top_skills.csv"
ROLE_PROFILES = DEMAND / "role_profiles.csv"
SKILLS_NOT_TAUGHT = DEMAND / "skills_not_taught_by_uts.csv"

ADS = DEMAND / "ads"
SEEK_ADS = ADS / "jobs_au_seek_datascientist_2019-2022_clean.csv"
RECENT_ADS = ADS / "jobs_au_recent_2024-2026_clean.csv"

COLLECTION = DEMAND / "collection"
ATS_COMPANIES = COLLECTION / "ats_companies.csv"
ATS_CANDIDATES = COLLECTION / "ats_candidates.csv"

EMERGING = DEMAND / "emerging"
EMERGING_CANDIDATES = EMERGING / "emerging_candidates.csv"

# ------------------------------------------------------------------ 4_evaluation
LABELS = EVALUATION / "labels"
AD_SKILLS = LABELS / "ad_skills.csv"
CV_JD_PAIRS = LABELS / "cv_jd_pairs.csv"
SKILL_SUBJECT_PAIRS = LABELS / "skill_subject_pairs.csv"
CHAT_QUESTIONS = LABELS / "chat_questions.csv"

INPUTS = EVALUATION / "inputs"
LABEL_SAMPLE = INPUTS / "seek_label_sample_200.csv"
RESUMES = INPUTS / "resumes_us_2021_clean.csv"

RESULTS = EVALUATION / "results"
LLM_CACHE_EVAL = EVALUATION / "llm_cache"                 # the 30 committed GPT-4o-mini responses; read only

# ------------------------------------------------------------------ 5_crosscheck
SKILL_COUNTS_PRIMARY = CROSSCHECK / "skill_counts_PRIMARY.csv"
SKILL_COUNTS_LINKEDIN_US = CROSSCHECK / "skill_counts_linkedin_us.csv"
SKILL_COUNTS_GLASSDOOR_AU = CROSSCHECK / "skill_counts_glassdoor_au_2022.csv"
AU_VS_US = CROSSCHECK / "au_vs_us_comparison.csv"
EXTRACTOR_AGREEMENT = CROSSCHECK / "extractor_agreement.csv"
EXTRACTOR_AGREEMENT_DECOMPOSED = CROSSCHECK / "extractor_agreement_decomposed.csv"
SOURCE_COUNTS = CROSSCHECK / "source_counts.csv"
ESCO_COVERAGE = CROSSCHECK / "esco_coverage"

# ------------------------------------------------------------------ raw (not in git; data/README.md says where each comes from)
ESCO_RAW = RAW / "taxonomy_esco_v1.2.1" / "skills_en.csv"
ONET_TOOLS_RAW = RAW / "taxonomy_onet_v31" / "software_skills.csv"
UTS_SUBJECTS_RAW = RAW / "uts_subjects_2026.csv"
SEEK_RAW = RAW / "jobs_au_seek_datascientist_2019-2022.csv"
SEEK_AUTHORFLAGS_RAW = RAW / "jobs_au_seek_datascience_2019-2022_authorflags.csv"
RESUMES_RAW = RAW / "resumes_us_2021.csv"
DATA_JOBS_RAW = RAW / "data_jobs_hf" / "data_jobs.csv"
GLASSDOOR_RAW = RAW / "glassdoor_au_2022"
EXTERNAL_PAGES_RAW = RAW / "external_courses_pages"       # official course pages saved for build_external.py

# ------------------------------------------------------------------ runtime (not in git)
CACHE = RUNTIME / "cache"
LLM_CACHE = CACHE / "llm_extract"                         # GPT responses for any other text; written here only
LIGHTCAST_CACHE = CACHE / "lightcast"
ESCO_INDEX = CACHE / "esco"                               # ESCO label table and embeddings
RAG_INDEX = CACHE / "rag"                                 # chat retrieval vectors
FEEDBACK = RUNTIME / "feedback.csv"                       # thumbs up/down from the app

# ------------------------------------------------------------------ outside data/
ENV_FILE = ROOT / ".env"                                  # API keys (gitignored; copy .env.example)
SAMPLES = ROOT / "app" / "mock"                           # the app's "use the sample" texts: not data
SAMPLE_AD = SAMPLES / "sample_ad.txt"
SAMPLE_RESUME = SAMPLES / "sample_resume.txt"
FIGURES = ROOT / "docs" / "figures"                       # EDA figures for the report
REPORT_FIGURES = ROOT / "docs" / "report" / "figures"
POSTER_ARCHIVE = ARCHIVE / "poster_AT2A"
POSTER_DATA = POSTER_ARCHIVE / "data"                     # the numbers on the AT2A poster, frozen
POSTER_GAP = POSTER_DATA / "gap.csv"
POSTER_AD_SKILL_LONG = POSTER_DATA / "ad_skill_long.csv"

# Committed files the code reads: tests/test_paths.py checks each one exists.
COMMITTED = (
    SKILLS_SEED, SKILL_TO_ESCO, SKILLS_SEED_V1, SKILL_TO_ESCO_V1, ESCO_SKILLS_CLEAN, ESCO_LABEL_LOOKUP,
    SUBJECT_PROFILES, PREREQUISITES, OFFERINGS, ASSESSMENTS_SCRAPED, SUBJECTS_TEMPLATE, EXTERNAL_COURSES,
    EXTERNAL_COURSES_MD, SKILL_COUNTS, SKILL_COUNTS_2026, TOP_SKILLS, ROLE_PROFILES, SKILLS_NOT_TAUGHT,
    SEEK_ADS, RECENT_ADS, ATS_COMPANIES, ATS_CANDIDATES, EMERGING_CANDIDATES, AD_SKILLS, CV_JD_PAIRS,
    SKILL_SUBJECT_PAIRS, CHAT_QUESTIONS, LABEL_SAMPLE, RESUMES, LLM_CACHE_EVAL, SKILL_COUNTS_PRIMARY,
    SKILL_COUNTS_LINKEDIN_US, SKILL_COUNTS_GLASSDOOR_AU, AU_VS_US, EXTRACTOR_AGREEMENT,
    EXTRACTOR_AGREEMENT_DECOMPOSED, SOURCE_COUNTS, ESCO_COVERAGE, SAMPLE_AD, SAMPLE_RESUME, FIGURES,
    POSTER_GAP, POSTER_AD_SKILL_LONG,
)
# Written while the app or pipeline runs; .gitignore keeps all of it out of git.
NOT_IN_GIT = (RAW, RUNTIME)
