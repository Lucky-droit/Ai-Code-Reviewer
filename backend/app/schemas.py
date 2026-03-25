from enum import Enum

from pydantic import BaseModel, Field, field_validator


class IssueType(str, Enum):
    bug = "bug"
    security = "security"
    performance = "performance"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Source code to review")
    language: str = Field(..., min_length=1, description="Programming language")

    @field_validator("code")
    @classmethod
    def code_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("code must not be empty or whitespace")
        return value

    @field_validator("language")
    @classmethod
    def language_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("language must not be empty or whitespace")
        return value.strip()


class Issue(BaseModel):
    type: IssueType
    line: int = Field(..., ge=1)
    severity: Severity
    message: str = Field(..., min_length=1)


class ReviewResponse(BaseModel):
    issues: list[Issue]


MOCK_ISSUES: list[Issue] = [
    Issue(
        type=IssueType.bug,
        line=2,
        severity=Severity.high,
        message="Possible None access without a guard.",
    ),
    Issue(
        type=IssueType.security,
        line=1,
        severity=Severity.medium,
        message="Validate untrusted inputs before using them.",
    ),
    Issue(
        type=IssueType.performance,
        line=4,
        severity=Severity.low,
        message="Consider caching repeated work inside loops.",
    ),
]