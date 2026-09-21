import sys
from pathlib import Path
import pytest


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
# IMPORT
# ==========================================

from replay import resolve_value


# ==========================================
# TEMPLATE VALUE RESOLVES
# ==========================================

def test_template_value_resolves():

    inputs = {
        "member_id": "12345"
    }

    result = resolve_value(
        "{{member_id}}",
        inputs
    )

    assert result == "12345"


# ==========================================
# DIFFERENT RUNTIME INPUT WORKS
# ==========================================

def test_different_runtime_input():

    inputs = {
        "member_id": "67890"
    }

    result = resolve_value(
        "{{member_id}}",
        inputs
    )

    assert result == "67890"


# ==========================================
# NORMAL STRING STAYS SAME
# ==========================================

def test_normal_value_unchanged():

    result = resolve_value(
        "hello",
        {
            "member_id": "12345"
        }
    )

    assert result == "hello"


# ==========================================
# NON-STRING VALUE STAYS SAME
# ==========================================

def test_non_string_value():

    result = resolve_value(
        100,
        {}
    )

    assert result == 100


# ==========================================
# MISSING INPUT RAISES ERROR
# ==========================================

def test_missing_input():

    with pytest.raises(
        ValueError,
        match="Missing required input"
    ):

        resolve_value(
            "{{member_id}}",
            {}
        )