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

from safety import (
    check_action_safety,
    check_url_safety
)


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


# ==========================================
# TENANT A URL SHOULD BE ALLOWED
# ==========================================

def test_tenant_a_url_allowed():

    result = check_url_safety(
        "http://127.0.0.1:5000/"
    )

    assert result["allowed"] is True
    assert result["decision"] == "allow"


# ==========================================
# TENANT B URL SHOULD BE ALLOWED
# ==========================================

def test_tenant_b_url_allowed():

    result = check_url_safety(
        "http://127.0.0.1:5000/tenant-b"
    )

    assert result["allowed"] is True
    assert result["decision"] == "allow"


# ==========================================
# EXTERNAL DOMAIN SHOULD BE BLOCKED
# ==========================================

def test_external_domain_blocked():

    result = check_url_safety(
        "https://example.com"
    )

    assert result["allowed"] is False
    assert result["decision"] == "block"

    assert (
        "not allowlisted"
        in result["reason"]
    )


# ==========================================
# UNAPPROVED ROUTE SHOULD BE BLOCKED
# ==========================================

def test_unapproved_route_blocked():

    result = check_url_safety(
        "http://127.0.0.1:5000/admin"
    )

    assert result["allowed"] is False
    assert result["decision"] == "block"

    assert (
        "not allowlisted"
        in result["reason"]
    )