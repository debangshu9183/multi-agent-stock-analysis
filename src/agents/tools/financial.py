#QUANTITATIVE ANALYSIS TOOLKT

#define the input schema for the tool
#what input the tool expects to receive from the agent
#Stock Analysisinput :defines the FundamentalAnalysisTool needs
#compare Stock input: defines the CompareStocksTool needs:ticker1 and ticker2
#ticker is the stock symbol, fofrom symtable import Class
from typing import Type,Dict,Any,Optional
from pydantic import BaseModel,Field #Field is used to add metadata to the fields in the model, such as description, example, etc.
from crewai.tools import BaseTool
import yfinance as yf

#define the input schema for the tool which is basically the rules for the input that the tool expects to receive from the agent
class StockAnalysisInput(BaseModel):
    '''The input schema for the Stock Analysis Tool. It defines the structure of the input that the tool expects to receive from the agent.
    Enforces that the input must contain a ticker field which is a string representing the stock symbol, for example AAPL for Apple Inc. The Field function is used to add metadata to the ticker field, such as description and example. This helps to ensure that the input is valid and provides clarity on what the input should look like.
    ... -- Ellipsis is used to indicate that there may be additional fields in the future, but for now, only the ticker field is required.
    '''
    ticker: str = Field(..., description="The stock symbol, for example AAPL for Apple Inc.", example="AAPL")   
#FIELDS are used to add metadata to the fields in the model, such as description, example, etc. This helps to ensure that the input is valid and provides clarity on what the input should look like.
class CompareStocksInput(BaseModel):
    '''The input schema for the Compare Stocks Tool. It defines the structure of the input that the tool expects to receive from the agent.
    Enforces that the input must contain two fields: ticker1 and ticker2, which are strings representing the stock symbols of the two stocks to be compared. For example, ticker1 could be AAPL for Apple Inc. and ticker2 could be MSFT for Microsoft Corporation. The Field function is used to add metadata to the ticker1 and ticker2 fields, such as description and example. This helps to ensure that the input is valid and provides clarity on what the input should look like.
    ... -- Ellipsis is used to indicate that there may be additional fields in the future, but for now, only the ticker1 and ticker2 fields are required.
    '''
    ticker1: str = Field(..., description="The stock symbol of the first stock to be compared, for example AAPL for Apple Inc.", example="AAPL")
    ticker2: str = Field(..., description="The stock symbol of the second stock to be compared, for example MSFT for Microsoft Corporation.", example="MSFT")
 
#building the tools
class FundamentalAnalysisTool(BaseTool):
    '''The Fundamental Analysis Tool is a tool that performs fundamental analysis on a given stock. It takes a StockAnalysisInput as input, which contains the ticker symbol of the stock to be analyzed. The tool uses the yfinance library to fetch the stock data and perform the analysis. The output of the tool is a dictionary containing the results of the fundamental analysis, such as the stock's current price, market capitalization, P/E ratio, etc.    '''
    name: str = "Fundamental Analysis Tool"
    description: str = ("Retrieves essential metrics for a given stock ticker. \
                        Useful for quantitative analysis, it returns JSON-formatted data \
                        including P/E ratio, Beta, Market Cap, EPS, 52-week High/Low.") #basically its the persona or the description of the tool that will be used by the agent to understand what the tool does and when to use it.
    args_schema  : Type[BaseModel] = StockAnalysisInput # its typehinting the args_schema attribute to be of type Type[BaseModel], which means that it expects a Pydantic model as the schema for the input arguments. In this case, the StockAnalysisInput model is used as the schema for the input arguments of the FundamentalAnalysisTool. This allows the tool to validate and parse the input arguments according to the defined schema, ensuring that the input is in the correct format and contains the required fields.
    
    def _run(self,ticker:str)-> str:
        """
        Executes the fundamental analysis for the given stock ticker.
        Args:
            ticker (str): The stock symbol to analyze, e.g., 'AAPL' for Apple Inc.
            Returns:
                str: A string containing the results of the fundamental analysis.
        """
        try:
            # initialize the yfinance Ticker object with the provided ticker symbol
            stock = yf.Ticker(ticker)
            info : Dict[str, Any] = stock.info # fetch the stock information using the info attribute of the Ticker object, which returns a dictionary containing various metrics and data about the stock
            metrics={
                "Ticker": ticker.upper(),
                "Current Price": info.get("currentPrice","N/A"),
                "Market Cap": info.get("marketCap","N/A"),
                "P/E Ratio(trailing)": info.get("trailingPE","N/A"),
                "P/E Ratio(forward)": info.get("forwardPE","N/A"),
                "PEG Ratio": info.get("pegRatio","N/A"),
                "EPS(Trailing)": info.get("trailingEps","N/A"),
                "52 Week High": info.get("fiftyTwoWeekHigh","N/A"),
                "52 Week Low": info.get("fiftyTwoWeekLow","N/A"),
                "Analyst Recommendation": info.get("recommendationKey","N/A"),
                
                "Beta": info.get("beta","N/A")
            }
            return str(metrics)
        except Exception as e:
            return f"Error fetching data for ticker {ticker}: {str(e)}"

