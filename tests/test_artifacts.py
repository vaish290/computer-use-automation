import sys
from pathlib import Path


# ==========================================
# ADD SRC FOLDER TO PYTHON PATH
# ==========================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

SRC_PATH = (
    PROJECT_ROOT
    / "src"
)

sys.path.insert(
    0,
    str(SRC_PATH)
)


# ==========================================
# IMPORTS
# ==========================================

from artifact.loader import load_artifact


# ==========================================
# ARTIFACT PATH
# ==========================================

ARTIFACT_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "get_savings_balance_generated.json"
)


# ==========================================
# ARTIFACT LOADS SUCCESSFULLY
# ==========================================

def test_artifact_loads():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    assert artifact is not None

    assert (
        artifact.name
        == "get_savings_balance"
    )


# ==========================================
# ARTIFACT IS VERSIONED
# ==========================================

def test_artifact_has_version():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    assert (
        artifact.schema_version
        == "1.1"
    )


# ==========================================
# INPUT IS DEFINED
# ==========================================

def test_member_id_input_exists():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    assert (
        "member_id"
        in artifact.inputs
    )

    assert (
        artifact.inputs[
            "member_id"
        ].required
        is True
    )


# ==========================================
# EXPECTED STEPS EXIST
# ==========================================

def test_artifact_steps():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    assert len(
        artifact.steps
    ) == 3

    assert (
        artifact.steps[0].action
        == "fill"
    )

    assert (
        artifact.steps[1].action
        == "click"
    )

    assert (
        artifact.steps[2].action
        == "read"
    )


# ==========================================
# INPUT IS PARAMETERIZED
# ==========================================

def test_member_id_is_parameterized():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    first_step = (
        artifact.steps[0]
    )

    assert (
        first_step.value
        == "{{member_id}}"
    )


# ==========================================
# OUTPUT IS DEFINED
# ==========================================

def test_savings_balance_output():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    assert (
        "savings_balance"
        in artifact.outputs
    )

    assert (
        artifact.outputs[
            "savings_balance"
        ].type
        == "string"
    )


# ==========================================
# CHECKPOINT EXISTS
# ==========================================

def test_success_checkpoint():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    assert (
        artifact.checkpoint.type
        == "text_present"
    )

    assert (
        artifact.checkpoint.value
        == "Savings Balance"
    )


# ==========================================
# BUSINESS OUTCOME EXISTS
# ==========================================

def test_member_not_found_outcome():

    artifact = load_artifact(
        ARTIFACT_PATH
    )

    codes = [
        outcome.code
        for outcome
        in artifact.business_outcomes
    ]

    assert (
        "member_not_found"
        in codes
    )