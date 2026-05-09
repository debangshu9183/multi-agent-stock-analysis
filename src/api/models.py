'''
Acts as a contract for your api 
It defines the expected input and output for the API endpoints, ensuring that the data being sent and received adheres to a specific structure. This helps to maintain consistency and reliability in the API's behavior, making it easier for clients to interact with the API and for developers to manage and update the API over time.
'''
from pydantic import BaseModel, Field

class StockAnalysisRequest(BaseModel):
    '''The StockAnalysisRequest model defines the structure of the request body that the API endpoint expects to receive when a client makes a request to analyze a stock. It contains a single field, ticker, which is a string representing the stock symbol that the client wants to analyze. The Field function is used to add metadata to the ticker field, such as description and example, which helps to ensure that the input is valid and provides clarity on what the input should look like. This model serves as a contract for the API endpoint, ensuring that any requests made to the endpoint adhere to this structure.
    '''
    ticker: str = Field(..., description="The stock symbol to analyze, e.g., 'AAPL' for Apple Inc.", example="AAPL")

        
class StockAnalysisResponse(BaseModel):
    status: str
    ticker: str
    analysis_result: str
    report_url: str
    message: str