# 1 Introduction

> Draft by Quan (with Claude), 4 Oct 2026. Numbers marked **[eval]** wait for section 6.

## 1.1 The problem

A UTS subject outline and a Sydney job ad can describe the same skill in words that never
overlap. Subject 36120's first learning objective reads *"Implement and evaluate advanced machine
learning techniques to real-world problems"*; a Robert Walters Data Scientist ad (Sydney CBD,
September 2026) asks for *"in-depth knowledge of deep learning, Generative AI, and other
advanced AI technologies"*. A student reading the ad cannot tell which subject already taught
them what it asks for, or which elective would close the gap. Their resume uses a third
vocabulary again.

The gap is measurable. Matching our 138-skill dictionary to the ESCO taxonomy by exact label
covers only 36% of it, and for 54% we found no ESCO concept at all.
And the market moves faster than either: none of 3,204 Seek Australia Data Scientist ads from
2019-22 mentions large language models, while 15.8% of 247 US Data Scientist ads from 2023-24 do.

## 1.2 Who it is for

| User | Question |
|---|---|
| Elective chooser | Which subject moves me closest to my target role? |
| Job seeker | What does my resume lack for this ad? |
| Career switcher | How far is my profile from a new role? |

## 1.3 What Skillabus does

Skillabus puts subject outlines, job ads and resumes into one skills vocabulary (ESCO, extended
with Lightcast and an explicit "emerging" class), then answers the three questions in one screen:
the skills the role asks for, which of them the student lacks, and the two or three UTS subjects
that close the most demand-weighted gaps, each backed by the sentence in the subject outline that
teaches the skill.

## 1.4 What is new

Existing tools stop one step short of the student's decision (section 2):

- **Job platforms** compare a profile with a job but know nothing about university subjects.
- **Curriculum analytics** such as Lightcast Skillabi align whole programs with the labour
  market, for program leaders, with a proprietary taxonomy; they do not tell one student which
  elective to take.
- **Research datasets** such as UniSkill match course sentences to ESCO skills but do not connect
  them to a student's resume or a live job ad.
- **Course handbooks** list subjects and requisites with no link to demand.

Skillabus closes that loop for the individual student. Its contributions:

1. **One vocabulary across three document types**, with a five-step normalisation (dictionary,
   ESCO exact, ESCO embedding, Lightcast, emerging) that keeps skills ESCO lacks instead of
   dropping or mislabelling them.
2. **Evidence by layer.** A subject is recommended only with the sentence that justifies it, labelled
   by where it came from: learning objective, assessment, weekly topic or description. This answers
   the main weakness of Handbook-only matching: our poster reported that no learning objective in
   the 70 subjects covers LLMs or generative AI and that 36118 mentions LLMs only in its
   description. Yet 36118 and 43023 list LLMs as topics, and 32130 teaches generative AI "in the
   data pipeline". Reading learning objectives alone hid all three.
3. **A demand-weighted learning path**: a greedy cover that picks the subjects closing the most
   employer demand, not the most keyword hits.
4. **Built-in validation**: students vote on whether a subject really teaches a skill, and every
   pipeline stage is scored against a baseline on hand-labelled data **[eval]**.

## 1.5 Report outline

Section 2 reviews related systems; 3 the data; 4 the methods and why each was chosen; 5 the system;
6 the evaluation and error analysis; 7 ethics and limitations; 8 conclusions.
