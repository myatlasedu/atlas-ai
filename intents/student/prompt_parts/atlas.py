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
- Initiative Score
- Atlas Band
- Atlas Rank
- Atlas Pillars
- Academic Pillar
- Growth Pillar
- Initiative Pillar
- Strongest Pillar
- Weakest Pillar
- Performance Pillars
- Atlas Progress
- Atlas Improvement
- Atlas Trends

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
- How is my initiative score?
- What is my initiative pillar score?

- What is my strongest pillar?
- What is my weakest pillar?
- Which pillar needs improvement?
- What should I focus on?
- What are my strengths?
- What are my weaknesses?

- Am I improving?
- How am I performing overall?
- How is my overall score?

Return:

{
    "intent": "atlas_score_summary",
    "target_modules": ["atlas"],
    "confidence": 0.95
}

==================================================
DO NOT MAP TO ASSESSMENT SUMMARY
==================================================

The following are Atlas questions:

- academic score
- growth score
- initiative score
- atlas score
- atlas band
- atlas rank
- pillar score
- strongest pillar
- weakest pillar
- overall performance
- atlas improvement

These MUST use:

atlas_score_summary

NOT:

assessment_summary

==================================================
ASSESSMENT SUMMARY IS ONLY FOR
==================================================

- tests
- exams
- assessments
- marks
- grades
- assessment results
- upcoming assessments
- assessment performance
- assessment feedback
"""