from tenant_config import get_tenant_workflow


def get_workflow_config(
    tenant,
    workflow
):

    config = get_tenant_workflow(
        tenant,
        workflow
    )

    return {
        "artifact_path":
            config["artifact_path"],

        "input_name":
            config["input_name"]
    }


def get_artifact(
    tenant,
    workflow
):

    config = get_workflow_config(
        tenant,
        workflow
    )

    return config[
        "artifact_path"
    ]