"""Video probing and thumbnail extraction via system ffprobe/ffmpeg."""

import json
import subprocess


class VideoProbeError(Exception):
    """Raised when a video file cannot be probed or a frame cannot be extracted."""


def probe(path):
    """Return (width, height, duration_seconds) for the first video stream.

    Raises VideoProbeError on non-zero ffprobe exit, missing streams,
    or unparseable output.
    """
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height:format=duration',
         '-of', 'json', path],
        capture_output=True, check=False, timeout=60,
    )
    if result.returncode != 0:
        raise VideoProbeError('ffprobe failed for {}'.format(path))
    try:
        data = json.loads(result.stdout.decode('utf-8'))
        stream = data['streams'][0]
        width = int(stream['width'])
        height = int(stream['height'])
        duration = float(data['format']['duration'])
    except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError) as exc:
        raise VideoProbeError('could not parse ffprobe output: {}'.format(exc))
    return width, height, duration


def extract_frame(path, out_jpeg, at_seconds=1):
    """Extract a single JPEG frame from path into out_jpeg.

    Videos shorter than at_seconds fall back to the middle of the video
    (or t=0 for zero-length durations) so ffmpeg always has a frame to grab.
    Raises VideoProbeError on failure.
    """
    try:
        _, _, duration = probe(path)
    except VideoProbeError:
        duration = None
    if duration is not None and duration <= at_seconds:
        at_seconds = duration / 2 if duration > 0 else 0
    result = subprocess.run(
        ['ffmpeg', '-v', 'error', '-y', '-ss', str(at_seconds),
         '-i', path, '-frames:v', '1', '-q:v', '2', out_jpeg],
        capture_output=True, check=False, timeout=60,
    )
    if result.returncode != 0:
        raise VideoProbeError('ffmpeg frame extraction failed for {}'.format(path))
