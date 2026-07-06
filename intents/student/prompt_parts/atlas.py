ATLAS_PROMPT = """
==================================================
ATLAS SCORE SUMMARY
==================================================

Intent:
atlas_score_summary

Used for ANY question related to:

- Atlas Score
- Academic Score
- Growth Score
- Atlas Band
- Atlas Rank
- Atlas Pillars
- Academic Pillar
- Growth Pillar
- Strongest Pillar
- Weakest Pillar
- Performance Pillars
- Atlas Progress
- Atlas Improvement
- Atlas Trends
- Engagement Score
- Engagement Pillar

IMPORTANT

The following MUST ALWAYS map to:

atlas_score_summary

Examples:

- What is my Atlas Score?
- Show my Atlas Score
- Explain my Atlas Score
- Why did my Atlas Score drop?
- How has my Atlas Score changed?
- What is my rank?
- What band am I in?

- How is my academic score?
- Show my academic score
- Am I doing well academically?
- What is my growth score?
- Show my growth score

- What is my strongest pillar?
- What is my weakest pillar?
- Which pillar needs improvement?
- What should I focus on?

If the query mentions:

- Atlas
- Band
- Pillar
- Academic Pillar
- Growth Pillar
- Engagement Pillar

it MUST return

atlas_score_summary

even if the query also mentions:

- performance
- improvement
- strengths
- weaknesses

Return:

{
    "intent": "atlas_score_summary",
    "target_modules": ["atlas"],
    "confidence": 0.95
}

Calibration questions are also Atlas questions.

Examples:

- Why is my Atlas Score unavailable?
- Why is my Atlas Score calibrating?
- When will Atlas Score be available?
- Why can't I see my Atlas Score?
- Why are my pillars unavailable?
- Which pillar is strongest?
- Which pillar is weakest?
- Which pillar needs work?
- Which pillar should I improve?
- Which Atlas pillar is best?
- Which Atlas pillar is lowest?

These MUST map to:

atlas_score_summary

==================================================
ATLAS VS STUDENT PERFORMANCE
==================================================

Use atlas_score_summary when the query asks about:

- Atlas Score
- Atlas Band
- Atlas Pillars
- Academic Pillar
- Growth Pillar
- Engagement Pillar
- Strongest Pillar
- Weakest Pillar
- Atlas calibration

Use student_performance when the query asks for:

- Overall academic performance
- Strengths
- Weaknesses
- Recommendations
- Areas to improve
- Academic review
- Performance analysis

Student performance may use Atlas as one input, but it is NOT an Atlas query unless Atlas, Band, or Pillars are explicitly mentioned.

"""