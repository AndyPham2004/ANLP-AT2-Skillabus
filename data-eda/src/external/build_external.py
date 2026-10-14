"""Build data/processed/external_courses.csv + external_courses.md from the downloaded official pages.

Text is taken verbatim: by block index from dl/<slug>.html (same parser as totext.py), from the
HTML-escaped JSON the Google Skills / Hugging Face pages embed, or pasted from the rendered page
text (Kaggle, dbt Learn, tensorflow.org, which only render in a browser).
"""
import csv
import html as htmlmod
import re
import sys
from collections import Counter, OrderedDict
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
DL = HERE / "dl"
ROOT = Path(r"C:\MDSI\03.Applied NLP\assessments\at2")
PROC = ROOT / "data" / "processed"
DATE = "2026-10-13"
COLLECTED_BY = "Claude (web)"

# ----------------------------------------------------------------------------- page parser
BLOCK = {"h1", "h2", "h3", "h4", "h5", "p", "li", "dt", "dd", "title", "summary", "blockquote"}
SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header"}


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.buf, self.out, self.skip = [], [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        if tag in BLOCK:
            self.flush()
            self.stack.append(tag)
        if tag == "br":
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        if tag in BLOCK:
            self.flush()
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if text:
            self.out.append((self.stack[-1] if self.stack else "-", text))


_cache = {}


def blocks(slug):
    if slug not in _cache:
        p = P()
        p.feed((DL / f"{slug}.html").read_text(encoding="utf-8", errors="replace"))
        p.flush()
        _cache[slug] = p.out
    return _cache[slug]


def B(slug, *idx):
    """Texts of the given block indices."""
    return [blocks(slug)[i][1] for i in idx]


def BR(slug, a, b, tags=None):
    """Texts of blocks a..b inclusive, optionally only those with the given tags."""
    out = []
    for i in range(a, b + 1):
        tag, text = blocks(slug)[i]
        if tags is None or tag in tags:
            out.append(text)
    return out


def clean_heading(t):
    return re.sub(r"[#¶\u200b]+$", "", t).strip()


TITLE_RX = re.compile(r'"title":"((?:[^"\\]|\\.){3,140})"')


def JT(slug):
    h = htmlmod.unescape((DL / f"{slug}.html").read_text(encoding="utf-8", errors="replace"))
    seen = []
    for m in TITLE_RX.findall(h):
        m = m.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8") if "\\u" in m else m
        if m not in seen:
            seen.append(m)
    return seen


GCS_DROP = re.compile(r"^(Quiz|Completion|Your Next Steps|Course [Rr]esources|Course [Ss]ummary|Reading List|Skill badge|Module \d+ Quiz)$")


def gcs_modules(slug, course_name):
    return [t for t in JT(slug) if not GCS_DROP.match(t) and t != course_name]


def dlai_lessons(slug, a, b):
    out = []
    for t in BR(slug, a, b):
        m = re.match(r"^(.*?)(Video with Code Example|Video)・\d+m$", t)
        out.append(m.group(1) if m else t)
    return out


def ms_modules(slug, a, b):
    """Microsoft Learn learning-path pages: '-' block 'Add <title>' followed by a <p> description."""
    out, bl = [], blocks(slug)
    i = a
    while i <= b:
        tag, text = bl[i]
        if tag == "-" and text != "Add Start":
            title = re.sub(r"^Add ", "", text)
            desc = bl[i + 1][1] if i + 1 <= b and bl[i + 1][0] == "p" else ""
            out.append(f"{title} — {desc}" if desc else title)
            i += 2
        else:
            i += 1
    return out


def pairs(slug, idx_pairs, sep=" — "):
    return [f"{clean_heading(blocks(slug)[a][1])}{sep}{blocks(slug)[b][1]}" for a, b in idx_pairs]


SENT_RX = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“(0-9🤗])")


def sentences(paragraphs):
    out = []
    for ptxt in paragraphs:
        for chunk in re.split(r"\s\*\s", ptxt):  # Coursera description bullets are written as " * "
            for s in SENT_RX.split(chunk):
                s = s.strip()
                if len(s) > 3:
                    out.append(s)
    return out


# ----------------------------------------------------------------------------- course definitions
C = []


def course(code, name, provider, url, cost, desc, modules, note=""):
    C.append(dict(code=code, name=name, provider=provider, url=url, cost=cost, desc=desc, modules=modules, note=note))


# --- Hugging Face LLM Course
hf_titles = JT("hf_llm")
hf_mods, chap = [], None
for t in hf_titles:
    if re.search(r"(quiz|exam|check!|completed!)$", t, re.I) or t == "Certification exam":
        continue
    if re.match(r"^\d+\. ", t):
        chap = t
        hf_mods.append(t)
    elif chap:
        hf_mods.append(f"{chap}: {t}")
course(
    "EXT-HF-LLM", "Hugging Face LLM Course", "Hugging Face", "https://huggingface.co/learn/llm-course/chapter1/1", "free",
    B("hf_llm", 11, 12, 13, 15, 16, 17, 18, 19) + BR("hf_llm", 22, 25) + B("hf_llm", 46),
    hf_mods,
)

