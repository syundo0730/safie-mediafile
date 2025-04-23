from datetime import datetime, timezone
import asyncio
from typing import BinaryIO

from safie_mediafile._client import SafieClient
from safie_mediafile._exceptions import SafieMediaFileError, SafieMediaFileTimeoutError


class MediaFileAPI:
    """Class providing API operations for Media Files"""

    def __init__(self, client: SafieClient):
        """
        Args:
            client: SafieClient instance
        """
        self._client = client

    async def create_mediafile(
        self, device_id: str, start_time: datetime, end_time: datetime
    ) -> str:
        """
        Create a media file and return the media file ID

        Args:
            device_id: Device ID
            start_time: Start time
            end_time: End time

        Returns:
            str: Media file ID
        """
        data = {
            "start": start_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "end": end_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        response = await self._client.post(
            f"/v2/devices/{device_id}/media_files/requests", json=data
        )
        result = response.json()
        return result["request_id"]

    async def list_mediafile_requests(self, device_id: str) -> list:
        """
        List all media file requests for a device

        Args:
            device_id: Device ID
        """
        response = await self._client.get(f"/v2/devices/{device_id}/media_files/requests")
        return response.json()["list"]

    async def delete_mediafile_request(self, device_id: str, request_id: str) -> None:
        """
        Delete a media file request

        Args:
            device_id: Device ID
            request_id: Request ID
        """
        await self._client.delete(f"/v2/devices/{device_id}/media_files/requests/{request_id}")

    async def get_mediafile_status(self, device_id: str, request_id: str) -> dict:
        """
        Get the status of a media file

        Args:
            device_id: Device ID
            request_id: Request ID

        Returns:
            dict: Media file status information
        """
        response = await self._client.get(
            f"/v2/devices/{device_id}/media_files/requests/{request_id}"
        )
        return response.json()

    async def download_mediafile(self, url: str, file: BinaryIO):
        """
        Download and save a media file

        Args:
            url: Download URL
            file: File to save the media file to

        Raises:
            SafieMediaFileError: On download error
        """
        # Stream download
        try:
            async for chunk in self._client.sync_stream(url):
                file.write(chunk)
        except Exception as e:
            raise SafieMediaFileError(f"Failed to download media file: {e}") from e

    async def wait_for_mediafile_ready(
        self,
        device_id: str,
        request_id: str,
        max_retries: int = 10,
        interval: float = 5.0,
    ) -> str:
        """
        Wait until the media file is ready

        Args:
            device_id: Device ID
            request_id: Request ID
            max_retries: Maximum number of retries
            interval: Retry interval (seconds)

        Returns:
            str: Download URL

        Raises:
            SafieMediaFileTimeoutError: On timeout
        """
        for _ in range(max_retries):
            status = await self.get_mediafile_status(device_id, request_id)
            print(f"wait_for_mediafile_ready status: {status}")
            state = status["state"]
            if state == "AVAILABLE":
                return status["url"]
            if state == "FAILED":
                raise SafieMediaFileError(
                    f"Media file generation failed: {status.get('error', 'Unknown error')}"
                )

            await asyncio.sleep(interval)

        raise SafieMediaFileTimeoutError(f"Media file generation timed out: {request_id}")
