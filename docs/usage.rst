=====
Usage
=====

pyembeddedfhir requires Docker to run the 🔥 FHIR server.
Connection to the Docker daemon can be configured via environment variables:

* ``DOCKER_HOST`` - The URL to the Docker host.
* ``DOCKER_TLS_VERIFY`` - Verify the host against a CA certificate.
* ``DOCKER_CERT_PATH`` - A path to a directory containing TLS certificates to use when connecting to the Docker host.

To use pyembeddedfhir in a project::

    from pyembeddedfhir.fhir_runner import FHIRFlavor, FHIRRunner

    with FHIRRunner(
        flavor=FHIRFlavor.HAPI,
        host_ip="0.0.0.0",
    ) as running_fhir:
        print("The FHIR server is up and running 🔥")
        docker_network_id = running_fhir.network_id
        container_ip = running_fhir.ip
        port = running_fhir.port
        path = running_fhir.path
        host_port = running_fhir.host_port

-----
API
-----

.. autoclass:: pyembeddedfhir.fhir_runner.FHIRRunner
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyembeddedfhir.models.FHIRFlavor
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyembeddedfhir.models.RunningFHIR
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: pyembeddedfhir.errors
    :members:
    :undoc-members:
    :show-inheritance: