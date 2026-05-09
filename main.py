"""
Main entry point for CrewAI Financial Analysis API.
Complete backend with SSE streaming - properly parses CrewAI output.
"""

import logging
import asyncio
import queue
import threading
import json
import sys
import re
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from src.agents.crew import run_financial_crew
from src.shared.storage import StorageService
from src.shared.database import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalysisRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", examples=["AAPL"])

class StockAnalysisResponse(BaseModel):
    status: str
    ticker: str
    analysis_result: str
    report_url: str
    message: str

app = FastAPI(
    title="📈 CrewAI Financial Analysis API",
    description="AI-Powered Stock Analysis using CrewAI agents.",
    version="1.0.0",
    contact={"name": "Debangshu", "email": "debangshu.data@gmail.com"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/v1", tags=["Financial Analysis"])

def strip_ansi(text: str) -> str:
    text = re.sub(r'\x1b\[[0-9;]*[mGKHFJA-Za-z]', '', text)
    text = re.sub(r'\[\d+m', '', text)
    text = re.sub(r'[╭╮╰╯│✨]+', '', text)
    text = re.sub(r'─{2,}', '', text)
    text = text.strip()
    return text

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/", tags=["General"])
async def root():
    return {"message": "CrewAI Financial Analysis API 📈", "docs": "http://127.0.0.1:8000/docs"}

@app.get("/health", tags=["General"])
async def health_check():
    return {"status": "healthy ✅"}

@router.post("/analyze_stock", response_model=StockAnalysisResponse)
async def analyze_stock(request: StockAnalysisRequest) -> StockAnalysisResponse:
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol must not be empty.")
    try:
        analysis_result = run_financial_crew(ticker)
        analysis_result_str = str(analysis_result)
        storage = StorageService()
        blob_url = storage.upload_report(analysis_result_str, f"{ticker}_analysis_report.md")
        db_service = DatabaseService()
        db_service.save_analysis_result(ticker, analysis_result_str)
        return StockAnalysisResponse(
            status="success", ticker=ticker,
            analysis_result=analysis_result_str, report_url=blob_url,
            message=f"Analysis for '{ticker}' completed.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze_stock/stream/{ticker}")
async def stream_analysis(ticker: str, request: Request):
    ticker = ticker.upper()
    q = queue.Queue()

    class QueueWriter:
        def __init__(self):
            self.buffer = ""
            self.seen_lines = set()   # dedup
            # state machine
            self.in_task_body      = False
            self.task_desc_lines   = []
            self.in_agent_body     = False
            self.current_agent     = ""
            self.in_tool_body      = False
            self.current_tool_name = ""
            self.current_tool_args = ""
            self.in_output         = False
            self.output_lines      = []
            self.in_final          = False
            self.final_lines       = []
            self.sent_crew_start   = False
            self.sent_crew_done    = False
            self.last_task_id      = 0
            self.last_agent        = ""

        def write(self, text):
            if not text:
                return
            self.buffer += text
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                c = strip_ansi(line)
                if c:
                    self.process(c)

        def emit(self, obj):
            q.put(obj)

        def process(self, c):
            # ── skip noisy lines ─────────────────────────────────
            noise = ['Update Available','Yanked Version','Tracing Status',
                     'crewai traces','CREWAI_TRACING','uv sync','pip install',
                     'WARNING:','INFO:root:OpenAI','INFO:httpx',
                     'INFO:azure','Request URL','Response status','Response headers',
                     'Content-Length','Content-MD5','x-ms-','Authorization',
                     'User-Agent','Accept','ETag','Server:','Date:',
                     'Last-Modified','No body','A body is']
            if any(n in c for n in noise):
                return

            # ── CREW EVENTS ──────────────────────────────────────
            if 'Crew Execution Started' in c and not self.sent_crew_start:
                self.sent_crew_start = True
                self.emit({"type":"crew_start","message":"Crew Execution Started"})
                return

            if 'Crew Execution Completed' in c and not self.sent_crew_done:
                self.sent_crew_done = True
                self.emit({"type":"crew_done","message":"Crew Execution Completed"})
                return

            # ── TASK STARTED ─────────────────────────────────────
            if 'Task Started' in c:
                self.last_task_id += 1
                self.in_task_body = True
                self.task_desc_lines = []
                self.emit({"type":"task_start","id":self.last_task_id,"message":"Task Started"})
                return

            if self.in_task_body:
                if c.startswith('Name:'):
                    name = c.replace('Name:','').strip()
                    self.emit({"type":"task_name","id":self.last_task_id,"message":name})
                    return
                if c.startswith('ID:') or c.startswith('Agent:'):
                    self.in_task_body = False
                    # fall through to agent processing

            # ── TASK COMPLETED ────────────────────────────────────
            if 'Task Completed' in c or 'Task Completion' in c:
                # flush final answer if any
                if self.final_lines:
                    self.emit({"type":"final_answer","message":" ".join(self.final_lines)[:800]})
                    self.final_lines = []
                    self.in_final = False
                self.emit({"type":"task_done","message":"Task Completed"})
                return

            if 'Task Failed' in c:
                self.emit({"type":"task_fail","message":c})
                return

            # ── AGENT STARTED ─────────────────────────────────────
            if 'Agent Started' in c or 'Agent Execution Started' in c:
                return  # skip, we use the Agent: line below

            if c.startswith('Agent:') and 'Agent Started' not in c and 'Agent Final' not in c:
                agent = c.replace('Agent:','').strip()
                # always emit agent name even if duplicate line — important for UI
                self.current_agent = agent
                if agent != self.last_agent:
                    self.last_agent = agent
                    self.emit({"type":"agent_name","message":agent})
                return

            if c.startswith('Task:') and self.current_agent:
                task_desc = c.replace('Task:','').strip()
                self.emit({"type":"agent_task","message":task_desc[:200]})
                return

            # ── TOOL EXECUTION STARTED ────────────────────────────
            if 'Tool Execution Started' in c:
                # flush previous output if any
                if self.in_output and self.output_lines:
                    self.emit({"type":"tool_output",
                               "message":" | ".join(self.output_lines)[:600]})
                    self.output_lines = []
                self.in_output = False
                self.in_tool_body = True
                self.current_tool_name = ""
                self.current_tool_args = ""
                num_match = re.search(r'\(#(\d+)\)', c)
                num = num_match.group(1) if num_match else ""
                self.emit({"type":"tool_start","num":num,"message":f"Tool Execution Started #{num}"})
                return

            if self.in_tool_body:
                if c.startswith('Tool:'):
                    self.current_tool_name = c.replace('Tool:','').strip()
                    self.emit({"type":"tool_name","message":self.current_tool_name})
                    return
                if c.startswith('Args:'):
                    self.current_tool_args = c.replace('Args:','').strip()
                    self.emit({"type":"tool_args","message":self.current_tool_args})
                    return

            # ── TOOL EXECUTION COMPLETED ──────────────────────────
            if 'Tool Execution Completed' in c:
                self.in_tool_body = False
                self.in_output = True
                self.output_lines = []
                self.emit({"type":"tool_done","message":"Tool Completed"})
                return

            # ── TOOL FAILED ───────────────────────────────────────
            if 'Tool Failed' in c or 'Tool Error' in c:
                self.in_tool_body = False
                self.in_output = False
                self.emit({"type":"tool_error","message":c})
                return

            # ── CAPTURE TOOL OUTPUT ───────────────────────────────
            if self.in_output:
                # Stop capturing when a new section starts
                stop_keys = ['Tool Execution Started','Task Started','Task Completed',
                             'Agent Started','Crew Execution','Memory Saved',
                             'Memory Retrieval','Thinking...','Agent Final Answer']
                if any(kw in c for kw in stop_keys):
                    # flush and fall through
                    if self.output_lines:
                        raw = "\n".join(self.output_lines)
                        raw = self._clean_output(raw)
                        self.emit({"type":"tool_output","message": raw[:800]})
                        self.output_lines = []
                    self.in_output = False
                    # don't return — process this line normally below
                elif c.startswith('Output:'):
                    val = c.replace('Output:','').strip()
                    if val:
                        self.output_lines.append(val)
                    return
                elif c:
                    self.output_lines.append(c[:400])
                    # flush every 10 lines to keep streaming live
                    if len(self.output_lines) >= 10:
                        raw = "\n".join(self.output_lines)
                        raw = self._clean_output(raw)
                        self.emit({"type":"tool_output","message": raw[:800]})
                        self.output_lines = []
                    return
                else:
                    return

            # ── AGENT FINAL ANSWER ────────────────────────────────
            if 'Agent Final Answer' in c:
                self.in_final = True
                self.final_lines = []
                self.emit({"type":"final_answer_start","message":"Agent Final Answer"})
                return

            if self.in_final:
                if 'Final Answer:' in c:
                    ans = c.split('Final Answer:',1)[1].strip()
                    if ans:
                        self.final_lines.append(ans)
                elif c and not any(kw in c for kw in
                    ['Task Completed','Crew Execution','Tracing','Agent Started']):
                    self.final_lines.append(c)
                return

            if 'Final Answer:' in c and not self.in_final:
                ans = c.split('Final Answer:',1)[1].strip()
                self.emit({"type":"final_answer","message":ans[:800]})
                return

            # ── MEMORY ────────────────────────────────────────────
            if 'Memory Retrieval Completed' in c:
                self.emit({"type":"memory","message":"Memory Retrieved"})
                return
            if 'Memory Saved' in c or 'Memory Save Completed' in c:
                self.emit({"type":"memory","message":"Memory Saved"})
                return
            if 'Thinking...' in c:
                self.emit({"type":"thinking","message":"Thinking..."})
                return

        def _clean_output(self, text):
            text = re.sub(r'https?://\S+', '', text)
            text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
            text = re.sub(r'data:image[^;]+;base64,[^\s)]+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        def flush(self):
            if self.buffer.strip():
                self.process(strip_ansi(self.buffer))
                self.buffer = ""
            if self.in_output and self.output_lines:
                raw = self._clean_output(" ".join(self.output_lines))
                self.emit({"type":"tool_output","message": raw[:800]})
            if self.in_final and self.final_lines:
                self.emit({"type":"final_answer",
                           "message":" ".join(self.final_lines)[:800]})

    def run_crew():
        writer = QueueWriter()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = writer
        sys.stderr = writer
        try:
            q.put({"type":"start","message":f"Starting analysis for {ticker}..."})
            result    = run_financial_crew(ticker)
            result_str = str(result)
            storage    = StorageService()
            blob_url   = storage.upload_report(result_str, f"{ticker}_analysis_report.md")
            db_service = DatabaseService()
            db_service.save_analysis_result(ticker, result_str)
            q.put({"type":"complete","message":"Analysis complete!",
                   "result":result_str,"blob_url":blob_url,"ticker":ticker})
        except Exception as e:
            q.put({"type":"error","message":str(e)})
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            writer.flush()
            q.put({"type":"end"})

    threading.Thread(target=run_crew, daemon=True).start()

    async def generate():
        while True:
            if await request.is_disconnected():
                break
            try:
                event = q.get(timeout=0.1)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event["type"] in ("end","error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type':'ping'})}\n\n"
                await asyncio.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"},
    )

@router.get("/reports")
async def get_all_reports():
    try:
        db = DatabaseService()
        reports = db.get_all_reports()
        return {"status":"success","count":len(reports),"reports":reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{ticker}")
async def get_report_by_ticker(ticker: str):
    try:
        db = DatabaseService()
        report = db.get_report_by_ticker(ticker.upper())
        if not report:
            raise HTTPException(status_code=404, detail=f"No report for '{ticker.upper()}'")
        return {"status":"success","report":report}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)