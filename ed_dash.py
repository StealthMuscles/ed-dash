import argparse
import sys
from datetime import datetime, timezone
import json
from json import JSONDecodeError
from pathlib import Path
import time

from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from edstatus import EDStatus
from vkbled import VKBDevice, LEDConfig, LEDId, ColorMode, LEDMode

# globals
parse_retries = 5
last_timestamp = datetime.min.replace(tzinfo=timezone.utc)
try:
    device = VKBDevice(0x0204)
except RuntimeError as e:
    print(f'\n{e} - exiting\n')
    sys.exit(1)


class FSEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.strip().lower().endswith("status.json"):
            read_file(event.src_path)


def read_file(file_path: str):
    global last_timestamp, parse_retries
    with open(file_path, 'r') as file:
        try:
            status_file = json.load(file)
        except JSONDecodeError:
            if parse_retries:
                # Try again
                print(f"Caught JSONDecodeError exception - {parse_retries} retries left\n")
                parse_retries = parse_retries - 1
                time.sleep(.1)
                read_file(file_path)
                parse_retries = parse_retries + 1
            else:
                print(f"Caught JSONDecodeError exception - giving up\n")
            return

        # Check if the timestamp has changed
        timestamp = datetime.fromisoformat(status_file['timestamp'].replace('Z', '+00:00'))
        if timestamp > last_timestamp:
            print(status_file)
            status = EDStatus.from_int(status_file['Flags'])
            print(status)
            device.update_leds(build_led_update_list(status))
            #print(device.get_leds())
            print("\nWaiting for next update...\n\n")
        last_timestamp = timestamp

def build_led_update_list(status: EDStatus) -> list[LEDConfig]:
    # Build a list of LEDConfigs for the current EDStatus
    # LEDMode.OFF doesn't seem to work correctly on previously lit lights, so pass LEDMode.CONSTANT
    # with no color instead which does work for off
    leds = []

    # SEM lights
    if status.hud_analysis_mode:
        leds.append(LEDConfig(LEDId.A1, ColorMode.COLOR1, LEDMode.CONSTANT, g1=7))
    else:
        leds.append(LEDConfig(LEDId.A1, ColorMode.COLOR1, LEDMode.CONSTANT))

    if status.flight_assist_off:
        leds.append(LEDConfig(LEDId.RIGHT, ColorMode.COLOR1, LEDMode.FAST_BLINK, g1=7))
    else:
        leds.append(LEDConfig(LEDId.RIGHT, ColorMode.COLOR1, LEDMode.CONSTANT))

    if status.night_vision_on:
        leds.append(LEDConfig(LEDId.B1, ColorMode.COLOR1, LEDMode.CONSTANT, g1=7))
    else:
        leds.append(LEDConfig(LEDId.B1, ColorMode.COLOR1, LEDMode.CONSTANT))

    if status.lights_on:
        leds.append(LEDConfig(LEDId.B2, ColorMode.COLOR1, LEDMode.CONSTANT, g1=7))
    else:
        leds.append(LEDConfig(LEDId.B2, ColorMode.COLOR1, LEDMode.CONSTANT))

    if status.overheating:
        leds.append(LEDConfig(LEDId.B3, ColorMode.COLOR2, LEDMode.FLASH, r2=7))
    elif status.silent_running:
        leds.append(LEDConfig(LEDId.B3, ColorMode.COLOR1, LEDMode.FAST_BLINK, g1=7))
    else:
        leds.append(LEDConfig(LEDId.B3, ColorMode.COLOR2, LEDMode.CONSTANT))

    if status.landing_gear_down or status.srv_handbrake_on:
        leds.append(LEDConfig(LEDId.A2, ColorMode.COLOR1, LEDMode.CONSTANT, g1=7))
    else:
        leds.append(LEDConfig(LEDId.A2, ColorMode.COLOR1, LEDMode.CONSTANT))

    if status.fsd_on_cooldown:
        leds.append(LEDConfig(LEDId.LEFT, ColorMode.COLOR2, LEDMode.FAST_BLINK, r2=7))
    elif status.fsd_mass_locked:
        leds.append(LEDConfig(LEDId.LEFT, ColorMode.COLOR1, LEDMode.FAST_BLINK, g1=7))
    else:
        leds.append(LEDConfig(LEDId.LEFT, ColorMode.COLOR1, LEDMode.CONSTANT))

    # Gladiator lights
    if status.hard_points_deployed and not status.in_supercruise:
        leds.append(LEDConfig(LEDId.RGB, ColorMode.COLOR1, LEDMode.CONSTANT, r1=7, b1=7))
    else:
        leds.append(LEDConfig(LEDId.RGB, ColorMode.COLOR1, LEDMode.CONSTANT))

    # LED 0 can be used as a single red or blue light
    if status.fsd_charging or status.fsd_jump:
        leds.append(LEDConfig(LEDId.BASE, ColorMode.COLOR2, LEDMode.FAST_BLINK, r2=7))
    elif not status.in_supercruise and (
            status.fsd_on_cooldown or status.fsd_mass_locked or status.hard_points_deployed or
            status.landing_gear_down or status.cargo_scop_deployed
    ):
        leds.append(LEDConfig(LEDId.BASE, ColorMode.COLOR2, LEDMode.CONSTANT, r2=7))
    else:
        leds.append(LEDConfig(LEDId.BASE, ColorMode.COLOR1, LEDMode.CONSTANT, b1=3))

    return leds


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Monitor Elite Dangerous status.json updates and set VKB HID LEDs")
    parser.add_argument("file_path",
                        metavar="N",
                        nargs="?",
                        default="C:\\Users\\steal\\Saved Games\\Frontier Developments\\Elite Dangerous\\Status.json",
                        help="path to status.json file")
    args = parser.parse_args()

    read_file(args.file_path)

    observer = Observer()
    observer.schedule(FSEventHandler(), Path(args.file_path).parent, event_filter=[FileModifiedEvent])
    observer.start()
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
