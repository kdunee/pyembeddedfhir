import os

DOCKER_LABEL_KEY = "python_fhir_integration_testing"


def get_docker_label_value() -> str:
    return str(os.getpid())
