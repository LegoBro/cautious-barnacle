# /home/pi/birdfeeder/recorder.py
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta

from utils import get_config, create_logger, ensure_free_space, timestamped_filename

running = True
current_proc = None

def handle_sigterm(signum, frame):
    global running, current_proc
    running = False
    if current_proc and current_proc.poll() is None:
        current_proc.terminate()

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def start_segment(cfg, logger):
    out_dir = cfg["recording"]["output_dir"]
    os.makedirs(out_dir, exist_ok=True)

    ensure_free_space(
        out_dir,
        cfg["storage"]["min_free_gb"],
        cfg["storage"]["max_days"],
    )

    filename = timestamped_filename("segment", "mp4")
    full_path = os.path.join(out_dir, filename)

    width = cfg["recording"]["width"]
    height = cfg["recording"]["height"]
    fps = cfg["recording"]["fps"]
    bitrate = cfg["recording"]["bitrate"]
    device = cfg["recording"]["device"]

    # Example using libcamera-vid piped to ffmpeg for MP4
    cmd = [
        "bash", "-lc",
        f"rpicam-vid -t 0 --width {width} --height {height} "
        f"--framerate {fps} --codec h264 --inline --profile high "
        f"-n -o - | ffmpeg -y -i - -c copy -movflags +faststart {full_path}"
    ]

    logger.info(f"Starting new segment: {full_path}")
    proc = subprocess.Popen(cmd)
    return proc, full_path

def main():
    cfg = get_config()
    logger = create_logger("recorder", cfg["logging"]["level"])

    segment_seconds = cfg["recording"]["segment_seconds"]
    segment_duration = timedelta(seconds=segment_seconds)

    global current_proc, running
    current_proc, current_file = start_segment(cfg, logger)
    segment_start = datetime.now()

    while running:
        time.sleep(1)
        if datetime.now() - segment_start >= segment_duration:
            logger.info("Rotating segment")
            if current_proc.poll() is None:
                current_proc.terminate()
                current_proc.wait()
            current_proc, current_file = start_segment(cfg, logger)
            segment_start = datetime.now()

        # If process crashed, restart
        if current_proc.poll() is not None and running:
            logger.warning("Recorder process exited unexpectedly, restarting segment")
            current_proc, current_file = start_segment(cfg, logger)
            segment_start = datetime.now()

    logger.info("Shutting down recorder")
    if current_proc and current_proc.poll() is None:
        current_proc.terminate()
        current_proc.wait()
    logger.info("Recorder stopped cleanly")

if __name__ == "__main__":
    main()
