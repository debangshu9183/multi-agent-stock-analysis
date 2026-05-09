"""
Configuration Management Module for CrewAI Agent Azure

Uses pydantic-settings to safely load and validate environment variables from a .env file.
This module contains configuration settings for the application, including API keys 
and connection strings.
"""

from functools import lru_cache
# lru_cache (Least Recently Used Cache): caches the result of get_settings() so the
# .env file is parsed only once, no matter how many times get_settings() is called.

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
# pydantic-settings is a separate package in Pydantic v2:
#   pip install pydantic-settings
#basesettings initialize groq_api_key and groq_model_name from the environment variables GROQ_API_KEY and GROQ_MODEL_NAME respectively. If the environment variables are not set, groq_api_key will be None and groq_model_name will default to "llama-3.3-70b-versatile". The Field function is used to specify the validation_alias, which tells Pydantic to look for the corresponding environment variable when populating the fields in the Settings model. This allows for a clear mapping between the environment variables and the fields in the Settings model, making it easier to manage configuration settings for the application.


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    Attributes:
        groq_api_key:                        API key for accessing Groq models.
        groq_model_name:                     Groq model identifier used by CrewAI.
        firecrawl_api_key:                   API key for Firecrawl web scraping.
        langchain_api_key:                   API key for LangSmith tracing.
        langchain_tracing_v2:                Enables LangChain v2 tracing when "true".
        azure_postgres_connection_string:    Azure PostgreSQL connection string.
        azure_blob_storage_connection_string: Azure Blob Storage connection string.
    """

    model_config = SettingsConfigDict(
        env_file=".env",           # load from .env in the project root
        env_file_encoding="utf-8",
        case_sensitive=False,      # GROQ_API_KEY and groq_api_key both match
        extra="ignore",            # silently ignore unknown env vars
    )

   #OPENAI
    openai_api_key:str = Field(None,description="API key for OpenAI services", validation_alias="OPENAI_API_KEY")
    openai_model_name: str = Field("gpt-4o", description="OpenAI model identifier used by CrewAI", validation_alias="OPENAI_MODEL_NAME")

    #Field is used to add metadata to the fields in the model, such as description, example, etc. This helps to ensure that the input is valid and provides clarity on what the input should look like. In this case, the validation_alias parameter is used to specify the name of the environment variable that corresponds to each field in the Settings model. For example, groq_api_key will be populated from the GROQ_API_KEY environment variable, and groq_model_name will be populated from the GROQ_MODEL_NAME environment variable. This allows for a clear mapping between the environment variables and the fields in the Settings model, making it easier to manage configuration settings for the application.

    # ── Firecrawl ─────────────────────────────────────────────────────────────
    firecrawl_api_key: Optional[str] = Field(None, validation_alias="FIRECRAWL_API_KEY")

    # ── LangSmith tracing (optional) ──────────────────────────────────────────
    langchain_api_key: Optional[str] = Field(None, validation_alias="LANGCHAIN_API_KEY")
    langchain_tracing_v2: Optional[str] = Field(None, validation_alias="LANGCHAIN_TRACING_V2")

    # ── Azure ─────────────────────────────────────────────────────────────────
    azure_postgres_connection_string: Optional[str] = Field(
        None, validation_alias="AZURE_POSTGRES_CONNECTION_STRING"
    )
    azure_blob_storage_connection_string: Optional[str] = Field(
        None, validation_alias="AZURE_BLOB_STORAGE_CONNECTION_STRING"
    )


@lru_cache  #its a decorator that caches the result of the get_settings function, so that the .env file is read and parsed only once. Subsequent calls to get_settings will return the cached Settings instance, improving performance by avoiding redundant parsing of the .env file.
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Call this anywhere in your project instead of instantiating Settings()
    directly, so the .env file is read only once.

        from config import get_settings
        settings = get_settings()
        print(settings.groq_model_name)
    """
    return Settings()

settings = get_settings()