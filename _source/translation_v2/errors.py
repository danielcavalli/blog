"""Error types for translation_v2 contract validation."""

from __future__ import annotations

from dataclasses import dataclass


class TranslationV2Error(Exception):
    """Base class for translation_v2 errors."""


@dataclass(slots=True)
class ContractValidationError(TranslationV2Error):
    """Base error that captures contract validation context."""

    message: str
    run_id: str
    stage: str
    field: str | None = None

    def __str__(self) -> str:
        location = f" field={self.field}" if self.field else ""
        return f"{self.message} (run_id={self.run_id} stage={self.stage}{location})"


@dataclass(slots=True)
class MissingFieldError(ContractValidationError):
    """Raised when a required field is missing from a payload."""


@dataclass(slots=True)
class TypeMismatchError(ContractValidationError):
    """Raised when a field has an unexpected type."""

    expected_type: str = ""
    actual_type: str = ""

    def __str__(self) -> str:
        base = super().__str__()
        return (
            f"{base} expected_type={self.expected_type} actual_type={self.actual_type}"
        )
