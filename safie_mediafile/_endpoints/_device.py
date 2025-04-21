from typing import Optional, Dict, Any

from safie_mediafile._client import SafieClient
from safie_mediafile._exceptions import SafieMediaFileError


class DeviceAPI:
    """Class providing API operations for devices"""

    def __init__(self, client: SafieClient):
        """
        Args:
            client: SafieClient instance
        """
        self._client = client

    async def list_devices(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get list of devices

        Args:
            offset: Start position
            limit: Number of items to retrieve

        Returns:
            Dict[str, Any]: Device list information
        """
        params = {"offset": offset, "limit": limit}
        response = await self._client.get("/v2/devices", params=params)
        return response.json()

    async def find_device_by_serial(self, serial: str) -> Optional[str]:
        """
        Get device ID from serial number

        Args:
            serial: Serial number

        Returns:
            Optional[str]: Device ID. None if not found
        """
        devices = await self.list_devices()
        for device in devices["list"]:
            if device["serial"] == serial:
                return device["device_id"]
        return None

    async def find_device_by_name(self, name: str) -> Optional[str]:
        """
        Get device ID from device name

        Args:
            name: Device name

        Returns:
            Optional[str]: Device ID. None if not found
        """
        devices = await self.list_devices()
        for device in devices["list"]:
            if device["setting"]["name"] == name:
                return device["device_id"]
        return None

    async def find_device_id(self, serial: Optional[str] = None, name: Optional[str] = None) -> str:
        """
        Get device ID from serial number or device name

        Args:
            serial: Serial number
            name: Device name

        Returns:
            str: Device ID

        Raises:
            SafieMediaFileError: When device is not found
        """
        device_id = None

        if serial:
            device_id = await self.find_device_by_serial(serial)
            if not device_id:
                raise SafieMediaFileError(f"Device with serial number {serial} not found")
        elif name:
            device_id = await self.find_device_by_name(name)
            if not device_id:
                raise SafieMediaFileError(f"Device with name {name} not found")
        else:
            raise SafieMediaFileError("Please specify serial number or device name")

        return device_id
