class PythonFHIRIntegrationTestingError(Exception):
    pass


class StartupTimeoutError(PythonFHIRIntegrationTestingError):
    pass


class ContainerRuntimeError(PythonFHIRIntegrationTestingError):
    pass


class NetworkNotFoundError(ContainerRuntimeError):
    pass


class AlreadyStoppedError(PythonFHIRIntegrationTestingError):
    pass
