import pytest
from unittest.mock import AsyncMock, patch
from src.analyzers.rule_based import RuleBasedAnalyzer
from src.analyzers.hybrid_analyzer import HybridAnalyzer
from src.models import PromptIssue, IssueType, Severity


@pytest.fixture
def rule_analyzer():
    return RuleBasedAnalyzer()


@pytest.fixture
def hybrid_analyzer():
    return HybridAnalyzer()


class TestRuleBasedAnalyzer:
    def test_vague_instruction_detection(self, rule_analyzer):
        """Test vague instruction detection."""
        text = "analyze data"
        issues = rule_analyzer.analyze(text)
        
        assert len(issues) >= 1
        vague_issue = next((i for i in issues if i.type == IssueType.VAGUE), None)
        assert vague_issue is not None
        assert Severity.MEDIUM == vague_issue.severity
    
    def test_role_detection(self, rule_analyzer):
        """Test role definition detection."""
        text = "Analyze data"
        issues = rule_analyzer.analyze(text)
        
        role_issue = next((i for i in issues if i.type == IssueType.MISSING_ROLE), None)
        assert role_issue is not None
    
    def test_quality_score_calculation(self, rule_analyzer):
        """Test quality score calculation."""
        text = "You are an expert. Analyze data specifically with charts."
        issues = rule_analyzer.analyze(text)
        score = rule_analyzer.calculate_quality_score(text, issues)
        
        assert 70 <= score <= 95  # Should be good quality


class TestHybridAnalyzer:
    @patch('src.analyzers.hybrid_analyzer.LLMOptimizer')
    def test_hybrid_analysis(self, mock_llm, hybrid_analyzer):
        """Test hybrid analysis combines rule-based and LLM."""
        # Mock LLM to return no issues
        mock_llm_instance = AsyncMock()
        mock_llm_instance.analyze_with_llm.return_value = []
        mock_llm.return_value.__aenter__.return_value = mock_llm_instance
        
        text = "analyze data"
        issues = asyncio.run(hybrid_analyzer.analyze(text, use_llm=True))
        
        # Should still find rule-based issues
        assert len(issues) > 0
        assert any(issue.type == IssueType.VAGUE for issue in issues)
