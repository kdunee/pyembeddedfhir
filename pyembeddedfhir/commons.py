import os

DOCKER_LABEL_KEY = "pyembeddedfhir"


def get_docker_label_value() -> str:
    return str(os.getpid())
