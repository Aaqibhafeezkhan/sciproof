"""Exception types used by SciProof."""


class SciProofError(Exception):
    """Base class for all expected SciProof errors (shown to the user without a traceback)."""


class ManifestError(SciProofError):
    """The manifest is missing, malformed, unsupported or contains unsafe values."""


class UnsafePathError(SciProofError):
    """A path is absolute, escapes the base directory, or otherwise cannot be trusted."""


class CaptureError(SciProofError):
    """The experiment could not be captured."""


class CommandFailed(CaptureError):
    """A run of the command failed; ``details`` are lines to show after the message."""

    def __init__(self, message: str, details: list[str]) -> None:
        super().__init__(message)
        self.details = details


class UsageError(SciProofError):
    """An option has an invalid value."""


class ConfirmationRequired(SciProofError):
    """Re-execution was requested but not confirmed by the user."""
