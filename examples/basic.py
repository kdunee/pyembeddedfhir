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
