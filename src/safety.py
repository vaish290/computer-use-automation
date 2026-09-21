# ==========================================
# SAFETY POLICY
# ==========================================

ALLOWED_ACTIONS = {
    "fill",
    "click",
    "read"
}


# ==========================================
# COMPLETELY BLOCKED ACTIONS
# ==========================================

BLOCKED_KEYWORDS = {
    "delete",
    "remove",
    "close account",
}


# ==========================================
# HUMAN CONFIRMATION REQUIRED
# ==========================================

HUMAN_REQUIRED_KEYWORDS = {
    "transfer",
    "payment",
    "submit",
    "confirm",
}


# ==========================================
# CHECK ACTION SAFETY
# ==========================================

def check_action_safety(
    action,
    target_name=None
):

    # --------------------------------------
    # Unknown action type
    # --------------------------------------

    if action not in ALLOWED_ACTIONS:

        return {
            "allowed": False,
            "decision": "block",
            "reason": (
                f"Action '{action}' is not "
                "in the allowed action list"
            )
        }

    # --------------------------------------
    # Check target
    # --------------------------------------

    if target_name:

        target_lower = (
            target_name.lower()
        )

        # ----------------------------------
        # Completely blocked
        # ----------------------------------

        for keyword in BLOCKED_KEYWORDS:

            if keyword in target_lower:

                return {
                    "allowed": False,
                    "decision": "block",
                    "reason": (
                        "Target contains blocked "
                        f"keyword: {keyword}"
                    )
                }

        # ----------------------------------
        # Human takeover required
        # ----------------------------------

        for keyword in HUMAN_REQUIRED_KEYWORDS:

            if keyword in target_lower:

                return {
                    "allowed": False,
                    "decision":
                        "human_required",

                    "reason": (
                        "Target requires human "
                        f"approval: {keyword}"
                    )
                }

    # --------------------------------------
    # Normal safe action
    # --------------------------------------

    return {
        "allowed": True,
        "decision": "allow",
        "reason": "Action allowed"
    }