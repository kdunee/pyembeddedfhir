from unittest.mock import MagicMock
import pytest

from pyembeddedfhir.implementations import (
    HAPIFHIRImplementation,
    MicrosoftFHIRImplemention,
)
from pyembeddedfhir.models import Configuration


@pytest.fixture
def network_mock():
    return MagicMock()


@pytest.fixture
def container_mock(network_mock):
    mock = MagicMock()
    mock.exec_run.return_value = (0, None)
    mock.attrs = {
        "NetworkSettings": {
            "Networks": {
                "a": {
                    "NetworkID": network_mock.id,
                    "IPAddress": "127.0.0.1",
                },
            },
        },
    }
    mock.wait.return_value = {"StatusCode": 0}
    return mock


@pytest.fixture
def docker_client_mock(container_mock):
    mock = MagicMock()
    mock.containers.run.return_value = container_mock
    return mock


@pytest.fixture
def sample_configuration(docker_client_mock):
    return Configuration(docker_client=docker_client_mock)


class SomeError(Exception):
    pass


class TestContainerRemoval:
    def test_microsoft_kills_both_containers_when_failure(
        self,
        docker_client_mock,
        network_mock,
        sample_configuration,
        container_mock,
    ):
        container_mock.wait.side_effect = SomeError()
        implementation = MicrosoftFHIRImplemention()
        with pytest.raises(SomeError):
            implementation.start(
                docker_client_mock,
                sample_configuration,
                network_mock,
            )
        assert container_mock.kill.call_count == 2

    def test_microsoft_kills_no_containers_when_success(
        self,
        docker_client_mock,
        network_mock,
        sample_configuration,
        container_mock,
    ):
        implementation = MicrosoftFHIRImplemention()
        implementation.start(
            docker_client_mock,
            sample_configuration,
            network_mock,
        )
        assert container_mock.kill.call_count == 0

    def test_hapi_kills_container_when_failure(
        self,
        docker_client_mock,
        network_mock,
        sample_configuration,
        container_mock,
    ):
        container_mock.wait.side_effect = SomeError()
        implementation = HAPIFHIRImplementation()
        with pytest.raises(SomeError):
            implementation.start(
                docker_client_mock,
                sample_configuration,
                network_mock,
            )
        assert container_mock.kill.call_count == 1

    def test_hapi_kills_no_containers_when_success(
        self,
        docker_client_mock,
        network_mock,
        sample_configuration,
        container_mock,
    ):
        implementation = HAPIFHIRImplementation()
        implementation.start(
            docker_client_mock,
            sample_configuration,
            network_mock,
        )
        assert container_mock.kill.call_count == 0
