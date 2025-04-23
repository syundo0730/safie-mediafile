from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import os
import shutil

from safie_mediafile import (
    create_and_download_mediafile,
    find_device_id,
)


async def download_media_from_device(
    serial: Optional[str],
    name: Optional[str],
    start_time: datetime,
    end_time: datetime,
    output_path: Path,
    api_token: str,
    base_url: Optional[str],
):
    """Download media from a device with clipping if necessary."""
    await _download_with_clipping(
        serial, name, start_time, end_time, output_path, api_token, base_url
    )


_MIN_DURATION = timedelta(minutes=1)


async def _download_with_clipping(
    serial: Optional[str],
    name: Optional[str],
    start_time: datetime,
    end_time: datetime,
    output_path: Path,
    api_token: str,
    base_url: Optional[str],
):
    original_end_time = end_time

    # Check if duration is less than 1 minute
    duration = end_time - start_time
    if duration < _MIN_DURATION:
        print(
            f"Requested duration ({duration}) is less than 1 minute. Will download a 1-minute video and clip it afterwards.",
        )
        adjusted_end_time = start_time + _MIN_DURATION
        needs_clipping = True
    else:
        needs_clipping = False
        adjusted_end_time = end_time

    await _download_media(
        serial, name, start_time, adjusted_end_time, output_path, api_token, base_url
    )

    if needs_clipping:
        print(
            f"Clipping video to the original requested duration: {start_time} to {original_end_time}"
        )
        temp_output_path = output_path.with_suffix(".temp.mp4")
        try:
            # Calculate duration for ffmpeg
            clip_duration = (original_end_time - start_time).total_seconds()

            # ffmpeg command
            cmd = [
                "ffmpeg",
                "-i",
                str(output_path),
                "-ss",
                "0",
                "-t",
                str(clip_duration),
                "-c",
                "copy",  # Copy streams without re-encoding
                "-y",  # Overwrite existing files
                str(temp_output_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                raise RuntimeError("Failed to clip the video with ffmpeg.")

            # Replace original file with clipped file
            shutil.move(str(temp_output_path), str(output_path))

        except FileNotFoundError:
            raise RuntimeError(
                "Error: ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH."
            )
        except Exception as e:
            raise RuntimeError(f"An error occurred during clipping: {e}")

        finally:
            # Remove temporary file if it still exists
            if temp_output_path.exists():
                os.remove(temp_output_path)


async def _download_media(
    serial: Optional[str],
    name: Optional[str],
    start_time: datetime,
    end_time: datetime,
    output_path: Path,
    api_token: str,
    base_url: Optional[str],
):
    """Process the device ID lookup and media file download in a single async function."""
    # Get device ID
    device_id = await find_device_id(
        api_token=api_token, serial=serial, name=name, base_url=base_url
    )

    # Create and download media file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            await create_and_download_mediafile(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                file=f,
                api_token=api_token,
                base_url=base_url,
            )
    except Exception as e:
        output_path.unlink(missing_ok=True)
        raise e
