from typing import Any, AsyncGenerator, Optional
import httpx
from contextlib import asynccontextmanager
import logging
import time

from safie_mediafile._exceptions import SafieAPIError, SafieMediaFileError


logger = logging.getLogger(__name__)


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

    async def get(self, path: str, **kwargs) -> Any:
        """
        Send GET request

        Args:
            path: API path
            **kwargs: Request parameters

        Returns:
            Any: Parsed JSON response
        """
        url = f"{self._base_url}{path}"
        start_time = time.perf_counter()
        response = await self._client.get(url, headers=self._headers, **kwargs)
        elapsed = time.perf_counter() - start_time
        logger.debug("GET %s -> %s in %.3fs", url, response.status_code, elapsed)
        response.raise_for_status()
        return self._parse_json_response(response)

    async def post(self, path: str, **kwargs) -> Any:
        """
        Send POST request

        Args:
            path: API path
            **kwargs: Request parameters

        Returns:
            Any: Parsed JSON response
        """
        url = f"{self._base_url}{path}"
        start_time = time.perf_counter()
        response = await self._client.post(url, headers=self._headers, **kwargs)
        elapsed = time.perf_counter() - start_time
        logger.debug("POST %s -> %s in %.3fs", url, response.status_code, elapsed)
        response.raise_for_status()
        return self._parse_json_response(response)

    async def delete(self, path: str, **kwargs) -> Any:
        """
        Send DELETE request

        Args:
            path: API path
            **kwargs: Request parameters

        Returns:
            Any: Parsed JSON response
        """
        url = f"{self._base_url}{path}"
        start_time = time.perf_counter()
        response = await self._client.delete(url, headers=self._headers, **kwargs)
        elapsed = time.perf_counter() - start_time
        logger.debug("DELETE %s -> %s in %.3fs", url, response.status_code, elapsed)
        response.raise_for_status()
        return self._parse_json_response(response)

    async def sync_stream(self, url: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """
        Send streaming request

        Args:
            url: URL
            **kwargs: Request parameters

        Returns:
            AsyncGenerator[bytes, None]: Streaming response bytes
        """
        start_time = time.perf_counter()
        logger.debug("STREAM GET %s starting", url)
        try:
            async with self._client.stream(
                "GET", url, headers=self._headers, **kwargs
            ) as response:
                response.raise_for_status()
                elapsed = time.perf_counter() - start_time
                logger.debug(
                    "STREAM GET %s -> %s in %.3fs", url, response.status_code, elapsed
                )
                async for chunk in response.aiter_bytes():
                    yield chunk
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            logger.debug("STREAM GET %s failed in %.3fs", url, elapsed)
            raise SafieMediaFileError(f"Failed to stream from {url}: {exc}") from exc

    def _parse_json_response(self, response: httpx.Response) -> Any:
        try:
            return response.json()
        except Exception as exc:
            content_summary = response.text
            max_length = 200
            if len(content_summary) > max_length:
                content_summary = f"{content_summary[:max_length]}..."
            message = (
                f"Failed to parse JSON response from {response.url}: {content_summary}"
            )
            raise SafieAPIError(message, response.status_code, content_summary) from exc


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
