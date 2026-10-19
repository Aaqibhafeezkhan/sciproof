"""SciProof: record computational experiments and create verifiable evidence for them.

SciProof checks *integrity* and *execution reproducibility* of recorded runs. It does not,
and cannot, establish that a scientific result is correct. See docs/CONCEPTS.md.

The names in ``__all__`` are the supported Python API (docs/PYTHON_API.md). Everything else in
the package is internal and may change in any release.
"""

__version__ = "0.1.1"

# The imports follow ``__version__`` on purpose: ``capture`` reads it while it is being imported.
from sciproof.capture import CaptureResult  # noqa: E402
from sciproof.capture import capture as capture_experiment  # noqa: E402
from sciproof.diffmanifests import DiffReport, diff_manifests  # noqa: E402
from sciproof.errors import (  # noqa: E402
    CaptureError,
    ConfirmationRequired,
    ManifestError,
    SciProofError,
    UsageError,
)
from sciproof.manifest import load_manifest  # noqa: E402
from sciproof.verify import Check, Report, Status, report_to_dict  # noqa: E402
from sciproof.verify import verify as verify_manifest  # noqa: E402

__all__ = [
    "CaptureError",
    "CaptureResult",
    "Check",
    "ConfirmationRequired",
    "DiffReport",
    "ManifestError",
    "Report",
    "SciProofError",
    "Status",
    "UsageError",
    "__version__",
    "capture_experiment",
    "diff_manifests",
    "load_manifest",
    "report_to_dict",
    "verify_manifest",
]