# --- DeepLearning.AI short courses
course(
    "EXT-DLAI-PROMPT-ENG", "ChatGPT Prompt Engineering for Developers", "DeepLearning.AI",
    "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/", "free",
    B("dlai_prompt", 23) + BR("dlai_prompt", 24, 27) + B("dlai_prompt", 28, 32) + BR("dlai_prompt", 19, 21) + B("dlai_prompt", 69),
    dlai_lessons("dlai_prompt", 35, 43),
)
course(
    "EXT-DLAI-LANGCHAIN", "LangChain for LLM Application Development", "DeepLearning.AI",
    "https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/", "free",
    B("dlai_langchain", 24, 25) + BR("dlai_langchain", 26, 30) + B("dlai_langchain", 31, 33) + BR("dlai_langchain", 20, 22) + B("dlai_langchain", 67),
    dlai_lessons("dlai_langchain", 36, 43),
)
course(
    "EXT-DLAI-VECTOR-DB", "Vector Databases: from Embeddings to Applications", "DeepLearning.AI",
    "https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/", "free",
    BR("dlai_vectordb", 23, 29) + B("dlai_vectordb", 31) + BR("dlai_vectordb", 19, 21) + B("dlai_vectordb", 63),
    dlai_lessons("dlai_vectordb", 34, 41),
)
course(
    "EXT-DLAI-ADVANCED-RAG", "Building and Evaluating Advanced RAG", "DeepLearning.AI",
    "https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/", "free",
    BR("dlai_rag", 23, 28) + B("dlai_rag", 30) + BR("dlai_rag", 19, 21) + B("dlai_rag", 62),
    dlai_lessons("dlai_rag", 33, 38),
)

# --- dbt Learn (rendered page text, Playwright, 13 Oct 2026)
course(
    "EXT-DBT-FUNDAMENTALS", "dbt Fundamentals (dbt Studio)", "dbt Labs (dbt Learn)", "https://learn.getdbt.com/courses/dbt-fundamentals", "free",
    ["Learn the foundational steps of transforming data in dbt with the dbt platform using dbt Studio. Start by connecting dbt to a data warehouse and Git repository, then explore key concepts like modeling, sources, testing, documentation, and deployment. Get hands-on by building a model and running tests in dbt. Course duration: approximately 5.0 hours."],
    ["01. Welcome to dbt Fundamentals (5min): Welcome", "02. Analytics Development Lifecycle (30min): dbt and the ADLC", "03. Set Up dbt (60min): Getting Started",
     "04. Models (60min): Building your First Model", "05. Sources (60min): Understanding Sources", "06. Data Tests (60min): Building Tests",
     "07. Documentation (40min): Documentation Basics", "08. Deployment (30min): Understanding Deployment", "09. Survey and Next Steps (5min): Course Feedback"],
    note="price not printed on the page; dbt Learn on-demand courses are free with registration",
)

# --- Kaggle Learn (rendered page text, Playwright, 13 Oct 2026)
course(
    "EXT-KAGGLE-INTRO-ML", "Intro to Machine Learning", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-machine-learning", "free",
    ["Learn the core ideas in machine learning, and build your first models.", "Hours to earn certificate: 3 (estimated).", "Cost: No cost, like all Kaggle Learn Courses.", "Instructor: Dan Becker.",
     "Builds on: Python. Preparation for: Machine Learning Explainability, Intermediate Machine Learning, Intro to Deep Learning."],
    ["1. How Models Work — The first step if you're new to machine learning.", "2. Basic Data Exploration — Load and understand your data.",
     "3. Your First Machine Learning Model — Building your first model. Hurray!", "4. Model Validation — Measure the performance of your model, so you can test and compare alternatives.",
     "5. Underfitting and Overfitting — Fine-tune your model for better performance.", "6. Random Forests — Using a more sophisticated machine learning algorithm.",
     "7. Machine Learning Competitions — Enter the world of machine learning competitions to keep improving and see your progress."],
)
course(
    "EXT-KAGGLE-INTERMEDIATE-ML", "Intermediate Machine Learning", "Kaggle Learn", "https://www.kaggle.com/learn/intermediate-machine-learning", "free",
    ["Handle missing values, non-numeric values, data leakage, and more.", "Hours to earn certificate: 4 (estimated).", "Cost: No cost, like all Kaggle Learn Courses.", "Instructor: Alexis Cook.",
     "Builds on: Intro to Machine Learning, Pandas. Preparation for: Feature Engineering, Time Series."],
    ["1. Introduction — Review what you need for this course.", "2. Missing Values — Missing values happen. Be prepared for this common challenge in real datasets.",
     "3. Categorical Variables — There's a lot of non-numeric data out there. Here's how to use it for machine learning.",
     "4. Pipelines — A critical skill for deploying (and even testing) complex models with pre-processing.", "5. Cross-Validation — A better way to test your models.",
     "6. XGBoost — The most accurate modeling technique for structured data.", "7. Data Leakage — Find and fix this problem that ruins your model in subtle ways."],
)
course(
    "EXT-KAGGLE-INTRO-DL", "Intro to Deep Learning", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-deep-learning", "free",
    ["Use TensorFlow and Keras to build and train neural networks for structured data.", "Hours to earn certificate: 4 (estimated).", "Cost: No cost, like all Kaggle Learn Courses.", "Instructor: Ryan Holbrook.",
     "Builds on: Intro to Machine Learning. Preparation for: Computer Vision."],
    ["1. A Single Neuron — Learn about linear units, the building blocks of deep learning.", "2. Deep Neural Networks — Add hidden layers to your network to uncover complex relationships.",
     "3. Stochastic Gradient Descent — Use Keras and Tensorflow to train your first neural network.", "4. Overfitting and Underfitting — Improve performance with extra capacity or early stopping.",
     "5. Dropout and Batch Normalization — Add these special layers to prevent overfitting and stabilize training.", "6. Binary Classification — Apply deep learning to another common task.",
     "Bonus Lessons: Detecting the Higgs Boson With TPUs — Get started with Tensor Processing Units (TPUs)!"],
)

