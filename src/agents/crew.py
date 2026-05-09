"""
Crew orchestration module.
Instantiates agents and tasks, configures the CrewAI execution process,
and handles the kickoff for the financial analysis workflow.
"""

from crewai import Crew, Process
from src.agents.agents import create_agents
from src.agents.tasks import create_tasks

def run_financial_crew(ticker: str) -> str:
    """
    Initialize and execute the financial analysis crew for a specific stock.
    Args:
        ticker: The stock ticker symbol to analyze, e.g. 'AAPL'.
    Returns:
        Final investment recommendation (BUY/SELL/HOLD) with narrative.
    """
    # Create agents
    quant_agent, strategist_agent = create_agents()

    # Assign tasks
    tasks = create_tasks(quant_agent, strategist_agent, ticker)

    # Assemble crew
    financial_crew = Crew(
        agents=[quant_agent, strategist_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=True,    # ← enables Long Term, Short Term and Entity Memory
    )

    print(f"Starting financial analysis crew for ticker '{ticker}'...")
    result = financial_crew.kickoff()

    return str(result)