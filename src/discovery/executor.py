def find_control(
    observation,
    control_id
):
    """
    Find an interactive control from
    the current observation.
    """

    for control in observation.get(
        "controls",
        []
    ):

        if control["control_id"] == control_id:
            return control

    raise ValueError(
        f"Control not found: {control_id}"
    )


def find_data(
    observation,
    data_id
):
    """
    Find a readable data item from
    the current observation.
    """

    for data_item in observation.get(
        "data",
        []
    ):

        if data_item["data_id"] == data_id:
            return data_item

    raise ValueError(
        f"Data item not found: {data_id}"
    )


def execute_action(
    page,
    observation,
    action
):

    action_type = action["action"]

    # ==========================================
    # FILL
    # ==========================================

    if action_type == "fill":

        target_id = action["target"]

        control = find_control(
            observation,
            target_id
        )

        value = action.get(
            "value",
            ""
        )

        # Prefer element ID
        if control.get("element_id"):

            locator = page.locator(
                f'#{control["element_id"]}'
            )

        # Fall back to name
        elif control.get("name"):

            locator = page.locator(
                f'[name="{control["name"]}"]'
            )

        # Fall back to label
        elif control.get("label"):

            locator = page.get_by_label(
                control["label"]
            )

        else:

            raise ValueError(
                f"Unable to locate control: {target_id}"
            )

        locator.fill(
            str(value)
        )

        return {
            "status": "executed",
            "action": "fill",
            "target": target_id
        }

    # ==========================================
    # CLICK
    # ==========================================

    elif action_type == "click":

        target_id = action["target"]

        control = find_control(
            observation,
            target_id
        )

        # Buttons are normally located by
        # role + accessible name.
        if (
            control.get("role") == "button"
            and control.get("accessible_name")
        ):

            locator = page.get_by_role(
                "button",
                name=control[
                    "accessible_name"
                ]
            )

        elif control.get("element_id"):

            locator = page.locator(
                f'#{control["element_id"]}'
            )

        elif control.get("name"):

            locator = page.locator(
                f'[name="{control["name"]}"]'
            )

        else:

            raise ValueError(
                f"Unable to locate control: {target_id}"
            )

        locator.click()

        return {
            "status": "executed",
            "action": "click",
            "target": target_id
        }

    # ==========================================
    # READ
    # ==========================================

    elif action_type == "read":

        target_id = action["target"]

        data_item = find_data(
            observation,
            target_id
        )

        value = data_item["value"]

        return {
            "status": "executed",
            "action": "read",
            "target": target_id,
            "save_as": action.get("save_as"),
            "value": value
        }

    # ==========================================
    # UNKNOWN ACTION
    # ==========================================

    else:

        raise ValueError(
            f"Unsupported action: {action_type}"
        )