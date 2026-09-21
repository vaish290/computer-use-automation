from playwright.sync_api import sync_playwright

from artifact.loader import load_artifact
from artifact.resolver import resolve_target

from safety import (
    check_action_safety,
    check_url_safety
)

from human_takeover import request_human_takeover
from logger import RunLogger


# ==========================================
# RESOLVE RUNTIME VALUE
# ==========================================

def resolve_value(
    value,
    inputs
):

    # Non-string values do not need
    # template resolution.
    if not isinstance(
        value,
        str
    ):
        return value

    # Check whether this value is a
    # runtime input placeholder.
    if (
        value.startswith("{{")
        and value.endswith("}}")
    ):

        input_name = (
            value[2:-2]
            .strip()
        )

        # Runtime input was not provided.
        if input_name not in inputs:

            raise ValueError(
                f"Missing required input: "
                f"{input_name}"
            )

        return str(
            inputs[input_name]
        )

    # Normal strings remain unchanged.
    return value


# ==========================================
# VALIDATE REQUIRED INPUTS
# ==========================================

def validate_inputs(
    artifact,
    inputs
):

    for input_name, input_definition in (
        artifact.inputs.items()
    ):

        if (
            input_definition.required
            and input_name not in inputs
        ):

            raise ValueError(
                f"Missing required input: "
                f"{input_name}"
            )


# ==========================================
# GET STEP TARGET NAME
# ==========================================

def get_step_target_name(
    step
):

    if not step.target:
        return ""

    if step.target.accessible_name:

        return (
            step.target
            .accessible_name
        )

    if step.target.primary:

        return (
            step.target
            .primary
            .value
        )

    return ""


# ==========================================
# CHECK BUSINESS OUTCOMES
# ==========================================

