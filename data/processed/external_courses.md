# external_courses.csv

Outside-UTS courses for the learning path's second tier (ideas doc 4.5; issue #77 is Akash's draft, this is the
data-backed version). Same shape as `subject_profiles.csv` plus `provider`, `cost`, `date_checked`, so
`recommend()` can run a second pass over it for the gaps no UTS subject fills. Courses carry no UTS credit.

| | |
|---|---|
| Rows | 1167 (414 `description`, 753 `weekly_topic`) |
| Courses | 56 from 42 providers |
| Built by | `Claude (web)`, 2026-10-13; builder script kept in the session scratchpad, not in the repo |
| Codes | `EXT-<PROVIDER>-<slug>`, `course` = `external` |
| Layers | `description` = one row per sentence of the course's own description; `weekly_topic` = one row per module / lesson / chapter / section title, copied verbatim |
| Cost | `free`, `free-to-audit` (Coursera), `paid` (none used) |

## How it was built

1. `uncovered_skills_2026-10-13.csv`: the 126 non-Professional dictionary skills (`skills_seed_v2.csv`) were matched
   against every row of `subject_profiles.csv` (6,848 rows, 360 subjects) as whole phrases, case-insensitive,
   canonical name or any alias (`(?<![A-Za-z0-9])phrase(?![A-Za-z0-9])`). 54 skills matched no subject; they are
   sorted by `pct_ads` of `skill_counts_v2.csv` (the 2019-22 Seek share) and followed by the 19 covered skills
   with `pct_2026 >= 10` in `skill_counts_2026.csv` (`covered_by_uts=y`), 73 rows in all.
2. For each uncovered skill (all 54, not only the top 30, because one page often covers several) the official
   course or tutorial page was downloaded (urllib, one request per page, 1.5 s apart) and the description and the
   module list were copied from the page's own text. Kaggle Learn, dbt Learn and tensorflow.org only render in a
   browser, so their text was read from the rendered page (Playwright). Google Skills and the Hugging Face course
   keep their module lists in JSON inside the page; those titles were taken from there. Nothing was paraphrased
   and no module was invented; where a page has no module list (Qlik) only description rows were kept.
3. Priority: free first (Hugging Face Learn, DeepLearning.AI short courses, fast.ai, Google Skills, Microsoft
   Learn, dbt Learn, Kaggle Learn, official documentation tutorials); Coursera only where free to audit (EPFL
   Scala, Erasmus Econometrics).
4. Coverage below was recomputed on this file with the same matcher as step 1, so a skill counts as covered only
   if the course text literally names it or an alias.

## Providers

| Provider | Courses |
|---|---|
| DeepLearning.AI | 4 |
| Google Skills (Google Cloud Skills Boost) | 4 |
| Microsoft Learn | 4 |
| Kaggle Learn | 3 |
| TensorFlow (tensorflow.org) | 2 |
| Keras (keras.io) | 2 |
| AWS Documentation (docs.aws.amazon.com) | 2 |
| Hugging Face | 1 |
| dbt Labs (dbt Learn) | 1 |
| fast.ai | 1 |
| PyTorch (docs.pytorch.org) | 1 |
| NumPy (numpy.org) | 1 |
| scikit-learn (scikit-learn.org) | 1 |
| XGBoost (xgboost.readthedocs.io) | 1 |
| LightGBM (lightgbm.readthedocs.io) | 1 |
| CatBoost (catboost.ai) | 1 |
| Kubernetes (kubernetes.io) | 1 |
| Jenkins (jenkins.io) | 1 |
| HashiCorp Developer | 1 |
| Django (docs.djangoproject.com) | 1 |
| FastAPI (fastapi.tiangolo.com) | 1 |
| Flask (flask.palletsprojects.com) | 1 |
| Streamlit (docs.streamlit.io) | 1 |
| MLflow (mlflow.org) | 1 |
| Kubeflow (kubeflow.org) | 1 |
| Explosion (course.spacy.io) | 1 |
| NLTK (nltk.org) | 1 |
| Coursera (École Polytechnique Fédérale de Lausanne) | 1 |
| Scala documentation (docs.scala-lang.org) | 1 |
| Coursera (Erasmus University Rotterdam) | 1 |
| The Julia Programming Language (julialang.org) | 1 |
| Plotly (plotly.com) | 1 |
| Observable (d3js.org) | 1 |
| Qlik (qlik.com) | 1 |
| AWS (aws.amazon.com) | 1 |
| Elastic (elastic.co/docs) | 1 |
| Redis (redis.io) | 1 |
| Apache Cassandra (cassandra.apache.org) | 1 |
| Apache Hive (cwiki.apache.org) | 1 |
| Dask (tutorial.dask.org) | 1 |
| Polars (docs.pola.rs) | 1 |
| OpenCV (docs.opencv.org) | 1 |

