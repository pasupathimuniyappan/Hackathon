from enum import Enum


class IssueType(str, Enum):
    """Types of prompt issues."""
    VAGUE = "vague"
    MISSING_CONTEXT = "missing_context"
    INEFFICIENT = "inefficient"
    AMBIGUOUS = "ambiguous"
    MISSING_ROLE = "missing_role"
    MISSING_FORMAT = "missing_format"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    MEDIUM = "medium"
    LOW = "low"


class Impact(str, Enum):
    """Expected impact of fixing the issue."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OptimizationFocus(str, Enum):
    """Focus areas for optimization."""
    CLARITY = "clarity"
    EFFICIENCY = "efficiency"
    SPECIFICITY = "specificity"
    ALL = "all"


class OptimizationLevel(str, Enum):
    """Optimization intensity levels."""
    BASIC = "basic"
    BALANCED = "balanced"
    ADVANCED = "advanced"
