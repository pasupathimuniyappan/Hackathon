from fastmcp import FastMCP
from typing import Dict, Any
import asyncio

from .config.settings import settings
from .config.logger import logger
from .analyzers import HybridAnalyzer
from .utils.token_counter import token_counter


# Initialize MCP server
mcp = FastMCP(
    name="PromptAssist",
    version="1.0.0"
)

# Initialize analyzer
analyzer = HybridAnalyzer()


@mcp.tool()
async def analyze_prompt(text: str, use_llm: bool = False) -> Dict[str, Any]:
    """
    Analyzes a prompt and returns improvement suggestions.
    
    Args:
        text: The prompt text to analyze
        use_llm: Whether to use LLM for deep analysis (slower but more accurate)
        
    Returns:
        Analysis results including issues, quality score, and token count
    """
    logger.info(f"[MCP] Analyzing prompt (LLM: {use_llm})")
    
    try:
        # Perform analysis
        issues = await analyzer.analyze(text, use_llm=use_llm)
        quality_score = analyzer.calculate_quality_score(text, issues)
        token_count = token_counter.count_tokens(text)
        
        result = {
            "issues": [issue.model_dump() for issue in issues],
            "quality_score": quality_score,
            "token_count": token_count,
            "estimated_improvement": max(0, 100 - quality_score)
        }
        
        logger.info(f"[MCP] Analysis complete: {len(issues)} issues found")
        return result
        
    except Exception as e:
        logger.error(f"[MCP] Analysis failed: {e}")
        return {
            "error": str(e),
            "issues": [],
            "quality_score": 0,
            "token_count": 0
        }


@mcp.tool()
async def optimize_prompt(text: str, focus: str = "all", level: str = "balanced") -> Dict[str, Any]:
    """
    Optimizes a prompt using AI.
    
    Args:
        text: The original prompt text
        focus: Focus area - "clarity", "efficiency", "specificity", or "all"
        level: Optimization level - "basic", "balanced", or "advanced"
        
    Returns:
        Optimized prompt with improvements and metrics
    """
    logger.info(f"[MCP] Optimizing prompt (focus={focus}, level={level})")
    
    try:
        # Get before metrics
        before_issues = await analyzer.analyze(text, use_llm=False)
        before_score = analyzer.calculate_quality_score(text, before_issues)
        before_tokens = token_counter.count_tokens(text)
        
        # Optimize
        optimization = await analyzer.llm_optimizer.optimize_prompt(text, focus, level)
        
        # Get after metrics
        optimized_text = optimization.get("optimized_prompt", text)
        after_issues = await analyzer.analyze(optimized_text, use_llm=False)
        after_score = analyzer.calculate_quality_score(optimized_text, after_issues)
        after_tokens = token_counter.count_tokens(optimized_text)
        
        result = {
            "optimized_prompt": optimized_text,
            "improvements": optimization.get("improvements", []),
            "token_savings": before_tokens - after_tokens,
            "quality_improvement": after_score - before_score,
            "before_score": before_score,
            "after_score": after_score
        }
        
        logger.info(f"[MCP] Optimization complete: {before_score}→{after_score}")
        return result
        
    except Exception as e:
        logger.error(f"[MCP] Optimization failed: {e}")
        return {
            "error": str(e),
            "optimized_prompt": text,
            "improvements": [],
            "token_savings": 0,
            "quality_improvement": 0,
            "before_score": 0,
            "after_score": 0
        }


@mcp.tool()
async def get_quality_metrics(text: str) -> Dict[str, Any]:
    """
    Returns detailed quality metrics for a prompt.
    
    Args:
        text: The prompt text to analyze
        
    Returns:
        Detailed metrics including quality breakdown and statistics
    """
    logger.info("[MCP] Getting quality metrics")
    
    try:
        issues = await analyzer.analyze(text, use_llm=False)
        quality_score = analyzer.calculate_quality_score(text, issues)
        token_count = token_counter.count_tokens(text)
        
        # Count by severity
        severity_breakdown = {
            "critical": len([i for i in issues if i.severity.value == "critical"]),
            "medium": len([i for i in issues if i.severity.value == "medium"]),
            "low": len([i for i in issues if i.severity.value == "low"]),
        }
        
        # Count by type
        type_breakdown = {}
        for issue in issues:
            issue_type = issue.type.value
            type_breakdown[issue_type] = type_breakdown.get(issue_type, 0) + 1
        
        return {
            "overall_quality": quality_score,
            "word_count": len(text.split()),
            "character_count": len(text),
            "token_count": token_count,
            "estimated_cost": token_counter.estimate_cost(token_count),
            "issue_count": len(issues),
            "severity_breakdown": severity_breakdown,
            "type_breakdown": type_breakdown
        }
        
    except Exception as e:
        logger.error(f"[MCP] Metrics failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("🚀 Starting MCP server...")
    mcp.run()
