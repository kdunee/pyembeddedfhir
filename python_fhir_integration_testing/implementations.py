import time
from typing import Any, List
from abc import ABC, abstractmethod
import logging

import docker  # type: ignore[import]
from docker.models.containers import Container  # type: ignore[import]
from docker.models.images import Image  # type: ignore[import]
from docker.models.networks import Network  # type: ignore[import]

from .errors import NetworkNotFoundError, StartupTimeoutError
from .commons import DOCKER_LABEL_KEY, get_docker_label_value
from .models import Configuration, RunningFHIR

LOGGER = logging.getLogger(__name__)


def _select_container_network_by_id(
    network_id: str,
    networks: List[Any],
) -> Any:
    try:
        return next(
            filter(
                lambda network: network["NetworkID"] == network_id,
                networks,
            )
        )
    except StopIteration:
        raise NetworkNotFoundError(f"Network {network_id} was not found.")


class FHIRImplementation(ABC):
    """Base class for all FHIR implementations."""

    @abstractmethod
    def start(
        self,
        docker_client: docker.DockerClient,
        configuration: Configuration,
        network: Network,
    ) -> RunningFHIR:
        raise NotImplementedError()

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError()


class HAPIFHIRImplementation(FHIRImplementation):
    _CONTAINER_PORT = "8080/tcp"

    def _wait_for_startup(
        self,
        docker_client: docker.DockerClient,
        network: Network,
        ip: str,
        timeout: float,
    ):
        start_time = time.monotonic()
        while True:
            current_time = time.monotonic()
            if current_time - start_time > timeout:
                raise StartupTimeoutError("Startup timeout exceeded.")

            probe_container = docker_client.containers.run(
                image="curlimages/curl:7.79.1",
                command=f"curl --silent --fail http://{ip}:8080/fhir/metadata",
                auto_remove=True,
                network=network.id,
                labels={DOCKER_LABEL_KEY: get_docker_label_value()},
                detach=True,
            )
            r = probe_container.wait()
            if r["StatusCode"] == 0:
                return

            time.sleep(1)

    def _pull_image(self, docker_client: docker.DockerClient) -> Image:
        LOGGER.info("Pulling HAPI FHIR image...")
        image = docker_client.images.pull(
            "hapiproject/hapi",
            "v5.5.1",
        )
        LOGGER.info("Image pull finished.")
        return image

    def _prepare_ports_config(self, configuration: Configuration) -> Any:
        host_ip = configuration.host_ip
        if host_ip:
            ports_config = {
                "ports": {
                    HAPIFHIRImplementation._CONTAINER_PORT: (host_ip, 0),
                }
            }
        else:
            ports_config = {}
        return ports_config

    def _run_container(
        self,
        docker_client: docker.DockerClient,
        network: Network,
        image: Image,
        ports_config: Any,
    ) -> Container:
        LOGGER.info("Starting HAPI FHIR...")
        container = docker_client.containers.run(
            image=image.id,
            auto_remove=True,
            detach=True,
            **ports_config,
            network=network.id,
            labels={DOCKER_LABEL_KEY: get_docker_label_value()},
        )
        self._container = container
        container.reload()
        return container

    def start(
        self,
        docker_client: docker.DockerClient,
        configuration: Configuration,
        network: Network,
    ) -> RunningFHIR:
        image = self._pull_image(docker_client)
        ports_config = self._prepare_ports_config(configuration)
        container = self._run_container(
            docker_client,
            network,
            image,
            ports_config,
        )

        network_settings = container.attrs["NetworkSettings"]

        # read container's IP in the specified network
        container_network = _select_container_network_by_id(
            network.id, network_settings["Networks"].values()
        )
        ip = container_network["IPAddress"]

        self._wait_for_startup(
            docker_client,
            network,
            ip,
            configuration.startup_timeout,
        )

        # read host port
        if configuration.host_ip:
            host_port = network_settings["Ports"][
                HAPIFHIRImplementation._CONTAINER_PORT
            ][0]["HostPort"]
        else:
            host_port = None

        return RunningFHIR(
            network_id=network.id,
            ip=ip,
            port=8080,
            path="/fhir/",
            host_port=host_port,
        )

    def stop(self) -> None:
        self._container.kill()
