"""Which of the 11 roles a job title is. Owner: Van Thong (rules), moved here from classify_ats_roles.py on 17 Oct
so that the app can weigh a pasted ad by its own role (backend.analyse); the data scripts import them from here.

    role_of(title)              -> one of the 11 roles, or "other"
    ad_role(ad_text, hint)      -> the role of an ad from its first line; else `hint` when it is a role; else None
"""
from __future__ import annotations

import re

OTHER = "other"
ENG = r"engineers?\b"                        # "engineer", "engineers"; never "engineering"
RULES: list[tuple[str, re.Pattern]] = [
    # Management titles are not individual-contributor roles.
    (OTHER, re.compile(r"\b(?:managers?|director|head of|chief|vp|vice president|officer|team lead|engineering lead)\b", re.I)),
    # DevOps named in the title stays DevOps even when the role is support ("Senior DevOps Support Engineer").
    ("DevOps/SRE", re.compile(rf"\bdevops\b.*\b{ENG}", re.I)),
    # Pre-sales, consulting, enablement and support "engineers" and "architects".
    (OTHER, re.compile(
        rf"\b(?:sales|solutions?|customer success|customer|support|services?|escalations?|enablement|onboarding|"
        rf"commercial|implementation|consulting|field)\b[^,]*\b{ENG}"
        r"|\b(?:solutions?|consulting|partner|delivery|specialist|enablement|customer)\b.*\barchitects?\b", re.I)),
    ("Machine Learning Engineer", re.compile(
        rf"machine learning {ENG}|\bML {ENG}|\bAI {ENG}|applied ai {ENG}|\b(?:AI|ML) platform {ENG}|mlops", re.I)),
    ("Software Engineer", re.compile(
        rf"software (?:{ENG}|developers?\b)|\bdevelopers?\b|programmer|full[- ]?stack|front[- ]?end|back[- ]?end"
        rf"|\b(?:mobile|web|android|ios|java|python|\.net|c#|react|search|language|forward deployed|deployment|salesforce) {ENG}"
        r"|\bengineers?\s*[-–(]\s*(?:salesforce|c#|\.net)", re.I)),
    ("Cybersecurity Analyst", re.compile(
        rf"security (?:{ENG}|analysts?\b|archi\w*|specialists?\b|consultants?\b|operations|researchers?\b)|cyber|infosec"
        r"|information security|penetration|\bsoc\b|identity (?:&|and) access|\biam engineer|devsecops|\bsiem\b"
        r"|threat (?:detection|intelligence|hunting)", re.I)),
    ("Cloud Engineer", re.compile(rf"\bcloud\b.*\b(?:{ENG}|architects?\b)|\b(?:aws|azure|gcp) (?:engineer|architect)", re.I)),
    ("DevOps/SRE", re.compile(
        rf"devops|site reliability|\bsre\b|(?:platform|production|infrastructure|reliability|release|build|observability) {ENG}"
        r"|compute (?:foundation|platform)", re.I)),
    ("Network/Systems Administrator", re.compile(
        rf"network (?:{ENG}|administrators?\b|operations|analysts?\b|tech)|systems? (?:administrators?\b|{ENG})|sysadmin"
        rf"|\bit support|service desk|desktop support|\bit operations|infrastructure (?:administrators?|analysts?)\b"
        rf"|\b(?:datacenter|data center)\b.*\b{ENG}|\b{ENG}.*\b(?:datacenter|data center)", re.I)),
    ("QA/Test Engineer", re.compile(
        rf"\bqa\b|quality assurance|test(?:ing)? (?:{ENG}|analysts?\b|automation|lead)|software tester|\bsdet\b|automation (?:{ENG}|testers?\b)", re.I)),
    ("Data Engineer", re.compile(rf"(?:data|analytics) {ENG}|data platform|\betl\b|data pipeline|database (?:{ENG}|developers?\b)", re.I)),
    ("Data Analyst", re.compile(
        r"data analysts?\b|analytics (?:senior )?analysts?\b|\banalysts?\b.*\banalytics|analytics\b.*\banalysts?\b|business intelligence"
        r"|\bbi (?:analyst|developer)|(?:reporting|insights?) analysts?\b", re.I)),
    ("Business Analyst", re.compile(
        r"business analysts?\b|business (?:and|&) process analysts?\b|functional analysts?\b|business systems analysts?\b|systems analysts?\b"
        r"|process analysts?\b|product owners? (?:&|and) business analysts", re.I)),
    ("Data Scientist", re.compile(
        r"\b(?:data|applied|research|decision|ai|ml|machine learning) scientists?\b|\bscientists?\b.*\b(?:ai|ml|data|machine learning|analytics)\b"
        r"|\b(?:ai|ml|data)\b.*\bscientists?\b", re.I)),
    ("Machine Learning Engineer", re.compile(
        rf"\b(?:ai|ml|machine learning|agentic|llms?|genai|deep learning|nlp)\b.*\b(?:{ENG}|architects?\b)"
        rf"|\b(?:{ENG}|architects?\b).*\b(?:ai|ml|machine learning|agentic|llms?|genai)\b", re.I)),
    ("Software Engineer", re.compile(rf"\b{ENG}", re.I)),
]


def role_of(title: str) -> str:
    """The first rule the title matches, else "other"."""
    t = re.sub(r"\s+", " ", title or "").strip()
    for role, rx in RULES:
        if rx.search(t):
            return role
    return OTHER


def ad_role(ad_text: str, hint: str | None = None, roles: set[str] | None = None) -> str | None:
    """The role an ad is for: its first non-empty line read as a title (ads usually open with it), else `hint`
    (the role the student picked, or the role a listed ad was filed under) when it is one of `roles`."""
    first = next((line.strip() for line in (ad_text or "").splitlines() if line.strip()), "")
    role = role_of(first[:160])
    if role != OTHER:
        return role
    return hint if hint and (roles is None or hint in roles) else None
