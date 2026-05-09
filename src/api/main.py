'''
Servers entrypoint for the FastAPI application. This file initializes the FastAPI app, includes API routes, and configures middleware if needed.
This file wires everything together and serves as the main entry point for the API server. It imports the necessary modules, creates an instance of FastAPI, includes the API routes defined in routes.py, and can also be used to add any global middleware or exception handlers if needed.
'''
#Instance of the Application
from fastapi import FastAPI
from src.api.routes import router as api_router

app= FastAPI(title="CrewAI Financial Analysis API",
             description="API for analyzing stock market data using CrewAI agents. Send a POST request to /analyze_stock with a ticker symbol to receive a comprehensive financial analysis report.",
             version="1.0.0")   

app.include_router(api_router, prefix="/api/v1") # this will include all the routes defined in routes.py under the /api prefix, so the endpoint to analyze a stock will be /api/analyze_stock. This helps to organize the API endpoints and makes it clear that they belong to the same API group.
#API versioning is important for maintaining backward compatibility as the API evolves. By using a version prefix (e.g., /api/v1), you can introduce new versions of the API in the future (e.g., /api/v2) without breaking existing clients that rely on the older version. This allows for smoother transitions and better management of changes to the API over time.
@app.get("/health")
async def health_check():
    '''A simple health check endpoint to verify that the API is running. It returns a JSON response with a status message indicating that the API is healthy. This can be used for monitoring and to ensure that the API is up and running before making requests to the other endpoints.'''
    return {"status": "API is healthy and running."}

