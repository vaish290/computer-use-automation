from playwright.sync_api import sync_playwright

from artifact.loader import load_artifact
from artifact.resolver import resolve_target

from safety import check_action_safety
from human_takeover import request_human_takeover
from logger import RunLogger


# ==========================================
# RESOLVE TEMPLATE VALUE
# ==========================================

def resolve_value(value, inputs):

    if not isinstance(value, str):
        return value

    if (
        value.startswith("{{")
        and value.endswith("}}")
    ):

        input_name = value[2:-2].strip()

        if input_name not in inputs:
            raise ValueError(
                f"Missing required input: {input_name}"
            )

        return inputs[input_name]

    return value


# ==========================================
# GET TARGET NAME
# ==========================================

def get_step_target_name(step):

    if step.target.accessible_name:
        return step.target.accessible_name

    primary = step.target.primary

    if primary.accessible_name:
        return primary.accessible_name

    return primary.value


# ==========================================
# CHECK BUSINESS OUTCOMES
# ==========================================

def check_business_outcomes(
    page,
    artifact
):

    page_text = page.locator(
        "body"
    ).inner_text()

    for outcome in artifact.business_outcomes:

        condition = outcome.condition

        if condition.type == "text_present":

            if condition.value in page_text:

                return {
                    "status":
                        "business_outcome",

                    "code":
                        outcome.code,

                    "message":
                        outcome.message
                }

    return None


# ==========================================
# CHECK CHECKPOINT
# ==========================================

def check_checkpoint(
    page,
    artifact
):

    checkpoint = artifact.checkpoint

    if checkpoint.type == "text_present":

        page_text = page.locator(
            "body"
        ).inner_text()

        return (
            checkpoint.value
            in page_text
        )

    return False


# ==========================================
# REPLAY
# ==========================================

