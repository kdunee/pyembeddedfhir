from unittest.mock import MagicMock, patch

import pytest

from pyembeddedfhir.fhir_runner import FHIRRunner
from pyembeddedfhir.models import FHIRFlavor


@pytest.fixture
def network_mock():
    return MagicMock()


@pytest.fixture
def docker_client_mock(network_mock):
    mock = MagicMock()
    mock.networks.create.return_value = network_mock
    return mock


class SomeUnexpectedError(Exception):
    pass


@pytest.fixture
def implementation_constructor_mock():
    return MagicMock()


@pytest.fixture
def patched_hapi_fhir_implementation(implementation_constructor_mock):
    with patch(
        "pyembeddedfhir.fhir_runner.HAPIFHIRImplementation",
        implementation_constructor_mock,
    ):
        yield implementation_constructor_mock


class TestNetworkRemoval:
    def test_network_removal_when_failure(
        self,
        docker_client_mock,
        patched_hapi_fhir_implementation,
        network_mock,
    ):
        """When faced with any error in the implementation,
        FHIRRunner should delete created network."""
        implementation = patched_hapi_fhir_implementation.return_value
        implementation.start.side_effect = SomeUnexpectedError()
        with pytest.raises(SomeUnexpectedError):
            FHIRRunner(
                FHIRFlavor.HAPI,
                docker_client=docker_client_mock,
            )
        network_mock.remove.assert_called_once()

    def test_when_success(
        self,
        docker_client_mock,
        patched_hapi_fhir_implementation,
        network_mock,
    ):
        """When the implementation succeeds,
        FHIRRunner should not delete created network."""
        FHIRRunner(
            FHIRFlavor.HAPI,
            docker_client=docker_client_mock,
        )
        network_mock.remove.assert_not_called()

    def test_when_context_manager(
        self,
        docker_client_mock,
        patched_hapi_fhir_implementation,
        network_mock,
    ):
        """When FHIRRunner is used as context manager,
        it should delete created network."""
        with FHIRRunner(
            FHIRFlavor.HAPI,
            docker_client=docker_client_mock,
        ):
            pass
        network_mock.remove.assert_called_once()

    def test_when_stop(
        self,
        docker_client_mock,
        patched_hapi_fhir_implementation,
        network_mock,
    ):
        """When stop() is explicitly called,
        FHIRRunner should delete created network."""
        runner = FHIRRunner(
            FHIRFlavor.HAPI,
            docker_client=docker_client_mock,
        )
        runner.stop()
        network_mock.remove.assert_called_once()
