import json
from datetime import datetime
from pathlib import Path


# ==========================================
# RUN LOGGER
# ==========================================

class RunLogger:

    def __init__(
        self,
        mode,
        artifact_name=None
    ):

        self.mode = mode
        self.artifact_name = artifact_name

        self.started_at = (
            datetime.now().isoformat()
        )

        self.events = []

        self.result = None


    # ======================================
    # ADD EVENT
    # ======================================

    def log_event(
        self,
        event,
        **details
    ):

        log_entry = {
            "timestamp":
                datetime.now().isoformat(),

            "event":
                event
        }

        log_entry.update(
            details
        )

        self.events.append(
            log_entry
        )


    # ======================================
    # SET FINAL RESULT
    # ======================================

    def set_result(
        self,
        result
    ):

        self.result = result


    # ======================================
    # SAVE LOG
    # ======================================

    def save(
        self,
        path
    ):

        log_data = {

            "mode":
                self.mode,

            "artifact":
                self.artifact_name,

            "started_at":
                self.started_at,

            "finished_at":
                datetime.now().isoformat(),

            "events":
                self.events,

            "result":
                self.result
        }

        output_path = Path(
            path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                log_data,
                file,
                indent=4
            )

        return str(
            output_path
        )