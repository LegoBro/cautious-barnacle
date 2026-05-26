# /home/pi/birdfeeder/gpio_listener.py
import time
import os
import subprocess
import RPi.GPIO as GPIO

from utils import load_config, setup_logger

cfg = load_config()
logger = setup_logger("gpio_listener", cfg["logging"]["dir"], cfg["logging"]["level"])

ON_PIN = cfg["gpio"]["on_pin"]
OFF_PIN = cfg["gpio"]["off_pin"]

GPIO.setmode(GPIO.BCM)
GPIO.setup(ON_PIN, GPIO.OUT)
GPIO.setup(OFF_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Signal "on" to external controller
GPIO.output(ON_PIN, GPIO.HIGH)
logger.info("GPIO on signal set HIGH")

def main():
    logger.info("Starting GPIO listener")
    try:
        while True:
            val = GPIO.input(OFF_PIN)
            if val == GPIO.LOW:  # active low shutdown signal
                logger.info("Shutdown signal detected on OFF_PIN")
                # Optional: small debounce
                time.sleep(0.5)
                if GPIO.input(OFF_PIN) == GPIO.LOW:
                    logger.info("Confirmed shutdown request, calling system shutdown")
                    # Let systemd handle stopping services; we just trigger shutdown
                    subprocess.call(["sudo", "shutdown", "-h", "now"])
                    break
            time.sleep(0.2)
    finally:
        GPIO.output(ON_PIN, GPIO.LOW)
        GPIO.cleanup()
        logger.info("GPIO cleaned up")

if __name__ == "__main__":
    main()
