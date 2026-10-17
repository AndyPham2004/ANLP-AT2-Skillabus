# 8 Conclusion, recommendations and next steps

## 8.1 What works

Skillabus puts ads, resumes and UTS subject outlines on one skills vocabulary and turns a resume-to-ad gap into a short list of subjects, each with a quoted sentence as evidence. On our small test sets the stages hold up (section 6). Dictionary extraction reaches F1 0.767, and on dictionary skills the three tiers are close (0.777, 0.796, 0.792). Matching is right for 90.9% of 287 skill rows. The ranker puts the supporting sentence in the top five for 94% of rows, and the chat finds a cited subject in its top five for 93% of questions.

## 8.2 What does not work yet

- Soft skills and the bare letter “R” are the main extraction misses, and partial matches are unreliable.
- Subject P@3 does not compare methods, and the chat judge is the same model that writes the answers.
- The test sets are small (20 ads, 45 pairs, 33 skill–subject pairs, 15 questions).
- We did not test the app with students (issue \#32), so we do not know whether it changes what they enrol in.

## 8.3 Recommendations

Use the app as a shortlist with evidence: read the quoted sentence before trusting a subject, and treat partial matches as hints. Have a person confirm new terms from GPT-4o-mini before they enter the vocabulary.

## 8.4 Next steps

1.  Tighten the umbrella rule to require a method or library, which removes four of six false partials.
2.  Rank subjects by similarity alone to compare the three methods.
3.  Label more ads and resumes with a second annotator.
4.  Run the user test with students.
