"""
Task Definitions Module.

This module defines the specific work orders (Tasks) that the agents must execute.
It acts as the 'Prompt Engineering' layer of the application.

Key Features:
    - Context Injection: The Strategist's task explicitly waits for and receives 
      the output from the Quant's task to ensure data-driven reasoning.
    - Output Formatting: Enforces Markdown structure for the final report.
"""

from crewai import Task, Agent


def create_tasks(quant_agent: Agent, strategist_agent: Agent, ticker: str) -> list[Task]:
    """
    Creates the sequence of tasks for the financial analysis workflow.

    Args:
        quant_agent: The agent responsible for financial metrics.
        strategist_agent: The agent responsible for news and synthesis.
        ticker: The stock ticker symbol to analyze e.g. 'NVDA'.

    Returns:
        list[Task]: A list of Task objects in the order of execution.
    """

    # Task 1: Quantitative Data Collection
    quant_task = Task(
        description=(
            f"Analyze the financial health of ticker '{ticker}'. "
            f"1. Use the FundamentalAnalysisTool to fetch P/E, EPS, Beta, and Market Cap. "
            f"2. Use the CompareStocksTool to compare '{ticker}' against 'SPY' (S&P 500) "
            f"to see its relative performance over the last year. "
            f"3. Identify any major numerical red flags (e.g., negative EPS, extremely high P/E). "
            f"Output a concise summary of the hard numbers."
        ),
        expected_output="A structured summary of financial metrics and 1-year performance comparison against SPY, highlighting any major red flags.",
        agent=quant_agent,
    )

    # Task 2: Strategic Synthesis and Recommendation
    recommendation_task = Task(
        description=(
            f"Formulate a final investment recommendation for '{ticker}'. "
            f"1. Read the financial metrics provided by the Quantitative Analyst. "
            f"2. Use the SentimentSearchTool to find the top 3 recent news articles "
            f"or analyst ratings for '{ticker}'. Look for leadership changes, "
            f"regulatory lawsuits, or product launches. "
            f"3. SYNTHESIZE the numbers (Quant) with the narrative (News). "
            f"- If numbers are good but news is bad (e.g., lawsuit), be cautious. "
            f"- If numbers are bad but news is hype, be skeptical. "
            f"4. Provide a final verdict: 'BUY', 'SELL', or 'HOLD', with clear reasoning."
        ),
        expected_output=f"""A comprehensive Markdown investment report with this exact structure:

## Investment Recommendation for {ticker}

### Verdict: [BUY/SELL/HOLD]

### Key Financial Metrics:
- **Current Price:** $X.XX
- **Market Cap:** $X Trillion/Billion
- **P/E Ratio (Trailing):** X.XX
- **Forward P/E:** X.XX
- **Beta (Volatility):** X.XX
- **EPS (Trailing):** $X.XX
- **52 Week High/Low:** $X.XX/$X.XX
- **1-Year Performance:** +X.XX% vs S&P 500 X.XX%
- **Analyst Recommendation:** Buy/Hold/Sell

### Recent Relevant News Highlights:
1. **[News Category]:**
   - **[News Title]:** Brief description of the news item.

### Synthesis:
A paragraph synthesizing the quantitative data with market sentiment.

### Final Recommendation:
A clear BUY, SELL, or HOLD with concise rationale.""",
        agent=strategist_agent,
        context=[quant_task], #IT MUST WAIT FOR THE QUANT TASK TO COMPLETE AND THEN READ ITS OUTPUT AS CONTEXT
        output_file=f"investment_report_{ticker}.md",
    )

    return [quant_task, recommendation_task]