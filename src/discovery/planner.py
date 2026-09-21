import os
import json

from groq import Groq
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()



# ==========================================
# GROQ CLIENT
# ==========================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ==========================================
# PLANNER
# ==========================================

def decide_next_action(
    goal,
    observation,
    history
):

    controls = observation.get(
        "controls",
        []
    )

    data = observation.get(
        "data",
        []
    )

    page_text = observation.get(
        "text",
        ""
    )

    # ======================================
    # PROMPT
    # ======================================

    prompt = f"""
You are controlling a web application.

Your job is to achieve the user's goal by choosing
ONE action at a time.

USER GOAL:
{goal}


INTERACTIVE CONTROLS:
{json.dumps(controls, indent=2)}


READABLE DATA:
{json.dumps(data, indent=2)}


PAGE TEXT:
{page_text}


PREVIOUS ACTIONS:
{json.dumps(history, indent=2)}


You may return exactly ONE of these actions:


1. FILL

Use this when you need to enter text into a control.

Format:

{{
    "action": "fill",
    "target": "control_X",
    "value": "value to enter"
}}


2. CLICK

Use this when you need to click a button.

Format:

{{
    "action": "click",
    "target": "control_X"
}}


3. READ

Use this when the information requested by the
user is available inside READABLE DATA.

The target MUST be a data_id such as data_1,
data_2, etc.

save_as should be a short reusable variable name
describing the information.

Example:

{{
    "action": "read",
    "target": "data_4",
    "save_as": "savings_balance"
}}


4. COMPLETE

Use COMPLETE only after the requested information
has already been READ in a previous action.

Format:

{{
    "action": "complete",
    "output": {{
        "result": "completed"
    }}
}}


IMPORTANT RULES:

- Return ONLY valid JSON.
- Do not include markdown.
- Do not explain your decision.
- Choose exactly ONE action.
- Never invent control IDs or data IDs.
- FILL and CLICK must target an item from
  INTERACTIVE CONTROLS.
- READ must target an item from READABLE DATA.
- If the user's requested information is visible
  in READABLE DATA and has not yet been read,
  choose READ instead of COMPLETE.
- After the required information has been read,
  choose COMPLETE.
- Use PREVIOUS ACTIONS to avoid repeating actions.
"""

    # ======================================
    # CALL GROQ
    # ======================================

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        response_format={
            "type": "json_object"
        },

        temperature=0
    )

    # ======================================
    # PARSE RESPONSE
    # ======================================

    content = (
        response
        .choices[0]
        .message
        .content
    )

    action = json.loads(
        content
    )

    return action