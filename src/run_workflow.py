import sys

from artifact_registry import (
    get_workflow_config
)

from replay import replay


# ==========================================
# RUN WORKFLOW
# ==========================================

def run_workflow(
    tenant,
    workflow,
    input_value
):

    # --------------------------------------
    # Resolve tenant/workflow configuration
    # --------------------------------------

    config = get_workflow_config(
        tenant,
        workflow
    )

    artifact_path = config[
        "artifact_path"
    ]

    input_name = config[
        "input_name"
    ]

    # --------------------------------------
    # Build runtime inputs dynamically
    # --------------------------------------

    inputs = {
        input_name: input_value
    }

    # --------------------------------------
    # Evidence path
    # --------------------------------------

    evidence_path = (
        f"evidence/"
        f"{tenant}_{workflow}.json"
    )

    print(
        "\nWORKFLOW CONFIGURATION:"
    )

    print(
        f"Tenant: {tenant}"
    )

    print(
        f"Workflow: {workflow}"
    )

    print(
        f"Artifact: {artifact_path}"
    )

    print(
        f"Input: {input_name} = {input_value}"
    )

    # --------------------------------------
    # Execute generic replay
    # --------------------------------------

    return replay(
        artifact_path=artifact_path,
        inputs=inputs,
        evidence_path=evidence_path
    )


# ==========================================
# COMMAND LINE ENTRY POINT
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 4:

        print(
            "Usage: python src/run_workflow.py "
            "<tenant> <workflow> <input_value>"
        )

        sys.exit(1)

    tenant = sys.argv[1]

    workflow = sys.argv[2]

    input_value = sys.argv[3]

    result = run_workflow(
        tenant=tenant,
        workflow=workflow,
        input_value=input_value
    )

    print(
        "\nWorkflow result:"
    )

    print(
        result
    )