class CompareStocksTool(BaseTool):
    '''
    calculates the relative performance of two stocks over the past  1-year. It takes a CompareStocksInput as input, which contains the ticker symbols of the two stocks to be compared. The tool uses the yfinance library to fetch the stock data and calculate the percentage change in price for each stock over the past year. The output of the tool is a dictionary containing the percentage change in price for each stock, as well as a comparison of their performance.
    '''
    name: str = "Compare Stocks Tool"
    description: str = (
                    "Compares the historical performance of two stocks over the past 365 days or 1 year, "
                    "returning the percentage gain or loss for each asset.")
    args_schema: Type[BaseModel] = CompareStocksInput
    def _run(self, ticker1: str, ticker2: str) -> str:
        """
        Executes the stock comparison for the given ticker symbols from historical data over the past year. 
        Formula: ((end_price - start_price) / start_price) * 100 to calculate the percentage change in price for each stock over the past year.
        

        Args:
            ticker1 (str): The stock symbol of the first stock to be compared, e.g., 'AAPL'.
            ticker2 (str): The stock symbol of the second stock to be compared, e.g., 'MSFT'.

        Returns:
            str: A string containing the results of the stock comparison,
                including percentage gain or loss for each stock.
        """
        try:
            tickers = f"{ticker1} {ticker2}"

            # Fetch historical stock data for the past 1 year
            data = yf.download(tickers, period="1y", progress=False)["Close"] # Use the "Close" price for performance comparison, which represents the stock's closing price at the end of each trading day. This is a common metric for evaluating stock performance over time.

            # Helper function to calculate percentage return
            def calculate_return(symbol: str) -> float:
                start_price = data[symbol].iloc[0]
                end_price = data[symbol].iloc[-1]
                return ((end_price - start_price) / start_price) * 100

            # Calculate performance
            performance_1 = calculate_return(ticker1)
            performance_2 = calculate_return(ticker2)

            # Create comparison summary
            comparison = (
                f"{ticker1.upper()} had a "
                f"{'gain' if performance_1 >= 0 else 'loss'} of {performance_1:.2f}%, "
                f"while {ticker2.upper()} had a "
                f"{'gain' if performance_2 >= 0 else 'loss'} of {performance_2:.2f}% "
                f"over the past year."
            )

            # Store results
            results = {
                ticker1.upper(): f"{performance_1:.2f}%",
                ticker2.upper(): f"{performance_2:.2f}%",
                "Comparison": comparison,
            }

            return str(results)

        except Exception as e:
            return f"Error fetching data for tickers {ticker1} and {ticker2}: {str(e)}"