# 1 Introduction

## 1.1 The problem

A UTS subject outline and a Sydney job ad can describe the same skill in words that never
overlap. Subject 36120's first learning objective reads *"Implement and evaluate advanced machine
learning techniques to real-world problems"*; a Robert Walters Data Scientist ad (Sydney CBD,
September 2026) asks for *"in-depth knowledge of deep learning, Generative AI, and other
advanced AI technologies"*. A student cannot tell which subject taught what the ad asks for, or which
elective would close the gap, and their resume uses a third vocabulary. The
market also moves faster than the Handbook: large language models appear in none of 3,204 Seek
Data Scientist ads from 2019-22 and in 36% of the Data Scientist ads of 2026 (section 3).

## 1.2 Users and scope

Skillabus answers one question for three users: *which subject moves me closest to the job I
want?* (UTS student), *what does my resume lack for this ad?* (job seeker) and *how far am I from
a new field?* (career switcher). It covers 11 data and IT roles in five families. Demand comes
from 1,932 Australian ads posted between 1 September and 16 October 2026 (89 to 216 per role);
supply from 360 UTS Handbook subjects in 44 courses, plus 56 outside courses, 248 self-study
resources and 49 certifications for skills UTS does not teach.

## 1.3 What is new

Existing tools stop one step short of the student's decision (section 2). Job platforms compare a
profile with a job but know nothing about university subjects. Curriculum analytics such as
Lightcast Skillabi align whole programs with the labour market for program leaders, with a
proprietary taxonomy. UniSkill links course sentences to ESCO skills but not to a resume or a live ad.
Handbooks list subjects with no link to demand.

**Skillabus closes that loop for the individual student.** It puts ads, resumes and subject
outlines on one skills vocabulary (ESCO plus 145 skills that Australian ads ask for and ESCO
lacks) and recommends the few UTS subjects that close the most demand-weighted gaps. Each
recommendation quotes the sentence of the subject outline that justifies it and says whether it
came from a learning objective, a weekly topic or the description. Gaps no subject covers are
filled with outside courses and certifications, marked as not counting for credit. For a sample
Data Scientist ad the path is 31250, 43007, 36106, which cover 96.9% of the demand-weighted gap.

## 1.4 Contributions

1. **One vocabulary for three document types**, with a five-step normalisation that keeps skills
   ESCO lacks instead of dropping or mislabelling them (section 4).
2. **Evidence by layer.** Reading learning objectives alone hid that 36118 and 43023 teach large
   language models as topics, so weaker layers are shown, not discarded.
3. **A demand-weighted learning path** that respects prerequisites and teaching sessions.
4. **Measured stages.** Each stage is scored against a baseline on labelled data (section 6), and
   students can vote on whether a subject really teaches a skill.