# --- fast.ai
fa_html = htmlmod.unescape((DL / "fastai.html").read_text(encoding="utf-8", errors="replace"))
fa_lessons = []
for m in re.finditer(r">(\d{1,2}): ([^<]{3,60})<", fa_html):
    t = f"Lesson {m.group(1)}: {m.group(2).strip()}"
    if t not in fa_lessons:
        fa_lessons.append(t)
fa_lessons.sort(key=lambda s: int(re.search(r"\d+", s).group()))
course(
    "EXT-FASTAI-PRACTICAL-DL", "Practical Deep Learning for Coders", "fast.ai", "https://course.fast.ai/", "free",
    B("fastai", 4, 6) + BR("fastai", 7, 10) + B("fastai", 11, 12, 31, 36, 39),
    fa_lessons,
)

# --- PyTorch
course(
    "EXT-PYTORCH-BASICS", "Learn the Basics (PyTorch Tutorials)", "PyTorch (docs.pytorch.org)", "https://docs.pytorch.org/tutorials/beginner/basics/intro.html", "free",
    B("pytorch", 15, 16, 17),
    [s.strip() for s in re.split(r"\s(?=\d\. )", B("pytorch", 25)[0])],
)

# --- TensorFlow (rendered page text, Playwright, 13 Oct 2026)
course(
    "EXT-TF-TUTORIALS", "TensorFlow Core tutorials", "TensorFlow (tensorflow.org)", "https://www.tensorflow.org/tutorials", "free",
    ["The TensorFlow tutorials are written as Jupyter notebooks and run directly in Google Colab—a hosted notebook environment that requires no setup. At the top of each tutorial, you'll see a Run in Google Colab button. Click the button to open the notebook and run the code yourself.",
     "For beginners: The best place to start is with the user-friendly Keras sequential API. Build models by plugging together building blocks. After these tutorials, read the Keras guide.",
     "For experts: The Keras functional and subclassing APIs provide a define-by-run interface for customization and advanced research. Build your model, then write the forward and backward pass. Create custom layers, activations, and training loops.",
     "The Advanced section has many instructive notebooks examples, including Neural machine translation, Transformers, and CycleGAN."],
    ["Beginner quickstart — This \"Hello, World!\" notebook shows the Keras Sequential API and model.fit.",
     "Keras basics — This notebook collection demonstrates basic machine learning tasks using Keras.",
     "Load data — These tutorials use tf.data to load various data formats and build input pipelines.",
     "Advanced quickstart — This \"Hello, World!\" notebook uses the Keras subclassing API and a custom training loop.",
     "Customization — This notebook collection shows how to build custom layers and training loops in TensorFlow.",
     "Distributed training — Distribute your model training across multiple GPUs, multiple machines or TPUs.",
     "Video tutorials: TensorFlow ML Zero to Hero; Basic Computer Vision with ML"],
)

# --- TensorFlow Text: Classify text with BERT (rendered page text, Playwright, 13 Oct 2026)
course(
    "EXT-TF-CLASSIFY-TEXT-BERT", "Classify text with BERT (TensorFlow Text tutorial)", "TensorFlow (tensorflow.org)", "https://www.tensorflow.org/text/tutorials/classify_text_with_bert", "free",
    ["This tutorial contains complete code to fine-tune BERT to perform sentiment analysis on a dataset of plain-text IMDB movie reviews. In addition to training a model, you will learn how to preprocess text into an appropriate format.",
     "BERT and other Transformer encoder architectures have been wildly successful on a variety of tasks in NLP (natural language processing). They compute vector-space representations of natural language that are suitable for use in deep learning models. The BERT family of models uses the Transformer encoder architecture to process each token of input text in the full context of all tokens before and after, hence the name: Bidirectional Encoder Representations from Transformers.",
     "BERT models are usually pre-trained on a large corpus of text, then fine-tuned for specific tasks.",
     "This notebook trains a sentiment analysis model to classify movie reviews as positive or negative, based on the text of the review."],
    ["About BERT", "Setup", "Sentiment analysis", "Download the IMDB dataset", "Loading models from TensorFlow Hub", "Choose a BERT model to fine-tune", "The preprocessing model",
     "Using the BERT model", "Define your model", "Model training", "Loss function", "Optimizer", "Loading the BERT model and training", "Evaluate the model",
     "Plot the accuracy and loss over time", "Export for inference", "Next steps"],
)

# --- Keras
course(
    "EXT-KERAS-INTRO-ENGINEERS", "Introduction to Keras for engineers", "Keras (keras.io)", "https://keras.io/getting_started/intro_to_keras_for_engineers/", "free",
    B("keras", 4, 7, 9),
    [clean_heading(t) for t in BR("keras", 6, 70, tags={"h2"})],
)
course(
    "EXT-KERAS-TUNER", "Getting started with KerasTuner", "Keras (keras.io)", "https://keras.io/keras_tuner/getting_started/", "free",
    B("keras_tuner2", 4, 8),
    [clean_heading(t) for t in BR("keras_tuner2", 7, 296, tags={"h2", "h3"})],
)

