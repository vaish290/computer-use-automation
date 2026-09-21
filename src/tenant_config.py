from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


TENANT_CONFIG = {

    "tenant_a": {

        "get_savings_balance": {

            "goal_template":
                "Retrieve the savings balance "
                "for member {input_value}",

            "input_name":
                "member_id",

            "target_url":
                "http://127.0.0.1:5000",

            "artifact_name":
                "get_savings_balance",

            "description":
                "Retrieve the savings balance "
                "for a member",

            "checkpoint":
                "Savings Balance",

            "artifact_path": str(
                PROJECT_ROOT
                / "artifacts"
                / "get_savings_balance_generated.json"
            ),

            "business_outcomes": [
                {
                    "code":
                        "member_not_found",

                    "condition": {
                        "type":
                            "text_present",

                        "value":
                            "Member not found"
                    },

                    "message":
                        "The requested member "
                        "was not found"
                }
            ]
        }
    },


    "tenant_b": {

        "get_savings_balance": {

            "goal_template":
                "Retrieve the savings amount "
                "for customer {input_value}",

            "input_name":
                "customer_id",

            "target_url":
                "http://127.0.0.1:5000/tenant-b",

            "artifact_name":
                "get_savings_balance",

            "description":
                "Retrieve the savings amount "
                "for a customer",

            "checkpoint":
                "Savings Amount",

            "artifact_path": str(
                PROJECT_ROOT
                / "artifacts"
                / "tenant_b_get_savings_balance.json"
            ),

            "business_outcomes": [
                {
                    "code":
                        "customer_not_found",

                    "condition": {
                        "type":
                            "text_present",

                        "value":
                            "Customer not found"
                    },

                    "message":
                        "The requested customer "
                        "was not found"
                }
            ]
        }
    }
}


def get_tenant_workflow(
    tenant,
    workflow
):

    if tenant not in TENANT_CONFIG:

        raise ValueError(
            f"Unknown tenant: {tenant}"
        )

    tenant_workflows = TENANT_CONFIG[
        tenant
    ]

    if workflow not in tenant_workflows:

        raise ValueError(
            f"Unknown workflow '{workflow}' "
            f"for tenant '{tenant}'"
        )

    return tenant_workflows[
        workflow
    ]