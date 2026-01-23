"""Test prompt data for various quality levels."""

TEST_PROMPTS = {
    "poor": [
        "analyze data",
        "check this",
        "give insights",
        "do something",
    ],
    "medium": [
        "Analyze the sales data and give me insights about revenue trends",
        "Write code to sort an array",
        "Summarize this report",
        "Compare these two datasets",
    ],
    "good": [
        "You are a data analyst. Analyze the sales dataset focusing on: 1) Revenue trends over the last quarter 2) Top performing products 3) Regional performance differences. Format as bullet points.",
        "You are a Python expert. Write an efficient quicksort algorithm with comments and edge case handling. Include time complexity analysis.",
    ],
    "excellent": [
        """You are a senior data scientist with 10+ years experience in sales analytics.

Analyze the Q4 2025 sales performance dataset with these objectives:

1. Revenue Analysis: Calculate MoM and YoY growth rates, identify top 3 trends
2. Product Performance: Rank products by revenue contribution (top 10), units sold, margin
3. Regional Insights: Compare all regions with KPIs (revenue, growth, market share)
4. Customer Segmentation: Identify high-value customers and churn patterns
5. Predictive Insights: Highlight potential Q1 2026 risks/opportunities

Output format:
- Executive Summary (3 bullet points)
- Detailed Analysis (tables + insights)
- Visual Recommendations (chart types)
- Actionable Recommendations (prioritized)

Include all relevant KPIs with percentages."""
    ]
}