# --- NumPy, scikit-learn, XGBoost, LightGBM, CatBoost
course(
    "EXT-NUMPY-ABSOLUTE-BASICS", "NumPy: the absolute basics for beginners", "NumPy (numpy.org)", "https://numpy.org/doc/stable/user/absolute_beginners.html", "free",
    B("numpy", 6, 7),
    [clean_heading(t) for t in BR("numpy", 8, 442, tags={"h2"})],
)
course(
    "EXT-SKLEARN-GETTING-STARTED", "scikit-learn Getting Started", "scikit-learn (scikit-learn.org)", "https://scikit-learn.org/stable/getting_started.html", "free",
    B("sklearn", 8, 9, 42),
    [clean_heading(t) for t in BR("sklearn", 10, 41, tags={"h2"})],
)
course(
    "EXT-XGBOOST-BOOSTED-TREES", "Introduction to Boosted Trees (XGBoost Tutorials)", "XGBoost (xgboost.readthedocs.io)", "https://xgboost.readthedocs.io/en/stable/tutorials/model.html", "free",
    B("xgb", 5, 6),
    [clean_heading(t) for t in BR("xgb", 7, 78, tags={"h2", "h3"})],
)
course(
    "EXT-LIGHTGBM-PYTHON-INTRO", "LightGBM Python-package Introduction", "LightGBM (lightgbm.readthedocs.io)", "https://lightgbm.readthedocs.io/en/stable/Python-Intro.html", "free",
    B("lightgbm", 4, 5, 6, 7, 8),
    [clean_heading(t) for t in BR("lightgbm", 9, 89, tags={"h2"})],
)
course(
    "EXT-CATBOOST-TUTORIALS", "CatBoost Tutorials", "CatBoost (catboost.ai)", "https://catboost.ai/docs/en/concepts/tutorials", "free",
    B("catboost", 3, 5, 11),
    B("catboost", 9, 10),
)

# --- Google Skills (Google Cloud Skills Boost)
GS = "Google Skills (Google Cloud Skills Boost)"
GS_NOTE = "enrolment free with a Google Skills account; hands-on labs may need credits or a subscription"
course("EXT-GCS-CORE-INFRASTRUCTURE", "Google Cloud Fundamentals: Core Infrastructure", GS, "https://www.cloudskillsboost.google/course_templates/60", "free",
       B("gcp_core", 6), gcs_modules("gcp_core", "Google Cloud Fundamentals: Core Infrastructure"), note=GS_NOTE)
bq_desc = re.sub(r"^.*?Updated \d+ months ago ", "", B("gcp_bq", 5)[0])
course("EXT-GCS-BIGQUERY-INSIGHTS", "Derive Insights from BigQuery Data", GS, "https://www.cloudskillsboost.google/course_templates/623", "free",
       [bq_desc] + BR("gcp_bq", 6, 10) + B("gcp_bq", 11), gcs_modules("gcp_bq", "Derive Insights from BigQuery Data"), note=GS_NOTE)
course("EXT-GCS-LOOKER-ANALYSIS", "Analyzing and Visualizing Data in Looker", GS, "https://www.cloudskillsboost.google/course_templates/323", "free",
       B("gcp_looker", 6), gcs_modules("gcp_looker", "Analyzing and Visualizing Data in Looker"), note=GS_NOTE)
course("EXT-GCS-VERTEX-AI-STUDIO", "Introduction to Vertex AI Studio", GS, "https://www.cloudskillsboost.google/course_templates/552", "free",
       B("gcp_vertex3", 6), gcs_modules("gcp_vertex3", "Introduction to Vertex AI Studio"), note=GS_NOTE)

# --- Microsoft Learn
course("EXT-MSLEARN-TSQL", "Query and modify data with Transact-SQL", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/", "free",
       B("ms_tsql", 16) + ["Prerequisites: " + B("ms_tsql", 18)[0], "Product: " + B("ms_tsql", 11)[0] + ".", "Level: " + B("ms_tsql", 7)[0] + ". Role: " + B("ms_tsql", 13)[0] + "."], ms_modules("ms_tsql", 24, 35))
course("EXT-MSLEARN-AZURE-ML-MLOPS", "Operationalize machine learning models (MLOps)", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/paths/build-first-machine-operations-workflow/", "free",
       B("ms_azureml", 16) + ["Prerequisites: " + "; ".join(BR("ms_azureml", 18, 20)) + "."], ms_modules("ms_azureml", 26, 39))
course("EXT-MSLEARN-GITHUB-ACTIONS-CI", "Build continuous integration workflows by using GitHub Actions", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/modules/github-actions-ci/", "free",
       B("ms_gha", 6) + ["Learning objectives: " + " ".join(BR("ms_gha", 9, 12))], [re.sub(r"\s+min$", "", t) for t in BR("ms_gha", 20, 27)])
course("EXT-MSLEARN-VBA-OFFICE", "Getting started with VBA in Office", "Microsoft Learn", "https://learn.microsoft.com/en-us/office/vba/library-reference/concepts/getting-started-with-vba-in-office", "free",
       B("ms_vba", 10, 11, 14), [clean_heading(t) for t in BR("ms_vba", 17, 150, tags={"h2"})])

# --- Kubernetes, Jenkins, Terraform
course("EXT-K8S-BASICS", "Learn Kubernetes Basics", "Kubernetes (kubernetes.io)", "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "free",
       B("k8s", 4) + ["Using the tutorials, you can learn to: " + " ".join(BR("k8s", 6, 9))] + B("k8s", 11), BR("k8s", 13, 18))
course("EXT-JENKINS-GUIDED-TOUR", "Jenkins Guided Tour: Getting started", "Jenkins (jenkins.io)", "https://www.jenkins.io/doc/pipeline/tour/getting-started/", "free",
       B("jenkins", 24), B("jenkins", 25, 33) + ['Continue to "Create your first Pipeline"'])
course("EXT-TERRAFORM-GET-STARTED-AWS", "Terraform Get Started - AWS", "HashiCorp Developer", "https://developer.hashicorp.com/terraform/tutorials/aws-get-started", "free",
       B("terraform", 4), [re.sub(r"^\d+min", "", t) for t in B("terraform", 6, 9, 12, 15, 18, 21)])