def replay(
    artifact_path,
    inputs,
    evidence_path="evidence/replay_success.json"
):

    # --------------------------------------
    # Load artifact
    # --------------------------------------

    artifact = load_artifact(
        artifact_path
    )

    outputs = {}

    # --------------------------------------
    # Create evidence logger
    # --------------------------------------

    logger = RunLogger(
        mode="replay",
        artifact_name=artifact.name
    )

    logger.log_event(
        "replay_started",
        artifact_path=artifact_path,
        target_url=artifact.target.url
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        try:

            # ==================================
            # OPEN APPLICATION
            # ==================================

            logger.log_event(
                "navigation_started",
                url=artifact.target.url
            )

            page.goto(
                artifact.target.url
            )

            logger.log_event(
                "navigation_completed",
                url=page.url
            )

            # ==================================
            # EXECUTE STEPS
            # ==================================

            for step in artifact.steps:

                print(
                    f"\nExecuting {step.id}: "
                    f"{step.action}"
                )

                target_name = (
                    get_step_target_name(
                        step
                    )
                )

                # ------------------------------
                # Log step start
                # ------------------------------

                logger.log_event(
                    "step_started",
                    step=step.id,
                    action=step.action,
                    target=target_name
                )

                # ==============================
                # SAFETY CHECK
                # ==============================

                safety_result = (
                    check_action_safety(
                        step.action,
                        target_name
                    )
                )

                print(
                    "SAFETY CHECK:"
                )

                print(
                    safety_result
                )

                logger.log_event(
                    "safety_check",
                    step=step.id,
                    action=step.action,
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

                decision = safety_result[
                    "decision"
                ]

                # ==============================
                # BLOCK
                # ==============================

                if decision == "block":

                    blocked_result = {

                        "status":
                            "blocked",

                        "step":
                            step.id,

                        "action":
                            step.action,

                        "target":
                            target_name,

                        "reason":
                            safety_result["reason"]
                    }

                    logger.log_event(
                        "action_blocked",
                        step=step.id,
                        action=step.action,
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
                # HUMAN TAKEOVER
                # ==============================

                if decision == "human_required":

                    logger.log_event(
                        "human_takeover_started",
                        step=step.id,
                        action=step.action,
                        target=target_name,
                        reason=(
                            safety_result[
                                "reason"
                            ]
                        )
                    )

                    takeover_result = (
                        request_human_takeover(

                            page=page,

                            reason=(
                                safety_result[
                                    "reason"
                                ]
                            ),

                            action=step.action,

                            target=target_name
                        )
                    )

                    if (
                        takeover_result["status"]
                        != "resumed"
                    ):

                        logger.log_event(
                            "human_takeover_failed",
                            step=step.id,
                            result=takeover_result
                        )

                        logger.set_result(
                            takeover_result
                        )

                        logger.save(
                            evidence_path
                        )

                        print(
                            "\nTAKEOVER FAILED"
                        )

                        print(
                            takeover_result
                        )

                        return takeover_result

                    logger.log_event(
                        "human_takeover_completed",
                        step=step.id,
                        resumed_url=page.url
                    )

                    print(
                        "\nHuman completed the "
                        "required action."
                    )

                    print(
                        "Skipping automatic "
                        f"execution of {step.id}."
                    )

                    logger.log_event(
                        "step_completed_by_human",
                        step=step.id,
                        action=step.action,
                        target=target_name
                    )

                    # --------------------------
                    # Business outcome check
                    # --------------------------

                    business_result = (
                        check_business_outcomes(
                            page,
                            artifact
                        )
                    )

                    if business_result:

                        logger.log_event(
                            "business_outcome",
                            step=step.id,
                            code=(
                                business_result[
                                    "code"
                                ]
                            ),
                            message=(
                                business_result[
                                    "message"
                                ]
                            )
                        )

                        logger.set_result(
                            business_result
                        )

                        logger.save(
                            evidence_path
                        )

                        print(
                            "\nBUSINESS OUTCOME"
                        )

                        print(
                            business_result
                        )

                        return business_result

                    continue

                # ==============================
                # NORMAL SAFE ACTION
                # ==============================

                try:

                    # --------------------------
                    # FILL
                    # --------------------------

                    if step.action == "fill":

                        locator = resolve_target(
                            page,
                            step.target
                        )

                        value = resolve_value(
                            step.value,
                            inputs
                        )

                        locator.fill(
                            str(value)
                        )

                    # --------------------------
                    # CLICK
                    # --------------------------

                    elif step.action == "click":

                        locator = resolve_target(
                            page,
                            step.target
                        )

                        locator.click()

                        page.wait_for_load_state(
                            "domcontentloaded"
                        )

                    # --------------------------
                    # READ
                    # --------------------------

                    elif step.action == "read":

                        locator = resolve_target(
                            page,
                            step.target
                        )

                        value = (
                            locator
                            .inner_text()
                            .strip()
                        )

                        if step.save_as:

                            outputs[
                                step.save_as
                            ] = value

                            logger.log_event(
                                "output_extracted",
                                step=step.id,
                                output=step.save_as,
                                value=value
                            )

                    else:

                        raise ValueError(
                            "Unsupported action: "
                            f"{step.action}"
                        )

                    # --------------------------
                    # Step completed
                    # --------------------------

                    logger.log_event(
                        "step_completed",
                        step=step.id,
                        action=step.action,
                        target=target_name
                    )

                # ==============================
                # STEP FAILURE
                # ==============================

                except Exception as error:

                    business_result = (
                        check_business_outcomes(
                            page,
                            artifact
                        )
                    )

                    if business_result:

                        logger.log_event(
                            "business_outcome",
                            step=step.id,
                            code=(
                                business_result[
                                    "code"
                                ]
                            ),
                            message=(
                                business_result[
                                    "message"
                                ]
                            )
                        )

                        logger.set_result(
                            business_result
                        )

                        logger.save(
                            evidence_path
                        )

                        print(
                            "\nBUSINESS OUTCOME"
                        )

                        print(
                            business_result
                        )

                        return business_result

                    failure = {

                        "status":
                            "failure",

                        "error":
                            "step_execution_failed",

                        "step":
                            step.id,

                        "action":
                            step.action,

                        "message":
                            str(error)
                    }

                    logger.log_event(
                        "step_failed",
                        step=step.id,
                        action=step.action,
                        target=target_name,
                        error=str(error)
                    )

                    logger.set_result(
                        failure
                    )

                    logger.save(
                        evidence_path
                    )

                    print(
                        "\nTECHNICAL FAILURE"
                    )

                    print(
                        failure
                    )

                    return failure

                # ==============================
                # BUSINESS OUTCOME AFTER STEP
                # ==============================

                business_result = (
                    check_business_outcomes(
                        page,
                        artifact
                    )
                )

                if business_result:

                    logger.log_event(
                        "business_outcome",
                        step=step.id,
                        code=(
                            business_result[
                                "code"
                            ]
                        ),
                        message=(
                            business_result[
                                "message"
                            ]
                        )
                    )

                    logger.set_result(
                        business_result
                    )

                    logger.save(
                        evidence_path
                    )

                    print(
                        "\nBUSINESS OUTCOME"
                    )

                    print(
                        business_result
                    )

                    return business_result

            # ==================================
            # FINAL BUSINESS OUTCOME
            # ==================================

            business_result = (
                check_business_outcomes(
                    page,
                    artifact
                )
            )

            if business_result:

                logger.log_event(
                    "business_outcome",
                    code=business_result["code"],
                    message=(
                        business_result[
                            "message"
                        ]
                    )
                )

                logger.set_result(
                    business_result
                )

                logger.save(
                    evidence_path
                )

                print(
                    "\nBUSINESS OUTCOME"
                )

                print(
                    business_result
                )

                return business_result

            # ==================================
            # CHECKPOINT
            # ==================================

            checkpoint_passed = (
                check_checkpoint(
                    page,
                    artifact
                )
            )

            logger.log_event(
                "checkpoint_checked",
                condition=(
                    artifact
                    .checkpoint
                    .value
                ),
                passed=checkpoint_passed
            )

            if not checkpoint_passed:

                failure = {

                    "status":
                        "failure",

                    "error":
                        "checkpoint_failed",

                    "message":
                        (
                            "Expected success "
                            "checkpoint was not found"
                        )
                }

                logger.log_event(
                    "checkpoint_failed",
                    condition=(
                        artifact
                        .checkpoint
                        .value
                    )
                )

                logger.set_result(
                    failure
                )

                logger.save(
                    evidence_path
                )

                print(
                    "\nTECHNICAL FAILURE"
                )

                print(
                    failure
                )

                return failure

            # ==================================
            # SUCCESS
            # ==================================

            result = {

                "status":
                    "success",

                "outputs":
                    outputs
            }

            logger.log_event(
                "replay_completed",
                status="success"
            )

            logger.set_result(
                result
            )

            saved_log = logger.save(
                evidence_path
            )

            print(
                "\nSUCCESS"
            )

            print(
                result
            )

            print(
                "\nEVIDENCE SAVED:"
            )

            print(
                saved_log
            )

            return result

        # ======================================
        # GENERAL TECHNICAL FAILURE
        # ======================================

        except Exception as error:

            failure = {

                "status":
                    "failure",

                "error":
                    "replay_failed",

                "message":
                    str(error)
            }

            logger.log_event(
                "replay_failed",
                error=str(error)
            )

            logger.set_result(
                failure
            )

            logger.save(
                evidence_path
            )

            print(
                "\nTECHNICAL FAILURE"
            )

            print(
                failure
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
# RUN REPLAY
# ==========================================

if __name__ == "__main__":

    replay(
        (
            "artifacts/"
            "get_savings_balance_generated.json"
        ),

        {
            "member_id": "123456789"
        },

        evidence_path=(
            "evidence/"
            "replay_success.json"
        )
    )