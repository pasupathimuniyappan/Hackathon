import json
import uuid
from typing import List, Dict, Any
from openai import AsyncOpenAI
from ..models import PromptIssue, IssueType, Severity, Impact
from ..config.settings import settings
from ..config.logger import logger
from ..utils.model_client import get_client


class LLMOptimizer:
    """LLM-powered prompt optimizer using OpenAI GPT models."""

    def __init__(self):
        """Initialize OpenAI client."""
        # self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.client = get_client()
        self.model = settings.model_engine_id
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

        logger.info(f"✅ LLM Optimizer initialized with model: {self.model}")

    async def analyze_with_llm(self, text: str) -> List[PromptIssue]:
        """
        Use GPT to analyze prompt quality and identify issues.

        Args:
            text: Prompt text to analyze

        Returns:
            List of PromptIssue objects
        """
        system_prompt = """You are an expert prompt engineer specializing in AI prompt optimization.

Analyze the given prompt and identify specific issues that could be improved.

Return a JSON object with this exact structure:
{
  "issues": [
    {
      "type": "vague" | "missing_context" | "inefficient" | "ambiguous" | "missing_role" | "missing_format",
      "severity": "critical" | "medium" | "low",
      "message": "Brief explanation of the issue (max 100 chars)",
      "suggestion": "Specific text to replace or add",
      "start": character_position_start,
      "end": character_position_end,
      "impact": "high" | "medium" | "low"
    }
  ]
}

Focus on:
1. Vague or unclear instructions
2. Missing role definitions or context
3. Unclear output format requirements
4. Ambiguous language or references
5. Inefficient token usage
6. Missing specificity in requirements

Be specific and actionable in your suggestions."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this prompt:\n\n{text}"},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"LLM response: {content}")

            result = json.loads(content)
            issues_data = result.get("issues", [])

            # Convert to PromptIssue objects
            issues = []
            for issue_data in issues_data:
                try:
                    issues.append(
                        PromptIssue(
                            id=f"llm-{uuid.uuid4().hex[:8]}",
                            start=issue_data.get("start", 0),
                            end=issue_data.get("end", len(text)),
                            type=IssueType(issue_data["type"]),
                            severity=Severity(issue_data["severity"]),
                            message=issue_data["message"],
                            suggestion=issue_data["suggestion"],
                            impact=Impact(issue_data.get("impact", "medium")),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse issue: {e}")
                    continue

            logger.info(f"✅ LLM found {len(issues)} issues")
            return issues

        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            return []

    async def optimize_prompt(
        self, text: str, focus: str = "all", level: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Generate an optimized version of the prompt.

        Args:
            text: Original prompt text
            focus: Focus area (clarity, efficiency, specificity, all)
            level: Optimization level (basic, balanced, advanced)

        Returns:
            Dictionary with optimization results
        """
        focus_instructions = {
            "clarity": "Focus on making the prompt clearer and more understandable.",
            "efficiency": "Focus on reducing token usage while maintaining effectiveness.",
            "specificity": "Focus on adding specific details and constraints.",
            "all": "Apply comprehensive improvements across all areas.",
        }

        level_instructions = {
            "basic": "Make minimal, essential improvements only.",
            "balanced": "Balance between improvements and maintaining original intent.",
            "advanced": "Apply comprehensive optimizations and restructuring.",
        }

        system_prompt = f"""You are an expert prompt engineer. Your task is to optimize prompts for better AI responses.

{focus_instructions.get(focus, focus_instructions["all"])}
{level_instructions.get(level, level_instructions["balanced"])}

Return a JSON object with this exact structure:
{{
  "optimized_prompt": "The fully optimized prompt text",
  "improvements": [
    {{
      "change": "Description of what was changed/added",
      "impact": "high" | "medium" | "low"
    }}
  ]
}}

Optimization guidelines:
1. Add clear role definition if missing
2. Structure requirements with numbered points
3. Specify expected output format
4. Add relevant constraints and context
5. Remove ambiguity and vague language
6. Optimize token usage
7. Ensure actionable and specific instructions

Maintain the original intent while maximizing clarity and effectiveness."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original prompt:\n\n{text}"},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            logger.info("✅ Prompt optimized successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            return {"optimized_prompt": text, "improvements": []}
