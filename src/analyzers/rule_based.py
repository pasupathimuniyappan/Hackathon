import uuid
import spacy
from typing import List
from ..models import PromptIssue, IssueType, Severity, Impact
from ..utils.patterns import PatternMatcher
from ..config.logger import logger


class RuleBasedAnalyzer:
    """Rule-based prompt analyzer using pattern matching and NLP."""
    
    def __init__(self):
        """Initialize analyzer with spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load spaCy model: {e}")
            raise
        
        self.pattern_matcher = PatternMatcher()
    
    def analyze(self, text: str) -> List[PromptIssue]:
        """
        Analyze prompt and return list of issues.
        
        Args:
            text: Prompt text to analyze
            
        Returns:
            List of PromptIssue objects
        """
        issues = []
        
        # Run all analysis checks
        issues.extend(self._check_vague_instructions(text))
        issues.extend(self._check_role_definition(text))
        issues.extend(self._check_output_format(text))
        issues.extend(self._check_length(text))
        issues.extend(self._check_specificity(text))
        issues.extend(self._check_ambiguous_pronouns(text))
        
        logger.info(f"Found {len(issues)} issues in prompt")
        return issues
    
    def _check_vague_instructions(self, text: str) -> List[PromptIssue]:
        """Check for vague instructions."""
        issues = []
        matches = self.pattern_matcher.find_matches(
            text,
            self.pattern_matcher.VAGUE_PATTERNS
        )
        
        for start, end, matched_text in matches:
            # Check if there's any specificity after the vague word
            context_after = text[end:end+50].lower()
            has_specificity = any(word in context_after for word in [
                'specifically', 'focusing', 'particularly', 'especially',
                'by analyzing', 'with emphasis'
            ])
            
            if not has_specificity:
                issues.append(PromptIssue(
                    id=f"issue-{uuid.uuid4().hex[:8]}",
                    start=start,
                    end=end,
                    type=IssueType.VAGUE,
                    severity=Severity.MEDIUM,
                    message=f"The instruction '{matched_text}' is vague. Add specific details about what to {matched_text.lower()}.",
                    suggestion=f"{matched_text} specifically focusing on",
                    impact=Impact.HIGH
                ))
        
        return issues
    
    def _check_role_definition(self, text: str) -> List[PromptIssue]:
        """Check if prompt has a role definition."""
        issues = []
        
        has_role = self.pattern_matcher.contains_pattern(
            text,
            self.pattern_matcher.ROLE_PATTERNS
        )
        
        if not has_role:
            issues.append(PromptIssue(
                id=f"issue-{uuid.uuid4().hex[:8]}",
                start=0,
                end=0,
                type=IssueType.MISSING_ROLE,
                severity=Severity.MEDIUM,
                message="Missing role definition. Adding a role helps the AI understand the expected expertise level.",
                suggestion="You are an expert analyst. " + text,
                impact=Impact.MEDIUM
            ))
        
        return issues
    
    def _check_output_format(self, text: str) -> List[PromptIssue]:
        """Check if output format is specified."""
        issues = []
        
        has_format = self.pattern_matcher.contains_pattern(
            text,
            self.pattern_matcher.FORMAT_PATTERNS + self.pattern_matcher.OUTPUT_PATTERNS
        )
        
        if not has_format and len(text.split()) > 10:
            issues.append(PromptIssue(
                id=f"issue-{uuid.uuid4().hex[:8]}",
                start=len(text),
                end=len(text),
                type=IssueType.MISSING_FORMAT,
                severity=Severity.LOW,
                message="No output format specified. Defining the format helps ensure consistent results.",
                suggestion=text + " Format the response as bullet points.",
                impact=Impact.MEDIUM
            ))
        
        return issues
    
    def _check_length(self, text: str) -> List[PromptIssue]:
        """Check if prompt length is appropriate."""
        issues = []
        word_count = self.pattern_matcher.count_words(text)
        
        if word_count < 5:
            issues.append(PromptIssue(
                id=f"issue-{uuid.uuid4().hex[:8]}",
                start=0,
                end=len(text),
                type=IssueType.TOO_SHORT,
                severity=Severity.CRITICAL,
                message=f"Prompt is too short ({word_count} words). Add more specific instructions and context.",
                suggestion=text + " Please provide detailed analysis including key metrics, trends, and actionable insights.",
                impact=Impact.HIGH
            ))
        elif word_count > 500:
            issues.append(PromptIssue(
                id=f"issue-{uuid.uuid4().hex[:8]}",
                start=0,
                end=len(text),
                type=IssueType.TOO_LONG,
                severity=Severity.LOW,
                message=f"Prompt is very long ({word_count} words). Consider breaking it into smaller, focused prompts.",
                suggestion="Consider splitting this into multiple focused prompts for better results.",
                impact=Impact.LOW
            ))
        
        return issues
    
    def _check_specificity(self, text: str) -> List[PromptIssue]:
        """Check if prompt has specific instructions."""
        issues = []
        
        has_structure = self.pattern_matcher.has_specific_instructions(text)
        word_count = self.pattern_matcher.count_words(text)
        
        if word_count > 15 and not has_structure:
            issues.append(PromptIssue(
                id=f"issue-{uuid.uuid4().hex[:8]}",
                start=0,
                end=len(text),
                type=IssueType.INEFFICIENT,
                severity=Severity.LOW,
                message="Consider structuring your requirements with numbered points for clarity.",
                suggestion="Structure your prompt with numbered requirements:\n1. First requirement\n2. Second requirement\n3. Third requirement",
                impact=Impact.MEDIUM
            ))
        
        return issues
    
    def _check_ambiguous_pronouns(self, text: str) -> List[PromptIssue]:
        """Check for ambiguous pronouns."""
        issues = []
        
        try:
            doc = self.nlp(text)
            
            # Find pronouns without clear antecedents
            ambiguous_pronouns = ['it', 'this', 'that', 'they', 'them']
            
            for token in doc:
                if token.text.lower() in ambiguous_pronouns and token.pos_ == "PRON":
                    # Simple heuristic: if pronoun is at start or has no clear noun before it
                    if token.i < 2:
                        issues.append(PromptIssue(
                            id=f"issue-{uuid.uuid4().hex[:8]}",
                            start=token.idx,
                            end=token.idx + len(token.text),
                            type=IssueType.AMBIGUOUS,
                            severity=Severity.LOW,
                            message=f"The pronoun '{token.text}' may be ambiguous. Consider being more explicit.",
                            suggestion="[specify what you're referring to]",
                            impact=Impact.LOW
                        ))
        except Exception as e:
            logger.warning(f"Error in pronoun analysis: {e}")
        
        return issues
    
    def calculate_quality_score(self, text: str, issues: List[PromptIssue]) -> int:
        """
        Calculate overall quality score (0-100).
        
        Args:
            text: Original prompt text
            issues: List of issues found
            
        Returns:
            Quality score from 0 to 100
        """
        base_score = 100
        
        # Deduct points based on severity
        for issue in issues:
            if issue.severity == Severity.CRITICAL:
                base_score -= 20
            elif issue.severity == Severity.MEDIUM:
                base_score -= 10
            else:
                base_score -= 5
        
        # Bonus for good practices
        word_count = self.pattern_matcher.count_words(text)
        if word_count >= 20:
            base_score = min(100, base_score + 5)
        
        if self.pattern_matcher.has_specific_instructions(text):
            base_score = min(100, base_score + 5)
        
        if self.pattern_matcher.contains_pattern(text, self.pattern_matcher.ROLE_PATTERNS):
            base_score = min(100, base_score + 5)
        
        return max(0, min(100, base_score))
