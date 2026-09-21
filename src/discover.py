from playwright.sync_api import sync_playwright

from discovery.observer import observe_page
from discovery.planner import decide_next_action
from discovery.executor import execute_action
from discovery.recorder import record_action

from artifact.builder import (
    build_artifact,
    save_artifact
)

from safety import check_action_safety
from logger import RunLogger


# ==========================================
# GET TARGET NAME FOR SAFETY CHECK
# ==========================================

def get_target_name(
    observation,
    action
):

    target_id = action.get("target")

    if not target_id:
        return None

    # --------------------------------------
    # Search interactive controls
    # --------------------------------------

    for control in observation.get(
        "controls",
        []
    ):

        if (
            control.get("control_id")
            == target_id
        ):

            return (
                control.get("label")
                or control.get(
                    "accessible_name"
                )
                or control.get("name")
                or control.get("element_id")
            )

    # --------------------------------------
    # Search readable data
    # --------------------------------------

    for data_item in observation.get(
        "data",
        []
    ):

        if (
            data_item.get("data_id")
            == target_id
        ):

            return data_item.get(
                "label"
            )

    return None


# ==========================================
# DISCOVERY
# ==========================================

def discover(
    goal,
    inputs,
    target_url,
    artifact_name,
    description,
    checkpoint,
    business_outcomes,
    artifact_path,
    evidence_path
):

    history = []
    records = []

    max_steps = 10

    # --------------------------------------
    # Create evidence logger
    # --------------------------------------

    logger = RunLogger(
        mode="discovery",
        artifact_name=artifact_name
    )

    logger.log_event(
        "discovery_started",
        goal=goal,
        target_url=target_url
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        try:

            # ==================================
            # OPEN TARGET APPLICATION
            # ==================================

            logger.log_event(
                "navigation_started",
                url=target_url
            )

            page.goto(
                target_url
            )

            logger.log_event(
                "navigation_completed",
                url=page.url
            )

            # ==================================
            # DISCOVERY LOOP
            # ==================================

            for step_number in range(
                1,
                max_steps + 1
            ):

                print(
                    "\n=========================="
                )

                print(
                    f"DISCOVERY STEP {step_number}"
                )

                print(
                    "=========================="
                )

                # ==============================
                # 1. OBSERVE
                # ==============================

                observation = observe_page(
                    page
                )

                logger.log_event(
                    "observation_created",
                    step=step_number,
                    url=observation.get(
                        "url"
                    ),
                    title=observation.get(
                        "title"
                    ),
                    control_count=len(
                        observation.get(
                            "controls",
                            []
                        )
                    ),
                    data_count=len(
                        observation.get(
                            "data",
                            []
                        )
                    )
                )

                print(
                    "\nOBSERVATION:"
                )

                for control in observation.get(
                    "controls",
                    []
                ):

                    print(
                        control
                    )

                print(
                    "\nOBSERVED DATA:"
                )

                for data_item in observation.get(
                    "data",
                    []
                ):

                    print(
                        data_item
                    )

                print(
                    "\nPAGE TEXT:"
                )

                print(
                    observation.get(
                        "text",
                        ""
                    )
                )

                # ==============================
                # 2. DECIDE
                # ==============================

                action = decide_next_action(
                    goal,
                    observation,
                    history
                )

                logger.log_event(
                    "llm_decision",
                    step=step_number,
                    decision=action
                )

                print(
                    "\nLLM DECISION:"
                )

                print(
                    action
                )

                # ==============================
                # 3. COMPLETE
                # ==============================

                if action["action"] == "complete":

                    print(
                        "\nGOAL COMPLETED"
                    )

                    print(
                        action.get("output")
                    )

                    logger.log_event(
                        "goal_completed",
                        step=step_number,
                        output=action.get(
                            "output"
                        )
                    )

                    # ==========================
                    # BUILD ARTIFACT
                    # ==========================

                    artifact = build_artifact(

                        name=artifact_name,

                        description=description,

                        url=target_url,

                        records=records,

                        inputs=inputs,

                        checkpoint=checkpoint,

                        business_outcomes=(
                            business_outcomes
                        )
                    )

                    logger.log_event(
                        "artifact_built",
                        artifact_name=(
                            artifact.name
                        ),
                        schema_version=(
                            artifact.schema_version
                        ),
                        step_count=len(
                            artifact.steps
                        )
                    )

                    # ==========================
                    # SAVE ARTIFACT
                    # ==========================

                    saved_artifact_path = (
                        save_artifact(
                            artifact,
                            artifact_path
                        )
                    )

                    logger.log_event(
                        "artifact_generated",
                        path=saved_artifact_path
                    )

                    print(
                        "\nARTIFACT GENERATED:"
                    )

                    print(
                        saved_artifact_path
                    )

                    result = {

                        "status":
                            "success",

                        "output":
                            action.get("output"),

                        "history":
                            history,

                        "records":
                            records,

                        "artifact_path":
                            saved_artifact_path
                    }

                    logger.log_event(
                        "discovery_completed",
                        status="success"
                    )

                    logger.set_result(
                        result
                    )

                    saved_log = logger.save(
                        evidence_path
                    )

                    print(
                        "\nDISCOVERY EVIDENCE SAVED:"
                    )

                    print(
                        saved_log
                    )

                    return result

                # ==============================
                # 4. SAFETY CHECK
                # ==============================

                target_name = get_target_name(
                    observation,
                    action
                )

                safety_result = (
                    check_action_safety(
                        action["action"],
                        target_name
                    )
                )

                logger.log_event(
                    "safety_check",
                    step=step_number,
                    action=action["action"],
                    target=target_name,
                    decision=(
                        safety_result[
                            "decision"
                        ]
                    ),
                    reason=(
                        safety_result[
                            "reason"
                        ]
                    )
                )

                print(
                    "\nSAFETY CHECK:"
                )

                print(
                    safety_result
                )

                # ==============================
                # BLOCK UNSAFE ACTION
                # ==============================

                if not safety_result["allowed"]:

                    blocked_result = {

                        "status":
                            "blocked",

                        "action":
                            action["action"],

                        "target":
                            target_name,

                        "reason":
                            safety_result["reason"]
                    }

                    logger.log_event(
                        "action_blocked",
                        step=step_number,
                        action=action["action"],
                        target=target_name,
                        reason=(
                            safety_result[
                                "reason"
                            ]
                        )
                    )

                    logger.set_result(
                        blocked_result
                    )

                    logger.save(
                        evidence_path
                    )

                    print(
                        "\nACTION BLOCKED"
                    )

                    print(
                        blocked_result
                    )

                    return blocked_result

                # ==============================
                # 5. EXECUTE
                # ==============================

                execution_result = execute_action(
                    page,
                    observation,
                    action
                )

                logger.log_event(
                    "action_executed",
                    step=step_number,
                    action=action["action"],
                    target=target_name,
                    status=(
                        execution_result.get(
                            "status"
                        )
                    )
                )

                print(
                    "\nEXECUTION RESULT:"
                )

                print(
                    execution_result
                )

                # ==============================
                # 6. RECORD
                # ==============================

                record = record_action(
                    observation,
                    action
                )

                records.append(
                    record
                )

                logger.log_event(
                    "action_recorded",
                    step=step_number,
                    action=action["action"]
                )

                print(
                    "\nRECORDED ACTION:"
                )

                print(
                    record
                )

                # ==============================
                # 7. UPDATE HISTORY
                # ==============================

                history.append(
                    action
                )

            # ==================================
            # MAXIMUM STEPS
            # ==================================

            print(
                "\nMAXIMUM STEPS REACHED"
            )

            failure = {

                "status":
                    "failure",

                "reason":
                    "Maximum discovery steps reached",

                "history":
                    history,

                "records":
                    records
            }

            logger.log_event(
                "discovery_failed",
                reason=(
                    "Maximum discovery "
                    "steps reached"
                )
            )

            logger.set_result(
                failure
            )

            logger.save(
                evidence_path
            )

            return failure

        # ======================================
        # TECHNICAL FAILURE
        # ======================================

        except Exception as error:

            print(
                "\nDISCOVERY FAILED"
            )

            print(
                str(error)
            )

            failure = {

                "status":
                    "failure",

                "reason":
                    str(error),

                "history":
                    history,

                "records":
                    records
            }

            logger.log_event(
                "discovery_failed",
                reason=str(error)
            )

            logger.set_result(
                failure
            )

            logger.save(
                evidence_path
            )

            return failure

        # ======================================
        # CLOSE BROWSER
        # ======================================

        finally:

            input(
                "\nPress Enter to close browser..."
            )

            browser.close()


# ==========================================
# RUN DISCOVERY
# ==========================================

if __name__ == "__main__":

    result = discover(

        goal=(
            "Retrieve the savings balance "
            "for member 12345"
        ),

        inputs={
            "member_id": "12345"
        },

        target_url=(
            "http://127.0.0.1:5000"
        ),

        artifact_name=(
            "get_savings_balance"
        ),

        description=(
            "Retrieve the savings "
            "balance for a member"
        ),

        checkpoint=(
            "Savings Balance"
        ),

        business_outcomes=[
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
        ],

        artifact_path=(
            "artifacts/"
            "get_savings_balance_"
            "generated.json"
        ),

        evidence_path=(
            "evidence/"
            "discovery_success.json"
        )
    )

    print(
        "\nFINAL DISCOVERY RESULT:"
    )

    print(
        result
    )