from urllib.parse import urljoin
from http import HTTPStatus

import requests
import pytest

from pyembeddedfhir.fhir_runner import FHIRFlavor, FHIRRunner


@pytest.fixture(
    scope="session",
    params=[FHIRFlavor.HAPI, FHIRFlavor.MICROSOFT],
)
def running_fhir_url(request):
    flavor = request.param
    with FHIRRunner(flavor, host_ip="127.0.0.1") as running_fhir:
        host_port = running_fhir.host_port
        path = running_fhir.path
        yield urljoin(f"http://127.0.0.1:{host_port}", path)


def test_metadata_returns_ok(running_fhir_url: str):
    metadata_url = urljoin(running_fhir_url, "metadata")
    r = requests.get(metadata_url)
    assert r.status_code == HTTPStatus.OK