course("EXT-AWS-API-GATEWAY-GET-STARTED", "Get started with API Gateway", "AWS Documentation (docs.aws.amazon.com)", "https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started.html", "free",
       B("aws_apigw", 5, 6, 8, 9, 10, 11), BR("aws_apigw", 13, 17), note="covers the dictionary's `API development` aliases (REST API); the exercise runs within the AWS Free Tier")

# --- web frameworks
course("EXT-DJANGO-FIRST-APP", "Writing your first Django app (Django Getting started)", "Django (docs.djangoproject.com)", "https://docs.djangoproject.com/en/5.2/intro/", "free",
       B("django_idx", 36) + B("django", 36, 37) + ["It'll consist of two parts: " + " ".join(B("django", 39, 40))], BR("django_idx", 37, 49))
fa_nav = re.findall(r'<span class="md-ellipsis">\s*(.*?)\s*</span>', (DL / "fastapi.html").read_text(encoding="utf-8", errors="replace"), re.S)
fa_nav = [t.strip() for t in fa_nav]
i1 = fa_nav.index("Advanced User Guide")
i0 = max(i for i, t in enumerate(fa_nav) if t == "Tutorial - User Guide" and i < i1)
course("EXT-FASTAPI-TUTORIAL", "FastAPI Tutorial - User Guide", "FastAPI (fastapi.tiangolo.com)", "https://fastapi.tiangolo.com/tutorial/", "free",
       B("fastapi", 3, 4, 5, 10, 11), fa_nav[i0 + 1:i1])
course("EXT-FLASK-QUICKSTART", "Flask Quickstart", "Flask (flask.palletsprojects.com)", "https://flask.palletsprojects.com/en/stable/quickstart/", "free",
       B("flask", 9, 11, 13), [clean_heading(t) for t in BR("flask", 10, 239, tags={"h2"})])
course("EXT-STREAMLIT-GET-STARTED", "Get started with Streamlit", "Streamlit (docs.streamlit.io)", "https://docs.streamlit.io/get-started", "free",
       B("streamlit", 2, 12), B("streamlit", 4, 6, 8, 10))

# --- MLOps tooling
course("EXT-MLFLOW-GETTING-STARTED", "Getting Started with MLflow for ML", "MLflow (mlflow.org)", "https://mlflow.org/docs/latest/ml/getting-started/", "free",
       B("mlflow2", 3), pairs("mlflow2", [(4, 5), (7, 8), (10, 11), (13, 14)]))
course("EXT-KUBEFLOW-INTRO", "Kubeflow Getting Started: Introduction", "Kubeflow (kubeflow.org)", "https://www.kubeflow.org/docs/started/introduction/", "free",
       B("kubeflow2", 5, 6, 8, 15), pairs("kubeflow", [(4, 5), (6, 7), (8, 9), (10, 11)]))

# --- NLP libraries
course("EXT-SPACY-ADVANCED-NLP", "Advanced NLP with spaCy", "Explosion (course.spacy.io)", "https://course.spacy.io/en/", "free",
       B("spacy", 3, 5, 7, 9), B("spacy", 2, 4, 6, 8))
course("EXT-NLTK-BOOK", "Natural Language Processing with Python (NLTK Book)", "NLTK (nltk.org)", "https://www.nltk.org/book/", "free",
       ["Natural Language Processing with Python – Analyzing Text with the Natural Language Toolkit. Steven Bird, Ewan Klein, and Edward Loper.",
      "This version of the NLTK book is updated for Python 3 and NLTK 3.", "The first edition of the book, published by O'Reilly, is available at http://nltk.org/book_1ed/.",
      "This book is made available under the terms of the Creative Commons Attribution Noncommercial No-Derivative-Works 3.0 US License."],
       ["0. Preface", "1. Language Processing and Python", "2. Accessing Text Corpora and Lexical Resources", "3. Processing Raw Text", "4. Writing Structured Programs",
      "5. Categorizing and Tagging Words", "6. Learning to Classify Text", "7. Extracting Information from Text", "8. Analyzing Sentence Structure",
      "9. Building Feature Based Grammars", "10. Analyzing the Meaning of Sentences", "11. Managing Linguistic Data", "12. Afterword: Facing the Language Challenge"])

# --- languages
course("EXT-COURSERA-SCALA-FP", "Functional Programming Principles in Scala", "Coursera (École Polytechnique Fédérale de Lausanne)", "https://www.coursera.org/learn/scala-functional-programming", "free-to-audit",
       B("scala_coursera", 48, 49) + ["What you'll learn: " + "; ".join(BR("scala_coursera", 19, 22)) + "."],
       pairs("scala_coursera", [(50, 52), (85, 87), (109, 111), (130, 132), (154, 156), (173, 175)]))
scala_chapters = []
for t in BR("scala_docs", 13, 89):
    if t not in scala_chapters:
        scala_chapters.append(t)
course("EXT-SCALA3-BOOK", "Scala 3 — Book", "Scala documentation (docs.scala-lang.org)", "https://docs.scala-lang.org/scala3/book/introduction.html", "free",
       B("scala_docs", 4, 6, 7), scala_chapters)
course("EXT-COURSERA-ECONOMETRICS", "Econometrics: Methods and Applications", "Coursera (Erasmus University Rotterdam)", "https://www.coursera.org/learn/erasmus-econometrics", "free-to-audit",
       B("econ_coursera", 38),
       pairs("econ_coursera", [(39, 41)]) + B("econ_coursera", 51, 76, 104, 129, 154, 180) + pairs("econ_coursera", [(205, 207), (213, 215)]))
