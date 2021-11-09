import logging
from typing import Optional

import docker  # type: ignore[import]
from docker.client import DockerClient  # type: ignore[import]
from docker.models.networks import Network  # type: ignore[import]
from docker.errors import APIError  # type: ignore[import]
import psutil  # type: ignore[import]

from .errors import AlreadyStoppedError, ContainerRuntimeError
from .commons import DOCKER_LABEL_KEY, get_docker_label_value
from .implementations import (
    FHIRImplementation,
    HAPIFHIRImplementation,
    MicrosoftFHIRImplemention,
)
from .models import Configuration, FHIRFlavor, RunningFHIR

LOGGER = logging.getLogger(__name__)


def _kill_orphaned_containers(docker_client: DockerClient):
    containers = docker_client.containers.list(
        filters={
            "label": DOCKER_LABEL_KEY,
        },
    )
    for container in containers:
        parent_pid = int(container.labels[DOCKER_LABEL_KEY])
        if not psutil.pid_exists(parent_pid):
            LOGGER.info(
                f"Found orphaned container {container.id}, \
                    created by pid {parent_pid}, killing..."
            )
            container.kill()


def _kill_orphaned_networks(docker_client: DockerClient):
    networks = docker_client.networks.list(
        filters={
            "label": DOCKER_LABEL_KEY,
        },
    )
    for network in networks:
        parent_pid = int(network.attrs["Labels"][DOCKER_LABEL_KEY])
        if not psutil.pid_exists(parent_pid):
            LOGGER.info(
                f"Found orphaned network {network.id}, \
                    created by pid {parent_pid}, killing..."
            )
            network.remove()


def _create_implementation(flavor: FHIRFlavor) -> FHIRImplementation:
    if flavor == FHIRFlavor.HAPI:
        return HAPIFHIRImplementation()
    elif flavor == FHIRFlavor.MICROSOFT:
        return MicrosoftFHIRImplemention()
    else:
        raise NotImplementedError()


class FHIRRunner(object):
    """A class responsible for running a selected FHIR implementation.

    Can be used in one of two ways:

    * Directly, using the ``running_fhir`` property and the ``stop`` method.
    * As a context manager: ``with FHIRRunner(configuration) as running_fhir:``

    :param flavor: Selected FHIR implementation.
    :type flavor: FHIRFlavor
    :param host_ip: Host IP used to expose the service externally
        , defaults to None
    :type host_ip: str, optional
    :param kill_orphans: Whether to destroy orphaned Docker objects
        from previous runs, defaults to True
    :type kill_orphans: bool, optional
    :param network_id: A Docker network id to attach to, defaults to None
    :type network_id: Optional[str], optional
    :param startup_timeout: Number of seconds to wait for server startup,
        defaults to 120
    :type startup_timeout: float, optional
    :param docker_client: A Docker client, will be created
        using ``docker.from_env()`` if not set, defaults to None
    :type docker_client: Optional[DockerClient], optional
    :ivar running_fhir: Descriptor of the running FHIR server.
    :vartype running_fhir: RunningFHIR
    :raises NotImplementedError: Selected implementation is not supported.
    :raises StartupTimeoutError: An error caused by exceeding the time limit.
    :raises ContainerRuntimeError: An error related to container runtime.
    """

    running_fhir: RunningFHIR

    _implementation: FHIRImplementation
    _configuration: Configuration
    _network: Network
    _stopped: bool = False

    def __init__(
        self,
        flavor: FHIRFlavor,
        host_ip: Optional[str] = None,
        kill_orphans: bool = True,
        network_id: Optional[str] = None,
        startup_timeout: float = 120,
        docker_client: Optional[DockerClient] = None,
    ) -> None:
        """A constructor of ``RunningFHIR``."""
        self._configuration = Configuration(
            host_ip=host_ip,
            kill_orphans=kill_orphans,
            network_id=network_id,
            startup_timeout=startup_timeout,
            docker_client=docker_client,
        )

        self._implementation = _create_implementation(flavor)
        self.running_fhir = self._start()

    def _start(self) -> RunningFHIR:
        try:
            configuration = self._configuration

            if configuration.docker_client:
                docker_client = configuration.docker_client
            else:
                docker_client = docker.from_env()

            if configuration.kill_orphans:
                _kill_orphaned_containers(docker_client)
                _kill_orphaned_networks(docker_client)

            new_network_created = configuration.network_id is None
            if new_network_created:
                network = docker_client.networks.create(
                    name="pyembeddedfhir",
                    driver="bridge",
                    labels={DOCKER_LABEL_KEY: get_docker_label_value()},
                )
            else:
                network = docker_client.networks.get(configuration.network_id)
            self._network = network

            try:
                return self._implementation.start(
                    docker_client,
                    configuration,
                    network,
                )
            except:  # noqa: E722 (intentionally using bare except)
                if new_network_created:
                    network.remove()
                raise
        except APIError as e:
            raise ContainerRuntimeError(e)

    def _stop(self) -> None:
        try:
            if self._stopped:
                raise AlreadyStoppedError(
                    "Tried stopping FHIR, but it was already stopped."
                )
            self._implementation.stop()
            self._network.remove()
            self._stopped = True
        except APIError as e:
            raise ContainerRuntimeError(e)

    def stop(self) -> None:
        """Stop the FHIR server and perform cleanup.

        :raises ContainerRuntimeError: An error related to container runtime.
        :raises AlreadyStoppedError: If the runner was already stopped.
        """
        self._stop()

    def __enter__(self) -> RunningFHIR:
        return self.running_fhir

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._stop()
