import re
from typing import List, Tuple


class PatternMatcher:
    """Utility class for pattern matching in text."""
    
    # Vague instruction patterns
    VAGUE_PATTERNS = [
        r'\b(analyze|check|look at|review|examine)\b(?!\s+(specifically|by|with|for|the|this))',
        r'\b(give|provide|show)\s+(me\s+)?insights?\b(?!\s+on)',
        r'\b(do|make|create)\s+something\b',
        r'\btell me about\b',
    ]
    
    # Role definition patterns
    ROLE_PATTERNS = [
        r'\byou are\s+(a|an)\s+\w+',
        r'\bact as\s+(a|an)\s+\w+',
        r'\bas\s+(a|an)\s+\w+\s+(expert|specialist)',
    ]
    
    # Format specification patterns
    FORMAT_PATTERNS = [
        r'\bformat\s+(as|the|your)\b',
        r'\bstructure\s+(as|the|your)\b',
        r'\bbullet\s+points?\b',
        r'\bnumbered\s+list\b',
        r'\btable\b',
        r'\bjson\b',
        r'\bmarkdown\b',
    ]
    
    # Output specification patterns
    OUTPUT_PATTERNS = [
        r'\boutput\s+(format|structure)\b',
        r'\bprovide\s+(in|as)\s+\w+\s+format\b',
        r'\bresponse\s+format\b',
    ]
    
    @staticmethod
    def find_matches(text: str, patterns: List[str]) -> List[Tuple[int, int, str]]:
        """
        Find all matches for given patterns in text.
        
        Returns:
            List of tuples: (start_pos, end_pos, matched_text)
        """
        matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append((match.start(), match.end(), match.group()))
        return matches
    
    @staticmethod
    def contains_pattern(text: str, patterns: List[str]) -> bool:
        """Check if text contains any of the given patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def count_sentences(text: str) -> int:
        """Count number of sentences in text."""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count number of words in text."""
        return len(text.split())
    
    @staticmethod
    def has_specific_instructions(text: str) -> bool:
        """Check if text has specific instructions (numbers, bullet points, etc.)."""
        numbered_list = re.search(r'\d+[\.)]\s+\w+', text)
        bullet_list = re.search(r'[-•*]\s+\w+', text)
        return bool(numbered_list or bullet_list)
