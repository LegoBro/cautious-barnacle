# Goals:
## Set "On pin" to high when pi booted
## Read "Off pin" and shutdown when high

import time
import subprocess
import RPi.GPIO as GPIO
from utils import load_config, create_logger

cfg = load_config()

logger = create_logger("gpio", cfg["logging"]["level"])

# Pin Setup
isPoweredPin = cfg["gpio"]["on_pin"]
detectShutdownPin = cfg["gpio"]["off_pin"]


GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(isPoweredPin, GPIO.OUT) # High = pi is now running
GPIO.setup(detectShutdownPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # High = Pi needs to shut down

## Pi is powered on = send "on" signal
GPIO.output(isPoweredPin, GPIO.HIGH)

def main():
    logger.info(f"The Pi is sending a high signal on pin {isPoweredPin}")
    try:
        while True:
            if GPIO.input(detectShutdownPin) == GPIO.HIGH:
                logger.info("Pi Shutdown detected")
                time.sleep(0.25) # De-Bounce
                if GPIO.input(detectShutdownPin) == GPIO.HIGH:
                    logger.info("Pi Shutdown confirmed")
                    subprocess.call(["sudo", "shutdown", "-h", "now"])
                    break

            time.sleep(0.5) # Delay between each detection
    finally:
        GPIO.output(isPoweredPin, GPIO.LOW)
        GPIO.cleanup()
        logger.info("GPIO cleaned up")

if __name__ == "__main__":
    main()