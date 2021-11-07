class PyFHIREmbeddedError(Exception):
    """A base class for errors in this package."""

    pass


class StartupTimeoutError(PyFHIREmbeddedError):
    """An error generated, when a startup timeout was reached."""

    pass


class ContainerRuntimeError(PyFHIREmbeddedError):
    """An error generated, when the container runtime failed."""

    pass


class NetworkNotFoundError(ContainerRuntimeError):
    """An error generated, when a specified network was not found."""

    pass


class AlreadyStoppedError(PyFHIREmbeddedError):
    """An error generated, when the user attempted to stop
    a server that was already stopped."""

    pass
