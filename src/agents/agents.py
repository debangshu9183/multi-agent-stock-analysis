"""
    Agents defiitions and module.
    Defines the specific AI personas that will execute financial analysis workflow 
    and the tools they will use to perform their tasks.
    Each agent is designed with a specific role in mind, such as a financial analyst or a stock market researcher, and is equipped with tools that allow them to perform their tasks effectively.
    Each agent hjas a backstory and a set of tools that they can use to perform their tasks. The agents are designed to work together in a collaborative manner, with each agent contributing their expertise to the overall workflow.
    The agents are designed to be flexible and adaptable, allowing them to handle a wide range of financial analysis tasks and scenarios. The agents are also designed to be scalable, allowing them to handle large volumes of data and complex analysis tasks.
    The agents are designed to be user-friendly, with clear instructions and prompts to guide users through
    
    Agents: Quantitative Analyst Agent: focuses on finacial metrics
    Investment Strategist: Focus on qualitative news,sentiment synthesis
"""
 # backstory is the persona of the agent, it gives the agent a personality and a way of thinking, which can help it to perform its tasks more effectively. The backstory provides context for the agent's behavior and decision-making process, allowing it to approach problems in a way that is consistent with its role and expertise. By giving the agent a backstory, we can create a more engaging and realistic experience for users, as the agent will be able to provide insights and recommendations that are informed by its unique perspective and background.

from typing import Tuple
from crewai import Agent
from src.agents.tools.financial import FundamentalAnalysisTool,CompareStocksTool
from src.agents.tools.scraper import SentimentSearchTool


def create_agents() -> Tuple[Agent, Agent]:
    '''
    Creates and returns the Quantitative Analyst Agent and the Investment Strategist Agent.
    The Quantitative Analyst Agent is equipped with the Fundamental Analysis Tool, which allows it to perform fundamental analysis on stocks and provide insights based on financial metrics. The Investment Strategist Agent is equipped with the Sentiment Search Tool, which allows it to search the web for news, analyst opinions, and social media sentiment about stocks, providing insights into market trends and investor sentiment.
    Returns:
        Tuple[Agent, Agent]: A tuple containing the Quantitative Analyst Agent and the Investment Strategist Agent.
    '''
    # Quant Analyst Agent : use yfinance tool to perform fundamental analysis on stocks and provide insights based on financial metrics.
    quant_agent = Agent(
        role="Senior Quantitative Analyst Agent",
        goal="Analyze thre financial  health and historical performance of the stock and provide insights based on financial metrics.",
        backstory = (
        "You are a veteran financial analyst with over 2 decades of experience. "
        "You do not care about news headlines or rumours; you only trust data. "
        "You judge companies based on their balance sheets, P/E ratios, "
        "earnings growth (EPS), and volatility (Beta)."
        "Your reeports are concise and data-driven, providing clear insights into a stock's financial health and historical performance. "),
        verbose=True,
        memory=True,
        tools=[FundamentalAnalysisTool(),
                CompareStocksTool()],
        allow_delegation=False # we want the agent to do their own analysis and not delegate tasks to other agents, as this agent is focused on quantitative analysis and should rely on its own expertise and tools to perform its tasks effectively.
    )
    
    #strategist agent : use firecrawl  to perform web search for news, analyst opinions, and social media sentiment about stocks, providing insights into market trends and investor sentiment.
    # job of this agent is to explain why the numbers are the way they are, and to provide a narrative around the stock's performance, based on qualitative data and market sentiment.
    strategist_agent = Agent(
        role="Chief Investment Strategist",
        goal="Synthesize quantitative data with the market sentiment to form a reccomendation on whether to buy, sell, or hold a stock. Provide a narrative around the stock's performance, based on qualitative data and market sentiment.",
        backstory = (
        "You are a visionary investment strategist who looks beyond spreadsheets. "
        "You understand that stock prices are driven by human psychology, news, and leadership changes. "
        "You read the news to uncover the narrative behind a stock. "
        "You combine quantitative analysis with your news insights to deliver a final verdict: "
        "'BUY', 'SELL', or 'HOLD'."),
        verbose=True,
        memory=True,
        tools=[SentimentSearchTool()],
        allow_delegation=False # we want the agent to do their own analysis and not delegate tasks to other agents, as this agent is focused on qualitative analysis and should rely on its own expertise and tools to perform its tasks effectively.
    )
    
    return quant_agent, strategist_agent

        
 