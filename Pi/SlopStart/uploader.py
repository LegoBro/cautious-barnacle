# /home/pi/birdfeeder/uploader.py
import os
import time
import shutil

from utils import load_config, setup_logger

def main():
    cfg = load_config()
    logger = setup_logger("uploader", cfg["logging"]["dir"], cfg["logging"]["level"])

    if not cfg["nas"]["enabled"]:
        logger.info("NAS upload disabled in config")
        return

    src_dir = cfg["recording"]["output_dir"]
    dst_dir = cfg["nas"]["remote_path"]
    retry_seconds = cfg["nas"]["retry_seconds"]

    logger.info(f"Starting uploader: {src_dir} -> {dst_dir}")

    while True:
        try:
            if not os.path.ismount(cfg["nas"]["mount_point"]):
                logger.warning("NAS not mounted, will retry")
                time.sleep(retry_seconds)
                continue

            os.makedirs(dst_dir, exist_ok=True)
            files = sorted(os.listdir(src_dir))
            for fn in files:
                src = os.path.join(src_dir, fn)
                dst = os.path.join(dst_dir, fn)
                if not os.path.isfile(src):
                    continue
                if os.path.exists(dst):
                    continue
                try:
                    logger.info(f"Copying {src} -> {dst}")
                    shutil.copy2(src, dst)
                except Exception as e:
                    logger.error(f"Failed to copy {src}: {e}")
                    break
        except Exception as e:
            logger.error(f"Uploader loop error: {e}")

        time.sleep(retry_seconds)

if __name__ == "__main__":
    main()
