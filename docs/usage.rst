=====
Usage
=====

python-fhir-integration-testing requires Docker to run the 🔥 FHIR server.
Connection to the Docker daemon can be configured via environment variables:

* ``DOCKER_HOST`` - The URL to the Docker host.
* ``DOCKER_TLS_VERIFY`` - Verify the host against a CA certificate.
* ``DOCKER_CERT_PATH`` - A path to a directory containing TLS certificates to use when connecting to the Docker host.

To use python-fhir-integration-testing in a project::

    from python_fhir_integration_testing.fhir_runner import FHIRFlavor, FHIRRunner

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

For available values of ``FHIRFlavor`` please refer to :class:`python_fhir_integration_testing.models.FHIRFlavor`.
