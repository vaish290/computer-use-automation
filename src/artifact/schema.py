from typing import List, Optional, Literal, Dict

from pydantic import BaseModel, Field


# ==========================================
# INPUT / OUTPUT DEFINITIONS
# ==========================================

class InputDefinition(BaseModel):

    type: Literal[
        "string",
        "integer",
        "boolean"
    ]

    required: bool = True


class OutputDefinition(BaseModel):

    type: Literal[
        "string",
        "integer",
        "boolean"
    ]


# ==========================================
# CONDITIONS
# ==========================================

class Condition(BaseModel):

    type: Literal[
        "text_present"
    ]

    value: str


# ==========================================
# BUSINESS OUTCOME
# ==========================================

class BusinessOutcome(BaseModel):

    code: str

    condition: Condition

    message: str


# ==========================================
# LOCATOR
# ==========================================

class LocatorDefinition(BaseModel):

    strategy: Literal[
        "id",
        "name",
        "label",
        "role",
        "css"
    ]

    value: str

    # Used mainly with role strategy.
    # Example:
    #
    # role = button
    # accessible_name = Search Member

    accessible_name: Optional[str] = None


# ==========================================
# TARGET
# ==========================================

class TargetDefinition(BaseModel):

    role: Optional[str] = None

    accessible_name: Optional[str] = None

    primary: LocatorDefinition

    fallbacks: List[
        LocatorDefinition
    ] = Field(
        default_factory=list
    )


# ==========================================
# STEP
# ==========================================

class Step(BaseModel):

    id: str

    action: Literal[
        "fill",
        "click",
        "read"
    ]

    target: TargetDefinition

    value: Optional[str] = None

    save_as: Optional[str] = None


# ==========================================
# APPLICATION TARGET
# ==========================================

class ApplicationTarget(BaseModel):

    url: str


# ==========================================
# ARTIFACT
# ==========================================

class Artifact(BaseModel):

    schema_version: str

    name: str

    description: Optional[str] = None

    target: ApplicationTarget

    inputs: Dict[
        str,
        InputDefinition
    ]

    steps: List[
        Step
    ]

    outputs: Optional[
        Dict[str, OutputDefinition]
    ] = None

    business_outcomes: List[
        BusinessOutcome
    ] = Field(
        default_factory=list
    )

    checkpoint: Condition