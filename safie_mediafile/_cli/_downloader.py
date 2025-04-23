import tempfile
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import os
import shutil
import asyncio

from safie_mediafile import (
    create_and_download_mediafile,
    find_device_id,
)

_MIN_DURATION = timedelta(minutes=1)
_MAX_DURATION = timedelta(minutes=10)


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
    # Get device ID
    device_id = await find_device_id(
        api_token=api_token, serial=serial, name=name, base_url=base_url
    )

    segments = _create_time_segments(start_time, end_time, _MAX_DURATION)
    if len(segments) > 1:
        print(
            f"Requested duration ({end_time - start_time}) is longer than 10 minutes. "
            f"Will download {len(segments)} segments and merge them afterwards."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        segments_paths = await _download_segments(
            device_id, segments, output_path.name, Path(temp_dir), api_token, base_url
        )
        _merge_segments(segments_paths, output_path)


def _create_time_segments(
    start_time: datetime, end_time: datetime, segment_duration: timedelta
) -> List[Tuple[datetime, datetime]]:
    """
    Create a list of time segments based on start and end times

    Args:
        start_time: Start time
        end_time: End time
        segment_duration: Maximum duration of each segment in minutes

    Returns:
        List of (segment_start, segment_end) tuples
    """
    segments = []
    current_start = start_time
    while current_start < end_time:
        segment_end = min(current_start + segment_duration, end_time)
        segments.append((current_start, segment_end))
        current_start = segment_end
    return segments


async def _download_segments(
    device_id: str,
    segments: List[Tuple[datetime, datetime]],
    output_file_name: str,
    temp_dir: Path,
    api_token: str,
    base_url: Optional[str],
) -> List[Path]:
    """Download segments from a device."""
    segments_paths = []
    tasks = []
    for i, (start_time, end_time) in enumerate(segments):
        temp_output_path = temp_dir / f"{i}_{output_file_name}"
        segments_paths.append(temp_output_path)
        task = asyncio.create_task(
            _download_with_clipping(
                device_id, start_time, end_time, temp_output_path, api_token, base_url
            )
        )
        tasks.append(task)
    await asyncio.gather(*tasks)
    return segments_paths


async def _download_with_clipping(
    device_id: str,
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
        device_id, start_time, adjusted_end_time, output_path, api_token, base_url
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
    device_id: str,
    start_time: datetime,
    end_time: datetime,
    output_path: Path,
    api_token: str,
    base_url: Optional[str],
):
    """Process the device ID lookup and media file download in a single async function."""
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


def _merge_segments(segment_files: List[Path], output_path: Path) -> None:
    """
    Merge video segments using ffmpeg

    Args:
        segment_files: List of segment file paths
        output_path: Path to save the merged output file

    Raises:
        SafieMediaFileError: If merging fails
    """
    if not segment_files:
        raise RuntimeError("No segments to merge")

    # If only one segment, just copy it
    if len(segment_files) == 1:
        shutil.move(str(segment_files[0]), str(output_path))
        return

    # Create a file list for ffmpeg
    filelist_path = os.path.join(os.path.dirname(segment_files[0]), "filelist.txt")
    with open(filelist_path, "w") as f:
        for segment_file in segment_files:
            f.write(f"file '{segment_file}'\n")

    try:
        # Merge segments using ffmpeg
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(filelist_path),
            "-c",
            "copy",
            "-y",
            str(output_path),
        ]
        # Run ffmpeg command
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Successfully merged {len(segment_files)} segments into {output_path}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to merge segments: {e.stderr.decode() if e.stderr else str(e)}"
        ) from e

    finally:
        # Clean up the file list
        if os.path.exists(filelist_path):
            try:
                os.remove(filelist_path)
            except Exception:
                pass
