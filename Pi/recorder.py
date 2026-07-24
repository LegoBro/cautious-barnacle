# /home/pi/birdfeeder/recorder.py
import os
import signal
import subprocess
import time
import shutil
from datetime import datetime, timedelta

# Import custom module functions safely
from utils import get_config, create_logger, ensure_free_space, timestamped_filename

# Global tracking variables
running = True
current_proc_cam = None
current_proc_ffmpeg = None

def handle_sigterm(signum, frame):
    """ Safely catch termination signals from the OS to trigger a clean exit. """
    global running
    running = False

# Register signal listeners
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def _kill_zombies(logger):
    """ Clear out any old lingering camera tasks to prevent hardware locking. """
    try:
        subprocess.run(
            ["sudo", "killall", "-9", "rpicam-vid", "ffmpeg"], 
            check=False, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        time.sleep(0.5)  # Small pause to let the Linux kernel release the device interface
    except Exception as e:
        logger.warning("Failed to run killall safety cleanup: %s", e)

def start_segment(cfg, logger):
    """
    Starts a new recording pipeline segment. 
    Writes to a hidden tmp file and returns (proc_cam, proc_ffmpeg, final_path, tmp_path).
    """
    out_dir = cfg["recording"]["output_dir"]
    os.makedirs(out_dir, exist_ok=True)
    
    # Prune old recordings if space limits are reached
    ensure_free_space(
        out_dir, 
        cfg["storage"]["min_free_gb"], 
        cfg["storage"]["max_days"],
    )

    filename = timestamped_filename("segment", "mp4")
    final_path = os.path.join(out_dir, filename)
    tmp_path = os.path.join(out_dir, f".tmp_{filename}")

    width = cfg["recording"]["width"]
    height = cfg["recording"]["height"]
    fps = cfg["recording"]["fps"]

    # Clear old processes before seizing hardware
    _kill_zombies(logger)

    # Build optimized commands
    rpicam_cmd = [
        "rpicam-vid", "-t", "0", "--width", str(width), "--height", str(height),
        "--framerate", str(fps), "--codec", "h264", "--inline", "--profile", "high",
        "-n", "-o", "-"
    ]
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", "-", "-c", "copy", "-movflags", "+faststart", tmp_path
    ]

    logger.info("Starting new segment: %s (tmp: %s)", final_path, tmp_path)
    
    try:
        # REDIRECT STDERR TO DEVNULL: Prevents 64KB kernel buffer exhaustion deadlock
        proc_cam = subprocess.Popen(
            rpicam_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL
        )
        proc_ffmpeg = subprocess.Popen(
            ffmpeg_cmd, 
            stdin=proc_cam.stdout, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        # Allows rpicam to receive a SIGPIPE error signal instantly if ffmpeg terminates
        proc_cam.stdout.close() 
        return proc_cam, proc_ffmpeg, final_path, tmp_path
        
    except Exception as e:
        logger.exception("Failed to initialize recording pipeline: %s", e)
        
        # Clean execution escape hatch if initialization crashes midway
        try:
            if 'proc_ffmpeg' in locals() and proc_ffmpeg.poll() is None:
                proc_ffmpeg.kill()
        except Exception:
            pass
        try:
            if 'proc_cam' in locals() and proc_cam.poll() is None:
                proc_cam.kill()
        except Exception:
            pass
        raise

def _finalize_and_move(proc_cam, proc_ffmpeg, tmp_path, final_path, logger, ffmpeg_timeout=15):
    """
    Terminate ffmpeg first so it can write MP4 indexes, then stop camera.
    Moves tmp_path -> final_path atomically to prevent corrupted readings.
    """
    # 1. Close out ffmpeg first so index data flushes nicely
    if proc_ffmpeg is not None:
        try:
            if proc_ffmpeg.poll() is None:
                logger.debug("Terminating ffmpeg (allowing it to finalize file indexes)...")
                try:
                    proc_ffmpeg.terminate()
                except ProcessLookupError:
                    pass  # Process closed early natively
                
                try:
                    proc_ffmpeg.wait(timeout=ffmpeg_timeout)
                except subprocess.TimeoutExpired:
                    logger.warning("ffmpeg hung past timeout threshold; issuing force kill")
                    proc_ffmpeg.kill()
                    proc_ffmpeg.wait(timeout=5)
        except Exception as e:
            logger.warning("Error encountered while finalizing ffmpeg: %s", e)

    # 2. Halt camera execution 
    if proc_cam is not None:
        try:
            if proc_cam.poll() is None:
                logger.debug("Terminating camera interface hardware...")
                try:
                    proc_cam.terminate()
                except ProcessLookupError:
                    pass
                
                try:
                    proc_cam.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Camera hardware pipeline hung; issuing force kill")
                    proc_cam.kill()
                    proc_cam.wait(timeout=5)
        except Exception as e:
            logger.warning("Error encountered while stopping camera process: %s", e)

    # 3. Swap file positions atomically
    try:
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            try:
                os.replace(tmp_path, final_path)
                logger.info("Saved segment to %s", final_path)
            except Exception as e:
                logger.warning("os.replace failed (%s); shifting to fallback shutil.move strategy", e)
                shutil.move(tmp_path, final_path)
                logger.info("Moved segment to %s", final_path)
        else:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                    logger.info("Removed empty, unwritten tmp file %s", tmp_path)
                except Exception as e:
                    logger.warning("Failed to clear dead file template %s: %s", tmp_path, e)
            else:
                logger.warning("No storage blocks found to finalize at target path %s", tmp_path)
    except Exception as e:
        logger.exception("Catastrophic error handling file finalization array: %s", e)

def main():
    cfg = get_config()
    logger = create_logger("recorder", cfg["logging"]["level"])
    segment_seconds = cfg["recording"]["segment_seconds"]
    segment_duration = timedelta(seconds=segment_seconds)
    ffmpeg_finalize_timeout = cfg["recording"].get("ffmpeg_finalize_timeout", 15)

    global current_proc_cam, current_proc_ffmpeg, running

    # Try starting the initial block
    try:
        current_proc_cam, current_proc_ffmpeg, current_file, current_tmp = start_segment(cfg, logger)
    except Exception:
        logger.error("Initial segment extraction failed to initiate; closing operations loop")
        return

    segment_start = datetime.now()

    try:
        while running:
            time.sleep(1)

            # --- TIME WINDOW SEGMENT ROTATION ---
            if datetime.now() - segment_start >= segment_duration:
                logger.info("Rotating tracking file block after %s seconds", segment_seconds)
                
                _finalize_and_move(
                    current_proc_cam, current_proc_ffmpeg, current_tmp, 
                    current_file, logger, ffmpeg_timeout=ffmpeg_finalize_timeout
                )
                
                # BREAK THE POINTERS: Protects the loop logic if the initialization crashes
                current_proc_cam, current_proc_ffmpeg = None, None
                
                try:
                    current_proc_cam, current_proc_ffmpeg, current_file, current_tmp = start_segment(cfg, logger)
                    segment_start = datetime.now()
                except Exception:
                    logger.exception("Failed to start new segment after rotation; sleeping 5 seconds")
                    time.sleep(5)
                    continue  # Forces loop to restart safely from the top

            # --- CRASH AND PIPELINE FAULT PROTECTION HANDLER ---
            cam_exited = (current_proc_cam is not None and current_proc_cam.poll() is not None)
            ffmpeg_exited = (current_proc_ffmpeg is not None and current_proc_ffmpeg.poll() is not None)

            if (cam_exited or ffmpeg_exited) and running:
                logger.warning(
                    "Recording pipeline closed abruptly (Camera Closed=%s, FFmpeg Closed=%s). Triggering self-heal.", 
                    cam_exited, ffmpeg_exited
                )
                
                _finalize_and_move(
                    current_proc_cam, current_proc_ffmpeg, current_tmp, 
                    current_file, logger, ffmpeg_timeout=ffmpeg_finalize_timeout
                )
                
                # BREAK POINTERS AGAIN: Avoids hitting this crash loop continuously every millisecond
                current_proc_cam, current_proc_ffmpeg = None, None
                
                try:
                    current_proc_cam, current_proc_ffmpeg, current_file, current_tmp = start_segment(cfg, logger)
                    segment_start = datetime.now()
                except Exception:
                    logger.exception("Self-heal stream replication failed; sleeping 5 seconds before retry pass")
                    time.sleep(5)

    except Exception as e:
        logger.exception("Unexpected catastrophic loop failure: %s", e)
        
    finally:
        logger.info("Shutting down bird feeder recording architecture cleanly...")
        running = False

        # Graceful wrap up 
        try:
            _finalize_and_move(
                current_proc_cam, current_proc_ffmpeg, current_tmp, 
                current_file, logger, ffmpeg_timeout=ffmpeg_finalize_timeout
            )
        except Exception as e:
            logger.exception("Failed cleanup step during loop termination phase: %s", e)

        # Wipe out all camera processes to leave /dev/video handles open for other user scripts
        try:
            _kill_zombies(logger)
        except Exception:
            pass
            
        logger.info("Recorder script fully stopped")

if __name__ == "__main__":
    main()
