"""
Database Service Module.
Handles connection to Azure PostgreSQL and stores financial analysis results.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
from src.shared.config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class FinancialAnalysisResult(Base):
    __tablename__ = "financial_analysis_results"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    ticker          = Column(String(10), nullable=False)
    analysis_date   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analysis_result = Column(Text, nullable=False)


class DatabaseService:
    def __init__(self):
        db_url = settings.azure_postgres_connection_string
        if not db_url:
            raise ValueError("AZURE_POSTGRES_CONNECTION_STRING is not set in .env")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        self.engine  = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def save_analysis_result(self, ticker: str, analysis_result: str):
        session = self.Session()
        try:
            record = FinancialAnalysisResult(ticker=ticker, analysis_result=analysis_result)
            session.add(record)
            session.commit()
            logger.info("Saved analysis result for '%s' to database.", ticker)
        except Exception as e:
            session.rollback()
            logger.error("Error saving result for '%s': %s", ticker, e)
            raise
        finally:
            session.close()

    def get_all_reports(self) -> list:
        session = self.Session()
        try:
            results = session.query(FinancialAnalysisResult).order_by(
                FinancialAnalysisResult.analysis_date.desc()
            ).all()
            return [
                {
                    "id":              r.id,
                    "ticker":          r.ticker,
                    "analysis_date":   r.analysis_date.isoformat(),
                    "analysis_result": r.analysis_result,
                }
                for r in results
            ]
        except Exception as e:
            logger.error("Error fetching all reports: %s", e)
            return []
        finally:
            session.close()

    def get_report_by_ticker(self, ticker: str) -> dict:
        session = self.Session()
        try:
            result = session.query(FinancialAnalysisResult).filter_by(
                ticker=ticker
            ).order_by(
                FinancialAnalysisResult.analysis_date.desc()
            ).first()
            if not result:
                return None
            return {
                "id":              result.id,
                "ticker":          result.ticker,
                "analysis_date":   result.analysis_date.isoformat(),
                "analysis_result": result.analysis_result,
            }
        except Exception as e:
            logger.error("Error fetching report for '%s': %s", ticker, e)
            return None
        finally:
            session.close()