course("EXT-JULIA-GET-STARTED", "Get Started with Julia (julialang.org/learning)", "The Julia Programming Language (julialang.org)", "https://julialang.org/learning/", "free",
       B("julia3", 3, 7, 10, 13, 17),
       ["Julia for Nervous Beginners — A course for people who are hesitant but curious about learning to write code in Julia. Taught by Dr Henri Laurie.",
      "Julia for Data Science — From zero knowledge of Julia's Data Science capabilities to training models and performing analysis. Taught by Dr Huda Nassar.",
      "Intro to DataFrames.jl — In-memory tabular data in Julia using DataFrames.jl. Taught by Bogumił Kamiński.",
      "Computational Modeling (COVID-19) — Computational modeling in Julia with applications to the COVID-19 pandemic. Taught by Alan Edelman & David Sanders.",
      "Decision Making Under Uncertainty — Build and solve decision making problems using the POMDPs.jl ecosystem. Taught by Robert Moss.",
      "High Performance Computing in Julia — Learn high-performance computing using Julia, from single-core optimization to multithreading, distributed computing and GPU programming. Taught by Dr Jamie Mair.",
      "Computational Thinking (MIT) — MIT's open course 18.S191 on computational thinking using Julia, with interactive Pluto notebooks."],
       note="juliaacademy.com timed out from this machine on 13 Oct (fetcher and browser); the julialang.org learning page was used instead")

# --- visualisation
course("EXT-PLOTLY-PYTHON", "Getting started with plotly in Python (+ Fundamentals)", "Plotly (plotly.com)", "https://plotly.com/python/getting-started/", "free",
       B("plotly", 7, 8, 9, 10), [re.sub(r"\s*View Tutorial$", "", t) for t in BR("plotly_fund", 7, 48)])
course("EXT-D3-GETTING-STARTED", "D3: What is D3? / Getting started", "Observable (d3js.org)", "https://d3js.org/getting-started", "free",
       B("d3_what", 3, 7) + B("d3", 3, 5), [clean_heading(t) for t in BR("d3", 4, 49, tags={"h2"})])
course("EXT-QLIK-FREE-TRAINING", "Free Data Analytics and Data Integration Training with Qlik (Get started with Qlik Sense)", "Qlik (qlik.com)", "https://www.qlik.com/us/customer-success/learn/qlik-academy/free-training", "free",
       B("qlik_free", 2, 4, 5, 35), [], note="course pages on learning.qlik.com return HTTP 403 to both the fetcher and the browser; no module list could be copied")

# --- cloud / data platforms
course("EXT-AWS-REDSHIFT-GET-STARTED", "Get started with Amazon Redshift provisioned data warehouses", "AWS Documentation (docs.aws.amazon.com)", "https://docs.aws.amazon.com/redshift/latest/gsg/new-user.html", "free",
       B("redshift", 6, 7, 10), BR("redshift", 33, 40), note="documentation is free; the sample cluster accrues AWS charges while it runs")
course("EXT-AWS-SAGEMAKER-GET-STARTED", "Getting started with Amazon SageMaker AI (Machine Learning Tutorials)", "AWS (aws.amazon.com)", "https://aws.amazon.com/sagemaker/ai/getting-started/", "free",
       B("sagemaker2", 12),
       ["Data Scientists: Develop ML models using code — " + t for t in B("sagemaker2", 15, 17, 19)]
       + ["Data Scientists: Low-code ML — " + t for t in B("sagemaker2", 23, 25, 27)]
       + ["ML Engineers: MLOps — " + t for t in B("sagemaker2", 31, 33, 35)]
       + ["Business Analysts: No-code ML — " + t for t in B("sagemaker2", 45, 47)])
course("EXT-ELASTIC-SEARCH-GET-STARTED", "Get started with search (Elasticsearch)", "Elastic (elastic.co/docs)", "https://www.elastic.co/docs/solutions/search/get-started", "free",
       B("elastic2", 5, 32), [clean_heading(t) for t in BR("elastic2", 13, 46, tags={"h2"}) if not t.startswith("Related")] + BR("elastic2", 33, 35))
course("EXT-REDIS-UNIVERSITY", "Redis University: Get Started with Redis", "Redis (redis.io)", "https://redis.io/tutorials/university/", "free",
       [B("redis", 6)[0][B("redis", 6)[0].index("Redis University offers"):]] + ["What you'll learn: " + "; ".join(BR("redis", 8, 12)) + "."] + B("redis", 19),
       BR("redis", 15, 18))
course("EXT-CASSANDRA-QUICKSTART", "Get Started with Apache Cassandra", "Apache Cassandra (cassandra.apache.org)", "https://cassandra.apache.org/_/quickstart.html", "free",
       B("cassandra2", 2, 11, 12), [t.title() if t.isupper() else t for t in B("cassandra2", 3, 7, 10, 14, 18, 23, 25, 27)])
course("EXT-HIVE-TUTORIAL", "Apache Hive Tutorial", "Apache Hive (cwiki.apache.org)", "https://cwiki.apache.org/confluence/display/Hive/Tutorial", "free",
       B("hive", 27, 28, 30, 34), B("hive", 26, 29, 31, 35, 47, 111, 316, 333, 376, 391), note="wiki is read-only since the migration; page last updated 23 Feb 2021")

# --- data wrangling
course("EXT-DASK-TUTORIAL", "Dask Tutorial", "Dask (tutorial.dask.org)", "https://tutorial.dask.org/", "free",
       B("dask", 10, 18), BR("dask", 11, 16))
course("EXT-POLARS-USER-GUIDE", "Polars user guide", "Polars (docs.pola.rs)", "https://docs.pola.rs/", "free",
       B("polars2", 3, 14, 22) + ["The goal of Polars is to provide a lightning fast DataFrame library that: " + " ".join(BR("polars2", 17, 21))],
       ["Getting started", "Concepts", "Expressions", "Transformations", "Lazy API", "IO", "Plugins", "SQL", "Migrating", "Misc"])

