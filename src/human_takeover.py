# ==========================================
# HUMAN TAKEOVER
# ==========================================

def request_human_takeover(
    page,
    reason,
    action=None,
    target=None
):
    """
    Pause automation and allow a human
    to interact with the SAME browser.

    The Playwright browser stays open,
    so the current page, cookies, login
    state, and session are preserved.
    """

    print(
        "\n=========================="
    )

    print(
        "HUMAN TAKEOVER REQUIRED"
    )

    print(
        "=========================="
    )

    print(
        f"\nReason: {reason}"
    )

    if action:

        print(
            f"Action: {action}"
        )

    if target:

        print(
            f"Target: {target}"
        )

    print(
        "\nThe browser will remain open."
    )

    print(
        "You can now interact with the "
        "browser manually."
    )

    print(
        "\nWhen you are finished, return "
        "to this terminal."
    )

    input(
        "\nPress Enter to resume automation..."
    )

    # --------------------------------------
    # Verify browser is still available
    # --------------------------------------

    if page.is_closed():

        return {
            "status":
                "failure",

            "error":
                "browser_closed",

            "message":
                (
                    "The browser was closed "
                    "during human takeover"
                )
        }

    # --------------------------------------
    # Human finished
    # --------------------------------------

    result = {

        "status":
            "resumed",

        "url":
            page.url,

        "message":
            (
                "Human takeover completed. "
                "Automation can continue."
            )
    }

    print(
        "\nAUTOMATION RESUMED"
    )

    print(
        result
    )

    return result