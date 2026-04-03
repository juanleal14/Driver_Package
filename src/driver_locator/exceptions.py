class DriverLocatorError(Exception):
    """Base exception for driver locator package."""


class NoDriversAvailableError(DriverLocatorError):
    """Raised when no tracked drivers are available for lookup."""


class InvalidDriverIdError(DriverLocatorError):
    """Raised when a driver id is invalid."""


class InvalidLocationError(DriverLocatorError):
    """Raised when a location is invalid."""
