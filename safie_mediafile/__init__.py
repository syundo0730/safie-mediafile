from datetime import datetime
from typing import BinaryIO, Optional

from safie_mediafile._client import async_client, SAFIE_API_BASE_URL
from safie_mediafile._endpoints._mediafile import MediaFileAPI
from safie_mediafile._endpoints._device import DeviceAPI


async def create_and_download_mediafile(
    *,
    device_id: str,
    start_time: datetime,
    end_time: datetime,
    file: BinaryIO,
    api_token: str,
    base_url: Optional[str] = None,
):
    """
    Create and download a media file for the specified device and time period

    Args:
        device_id: Device ID
        start_time: Start time
        end_time: End time
        file: File-like object to write the media file to
        api_token: Safie API token
        base_url: Base URL for Safie API. If None, default URL will be used

    Returns:
        str: Path of the saved file
    """
    async with async_client(api_token=api_token, base_url=base_url) as client:
        mediafile_api = MediaFileAPI(client)
        print(f"Creating mediafile for device {device_id} from {start_time} to {end_time}")
        request_id = await mediafile_api.create_mediafile(device_id, start_time, end_time)
        print(f"Mediafile request ID: {request_id}")
        download_url = await mediafile_api.wait_for_mediafile_ready(device_id, request_id)
        print(f"Downloading mediafile from {download_url}")

        download_success = False
        try:
            await mediafile_api.download_mediafile(download_url, file)
            download_success = True
        finally:
            # Only delete the request if download was successful
            if download_success:
                print(f"Download completed successfully, deleting request {request_id}")
                await mediafile_api.delete_mediafile_request(device_id, request_id)


async def find_device_id(
    *,
    api_token: str,
    serial: Optional[str] = None,
    name: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Get device ID from serial number or device name

    Args:
        api_token: Safie API token
        serial: Serial number
        name: Device name
        base_url: Base URL for Safie API. If None, default URL will be used

    Returns:
        str: Device ID
    """
    assert serial is not None or name is not None, "Either serial or name must be provided"

    async with async_client(api_token=api_token, base_url=base_url) as client:
        device_api = DeviceAPI(client)
        return await device_api.find_device_id(serial=serial, name=name)


__all__ = [
    "create_and_download_mediafile",
    "find_device_id",
    "async_client",
    "MediaFileAPI",
    "DeviceAPI",
    "SAFIE_API_BASE_URL",
]
