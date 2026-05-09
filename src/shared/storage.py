"""
Storage module for managing data persistence and retrieval.
Handles interactions with Azure Blob Storage for uploading final markdown reports.
"""

from azure.storage.blob import BlobServiceClient
from src.shared.config import settings


class StorageService:
    def __init__(self):
        self.service_client = BlobServiceClient.from_connection_string(
            settings.azure_blob_storage_connection_string
        )
        self.container_name = "financial-reports"
        self.ensure_container_exists()

    def ensure_container_exists(self):
        try:
            container_client = self.service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"Container '{self.container_name}' created successfully.")
        except Exception as e:
            print(f"Error ensuring container exists: {str(e)}")

    def upload_report(self, content: str, destination_name: str) -> str:
        """
        Uploads report content string to Azure Blob Storage.

        Args:
            content: The report text content to upload.          # fix: was file_path
            destination_name: The blob name e.g. 'AAPL_analysis_report.md'
        Returns:
            URL of the uploaded blob.
        """
        try:
            blob_client = self.service_client.get_blob_client(
                container=self.container_name,
                blob=destination_name
            )
            # fix: encode string to bytes directly — no file needed
            blob_client.upload_blob(content.encode("utf-8"), overwrite=True)

            return (
                f"https://{self.service_client.account_name}.blob.core.windows.net"
                f"/{self.container_name}/{destination_name}"
            )
        except Exception as e:
            return f"Error uploading file to Azure Blob Storage: {str(e)}"