## Courses

| Code | Course | Cost | Rows | Uncovered skills it names |
|---|---|---|---|---|
| `EXT-HF-LLM` | [Hugging Face LLM Course](https://huggingface.co/learn/llm-course/chapter1/1) | free | 117 | Hugging Face, Transformers, Named entity recognition, Vector databases, Streamlit |
| `EXT-DLAI-PROMPT-ENG` | [ChatGPT Prompt Engineering for Developers](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/) | free | 25 | Prompt engineering |
| `EXT-DLAI-LANGCHAIN` | [LangChain for LLM Application Development](https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/) | free | 22 | LangChain |
| `EXT-DLAI-VECTOR-DB` | [Vector Databases: from Embeddings to Applications](https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/) | free | 21 | RAG, Vector databases |
| `EXT-DLAI-ADVANCED-RAG` | [Building and Evaluating Advanced RAG](https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/) | free | 18 | RAG |
| `EXT-DBT-FUNDAMENTALS` | [dbt Fundamentals (dbt Studio)](https://learn.getdbt.com/courses/dbt-fundamentals) | free | 13 | dbt |
| `EXT-KAGGLE-INTRO-ML` | [Intro to Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning) | free | 13 | — |
| `EXT-KAGGLE-INTERMEDIATE-ML` | [Intermediate Machine Learning](https://www.kaggle.com/learn/intermediate-machine-learning) | free | 13 | XGBoost |
| `EXT-KAGGLE-INTRO-DL` | [Intro to Deep Learning](https://www.kaggle.com/learn/intro-to-deep-learning) | free | 13 | TensorFlow, Keras |
| `EXT-FASTAI-PRACTICAL-DL` | [Practical Deep Learning for Coders](https://course.fast.ai/) | free | 42 | PyTorch, Hugging Face, Transformers, Streamlit |
| `EXT-PYTORCH-BASICS` | [Learn the Basics (PyTorch Tutorials)](https://docs.pytorch.org/tutorials/beginner/basics/intro.html) | free | 12 | PyTorch |
| `EXT-TF-TUTORIALS` | [TensorFlow Core tutorials](https://www.tensorflow.org/tutorials) | free | 17 | TensorFlow, Keras, Transformers |
| `EXT-TF-CLASSIFY-TEXT-BERT` | [Classify text with BERT (TensorFlow Text tutorial)](https://www.tensorflow.org/text/tutorials/classify_text_with_bert) | free | 24 | TensorFlow, Transformers, BERT |
| `EXT-KERAS-INTRO-ENGINEERS` | [Introduction to Keras for engineers](https://keras.io/getting_started/intro_to_keras_for_engineers/) | free | 13 | TensorFlow, PyTorch, Keras |
| `EXT-KERAS-TUNER` | [Getting started with KerasTuner](https://keras.io/keras_tuner/getting_started/) | free | 20 | scikit-learn, Hyperparameter tuning, Keras |
| `EXT-NUMPY-ABSOLUTE-BASICS` | [NumPy: the absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html) | free | 31 | NumPy |
| `EXT-SKLEARN-GETTING-STARTED` | [scikit-learn Getting Started](https://scikit-learn.org/stable/getting_started.html) | free | 13 | scikit-learn, Transformers |
| `EXT-XGBOOST-BOOSTED-TREES` | [Introduction to Boosted Trees (XGBoost Tutorials)](https://xgboost.readthedocs.io/en/stable/tutorials/model.html) | free | 15 | XGBoost, Gradient boosting |
| `EXT-LIGHTGBM-PYTHON-INTRO` | [LightGBM Python-package Introduction](https://lightgbm.readthedocs.io/en/stable/Python-Intro.html) | free | 12 | LightGBM |
| `EXT-CATBOOST-TUTORIALS` | [CatBoost Tutorials](https://catboost.ai/docs/en/concepts/tutorials) | free | 5 | CatBoost |
| `EXT-GCS-CORE-INFRASTRUCTURE` | [Google Cloud Fundamentals: Core Infrastructure](https://www.cloudskillsboost.google/course_templates/60) | free | 46 | Prompt engineering, Google Cloud, Kubernetes |
| `EXT-GCS-BIGQUERY-INSIGHTS` | [Derive Insights from BigQuery Data](https://www.cloudskillsboost.google/course_templates/623) | free | 17 | BigQuery |
| `EXT-GCS-LOOKER-ANALYSIS` | [Analyzing and Visualizing Data in Looker](https://www.cloudskillsboost.google/course_templates/323) | free | 40 | Looker |
| `EXT-GCS-VERTEX-AI-STUDIO` | [Introduction to Vertex AI Studio](https://www.cloudskillsboost.google/course_templates/552) | free | 10 | Prompt engineering, Vertex AI |
| `EXT-MSLEARN-TSQL` | [Query and modify data with Transact-SQL](https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/) | free | 11 | SQL Server |
| `EXT-MSLEARN-AZURE-ML-MLOPS` | [Operationalize machine learning models (MLOps)](https://learn.microsoft.com/en-us/training/paths/build-first-machine-operations-workflow/) | free | 11 | Hyperparameter tuning, Azure ML, MLflow |
| `EXT-MSLEARN-GITHUB-ACTIONS-CI` | [Build continuous integration workflows by using GitHub Actions](https://learn.microsoft.com/en-us/training/modules/github-actions-ci/) | free | 13 | CI/CD |
| `EXT-MSLEARN-VBA-OFFICE` | [Getting started with VBA in Office](https://learn.microsoft.com/en-us/office/vba/library-reference/concepts/getting-started-with-vba-in-office) | free | 11 | VBA |
| `EXT-K8S-BASICS` | [Learn Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/) | free | 16 | Kubernetes |
| `EXT-JENKINS-GUIDED-TOUR` | [Jenkins Guided Tour: Getting started](https://www.jenkins.io/doc/pipeline/tour/getting-started/) | free | 5 | Jenkins |
| `EXT-TERRAFORM-GET-STARTED-AWS` | [Terraform Get Started - AWS](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) | free | 8 | Terraform |
| `EXT-AWS-API-GATEWAY-GET-STARTED` | [Get started with API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started.html) | free | 20 | API development |
| `EXT-DJANGO-FIRST-APP` | [Writing your first Django app (Django Getting started)](https://docs.djangoproject.com/en/5.2/intro/) | free | 20 | Django |
| `EXT-FASTAPI-TUTORIAL` | [FastAPI Tutorial - User Guide](https://fastapi.tiangolo.com/tutorial/) | free | 55 | FastAPI |
| `EXT-FLASK-QUICKSTART` | [Flask Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/) | free | 20 | Flask |
| `EXT-STREAMLIT-GET-STARTED` | [Get started with Streamlit](https://docs.streamlit.io/get-started) | free | 7 | Streamlit |
| `EXT-MLFLOW-GETTING-STARTED` | [Getting Started with MLflow for ML](https://mlflow.org/docs/latest/ml/getting-started/) | free | 6 | scikit-learn, Hyperparameter tuning, TensorFlow, PyTorch, MLflow |
| `EXT-KUBEFLOW-INTRO` | [Kubeflow Getting Started: Introduction](https://www.kubeflow.org/docs/started/introduction/) | free | 12 | Kubernetes, Kubeflow |
| `EXT-SPACY-ADVANCED-NLP` | [Advanced NLP with spaCy](https://course.spacy.io/en/) | free | 12 | spaCy |
| `EXT-NLTK-BOOK` | [Natural Language Processing with Python (NLTK Book)](https://www.nltk.org/book/) | free | 18 | NLTK |
| `EXT-COURSERA-SCALA-FP` | [Functional Programming Principles in Scala](https://www.coursera.org/learn/scala-functional-programming) | free-to-audit | 21 | Scala |
| `EXT-SCALA3-BOOK` | [Scala 3 — Book](https://docs.scala-lang.org/scala3/book/introduction.html) | free | 76 | Scala |
| `EXT-COURSERA-ECONOMETRICS` | [Econometrics: Methods and Applications](https://www.coursera.org/learn/erasmus-econometrics) | free-to-audit | 33 | Econometrics |
| `EXT-JULIA-GET-STARTED` | [Get Started with Julia (julialang.org/learning)](https://julialang.org/learning/) | free | 15 | Julia |
| `EXT-PLOTLY-PYTHON` | [Getting started with plotly in Python (+ Fundamentals)](https://plotly.com/python/getting-started/) | free | 49 | Plotly |
| `EXT-D3-GETTING-STARTED` | [D3: What is D3? / Getting started](https://d3js.org/getting-started) | free | 16 | D3.js |
| `EXT-QLIK-FREE-TRAINING` | [Free Data Analytics and Data Integration Training with Qlik (Get started with Qlik Sense)](https://www.qlik.com/us/customer-success/learn/qlik-academy/free-training) | free | 7 | Qlik |
| `EXT-AWS-REDSHIFT-GET-STARTED` | [Get started with Amazon Redshift provisioned data warehouses](https://docs.aws.amazon.com/redshift/latest/gsg/new-user.html) | free | 18 | Redshift |
| `EXT-AWS-SAGEMAKER-GET-STARTED` | [Getting started with Amazon SageMaker AI (Machine Learning Tutorials)](https://aws.amazon.com/sagemaker/ai/getting-started/) | free | 12 | SageMaker |
| `EXT-ELASTIC-SEARCH-GET-STARTED` | [Get started with search (Elasticsearch)](https://www.elastic.co/docs/solutions/search/get-started) | free | 12 | Elasticsearch |
| `EXT-REDIS-UNIVERSITY` | [Redis University: Get Started with Redis](https://redis.io/tutorials/university/) | free | 8 | Redis |
| `EXT-CASSANDRA-QUICKSTART` | [Get Started with Apache Cassandra](https://cassandra.apache.org/_/quickstart.html) | free | 13 | Cassandra |
| `EXT-HIVE-TUTORIAL` | [Apache Hive Tutorial](https://cwiki.apache.org/confluence/display/Hive/Tutorial) | free | 19 | Hive |
| `EXT-DASK-TUTORIAL` | [Dask Tutorial](https://tutorial.dask.org/) | free | 9 | NumPy, Dask |
| `EXT-POLARS-USER-GUIDE` | [Polars user guide](https://docs.pola.rs/) | free | 21 | Polars |
| `EXT-OPENCV-PYTHON-TUTORIALS` | [OpenCV-Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html) | free | 21 | OpenCV |

## Uncovered skills: course found

| Skill | 2019-22 % | 2026 % | Courses |
|---|---|---|---|
| Scala | 15.1 | 0.0 | `EXT-COURSERA-SCALA-FP`, `EXT-SCALA3-BOOK` |
| Google Cloud | 8.6 | 18.2 | `EXT-GCS-CORE-INFRASTRUCTURE` |
| TensorFlow | 7.2 | 0.0 | `EXT-KAGGLE-INTRO-DL`, `EXT-TF-TUTORIALS`, `EXT-TF-CLASSIFY-TEXT-BERT`, `EXT-KERAS-INTRO-ENGINEERS`, `EXT-MLFLOW-GETTING-STARTED` |
| Redshift | 5.8 | 4.5 | `EXT-AWS-REDSHIFT-GET-STARTED` |
| Econometrics | 5.1 | 0.0 | `EXT-COURSERA-ECONOMETRICS` |
| XGBoost | 4.8 | 0.0 | `EXT-KAGGLE-INTERMEDIATE-ML`, `EXT-XGBOOST-BOOSTED-TREES` |
| SQL Server | 4.1 | 0.0 | `EXT-MSLEARN-TSQL` |
| scikit-learn | 3.9 | 0.0 | `EXT-KERAS-TUNER`, `EXT-SKLEARN-GETTING-STARTED`, `EXT-MLFLOW-GETTING-STARTED` |
| Qlik | 3.7 | 4.5 | `EXT-QLIK-FREE-TRAINING` |
| Keras | 3.2 | 0.0 | `EXT-KAGGLE-INTRO-DL`, `EXT-TF-TUTORIALS`, `EXT-KERAS-INTRO-ENGINEERS`, `EXT-KERAS-TUNER` |
| NumPy | 3.1 | 0.0 | `EXT-NUMPY-ABSOLUTE-BASICS`, `EXT-DASK-TUTORIAL` |
| PyTorch | 3.0 | 4.5 | `EXT-FASTAI-PRACTICAL-DL`, `EXT-PYTORCH-BASICS`, `EXT-KERAS-INTRO-ENGINEERS`, `EXT-MLFLOW-GETTING-STARTED` |
| Plotly | 2.6 | 0.0 | `EXT-PLOTLY-PYTHON` |
| Gradient boosting | 2.5 | 0.0 | `EXT-XGBOOST-BOOSTED-TREES` |
| SageMaker | 2.5 | 0.0 | `EXT-AWS-SAGEMAKER-GET-STARTED` |
| CI/CD | 2.4 | 18.2 | `EXT-MSLEARN-GITHUB-ACTIONS-CI` |
| BigQuery | 2.1 | 13.6 | `EXT-GCS-BIGQUERY-INSIGHTS` |
| Julia | 1.9 | 0.0 | `EXT-JULIA-GET-STARTED` |
| Kubernetes | 1.4 | 4.5 | `EXT-GCS-CORE-INFRASTRUCTURE`, `EXT-K8S-BASICS`, `EXT-KUBEFLOW-INTRO` |
| VBA | 1.2 | 0.0 | `EXT-MSLEARN-VBA-OFFICE` |
| D3.js | 1.2 | 0.0 | `EXT-D3-GETTING-STARTED` |
| API development | 0.8 | 0.0 | `EXT-AWS-API-GATEWAY-GET-STARTED` |
| Azure ML | 0.7 | 0.0 | `EXT-MSLEARN-AZURE-ML-MLOPS` |
| Elasticsearch | 0.7 | 9.1 | `EXT-ELASTIC-SEARCH-GET-STARTED` |
| Jenkins | 0.5 | 0.0 | `EXT-JENKINS-GUIDED-TOUR` |
| Django | 0.5 | 0.0 | `EXT-DJANGO-FIRST-APP` |
| MLflow | 0.4 | 0.0 | `EXT-MSLEARN-AZURE-ML-MLOPS`, `EXT-MLFLOW-GETTING-STARTED` |
| Kubeflow | 0.4 | 0.0 | `EXT-KUBEFLOW-INTRO` |
| spaCy | 0.3 | 0.0 | `EXT-SPACY-ADVANCED-NLP` |
| Looker | 0.3 | 0.0 | `EXT-GCS-LOOKER-ANALYSIS` |
| dbt | 0.3 | 18.2 | `EXT-DBT-FUNDAMENTALS` |
| Flask | 0.3 | 0.0 | `EXT-FLASK-QUICKSTART` |
| LightGBM | 0.2 | 0.0 | `EXT-LIGHTGBM-PYTHON-INTRO` |
| BERT | 0.2 | 0.0 | `EXT-TF-CLASSIFY-TEXT-BERT` |
| NLTK | 0.2 | 0.0 | `EXT-NLTK-BOOK` |
| Named entity recognition | 0.2 | 0.0 | `EXT-HF-LLM` |
| OpenCV | 0.2 | 0.0 | `EXT-OPENCV-PYTHON-TUTORIALS` |
| Vertex AI | 0.2 | 0.0 | `EXT-GCS-VERTEX-AI-STUDIO` |
| Cassandra | 0.2 | 0.0 | `EXT-CASSANDRA-QUICKSTART` |
| Redis | 0.2 | 4.5 | `EXT-REDIS-UNIVERSITY` |
| Hive | 0.1 | 0.0 | `EXT-HIVE-TUTORIAL` |
| Dask | 0.1 | 0.0 | `EXT-DASK-TUTORIAL` |
| Hyperparameter tuning | 0.1 | 0.0 | `EXT-KERAS-TUNER`, `EXT-MSLEARN-AZURE-ML-MLOPS`, `EXT-MLFLOW-GETTING-STARTED` |
| Terraform | 0.1 | 0.0 | `EXT-TERRAFORM-GET-STARTED-AWS` |
| Polars | 0.0 | 0.0 | `EXT-POLARS-USER-GUIDE` |
| CatBoost | 0.0 | 0.0 | `EXT-CATBOOST-TUTORIALS` |
| Hugging Face | 0.0 | 0.0 | `EXT-HF-LLM`, `EXT-FASTAI-PRACTICAL-DL` |
| Transformers | 0.0 | 0.0 | `EXT-HF-LLM`, `EXT-FASTAI-PRACTICAL-DL`, `EXT-TF-TUTORIALS`, `EXT-TF-CLASSIFY-TEXT-BERT`, `EXT-SKLEARN-GETTING-STARTED` |
| RAG | 0.0 | 0.0 | `EXT-DLAI-VECTOR-DB`, `EXT-DLAI-ADVANCED-RAG` |
| Prompt engineering | 0.0 | 18.2 | `EXT-DLAI-PROMPT-ENG`, `EXT-GCS-CORE-INFRASTRUCTURE`, `EXT-GCS-VERTEX-AI-STUDIO` |
| LangChain | 0.0 | 0.0 | `EXT-DLAI-LANGCHAIN` |
| Vector databases | 0.0 | 0.0 | `EXT-HF-LLM`, `EXT-DLAI-VECTOR-DB` |
| FastAPI | 0.0 | 0.0 | `EXT-FASTAPI-TUTORIAL` |
| Streamlit | 0.0 | 0.0 | `EXT-HF-LLM`, `EXT-FASTAI-PRACTICAL-DL`, `EXT-STREAMLIT-GET-STARTED` |

## Uncovered skills: still without a course

None: every one of the 54 uncovered skills is named by at least one course.

## Notes and caveats

- `EXT-DBT-FUNDAMENTALS`: price not printed on the page; dbt Learn on-demand courses are free with registration.
- `EXT-GCS-CORE-INFRASTRUCTURE`: enrolment free with a Google Skills account; hands-on labs may need credits or a subscription.
- `EXT-GCS-BIGQUERY-INSIGHTS`: enrolment free with a Google Skills account; hands-on labs may need credits or a subscription.
- `EXT-GCS-LOOKER-ANALYSIS`: enrolment free with a Google Skills account; hands-on labs may need credits or a subscription.
- `EXT-GCS-VERTEX-AI-STUDIO`: enrolment free with a Google Skills account; hands-on labs may need credits or a subscription.
- `EXT-AWS-API-GATEWAY-GET-STARTED`: covers the dictionary's `API development` aliases (REST API); the exercise runs within the AWS Free Tier.
- `EXT-JULIA-GET-STARTED`: juliaacademy.com timed out from this machine on 13 Oct (fetcher and browser); the julialang.org learning page was used instead.
- `EXT-QLIK-FREE-TRAINING`: course pages on learning.qlik.com return HTTP 403 to both the fetcher and the browser; no module list could be copied.
- `EXT-AWS-REDSHIFT-GET-STARTED`: documentation is free; the sample cluster accrues AWS charges while it runs.
- `EXT-HIVE-TUTORIAL`: wiki is read-only since the migration; page last updated 23 Feb 2021.
- DeepLearning.AI short courses: the page says "Course access is free for a limited time during the DeepLearning.AI
  learning platform beta!"; the graded assignment and the accomplishment need PRO. Recorded as `free`.
- Coursera (EPFL Scala, Erasmus Econometrics): `free-to-audit`; the certificate is paid.
- Google Skills (the cloudskillsboost.google URLs now redirect to skills.google): enrolment is free, hands-on labs
  may need credits or a subscription; the course descriptions and module titles are what the page carries.
- Kaggle Learn pages state "No cost, like all Kaggle Learn Courses".
- Documentation tutorials (PyTorch, TensorFlow, Keras, NumPy, scikit-learn, XGBoost, LightGBM, CatBoost, Kubernetes,
  Jenkins, Django, FastAPI, Flask, Streamlit, MLflow, Kubeflow, Terraform, AWS, Elastic, Cassandra, Hive, Dask,
  Polars, OpenCV, NLTK, D3, Plotly, Scala 3 Book) have no cost; their "modules" are the tutorial's own section
  or chapter titles.
- `pct_2019_22` in `uncovered_skills_2026-10-13.csv` is `pct_ads` from `skill_counts_v2.csv`; the column of the same
  name in `skill_counts_2026.csv` differs slightly (e.g. Python 82.8 vs 84.5, Scala 15.1 vs 16.4), a different
  matcher run. The task said to sort by the v2 file, so that is what is stored.
- The step-1 matcher is case-insensitive as instructed, so a few *covered* verdicts rest on common words: `Go`
  (6 subjects), `R` (13, incl. the bare letter), `Spark`, `Excel`, `A/B testing` via the alias `experimentation`.
  Those skills are therefore absent from the uncovered list even though no subject may teach them.
- Two matches in the coverage table are alias artefacts rather than course content: `Transformers` on
  `EXT-SKLEARN-GETTING-STARTED` (scikit-learn's "Transformers and pre-processors" section, not NLP transformers) and
  `Streamlit` on `EXT-HF-LLM` / `EXT-FASTAI-PRACTICAL-DL` (the dictionary lists `gradio` as a Streamlit alias). Every
  other skill in that table has a course that is actually about it.
- 56 courses rather than the 25-40 aimed for: 54 skills had no UTS subject and most needed their own page; the
  thinnest entries (CatBoost, Jenkins, Qlik, Kubeflow) can be dropped without losing a skill except Qlik and Jenkins.
- Pages that only render in a browser were read with Playwright (Kaggle Learn blocks urllib with reCAPTCHA, dbt Learn
  and tensorflow.org serve their content by script). juliaacademy.com timed out; learning.qlik.com returned 403.
- Read with `dtype=str`; the file has no leading `#` line.

## Check, 14 Oct 2026 (#66)

Every `source_url` was requested again (one request per second) and the stored text compared with the live page.

| Check | Result |
|---|---|
| Links | **56 of 56 answer HTTP 200** to GET (Kaggle Learn answers 404 to HEAD, so use GET). Redirects that still land on the same course: the four DeepLearning.AI links (to `/courses/...`), OpenCV (to the 4.13.0 docs), Apache Hive's wiki page, and the four Google Cloud Skills Boost pages (now at skills.google). `date_checked` is 2026-10-14 on every row |
| Module titles on the page, word for word | 36 of the 55 courses with a module list match at least half their titles exactly; the rest differ only in formatting (the file joins title and blurb with " — ", the page shows them apart). Comparing words instead of whole strings, every module is on its page except one Kubeflow blurb and the 6 Terraform rows below |
| Not checkable by script | Kaggle Learn (3 courses) and dbt Learn (1) render their module list in the browser only; check by hand |
| `cost` | 54 free, 2 Coursera free-to-audit; not re-checked against the providers' pricing |

Fixed in the file: 18 module titles from the XGBoost and LightGBM docs ended in the docs' link icon (U+F0C1), now removed; the 6 Terraform rows had title and blurb glued ("Install TerraformInstall Terraform on ..."), now "Install Terraform — Install Terraform on ...". No other row changed.
