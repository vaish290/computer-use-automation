def find_control(observation, control_id):
    """
    Find the full control information
    for a temporary control ID.
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


def find_data(observation, data_id):
    """
    Find the full readable data information
    for a temporary data ID.
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


def record_action(
    observation,
    action
):
    """
    Convert an LLM action into a richer
    discovery record.

    Controls are recorded for fill/click.
    Data items are recorded for read.
    """

    action_type = action["action"]

    # ==========================================
    # COMPLETE
    # ==========================================

    if action_type == "complete":

        return {
            "action": "complete",
            "output": action.get("output")
        }

    target_id = action.get("target")

    if not target_id:

        raise ValueError(
            "Action does not contain a target"
        )

    # ==========================================
    # FILL / CLICK
    # ==========================================

    if action_type in [
        "fill",
        "click"
    ]:

        control = find_control(
            observation,
            target_id
        )

        record = {
            "action": action_type,

            # Temporary discovery ID
            "control_id": target_id,

            # Durable information about
            # the actual UI control
            "control": control.copy()
        }

        if action_type == "fill":

            record["value"] = action.get(
                "value"
            )

        return record

    # ==========================================
    # READ
    # ==========================================

    elif action_type == "read":

        data_item = find_data(
            observation,
            target_id
        )

        record = {
            "action": "read",

            # Temporary discovery reference
            "data_id": target_id,

            # Information about what was read
            "data": data_item.copy(),

            # Name that replay should use
            # when returning the value
            "save_as": action.get(
                "save_as"
            )
        }

        return record

    # ==========================================
    # UNKNOWN ACTION
    # ==========================================

    else:

        raise ValueError(
            f"Unsupported action: {action_type}"
        )