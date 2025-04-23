import asyncio
from datetime import datetime, tzinfo
from dateutil.tz import gettz
from pathlib import Path
from typing import Optional

import click

from safie_mediafile import SAFIE_API_BASE_URL

from ._downloader import download_media_from_device


def _parse_time_string(time_string: str, default_tz: Optional[tzinfo]) -> datetime:
    """Parse time string with timezone handling.

    Args:
        time_string: ISO8601 format time string
        default_tz: Default timezone to use if no timezone info is provided

    Returns:
        datetime object with timezone info

    Raises:
        ValueError: If time string format is invalid
    """
    try:
        # Try parsing as is first (may contain timezone info)
        dt = datetime.fromisoformat(time_string)
        # If no timezone info, apply the default timezone
        if dt.tzinfo is None and default_tz is not None:
            dt = dt.replace(tzinfo=default_tz)
        return dt
    except ValueError as e:
        # Handle 'Z' suffix for UTC
        if time_string.endswith("Z"):
            time_string = time_string.replace("Z", "+00:00")
            return datetime.fromisoformat(time_string)
        # Try other formats or raise error
        raise ValueError(f"Invalid time format: {time_string}") from e


@click.command()
@click.option(
    "--serial",
    help="Device serial number",
    default=None,
)
@click.option(
    "--name",
    help="Device name",
    default=None,
)
@click.argument("start_time")
@click.argument("end_time")
@click.option(
    "--output-path",
    default=None,
    help="Output file path. If not specified, it's generated from start_time (e.g., YYYY-MM-DD_HH-mm-ss.mp4)",
)
@click.option("--api-token", required=True, help="Safie API token", envvar="SAFIE_TOKEN")
@click.option(
    "--base-url",
    default=None,
    help="Base URL for Safie API. Default: " + SAFIE_API_BASE_URL,
)
@click.option(
    "--timezone",
    "timezone_str",
    default=None,
    help="Timezone for interpreting times with timezone info (e.g. UTC, Asia/Tokyo, JST, etc.)."
    "If not specified, it will be inferred from time string or the local time.",
)
def main(
    serial: Optional[str],
    name: Optional[str],
    start_time: str,
    end_time: str,
    output_path: Optional[str],
    api_token: str,
    base_url: Optional[str],
    timezone_str: str,
):
    """Download Safie media file

    START_TIME: Start time (ISO8601 format, e.g. 2024-03-22T10:00:00 or 2024-03-22T10:00:00+09:00)
    END_TIME: End time (ISO8601 format, e.g. 2024-03-22T11:00:00 or 2024-03-22T11:00:00+09:00)

    Times with 'Z' suffix (e.g. 2024-03-22T10:00:00Z) are treated as UTC.
    Times with explicit offset (e.g. 2024-03-22T10:00:00+09:00) use that timezone.
    Times without timezone info use the specified --timezone option (default: UTC).
    """
    try:
        # Validate inputs
        if not serial and not name:
            raise ValueError("Either --serial or --name must be specified")

        # Parse timezone and time strings
        default_tz = gettz(timezone_str)
        start = _parse_time_string(start_time, default_tz)
        end = _parse_time_string(end_time, default_tz)

        # Generate output_path from start_time if not specified
        if output_path is None:
            output_path = start.strftime("%Y-%m-%d_%H-%M-%S") + ".mp4"

        # Run the async download process with a single asyncio.run call
        asyncio.run(
            download_media_from_device(
                serial=serial,
                name=name,
                start_time=start,
                end_time=end,
                output_path=Path(output_path),
                api_token=api_token,
                base_url=base_url,
            )
        )

        click.echo(f"Media file download completed: {output_path}")

    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)
        exit(1)