# --- computer vision
course("EXT-OPENCV-PYTHON-TUTORIALS", "OpenCV-Python Tutorials", "OpenCV (docs.opencv.org)", "https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html", "free",
       BR("opencv", 3, 23)[::2], pairs("opencv", [(i, i + 1) for i in range(2, 23, 2)]))

# ----------------------------------------------------------------------------- write CSV
rows = []
for c in C:
    seen = set()
    desc = [s for s in sentences(c["desc"]) if not (s in seen or seen.add(s))]
    mods = [m.strip() for m in c["modules"] if m and m.strip()]
    mods = [m for m in mods if not (m in seen or seen.add(m))]
    for s in desc:
        rows.append([c["code"], c["name"], "external", "description", s, c["url"], COLLECTED_BY, c["provider"], c["cost"], DATE])
    for m in mods:
        rows.append([c["code"], c["name"], "external", "weekly_topic", m, c["url"], COLLECTED_BY, c["provider"], c["cost"], DATE])
    c["n_desc"], c["n_mod"] = len(desc), len(mods)

out_csv = PROC / "external_courses.csv"
with open(out_csv, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["subject_code", "subject_name", "course", "layer", "text", "source_url", "collected_by", "provider", "cost", "date_checked"])
    w.writerows(rows)

# ----------------------------------------------------------------------------- coverage (same matcher as step 1)
with open(PROC / "skills_seed_v2.csv", encoding="utf-8", newline="") as f:
    skills = [s for s in csv.DictReader([ln for ln in f if not ln.startswith("#")]) if s["category"] != "Professional"]
with open(PROC / "uncovered_skills_2026-10-13.csv", encoding="utf-8", newline="") as f:
    unc = list(csv.DictReader(f))
uncovered = [r["skill"] for r in unc if r["covered_by_uts"] == "n"]


def pat(phrase):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(phrase) + r"(?![A-Za-z0-9])", re.I)


text_by_course = OrderedDict()
for r in rows:
    text_by_course.setdefault(r[0], []).append(r[4])
skill_courses = {}
for s in skills:
    phrases = [s["canonical"]] + [a.strip() for a in s["aliases"].split("|") if a.strip()]
    rxs = [pat(p) for p in phrases]
    hit = [code for code, texts in text_by_course.items() if any(rx.search(t) for rx in rxs for t in texts)]
    skill_courses[s["canonical"]] = hit
course_skills = {code: [k for k, v in skill_courses.items() if code in v] for code in text_by_course}

covered_unc = [k for k in uncovered if skill_courses[k]]
missing_unc = [k for k in uncovered if not skill_courses[k]]
pct = {r["skill"]: (r["pct_2019_22"], r["pct_2026"]) for r in unc}

print(f"courses: {len(C)}  rows: {len(rows)}  description rows: {sum(c['n_desc'] for c in C)}  module rows: {sum(c['n_mod'] for c in C)}")
print(f"uncovered skills: {len(uncovered)}  with a course: {len(covered_unc)}  still without: {len(missing_unc)} -> {missing_unc}")
thin = [c["code"] for c in C if c["n_desc"] + c["n_mod"] < 3]
print("courses with < 3 rows:", thin)
for c in C:
    print(f"  {c['code']:34s} desc={c['n_desc']:3d} mod={c['n_mod']:3d}  uncovered skills matched: {[k for k in course_skills[c['code']] if k in uncovered]}")

# ----------------------------------------------------------------------------- markdown notes
providers = Counter(c["provider"] for c in C)
md = []
md.append("# external_courses.csv\n")
md.append("Outside-UTS courses for the learning path's second tier (ideas doc 4.5; issue #77 is Akash's draft, this is the\n"
          "data-backed version). Same shape as `subject_profiles.csv` plus `provider`, `cost`, `date_checked`, so\n"
          "`recommend()` can run a second pass over it for the gaps no UTS subject fills. Courses carry no UTS credit.\n")
md.append("| | |\n|---|---|")
md.append(f"| Rows | {len(rows)} ({sum(c['n_desc'] for c in C)} `description`, {sum(c['n_mod'] for c in C)} `weekly_topic`) |")
md.append(f"| Courses | {len(C)} from {len(providers)} providers |")
md.append(f"| Built by | `Claude (web)`, {DATE}; builder script kept in the session scratchpad, not in the repo |")
md.append("| Codes | `EXT-<PROVIDER>-<slug>`, `course` = `external` |")
md.append("| Layers | `description` = one row per sentence of the course's own description; `weekly_topic` = one row per module / lesson / chapter / section title, copied verbatim |")
md.append("| Cost | `free`, `free-to-audit` (Coursera), `paid` (none used) |\n")
md.append("## How it was built\n")
md.append("1. `uncovered_skills_2026-10-13.csv`: the 126 non-Professional dictionary skills (`skills_seed_v2.csv`) were matched\n"
          "   against every row of `subject_profiles.csv` (6,848 rows, 360 subjects) as whole phrases, case-insensitive,\n"
          "   canonical name or any alias (`(?<![A-Za-z0-9])phrase(?![A-Za-z0-9])`). 54 skills matched no subject; they are\n"
          "   sorted by `pct_ads` of `skill_counts_v2.csv` (the 2019-22 Seek share) and followed by the 19 covered skills\n"
          "   with `pct_2026 >= 10` in `skill_counts_2026.csv` (`covered_by_uts=y`), 73 rows in all.")
