import json
from pathlib import Path

from artifact.schema import Artifact


# ==========================================
# PARAMETERIZATION
# ==========================================

def parameterize_value(value, inputs):
    """
    Convert a concrete discovery value into
    a reusable runtime parameter.

    Example:
        12345 -> {{member_id}}
    """

    for input_name, input_value in inputs.items():

        if str(value) == str(input_value):
            return "{{" + input_name + "}}"

    return value


# ==========================================
# BUILD CONTROL TARGET
# ==========================================

def build_target(control):
    """
    Convert observed control metadata into
    durable locator strategies.
    """

    role = control.get("role")

    accessible_name = (
        control.get("label")
        or control.get("accessible_name")
    )

    locators = []

    # --------------------------------------
    # ID
    # --------------------------------------

    if control.get("element_id"):

        locators.append({
            "strategy": "id",
            "value": control["element_id"]
        })

    # --------------------------------------
    # NAME
    # --------------------------------------

    if control.get("name"):

        locators.append({
            "strategy": "name",
            "value": control["name"]
        })

    # --------------------------------------
    # LABEL
    # --------------------------------------

    if control.get("label"):

        locators.append({
            "strategy": "label",
            "value": control["label"]
        })

    # --------------------------------------
    # ROLE
    # --------------------------------------

    if role and accessible_name:

        locators.append({
            "strategy": "role",
            "value": role,
            "accessible_name": accessible_name
        })

    if not locators:

        raise ValueError(
            "Unable to create durable target "
            f"for control: {control}"
        )

    return {
        "role": role,
        "accessible_name": accessible_name,
        "primary": locators[0],
        "fallbacks": locators[1:]
    }


# ==========================================
# BUILD READ TARGET
# ==========================================

def build_read_target(data_item):
    """
    Build a locator for a table value.

    Example HTML:

    <tr>
        <td>Savings Balance</td>
        <td>$4,320.50</td>
    </tr>

    We locate the row using its label and then
    select the second td containing the value.
    """

    label = data_item["label"]

    css_selector = (
        f'tr:has(td:text-is("{label}")) '
        f'td:nth-child(2)'
    )

    return {
        "role": None,
        "accessible_name": label,

        "primary": {
            "strategy": "css",
            "value": css_selector
        },

        "fallbacks": []
    }


# ==========================================
# BUILD STEPS
# ==========================================

def build_steps(records, inputs):

    steps = []

    step_number = 1

    for record in records:

        action = record["action"]

        # COMPLETE is not a browser action.
        if action == "complete":
            continue

        # ==================================
        # FILL
        # ==================================

        if action == "fill":

            step = {
                "id": f"step_{step_number}",
                "action": "fill",

                "target": build_target(
                    record["control"]
                ),

                "value": parameterize_value(
                    record.get("value"),
                    inputs
                )
            }

        # ==================================
        # CLICK
        # ==================================

        elif action == "click":

            step = {
                "id": f"step_{step_number}",
                "action": "click",

                "target": build_target(
                    record["control"]
                )
            }

        # ==================================
        # READ
        # ==================================

        elif action == "read":

            step = {
                "id": f"step_{step_number}",
                "action": "read",

                "target": build_read_target(
                    record["data"]
                ),

                "save_as": record.get(
                    "save_as"
                )
            }

        else:

            raise ValueError(
                f"Unsupported recorded action: {action}"
            )

        steps.append(
            step
        )

        step_number += 1

    return steps


# ==========================================
# BUILD INPUT DEFINITIONS
# ==========================================

def build_input_definitions(inputs):

    definitions = {}

    for name, value in inputs.items():

        if isinstance(value, bool):
            input_type = "boolean"

        elif isinstance(value, int):
            input_type = "integer"

        else:
            input_type = "string"

        definitions[name] = {
            "type": input_type,
            "required": True
        }

    return definitions


# ==========================================
# BUILD OUTPUT DEFINITIONS
# ==========================================

def build_output_definitions(records):
    """
    Every recorded READ action becomes
    an artifact output.
    """

    outputs = {}

    for record in records:

        if record["action"] != "read":
            continue

        save_as = record.get(
            "save_as"
        )

        if save_as:

            outputs[save_as] = {
                "type": "string"
            }

    return outputs


# ==========================================
# BUILD ARTIFACT
# ==========================================

def build_artifact(
    name,
    description,
    url,
    records,
    inputs,
    checkpoint,
    output=None,
    business_outcomes=None
):

    artifact_data = {

        "schema_version": "1.1",

        "name": name,

        "description": description,

        "target": {
            "url": url
        },

        "inputs":
            build_input_definitions(inputs),

        "steps":
            build_steps(
                records,
                inputs
            ),

        "outputs":
            build_output_definitions(
                records
            ),

        "business_outcomes":
            business_outcomes or [],

        "checkpoint": {
            "type": "text_present",
            "value": checkpoint
        }
    }

    # Validate generated artifact against
    # our Pydantic schema.
    artifact = Artifact.model_validate(
        artifact_data
    )

    return artifact


# ==========================================
# SAVE ARTIFACT
# ==========================================

def save_artifact(
    artifact,
    path
):

    output_path = Path(
        path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    artifact_dict = artifact.model_dump(
        exclude_none=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            artifact_dict,
            file,
            indent=4
        )

    return str(
        output_path
    )