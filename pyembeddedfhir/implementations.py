import time
from typing import Any, List, Optional
from abc import ABC, abstractmethod
import logging
from urllib.parse import urljoin

from docker.client import DockerClient  # type: ignore[import]
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


def _prepare_ports_config(
    host_ip: Optional[str],
    container_port: int,
) -> Any:
    if host_ip:
        ports_config = {
            "ports": {
                f"{container_port}/tcp": (host_ip, 0),
            }
        }
    else:
        ports_config = {}
    return ports_config


def _wait_for_startup(
    docker_client: DockerClient,
    network: Network,
    ip: str,
    port: int,
    base_path: str,
    timeout: float,
):
    base_url = urljoin(f"http://{ip}:{port}/", base_path)
    metadata_url = urljoin(base_url, "metadata")
    start_time = time.monotonic()
    while True:
        current_time = time.monotonic()
        if current_time - start_time > timeout:
            raise StartupTimeoutError("Startup timeout exceeded.")

        probe_container = docker_client.containers.run(
            image="curlimages/curl:7.79.1",
            command=f"curl --silent --fail {metadata_url}",
            auto_remove=True,
            network=network.id,
            labels={DOCKER_LABEL_KEY: get_docker_label_value()},
            detach=True,
        )
        r = probe_container.wait()
        if r["StatusCode"] == 0:
            return

        time.sleep(1)


def _create_running_fhir_from_container(
    docker_client: DockerClient,
    configuration: Configuration,
    network: Network,
    container: Container,
    base_path: str,
    port: int,
) -> RunningFHIR:
    network_settings = container.attrs["NetworkSettings"]

    # read container's IP in the specified network
    container_network = _select_container_network_by_id(
        network.id, network_settings["Networks"].values()
    )
    ip = container_network["IPAddress"]

    _wait_for_startup(
        docker_client,
        network,
        ip,
        port,
        base_path,
        configuration.startup_timeout,
    )

    # read host port
    if configuration.host_ip:
        host_port = network_settings["Ports"][f"{port}/tcp"][0]["HostPort"]
    else:
        host_port = None

    return RunningFHIR(
        network_id=network.id,
        ip=ip,
        port=port,
        path=base_path,
        host_port=host_port,
    )


class FHIRImplementation(ABC):
    """Base class for all FHIR implementations."""

    @abstractmethod
    def start(
        self,
        docker_client: DockerClient,
        configuration: Configuration,
        network: Network,
    ) -> RunningFHIR:
        raise NotImplementedError()

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError()


