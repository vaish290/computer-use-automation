def build_locator(page, locator_definition):
    """
    Convert one artifact locator definition
    into a Playwright locator.
    """

    strategy = locator_definition.strategy
    value = locator_definition.value

    # -----------------------------
    # ID
    # -----------------------------
    if strategy == "id":
        return page.locator(
            f'#{value}'
        )

    # -----------------------------
    # NAME
    # -----------------------------
    elif strategy == "name":
        return page.locator(
            f'[name="{value}"]'
        )

    # -----------------------------
    # LABEL
    # -----------------------------
    elif strategy == "label":
        return page.get_by_label(
            value
        )

    # -----------------------------
    # ROLE
    # -----------------------------
    elif strategy == "role":

        if locator_definition.accessible_name:

            return page.get_by_role(
                value,
                name=locator_definition.accessible_name
            )

        return page.get_by_role(
            value
        )

    # -----------------------------
    # CSS
    # -----------------------------
    elif strategy == "css":
        return page.locator(
            value
        )

    else:
        raise ValueError(
            f"Unsupported locator strategy: {strategy}"
        )


def resolve_target(page, target):
    """
    Try the primary locator first.
    If it does not uniquely identify a visible
    element, try the fallback locators.
    """

    locator_definitions = [
        target.primary,
        *target.fallbacks
    ]

    errors = []

    for locator_definition in locator_definitions:

        try:

            locator = build_locator(
                page,
                locator_definition
            )

            # We want exactly one matching element.
            count = locator.count()

            if count == 1 and locator.is_visible():

                print(
                    "Using locator:",
                    locator_definition.strategy,
                    "=",
                    locator_definition.value
                )

                return locator

            if count == 0:

                errors.append(
                    f"{locator_definition.strategy}="
                    f"{locator_definition.value}: "
                    f"not found"
                )

            else:

                errors.append(
                    f"{locator_definition.strategy}="
                    f"{locator_definition.value}: "
                    f"matched {count} elements"
                )

        except Exception as error:

            errors.append(
                f"{locator_definition.strategy}="
                f"{locator_definition.value}: "
                f"{str(error)}"
            )

    raise ValueError(
        "Unable to resolve target. Tried: "
        + " | ".join(errors)
    )