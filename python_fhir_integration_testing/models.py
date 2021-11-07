from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

import docker  # type: ignore[import]


class FHIRFlavor(Enum):
    HAPI = auto()
    MICROSOFT = auto()


@dataclass
class Configuration:
    host_ip: Optional[str] = None
    kill_orphans: bool = True
    network_id: Optional[str] = None
    startup_timeout: float = 180
    docker_client: Optional[docker.DockerClient] = None


@dataclass
class RunningFHIR:
    """A descriptor of a running FHIR instance.

    :ivar network_id: The ID of the Docker network
    :vartype network_id: str
    :ivar ip: The IP address of the Docker container
    :vartype ip: str
    :ivar port: The port of a running FHIR instance
    :vartype port: int
    :ivar path: URL path to the FHIR instance
    :vartype path: str
    :ivar host_ip: The IP address of the interface on the host
    :vartype host_ip: Optional[str], optional
    """

    network_id: str
    ip: str
    port: int
    path: str
    host_port: Optional[int]