class HAPIFHIRImplementation(FHIRImplementation):
    _CONTAINER_PORT = 8080
    _containers: List[Container]

    def __init__(self):
        super().__init__()
        self._containers = []

    def _pull_image(self, docker_client: DockerClient) -> Image:
        LOGGER.info("Pulling HAPI FHIR image...")
        image = docker_client.images.pull(
            "hapiproject/hapi",
            "v5.5.1",
        )
        LOGGER.info("Image pull finished.")
        return image

    def _run_container(
        self,
        docker_client: DockerClient,
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
        self._containers.append(container)
        container.reload()
        return container

    def start(
        self,
        docker_client: DockerClient,
        configuration: Configuration,
        network: Network,
    ) -> RunningFHIR:
        try:
            image = self._pull_image(docker_client)
            ports_config = _prepare_ports_config(
                configuration.host_ip, HAPIFHIRImplementation._CONTAINER_PORT
            )
            container = self._run_container(
                docker_client,
                network,
                image,
                ports_config,
            )

            return _create_running_fhir_from_container(
                docker_client=docker_client,
                configuration=configuration,
                network=network,
                container=container,
                base_path="/fhir/",
                port=HAPIFHIRImplementation._CONTAINER_PORT,
            )
        except:  # noqa: E722 (intentionally using bare except)
            self.stop()
            raise

    def stop(self) -> None:
        for container in self._containers:
            container.kill()


class MicrosoftFHIRImplemention(FHIRImplementation):
    _SAPASSWORD = "wW89*XK6aedjMSz9s"
    _CONTAINER_PORT = 8080

    _containers: List[Container]

    def __init__(self):
        super().__init__()
        self._containers = []

    def _pull_mssql_image(self, docker_client: DockerClient) -> Image:
        LOGGER.info("Pulling MSSQL image...")
        image = docker_client.images.pull(
            "mcr.microsoft.com/mssql/server",
            "2019-GDR2-ubuntu-16.04",
        )
        LOGGER.info("Image pull finished.")
        return image

    def _wait_for_mssql(
        self,
        container: Container,
        timeout_seconds: float,
    ) -> None:
        password = MicrosoftFHIRImplemention._SAPASSWORD
        time_start = time.monotonic()
        while True:
            time_current = time.monotonic()
            if time_current - time_start > timeout_seconds:
                raise StartupTimeoutError("Startup timeout exceeded.")

            exit_code, _ = container.exec_run(
                [
                    "/bin/bash",
                    "-c",
                    f"/opt/mssql-tools/bin/sqlcmd -U sa -P {password}\
                         -Q 'SELECT * FROM INFORMATION_SCHEMA.TABLES'",
                ]
            )
            if exit_code == 0:
                return

    def _run_mssql(
        self,
        image: Image,
        docker_client: DockerClient,
        network: Network,
    ) -> Container:
        LOGGER.info("Starting MSSQL...")
        password = MicrosoftFHIRImplemention._SAPASSWORD
        container = docker_client.containers.run(
            image=image.id,
            auto_remove=True,
            detach=True,
            network=network.id,
            labels={DOCKER_LABEL_KEY: get_docker_label_value()},
            environment={
                "SA_PASSWORD": password,
                "ACCEPT_EULA": "Y",
            },
        )
        self._containers.append(container)
        container.reload()
        return container

    def _pull_fhir_server(self, docker_client: DockerClient) -> Image:
        LOGGER.info("Pulling fhir-server image...")
        image = docker_client.images.pull(
            "mcr.microsoft.com/healthcareapis/r4-fhir-server",
            "2.2.0",
        )
        LOGGER.info("Image pull finished.")
        return image

    def _run_fhir_server(
        self,
        image: Image,
        docker_client: DockerClient,
        network: Network,
        mssql_host: str,
        ports_config: Any,
    ) -> Container:
        LOGGER.info("Starting fhir-server...")
        password = MicrosoftFHIRImplemention._SAPASSWORD
        container = docker_client.containers.run(
            image=image.id,
            auto_remove=True,
            detach=True,
            **ports_config,
            network=network.id,
            labels={DOCKER_LABEL_KEY: get_docker_label_value()},
            environment={
                "FHIRServer__Security__Enabled": "false",
                "SqlServer__ConnectionString": f"Server=tcp:{mssql_host},\
                    1433;Initial Catalog=FHIR;Persist Security Info=False;\
                    User ID=sa;Password={password};\
                    MultipleActiveResultSets=False;\
                    Connection Timeout=30;",
                "SqlServer__AllowDatabaseCreation": "true",
                "SqlServer__Initialize": "true",
                "SqlServer__SchemaOptions__AutomaticUpdatesEnabled": "true",
                "DataStore": "SqlServer",
            },
        )
        self._containers.append(container)
        container.reload()
        return container

    def start(
        self,
        docker_client: DockerClient,
        configuration: Configuration,
        network: Network,
    ) -> RunningFHIR:
        try:
            mssql_image = self._pull_mssql_image(docker_client)
            mssql_container = self._run_mssql(
                mssql_image,
                docker_client,
                network,
            )
            self._wait_for_mssql(
                mssql_container,
                configuration.startup_timeout,
            )
            mssql_network_settings = mssql_container.attrs["NetworkSettings"]
            mssql_network = _select_container_network_by_id(
                network.id, mssql_network_settings["Networks"].values()
            )
            mssql_host = mssql_network["IPAddress"]

            ports_config = _prepare_ports_config(
                configuration.host_ip,
                MicrosoftFHIRImplemention._CONTAINER_PORT,
            )
            fhir_image = self._pull_fhir_server(docker_client)
            fhir_container = self._run_fhir_server(
                fhir_image, docker_client, network, mssql_host, ports_config
            )

            return _create_running_fhir_from_container(
                docker_client=docker_client,
                configuration=configuration,
                network=network,
                container=fhir_container,
                base_path="/",
                port=MicrosoftFHIRImplemention._CONTAINER_PORT,
            )
        except:  # noqa: E722 (intentionally using bare except)
            self.stop()
            raise

    def stop(self) -> None:
        for container in self._containers:
            container.kill()
