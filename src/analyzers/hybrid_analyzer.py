from typing import List, Set, Tuple
from .rule_based import RuleBasedAnalyzer
from ..optimizers.llm_optimizer import LLMOptimizer
from ..models import PromptIssue
from ..config.logger import logger


class HybridAnalyzer:
    """Combines rule-based and LLM analysis for comprehensive prompt evaluation."""
    
    def __init__(self):
        """Initialize both analyzers."""
        self.rule_analyzer = RuleBasedAnalyzer()
        self.llm_optimizer = LLMOptimizer()
        logger.info("✅ Hybrid Analyzer initialized")
    
    async def analyze(self, text: str, use_llm: bool = False) -> List[PromptIssue]:
        """
        Perform hybrid analysis combining rule-based and optional LLM analysis.
        
        Args:
            text: Prompt text to analyze
            use_llm: Whether to include LLM-based deep analysis
            
        Returns:
            List of deduplicated PromptIssue objects
        """
        # Always perform fast rule-based analysis
        rule_issues = self.rule_analyzer.analyze(text)
        logger.info(f"Rule-based analysis found {len(rule_issues)} issues")
        
        if not use_llm:
            return rule_issues
        
        # Add LLM analysis for deeper insights
        llm_issues = await self.llm_optimizer.analyze_with_llm(text)
        logger.info(f"LLM analysis found {len(llm_issues)} issues")
        
        # Merge and deduplicate
        all_issues = rule_issues + llm_issues
        deduplicated = self._deduplicate_issues(all_issues)
        
        logger.info(f"Total unique issues after deduplication: {len(deduplicated)}")
        return deduplicated
    
    def _deduplicate_issues(self, issues: List[PromptIssue]) -> List[PromptIssue]:
        """
        Remove duplicate or overlapping issues.
        
        Deduplication strategy:
        1. Group by position range (start, end)
        2. Keep the issue with higher severity
        3. Prefer LLM-generated issues for same severity
        
        Args:
            issues: List of potentially duplicate issues
            
        Returns:
            Deduplicated list of issues
        """
        if not issues:
            return []
        
        # Group by approximate position
        position_groups: dict[Tuple[int, int], List[PromptIssue]] = {}
        
        for issue in issues:
            # Create position key with some tolerance (±5 chars)
            key = (issue.start // 5 * 5, issue.end // 5 * 5)
            
            if key not in position_groups:
                position_groups[key] = []
            position_groups[key].append(issue)
        
        # Select best issue from each group
        deduplicated = []
        severity_order = {"critical": 3, "medium": 2, "low": 1}
        
        for group in position_groups.values():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Sort by severity (descending) and prefer LLM issues
                best_issue = max(
                    group,
                    key=lambda x: (
                        severity_order.get(x.severity.value, 0),
                        1 if x.id.startswith("llm-") else 0
                    )
                )
                deduplicated.append(best_issue)
        
        # Sort by start position
        deduplicated.sort(key=lambda x: x.start)
        
        return deduplicated
    
    def calculate_quality_score(self, text: str, issues: List[PromptIssue]) -> int:
        """
        Calculate quality score using rule-based analyzer.
        
        Args:
            text: Original prompt text
            issues: List of issues found
            
        Returns:
            Quality score (0-100)
        """
        return self.rule_analyzer.calculate_quality_score(text, issues)
