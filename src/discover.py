from playwright.sync_api import sync_playwright

from discovery.observer import observe_page
from discovery.planner import decide_next_action
from discovery.executor import execute_action
from discovery.recorder import record_action

from artifact.builder import (
    build_artifact,
    save_artifact
)

from safety import (
    check_action_safety,
    check_url_safety
)

from logger import RunLogger


# ==========================================
# GET TARGET NAME
# ==========================================

def get_target_name(
    observation,
    action
):

    target_id = action.get(
        "target"
    )

    # --------------------------------------
    # Search interactive controls
    # --------------------------------------

    for control in observation.get(
        "controls",
        []
    ):

        if control.get(
            "control_id"
        ) == target_id:

            return (
                control.get("label")
                or control.get("accessible_name")
                or control.get("name")
                or control.get("element_id")
                or ""
            )

    # --------------------------------------
    # Search readable data
    # --------------------------------------

    for item in observation.get(
        "data",
        []
    ):

        if item.get(
            "data_id"
        ) == target_id:

            return (
                item.get("label")
                or ""
            )

    return ""


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

    max_steps = 10

    recorded_actions = []

    history = []

    logger = RunLogger(
        mode="discovery",
        artifact_name=artifact_name
    )

    logger.log_event(
        "discovery_started",
        goal=goal,
        target_url=target_url
    )

    playwright = None
    browser = None

    try:

        # ==================================
        # START PLAYWRIGHT
        # ==================================

        playwright = sync_playwright().start()

        browser = playwright.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        # ==================================
        # URL SAFETY CHECK
        # ==================================

        url_safety = check_url_safety(
            target_url
        )

        logger.log_event(
            "url_safety_check",
            url=target_url,
            decision=url_safety
        )

        if not url_safety["allowed"]:

            result = {
                "status": "blocked",
                "reason": url_safety["reason"]
            }

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
        # DISCOVERY LOOP
        # ==================================

        for step_number in range(
            1,
            max_steps + 1
        ):

            # ------------------------------
            # OBSERVE
            # ------------------------------

            observation = observe_page(
                page
            )

            logger.log_event(
                "observation_created",
                step=step_number,
                url=observation.get("url"),
                controls_count=len(
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

            # ------------------------------
            # LLM DECISION
            # ------------------------------

            action = decide_next_action(
                goal,
                observation,
                history
            )

            logger.log_event(
                "llm_decision",
                step=step_number,
                action=action
            )

            action_type = action.get(
                "action"
            )

            # ------------------------------
            # COMPLETE
            # ------------------------------

            if action_type == "complete":

                artifact = build_artifact(
                    name=artifact_name,
                    description=description,
                    target_url=target_url,
                    inputs=inputs,
                    recorded_actions=recorded_actions,
                    checkpoint=checkpoint,
                    business_outcomes=business_outcomes
                )

                logger.log_event(
                    "artifact_built",
                    artifact_name=artifact_name,
                    steps_count=len(
                        artifact.steps
                    )
                )

                save_artifact(
                    artifact,
                    artifact_path
                )

                logger.log_event(
                    "artifact_generated",
                    path=str(
                        artifact_path
                    )
                )

                result = {
                    "status": "success",
                    "artifact_path": str(
                        artifact_path
                    )
                }

                logger.log_event(
                    "discovery_completed",
                    artifact_path=str(
                        artifact_path
                    )
                )

                logger.set_result(
                    result
                )

                logger.save(
                    evidence_path
                )

                return result

            # ------------------------------
            # TARGET NAME
            # ------------------------------

            target_name = get_target_name(
                observation,
                action
            )

            # ------------------------------
            # ACTION SAFETY CHECK
            # ------------------------------

            safety_result = (
                check_action_safety(
                    action_type,
                    target_name
                )
            )

            logger.log_event(
                "safety_check",
                step=step_number,
                action=action_type,
                target=target_name,
                decision=safety_result
            )

            if not safety_result[
                "allowed"
            ]:

                result = {
                    "status": "blocked",
                    "reason": safety_result[
                        "reason"
                    ]
                }

                logger.log_event(
                    "action_blocked",
                    step=step_number,
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

            # ------------------------------
            # EXECUTE
            # ------------------------------

            execute_action(
                page,
                observation,
                action
            )

            logger.log_event(
                "action_executed",
                step=step_number,
                action=action_type,
                target=target_name
            )

            # ------------------------------
            # RECORD
            # ------------------------------

            recorded_action = record_action(
                observation,
                action
            )

            if recorded_action:

                recorded_actions.append(
                    recorded_action
                )

                logger.log_event(
                    "action_recorded",
                    step=step_number,
                    action=recorded_action
                )

            # ------------------------------
            # HISTORY
            # ------------------------------

            history.append(
                action
            )

        # ==================================
        # MAX STEPS REACHED
        # ==================================

        result = {
            "status": "failure",
            "reason": (
                "Maximum discovery steps reached"
            )
        }

        logger.log_event(
            "discovery_failure",
            reason=result["reason"]
        )

        logger.set_result(
            result
        )

        logger.save(
            evidence_path
        )

        return result

    except Exception as error:

        result = {
            "status": "failure",
            "reason": str(error)
        }

        logger.log_event(
            "discovery_failure",
            reason=str(error)
        )

        logger.set_result(
            result
        )

        logger.save(
            evidence_path
        )

        return result

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