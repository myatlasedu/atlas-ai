from datetime import date

from intents.student.prompt_parts.base import BASE_PROMPT
from intents.student.prompt_parts.attendance import ATTENDANCE_PROMPT
from intents.student.prompt_parts.homework import HOMEWORK_PROMPT
from intents.student.prompt_parts.assessment import ASSESSMENT_PROMPT
from intents.student.prompt_parts.atlas import ATLAS_PROMPT
from intents.student.prompt_parts.performance import PERFORMANCE_PROMPT
from intents.student.prompt_parts.misc import MISC_PROMPTS
from intents.student.prompt_parts.date_rules import DATE_RULES
from intents.student.prompt_parts.module_rules import MODULE_RULES
from intents.student.prompt_parts.response_format import RESPONSE_FORMAT
from intents.student.prompt_parts.accouncement import ANNOUNCEMENT_PROMPT
from intents.student.prompt_parts.forum import FORUM_PROMPT
from intents.student.prompt_parts.subject import SUBJECT_PROMPT
from intents.student.prompt_parts.personal_event import PERSONAL_EVENT_PROMPT
from intents.student.prompt_parts.action_confirmation import ACTION_CONFIRMATION_PROMPT
from intents.student.prompt_parts.journal_prompt import JOURNAL_PROMPT


def get_student_intent_prompt():

    today = date.today().isoformat()

    return f"""
{BASE_PROMPT}

Today's date:

{today}

==================================================
SUPPORTED INTENTS
==================================================

{ACTION_CONFIRMATION_PROMPT}

{ATTENDANCE_PROMPT}

{HOMEWORK_PROMPT}

{ASSESSMENT_PROMPT}

{SUBJECT_PROMPT}

{FORUM_PROMPT}

{ANNOUNCEMENT_PROMPT}

{ATLAS_PROMPT}

{PERFORMANCE_PROMPT}

{PERSONAL_EVENT_PROMPT}

{JOURNAL_PROMPT}

{MISC_PROMPTS}

{DATE_RULES}

{MODULE_RULES}

{RESPONSE_FORMAT}
"""