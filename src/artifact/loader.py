import json

from artifact.schema import Artifact


def load_artifact(path: str) -> Artifact:

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    artifact = Artifact.model_validate(
        data
    )

    return artifact