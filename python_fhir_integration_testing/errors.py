class PythonFHIRIntegrationTestingError(Exception):
    """A base class for errors in this package."""

    pass


class StartupTimeoutError(PythonFHIRIntegrationTestingError):
    """An error generated, when a startup timeout was reached."""

    pass


class ContainerRuntimeError(PythonFHIRIntegrationTestingError):
    """An error generated, when the container runtime failed."""

    pass


class NetworkNotFoundError(ContainerRuntimeError):
    """An error generated, when a specified network was not found."""

    pass


class AlreadyStoppedError(PythonFHIRIntegrationTestingError):
    """An error generated, when the user attempted to stop
    a server that was already stopped."""

    pass
