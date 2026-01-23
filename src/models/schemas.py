from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from .enums import IssueType, Severity, Impact, OptimizationFocus, OptimizationLevel


class PromptIssue(BaseModel):
    """Represents a single issue found in a prompt."""
    
    id: str = Field(..., description="Unique identifier for the issue")
    start: int = Field(..., ge=0, description="Start position in text")
    end: int = Field(..., ge=0, description="End position in text")
    type: IssueType = Field(..., description="Type of issue")
    severity: Severity = Field(..., description="Severity level")
    message: str = Field(..., min_length=1, max_length=500, description="Human-readable message")
    suggestion: str = Field(..., min_length=1, max_length=1000, description="Suggested fix")
    impact: Optional[Impact] = Field(None, description="Expected impact of fix")
    
    @field_validator('end')
    @classmethod
    def end_must_be_greater_than_start(cls, v, info):
        if 'start' in info.data and v < info.data['start']:
            raise ValueError('end must be greater than or equal to start')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "issue-abc123",
                "start": 0,
                "end": 7,
                "type": "vague",
                "severity": "critical",
                "message": "The instruction is too vague",
                "suggestion": "analyze specifically focusing on",
                "impact": "high"
            }
        }


class AnalysisRequest(BaseModel):
    """Request model for prompt analysis."""
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The prompt text to analyze"
    )
    use_llm: bool = Field(
        default=False,
        description="Whether to use LLM for deeper analysis"
    )
    
    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('text cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "analyze data",
                "use_llm": False
            }
        }


class AnalysisResult(BaseModel):
    """Result of prompt analysis."""
    
    issues: List[PromptIssue] = Field(default_factory=list, description="List of issues found")
    quality_score: int = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    token_count: int = Field(..., ge=0, description="Estimated token count")
    estimated_improvement: Optional[int] = Field(None, ge=0, le=100, description="Potential quality improvement")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "issues": [],
                "quality_score": 85,
                "token_count": 45,
                "estimated_improvement": 10,
                "analyzed_at": "2026-01-21T10:00:00Z"
            }
        }


class Improvement(BaseModel):
    """Represents a single improvement made during optimization."""
    
    change: str = Field(..., min_length=1, max_length=500, description="Description of the change")
    impact: Impact = Field(..., description="Impact level of this improvement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "change": "Added specific role definition",
                "impact": "high"
            }
        }


class OptimizationRequest(BaseModel):
    """Request model for prompt optimization."""
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The prompt text to optimize"
    )
    focus: OptimizationFocus = Field(
        default=OptimizationFocus.ALL,
        description="Focus area for optimization"
    )
    level: OptimizationLevel = Field(
        default=OptimizationLevel.BALANCED,
        description="Optimization intensity level"
    )
    
    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('text cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "analyze data",
                "focus": "all",
                "level": "balanced"
            }
        }


class OptimizationResult(BaseModel):
    """Result of prompt optimization."""
    
    optimized_prompt: str = Field(..., min_length=1, description="The optimized prompt")
    improvements: List[Improvement] = Field(default_factory=list, description="List of improvements made")
    token_savings: int = Field(..., description="Token difference (negative means more tokens)")
    quality_improvement: int = Field(..., description="Quality score improvement")
    before_score: int = Field(..., ge=0, le=100, description="Quality score before optimization")
    after_score: int = Field(..., ge=0, le=100, description="Quality score after optimization")
    optimized_at: datetime = Field(default_factory=datetime.utcnow, description="Optimization timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "optimized_prompt": "You are a data analyst...",
                "improvements": [
                    {"change": "Added role definition", "impact": "high"}
                ],
                "token_savings": -15,
                "quality_improvement": 65,
                "before_score": 30,
                "after_score": 95,
                "optimized_at": "2026-01-21T10:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    redis_connected: bool = Field(..., description="Redis connection status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-01-21T10:00:00Z",
                "redis_connected": True
            }
        }
