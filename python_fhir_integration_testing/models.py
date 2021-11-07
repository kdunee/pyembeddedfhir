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
    network_id: str
    ip: str
    port: int
    path: str
    host_port: Optional[int]
