import sys

from discover import discover
from tenant_config import get_tenant_workflow


def run_discovery(
    tenant,
    workflow,
    input_value
):

    # --------------------------------------
    # Get tenant configuration
    # --------------------------------------

    config = get_tenant_workflow(
        tenant,
        workflow
    )

    input_name = config[
        "input_name"
    ]

    # --------------------------------------
    # Build runtime input
    # --------------------------------------

    inputs = {
        input_name: input_value
    }

    # --------------------------------------
    # Build discovery goal
    # --------------------------------------

    goal = config[
        "goal_template"
    ].format(
        input_value=input_value
    )

    # --------------------------------------
    # Evidence path
    # --------------------------------------

    evidence_path = (
        f"evidence/"
        f"{tenant}_{workflow}_discovery.json"
    )

    print(
        "\nDISCOVERY CONFIGURATION:"
    )

    print(
        f"Tenant: {tenant}"
    )

    print(
        f"Workflow: {workflow}"
    )

    print(
        f"Target: {config['target_url']}"
    )

    print(
        f"Input: {input_name} = {input_value}"
    )

    # --------------------------------------
    # Generic discovery
    # --------------------------------------

    return discover(

        goal=goal,

        inputs=inputs,

        target_url=(
            config["target_url"]
        ),

        artifact_name=(
            config["artifact_name"]
        ),

        description=(
            config["description"]
        ),

        checkpoint=(
            config["checkpoint"]
        ),

        business_outcomes=(
            config["business_outcomes"]
        ),

        artifact_path=(
            config["artifact_path"]
        ),

        evidence_path=(
            evidence_path
        )
    )


if __name__ == "__main__":

    if len(sys.argv) != 4:

        print(
            "Usage: python src/run_discovery.py "
            "<tenant> <workflow> <input_value>"
        )

        sys.exit(1)

    tenant = sys.argv[1]

    workflow = sys.argv[2]

    input_value = sys.argv[3]

    result = run_discovery(
        tenant=tenant,
        workflow=workflow,
        input_value=input_value
    )

    print(
        "\nFINAL DISCOVERY RESULT:"
    )

    print(
        result
    )