def check_business_outcomes(
    page,
    artifact
):

    page_text = (
        page
        .locator("body")
        .inner_text()
    )

    for outcome in (
        artifact.business_outcomes
        or []
    ):

        condition = (
            outcome.condition
        )

        if (
            condition.type
            == "text_present"
        ):

            if (
                condition.value
                in page_text
            ):

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

    if not artifact.checkpoint:
        return True

    checkpoint = (
        artifact.checkpoint
    )

    if (
        checkpoint.type
        == "text_present"
    ):

        page_text = (
            page
            .locator("body")
            .inner_text()
        )

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
    evidence_path=(
        "evidence/replay_success.json"
    )
):

    # ======================================
    # LOAD ARTIFACT
    # ======================================

    artifact = load_artifact(
        artifact_path
    )

    # ======================================
    # VALIDATE REQUIRED INPUTS
    # ======================================

    validate_inputs(
        artifact,
        inputs
    )

    # ======================================
    # CREATE LOGGER
    # ======================================

    logger = RunLogger(
        mode="replay",
        artifact_name=artifact.name
    )

    logger.log_event(
        "replay_started",
        artifact_path=str(
            artifact_path
        ),
        inputs=inputs
    )

    outputs = {}

    playwright = None
    browser = None

    try:

        # ==================================
        # START PLAYWRIGHT
        # ==================================

        playwright = (
            sync_playwright()
            .start()
        )

        browser = (
            playwright
            .chromium
            .launch(
                headless=False
            )
        )

        page = (
            browser
            .new_page()
        )

        # ==================================
        # URL SAFETY CHECK
        # ==================================

        target_url = (
            artifact.target.url
        )

        url_safety = (
            check_url_safety(
                target_url
            )
        )

        logger.log_event(
            "url_safety_check",
            url=target_url,
            decision=url_safety
        )

        # ==================================
        # BLOCK UNSAFE URL
        # ==================================

        if not url_safety[
            "allowed"
        ]:

            result = {
                "status":
                    "blocked",

                "reason":
                    url_safety[
                        "reason"
                    ]
            }

            logger.log_event(
                "navigation_blocked",
                url=target_url,
                reason=url_safety[
                    "reason"
                ]
            )

            logger.set_result(
                result
            )

            logger.save(
                evidence_path
            )

            return result

        # ==================================
        # NAVIGATE
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
        # EXECUTE STEPS
        # ==================================

        for step in artifact.steps:

            step_id = (
                step.id
                if hasattr(
                    step,
                    "id"
                )
                else None
            )

            action_type = (
                step.action
            )

            target_name = (
                get_step_target_name(
                    step
                )
            )

            logger.log_event(
                "step_started",
                step=step_id,
                action=action_type,
                target=target_name
            )

            # ==================================
            # ACTION SAFETY CHECK
            # ==================================

            safety_result = (
                check_action_safety(
                    action_type,
                    target_name
                )
            )

            logger.log_event(
                "safety_check",
                step=step_id,
                action=action_type,
                target=target_name,
                decision=safety_result
            )

            # ==================================
            # HARD BLOCK
            # ==================================

            if (
                safety_result[
                    "decision"
                ]
                == "block"
            ):

                result = {
                    "status":
                        "blocked",

                    "reason":
                        safety_result[
                            "reason"
                        ]
                }

                logger.log_event(
                    "action_blocked",
                    step=step_id,
                    action=action_type,
                    target=target_name,
                    reason=safety_result[
                        "reason"
                    ]
                )

                logger.set_result(
                    result
                )

                logger.save(
                    evidence_path
                )

                return result

            # ==================================
            # HUMAN TAKEOVER
            # ==================================

            if (
                safety_result[
                    "decision"
                ]
                == "human_required"
            ):

                logger.log_event(
                    "human_takeover_requested",
                    step=step_id,
                    action=action_type,
                    target=target_name,
                    reason=safety_result[
                        "reason"
                    ]
                )

                takeover_result = (
                    request_human_takeover(
                        page,
                        safety_result[
                            "reason"
                        ],
                        action=action_type,
                        target=target_name
                    )
                )

                logger.log_event(
                    "human_takeover_result",
                    step=step_id,
                    result=takeover_result
                )

                if (
                    takeover_result[
                        "status"
                    ]
                    != "resumed"
                ):

                    result = {
                        "status":
                            "failure",

                        "reason":
                            takeover_result.get(
                                "message",
                                (
                                    "Human takeover "
                                    "failed"
                                )
                            )
                    }

                    logger.set_result(
                        result
                    )

                    logger.save(
                        evidence_path
                    )

                    return result

                # Human completed the step
                # manually in the same browser.

                logger.log_event(
                    "step_completed",
                    step=step_id,
                    action=action_type,
                    completed_by="human"
                )

                # Check whether the human
                # interaction caused a known
                # business outcome.

                business_result = (
                    check_business_outcomes(
                        page,
                        artifact
                    )
                )

                if business_result:

                    logger.log_event(
                        "business_outcome",
                        step=step_id,
                        result=business_result
                    )

                    logger.set_result(
                        business_result
                    )

                    logger.save(
                        evidence_path
                    )

                    return business_result

                # Do not execute the same
                # action automatically.
                continue

            # ==================================
            # NORMAL AUTOMATED EXECUTION
            # ==================================

            try:

                # ==============================
                # FILL
                # ==============================

                if action_type == "fill":

                    locator = (
                        resolve_target(
                            page,
                            step.target
                        )
                    )

                    runtime_value = (
                        resolve_value(
                            step.value,
                            inputs
                        )
                    )

                    locator.fill(
                        runtime_value
                    )

                    logger.log_event(
                        "step_completed",
                        step=step_id,
                        action="fill",
                        target=target_name
                    )

                # ==============================
                # CLICK
                # ==============================

                elif action_type == "click":

                    locator = (
                        resolve_target(
                            page,
                            step.target
                        )
                    )

                    locator.click()

                    page.wait_for_load_state(
                        "domcontentloaded"
                    )

                    logger.log_event(
                        "step_completed",
                        step=step_id,
                        action="click",
                        target=target_name
                    )

                # ==============================
                # READ
                # ==============================

                elif action_type == "read":

                    locator = (
                        resolve_target(
                            page,
                            step.target
                        )
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
                            step=step_id,
                            output=step.save_as,
                            value=value
                        )

                    logger.log_event(
                        "step_completed",
                        step=step_id,
                        action="read",
                        target=target_name
                    )

                # ==============================
                # UNSUPPORTED ACTION
                # ==============================

                else:

                    raise ValueError(
                        (
                            "Unsupported replay "
                            f"action: "
                            f"{action_type}"
                        )
                    )

            # ==================================
            # STEP FAILURE
            # ==================================

            except Exception as error:

                # Before treating this as a
                # technical failure, check if
                # the page shows a known
                # business outcome.

                business_result = (
                    check_business_outcomes(
                        page,
                        artifact
                    )
                )

                if business_result:

                    logger.log_event(
                        "business_outcome",
                        step=step_id,
                        result=business_result
                    )

                    logger.set_result(
                        business_result
                    )

                    logger.save(
                        evidence_path
                    )

                    return business_result

                result = {
                    "status":
                        "failure",

                    "code":
                        "step_execution_failed",

                    "step":
                        step_id,

                    "reason":
                        str(error)
                }

                logger.log_event(
                    "step_failed",
                    step=step_id,
                    action=action_type,
                    reason=str(error)
                )

                logger.set_result(
                    result
                )

                logger.save(
                    evidence_path
                )

                return result

            # ==================================
            # BUSINESS OUTCOME AFTER STEP
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
                    step=step_id,
                    result=business_result
                )

                logger.set_result(
                    business_result
                )

                logger.save(
                    evidence_path
                )

                return business_result

        # ==================================
        # FINAL BUSINESS OUTCOME CHECK
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
                result=business_result
            )

            logger.set_result(
                business_result
            )

            logger.save(
                evidence_path
            )

            return business_result

        # ==================================
        # FINAL CHECKPOINT
        # ==================================

        checkpoint_passed = (
            check_checkpoint(
                page,
                artifact
            )
        )

        logger.log_event(
            "checkpoint_checked",
            passed=checkpoint_passed
        )

        if not checkpoint_passed:

            result = {
                "status":
                    "failure",

                "code":
                    "checkpoint_failed",

                "reason":
                    (
                        "Expected checkpoint "
                        "was not found"
                    )
            }

            logger.set_result(
                result
            )

            logger.save(
                evidence_path
            )

            return result

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
            outputs=outputs
        )

        logger.set_result(
            result
        )

        logger.save(
            evidence_path
        )

        return result

    # ======================================
    # GENERAL REPLAY FAILURE
    # ======================================

    except Exception as error:

        result = {
            "status":
                "failure",

            "code":
                "replay_failed",

            "reason":
                str(error)
        }

        logger.log_event(
            "replay_failure",
            reason=str(error)
        )

        logger.set_result(
            result
        )

        logger.save(
            evidence_path
        )

        return result

    # ======================================
    # CLEANUP
    # ======================================

    finally:

        if browser:

            try:

                input(
                    "\nPress Enter to close browser..."
                )

            except EOFError:

                pass

            browser.close()

        if playwright:

            playwright.stop()