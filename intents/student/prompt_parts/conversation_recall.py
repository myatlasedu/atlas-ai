CONVERSATION_RECALL_PROMPT = """
==================================================
CONVERSATION RECALL
==================================================

Intent:
conversation_recall

The student is asking about THIS CHAT itself, not
about school data.

Your only job is to decide WHAT they want recalled
and return it as "recall_scope".

==================================================
RECALL SCOPE
==================================================

Exactly one of:

created

The student asks what Atlas created, saved, added,
made or did during this chat.

- What did you create now?
- What did you just save?
- What did you add?
- What did you do?
- Did you save it?
- What journal did you create?
- What reminder did you set?

--------------------------------------------------

asked

The student asks what THEY asked, said, told or
requested earlier in this chat.

- What did I ask you?
- What did I say earlier?
- What did I tell you?
- What was my last question?
- What did I ask you to do?

--------------------------------------------------

summary

The student wants a recap of the whole chat.

- Summarize our conversation.
- Summarize all the conversation.
- What have we discussed so far?
- Recap this chat.
- What did we talk about?

==================================================
RETURN
==================================================

{
    "intent": "conversation_recall",
    "recall_scope": "created",
    "navigation_target": null,
    "subject": null,
    "topic": null,
    "start_date": null,
    "end_date": null,
    "target_modules": [],
    "confidence": 0.95
}

Never extract dates, subjects or topics for this
intent. Leave them null.
"""
