from urllib.parse import urlparse


# ==========================================
# ALLOWED ACTION TYPES
# ==========================================

ALLOWED_ACTIONS = {
    "fill",
    "click",
    "read"
}


# ==========================================
# BLOCKED / HUMAN REQUIRED KEYWORDS
# ==========================================

BLOCKED_KEYWORDS = {
    "delete",
    "remove",
    "close account"
}


HUMAN_REQUIRED_KEYWORDS = {
    "transfer",
    "payment",
    "submit",
    "confirm"
}


# ==========================================
# ALLOWED DOMAINS / ORIGINS
# ==========================================

ALLOWED_ORIGINS = {
    "http://127.0.0.1:5000",
    "http://localhost:5000"
}


# ==========================================
# ALLOWED ROUTES
# ==========================================

ALLOWED_ROUTE_PREFIXES = {
    "/",
    "/member",
    "/tenant-b"
}


# ==========================================
# URL SAFETY CHECK
# ==========================================

def check_url_safety(url):

    try:

        parsed = urlparse(url)

        origin = f"{parsed.scheme}://{parsed.netloc}"

        path = parsed.path or "/"

        # ----------------------------------
        # Check allowed origin/domain
        # ----------------------------------

        if origin not in ALLOWED_ORIGINS:

            return {
                "allowed": False,
                "decision": "block",
                "reason": f"Domain is not allowlisted: {origin}"
            }

        # ----------------------------------
        # Check allowed route
        # ----------------------------------

        route_allowed = any(
            path == prefix
            or path.startswith(prefix + "/")
            for prefix in ALLOWED_ROUTE_PREFIXES
        )

        if not route_allowed:

            return {
                "allowed": False,
                "decision": "block",
                "reason": f"Route is not allowlisted: {path}"
            }

        return {
            "allowed": True,
            "decision": "allow",
            "reason": "URL is allowlisted"
        }

    except Exception:

        return {
            "allowed": False,
            "decision": "block",
            "reason": "Invalid URL"
        }


# ==========================================
# ACTION SAFETY CHECK
# ==========================================

def check_action_safety(
    action_type,
    target_name=""
):

    # --------------------------------------
    # Unsupported action
    # --------------------------------------

    if action_type not in ALLOWED_ACTIONS:

        return {
            "allowed": False,
            "decision": "block",
            "reason": (
                f"Action type '{action_type}' "
                f"is not allowed"
            )
        }

    target_lower = (
        target_name or ""
    ).lower()

    # --------------------------------------
    # Explicitly blocked actions
    # --------------------------------------

    for keyword in BLOCKED_KEYWORDS:

        if keyword in target_lower:

            return {
                "allowed": False,
                "decision": "block",
                "reason": (
                    f"Target contains blocked "
                    f"keyword: {keyword}"
                )
            }

    # --------------------------------------
    # Human approval required
    # --------------------------------------

    for keyword in HUMAN_REQUIRED_KEYWORDS:

        if keyword in target_lower:

            return {
                "allowed": False,
                "decision": "human_required",
                "reason": (
                    f"Human interaction required "
                    f"for target containing: {keyword}"
                )
            }

    # --------------------------------------
    # Safe action
    # --------------------------------------

    return {
        "allowed": True,
        "decision": "allow",
        "reason": "Action is allowed"
    }