md.append("2. For each uncovered skill (all 54, not only the top 30, because one page often covers several) the official\n"
          "   course or tutorial page was downloaded (urllib, one request per page, 1.5 s apart) and the description and the\n"
          "   module list were copied from the page's own text. Kaggle Learn, dbt Learn and tensorflow.org only render in a\n"
          "   browser, so their text was read from the rendered page (Playwright). Google Skills and the Hugging Face course\n"
          "   keep their module lists in JSON inside the page; those titles were taken from there. Nothing was paraphrased\n"
          "   and no module was invented; where a page has no module list (Qlik) only description rows were kept.")
md.append("3. Priority: free first (Hugging Face Learn, DeepLearning.AI short courses, fast.ai, Google Skills, Microsoft\n"
          "   Learn, dbt Learn, Kaggle Learn, official documentation tutorials); Coursera only where free to audit (EPFL\n"
          "   Scala, Erasmus Econometrics).")
md.append("4. Coverage below was recomputed on this file with the same matcher as step 1, so a skill counts as covered only\n"
          "   if the course text literally names it or an alias.\n")
md.append("## Providers\n")
md.append("| Provider | Courses |\n|---|---|")
for p, n in providers.most_common():
    md.append(f"| {p} | {n} |")
md.append("")
md.append("## Courses\n")
md.append("| Code | Course | Cost | Rows | Uncovered skills it names |\n|---|---|---|---|---|")
for c in C:
    ks = ", ".join(k for k in course_skills[c["code"]] if k in uncovered) or "—"
    md.append(f"| `{c['code']}` | [{c['name']}]({c['url']}) | {c['cost']} | {c['n_desc'] + c['n_mod']} | {ks} |")
md.append("")
md.append("## Uncovered skills: course found\n")
md.append("| Skill | 2019-22 % | 2026 % | Courses |\n|---|---|---|---|")
for k in covered_unc:
    md.append(f"| {k} | {pct[k][0]} | {pct[k][1]} | {', '.join('`' + c + '`' for c in skill_courses[k])} |")
md.append("")
md.append("## Uncovered skills: still without a course\n")
if missing_unc:
    md.append("| Skill | 2019-22 % | 2026 % | Why |\n|---|---|---|---|")
    for k in missing_unc:
        md.append(f"| {k} | {pct[k][0]} | {pct[k][1]} | see notes below |")
else:
    md.append("None: every one of the 54 uncovered skills is named by at least one course.")
md.append("")
md.append("## Notes and caveats\n")
for c in C:
    if c["note"]:
        md.append(f"- `{c['code']}`: {c['note']}.")
md.append("- DeepLearning.AI short courses: the page says \"Course access is free for a limited time during the DeepLearning.AI\n"
          "  learning platform beta!\"; the graded assignment and the accomplishment need PRO. Recorded as `free`.")
md.append("- Coursera (EPFL Scala, Erasmus Econometrics): `free-to-audit`; the certificate is paid.")
md.append("- Google Skills (the cloudskillsboost.google URLs now redirect to skills.google): enrolment is free, hands-on labs\n"
          "  may need credits or a subscription; the course descriptions and module titles are what the page carries.")
md.append("- Kaggle Learn pages state \"No cost, like all Kaggle Learn Courses\".")
md.append("- Documentation tutorials (PyTorch, TensorFlow, Keras, NumPy, scikit-learn, XGBoost, LightGBM, CatBoost, Kubernetes,\n"
          "  Jenkins, Django, FastAPI, Flask, Streamlit, MLflow, Kubeflow, Terraform, AWS, Elastic, Cassandra, Hive, Dask,\n"
          "  Polars, OpenCV, NLTK, D3, Plotly, Scala 3 Book) have no cost; their \"modules\" are the tutorial's own section\n"
          "  or chapter titles.")
md.append("- `pct_2019_22` in `uncovered_skills_2026-10-13.csv` is `pct_ads` from `skill_counts_v2.csv`; the column of the same\n"
          "  name in `skill_counts_2026.csv` differs slightly (e.g. Python 82.8 vs 84.5, Scala 15.1 vs 16.4), a different\n"
          "  matcher run. The task said to sort by the v2 file, so that is what is stored.")
md.append("- The step-1 matcher is case-insensitive as instructed, so a few *covered* verdicts rest on common words: `Go`\n"
          "  (6 subjects), `R` (13, incl. the bare letter), `Spark`, `Excel`, `A/B testing` via the alias `experimentation`.\n"
          "  Those skills are therefore absent from the uncovered list even though no subject may teach them.")
md.append("- Two matches in the coverage table are alias artefacts rather than course content: `Transformers` on\n"
          "  `EXT-SKLEARN-GETTING-STARTED` (scikit-learn's \"Transformers and pre-processors\" section, not NLP transformers) and\n"
          "  `Streamlit` on `EXT-HF-LLM` / `EXT-FASTAI-PRACTICAL-DL` (the dictionary lists `gradio` as a Streamlit alias). Every\n"
          "  other skill in that table has a course that is actually about it.")
md.append("- 56 courses rather than the 25-40 aimed for: 54 skills had no UTS subject and most needed their own page; the\n"
          "  thinnest entries (CatBoost, Jenkins, Qlik, Kubeflow) can be dropped without losing a skill except Qlik and Jenkins.")
md.append("- Pages that only render in a browser were read with Playwright (Kaggle Learn blocks urllib with reCAPTCHA, dbt Learn\n"
          "  and tensorflow.org serve their content by script). juliaacademy.com timed out; learning.qlik.com returned 403.")
md.append("- Read with `dtype=str`; the file has no leading `#` line.")
(PROC / "external_courses.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", out_csv, "and external_courses.md")
