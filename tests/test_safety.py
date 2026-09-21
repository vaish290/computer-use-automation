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
# IMPORT SAFETY
# ==========================================

from safety import check_action_safety


# ==========================================
# NORMAL ACTION SHOULD BE ALLOWED
# ==========================================

def test_normal_action_allowed():

    result = check_action_safety(
        "click",
        "Search Member"
    )

    assert result["allowed"] is True
    assert result["decision"] == "allow"


# ==========================================
# DELETE SHOULD BE BLOCKED
# ==========================================

def test_delete_action_blocked():

    result = check_action_safety(
        "click",
        "Delete Member"
    )

    assert result["allowed"] is False
    assert result["decision"] == "block"


# ==========================================
# PAYMENT REQUIRES HUMAN
# ==========================================

def test_payment_requires_human():

    result = check_action_safety(
        "click",
        "Confirm Payment"
    )

    assert result["allowed"] is False

    assert (
        result["decision"]
        == "human_required"
    )


# ==========================================
# UNSUPPORTED ACTION SHOULD BE BLOCKED
# ==========================================

def test_unsupported_action_blocked():

    result = check_action_safety(
        "download",
        "Download Statement"
    )

    assert result["allowed"] is False
    assert result["decision"] == "block"


# ==========================================
# READ SHOULD BE ALLOWED
# ==========================================

def test_read_action_allowed():

    result = check_action_safety(
        "read",
        "Savings Balance"
    )

    assert result["allowed"] is True
    assert result["decision"] == "allow"