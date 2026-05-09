"""
Building the API endpoint
This is the 'Controller'. It receives the request, calls the AI agents, and returns a JSON result.
"""

from fastapi import APIRouter, HTTPException
from src.api.models import StockAnalysisRequest, StockAnalysisResponse
from src.agents.crew import run_financial_crew
from src.shared.storage import StorageService  
from src.shared.database import DatabaseService  
import logging

logger = logging.getLogger(__name__)

# Router organises all financial-analysis endpoints.
# It handles incoming requests, invokes the AI agents, uploads reports to
# Azure Blob Storage, and logs results to Azure PostgreSQL.
router = APIRouter()


@router.post("/analyze_stock", response_model=StockAnalysisResponse) #ensure api wil response with a json response 
async def analyze_stock(request: StockAnalysisRequest) -> StockAnalysisResponse: #request is the input model that contains the ticker symbol.
    """
    Trigger a financial analysis for a given ticker symbol (e.g. MSFT).

    Steps:
        1. Run the CrewAI financial crew to produce an analysis report.
        2. Upload the report to Azure Blob Storage.
        3. Persist the result to Azure PostgreSQL.

    Returns:
        StockAnalysisResponse with the ticker, analysis text, blob URL, and a status message.

    Raises:
        HTTPException 400: if the ticker symbol is empty.
        HTTPException 500: if any step in the pipeline fails.
    """
    ticker = request.ticker.strip().upper()

    # ── Basic input guard ────────────────────────────────────────────────────
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol must not be empty.")

    logger.info("Received analysis request for ticker '%s'", ticker)

    try:
        # Run CrewAI agents
        analysis_result = run_financial_crew(ticker)
        analysis_result_str = str(analysis_result)

        # Upload report to Azure Blob Storage
        filename = f"{ticker}_analysis_report.md"
        storage = StorageService()                          
        blob_url = storage.upload_report(analysis_result_str, filename)
        logger.info("Report uploaded for '%s': %s", ticker, blob_url)

        # Persist to Azure PostgreSQL 
        db_service = DatabaseService()
        db_service.save_analysis_result(ticker, analysis_result_str)
        logger.info("Analysis result saved to database for '%s'", ticker)

        # Return structured response
        return StockAnalysisResponse(
            status="success",
            ticker=ticker,
            analysis_result=analysis_result_str,
            report_url=blob_url,                           
            message=f"Financial analysis for '{ticker}' completed successfully.",
        )

    except HTTPException:
        raise  # re-raise 400s without wrapping them in a 500

    except Exception as e:
        logger.exception("Unexpected error while analysing ticker '%s'", ticker)
        raise HTTPException(
            status_code=500,
            detail=f"Error analysing stock '{ticker}': {str(e)}",
        )
        
