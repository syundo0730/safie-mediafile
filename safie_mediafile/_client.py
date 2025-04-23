from typing import AsyncGenerator, Optional
import httpx
from contextlib import asynccontextmanager


SAFIE_API_BASE_URL = "https://openapi.safie.link"


class SafieClient:
    """Safie API client"""

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_token: str,
        base_url: Optional[str] = None,
    ):
        """
        Args:
            client: httpx AsyncClient instance
            api_token: Safie API token
            base_url: Base URL for Safie API. If None, default URL will be used
        """
        self._base_url = base_url or SAFIE_API_BASE_URL
        self._client = client
        self._headers = {"Safie-API-Key": api_token}

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """
        Send GET request

        Args:
            path: API path
            **kwargs: Request parameters

        Returns:
            httpx.Response: Response
        """
        url = f"{self._base_url}{path}"
        response = await self._client.get(url, headers=self._headers, **kwargs)
        print(f"get response: {response.json()}")
        response.raise_for_status()
        return response

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """
        Send POST request

        Args:
            path: API path
            **kwargs: Request parameters

        Returns:
            httpx.Response: Response
        """
        url = f"{self._base_url}{path}"
        response = await self._client.post(url, headers=self._headers, **kwargs)
        print(f"post response: {response.json()}")
        response.raise_for_status()
        return response

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """
        Send DELETE request

        Args:
            path: API path
            **kwargs: Request parameters

        Returns:
            httpx.Response: Response
        """
        url = f"{self._base_url}{path}"
        response = await self._client.delete(url, headers=self._headers, **kwargs)
        print(f"delete response: {response.status_code}")
        response.raise_for_status()
        return response

    async def sync_stream(self, url: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """
        Send streaming request

        Args:
            url: URL
            **kwargs: Request parameters

        Returns:
            httpx.Response: Response
        """
        async with self._client.stream("GET", url, headers=self._headers, **kwargs) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk


@asynccontextmanager
async def async_client(api_token: str, base_url: Optional[str] = None):
    """
    Create a SafieClient instance as an async context manager

    Args:
        api_token: Safie API token
        base_url: Base URL for Safie API. If None, default URL will be used

    Yields:
        SafieClient: Client instance
    """
    async with httpx.AsyncClient() as httpx_client:
        yield SafieClient(httpx_client, api_token, base_url)
