import os
import struct
from enum import IntEnum, auto

import bitstruct as bs
import hid


class LEDId(IntEnum):
    # Gladiator
    BASE = 0
    RGB = 10
    POV = auto()
    # SEM
    A1 = auto()
    A2 = auto()
    B1 = auto()
    B2 = auto()
    B3 = auto()
    LEFT = auto()
    MIDDLE = auto()
    RIGHT = auto()
    DUMMY = 128


class ColorMode(IntEnum):
    COLOR1 = 0
    COLOR2 = auto()
    COLOR1_d_2 = auto()
    COLOR2_d_1 = auto()
    COLOR1_p_2 = auto()


class ColorValue(IntEnum):
    VALUE_0 = 0
    VALUE_1 =auto()
    VALUE_2 = auto()
    VALUE_3 = auto()
    VALUE_4 = auto()
    VALUE_5 = auto()
    VALUE_6 = auto()
    VALUE_7 = auto()


class LEDMode(IntEnum):
    OFF = 0
    CONSTANT = auto()
    SLOW_BLINK = auto()
    FAST_BLINK = auto()
    ULTRA_BLINK = auto()
    FLASH = auto()


class LEDConfig:
    """
    An configuration for an LED in a VKB device.

    Setting the LEDs consists of a possible 30 LED configs each of which is a 4 byte structure as follows:

    byte 0:  LED ID
    bytes 2-4: a 24 bit color config as follows::

        000 001 010 011 100 101 110 111
        clm lem  b2  g2  r2  b1  g1  r1

    color mode (clm):
        0 - color1
        1 - color2
        2 - color1/2
        3 - color2/1
        4 - color1+2

    led mode (lem):
        0 - off
        1 - constant
        2 - slow blink
        3 - fast blink
        4 - ultra fast

    Colors:
        VKB uses a simple RGB color configuration for all LEDs. Non-rgb LEDs will not light if you set their primary
        color to 0 in the color config. The LEDs have a very reduced color range due to VKB using 0-7 to determine the
        brightness of R, G, and B.

    Bytes:
        Convert the LEDConfig to an appropriate binary representation by using `bytes`::

        >>> led1 = LEDConfig(led=1, led_mode=LEDMode.CONSTANT)
        >>> bytes(led1)
        b'\\x01\\x07p\\x04'


    :param led: `int` ID of the LED to control
    :param color_mode: `int` color mode, see :class:`ColorMode`
    :param led_mode: `int` LED mode, see :class:`LEDMode`
    :param color1: `str` hex color code for use as `color1`
    :param color2: `str` hex color code for use as `color2`
    """

    def __init__(
        self,
        led_id: int,
        color_mode: int = 0,
        led_mode: int = 0,
        r1: int = 0,
        g1: int = 0,
        b1: int = 0,
        r2: int = 0,
        g2: int = 0,
        b2: int = 0
    ):
        self.led_id = led_id
        self.color_mode = ColorMode(color_mode)
        self.led_mode = LEDMode(led_mode)
        self.r1 = ColorValue(r1)
        self.g1 = ColorValue(g1)
        self.b1 = ColorValue(b1)
        self.r2 = ColorValue(r2)
        self.g2 = ColorValue(g2)
        self.b2 = ColorValue(b2)

    def __repr__(self):
        return (
            f"<LEDConfig {self.led_id} clm:{self.color_mode.name} lem:{self.led_mode.name} "
            f"color1:({self.r1},{self.g1},{self.b1}) color2:({self.r2},{self.g2},{self.b2})>"
        )

    def __bytes__(self):
        return struct.pack(">B", self.led_id) + bs.byteswap(
            "3",
            bs.pack(
                "u3" * 8,
                self.color_mode,
                self.led_mode,
                self.b2,
                self.g2,
                self.r2,
                self.b1,
                self.g1,
                self.r1
            )
        )

    @classmethod
    def from_bytes(cls, buf) -> LEDConfig:
        """ Creates an :class:`LEDConfig` from a bytes object """
        assert len(buf) == 4
        led_id = int(buf[0])
        buf = bs.byteswap("3", buf[1:])
        clm, lem, b2, g2, r2, b1, g1, r1 = bs.unpack("u3" * 8, buf)
        return cls(
            led_id=led_id,
            color_mode=clm,
            led_mode=lem,
            r1=r1,
            g1=g1,
            b1=b1,
            r2=r2,
            g2=g2,
            b2=b2
        )

class VKBDevice:
    VENDOR_ID = 0x231d
    LED_CONFIG_MAX = 12
    __LED_COUNT_INDEX = 7
    __LED_REPORT_ID = 0x59
    __LED_REPORT_LEN = 129
    __LED_SET_OP_CODE = bytes.fromhex("59a50a")

    def __init__(self, product_id: int):
        try:
            with hid.Device(VKBDevice.VENDOR_ID, product_id) as device:
                print(f'Device {VKBDevice.VENDOR_ID:04X}{product_id:04X} found')
        except hid.HIDException as e:
            raise RuntimeError(f'Unable to open device {VKBDevice.VENDOR_ID:04X}{product_id:04X}') from e

        self.product_id = product_id

    def _led_checksum(self, num_configs, buf):
        """
        It's better not to ask too many questions about this. Why didn't they just use a CRC?
        Why do we only check (num_configs+1)*3 bytes instead of the whole buffer?
        We may never know...  it works...
        """

        def conf_checksum_bit(chk, b):
            chk ^= b
            for i in range(8):
                _ = chk & 1
                chk >>= 1
                if _ != 0:
                    chk ^= 0xA001
            return chk

        chk = 0xFFFF
        for i in range((num_configs + 1) * 3):
            chk = conf_checksum_bit(chk, buf[i])
        return struct.pack("<H", chk)

    def get_leds(self) -> list[LEDConfig]:
        with hid.Device(VKBDevice.VENDOR_ID, self.product_id) as device:
            print(f'Device manufacturer: {device.manufacturer}')
            print(f'Product: {device.product}')
            report = device.get_feature_report(VKBDevice.__LED_REPORT_ID, VKBDevice.__LED_REPORT_LEN)
            print(report.hex())

            assert report[:3] == VKBDevice.__LED_SET_OP_CODE
            num_led_configs = int(report[VKBDevice.__LED_COUNT_INDEX])
            data = report[VKBDevice.__LED_COUNT_INDEX+1:]
            leds = []
            while num_led_configs:
                leds.append(LEDConfig.from_bytes(data[:4]))
                data = data[4:]
                num_led_configs -= 1
            return leds

    def update_leds(self, leds: list[LEDConfig]) -> None:
        # Note - there's supposedly a max of 12 leds here, 11 excluding the dummy entry added on the end
        assert len(leds) < self.LED_CONFIG_MAX
        leds.append(LEDConfig(LEDId.DUMMY, ColorMode.COLOR1, LEDMode.OFF))
        with hid.Device(VKBDevice.VENDOR_ID, self.product_id) as device:
            num_configs = len(leds)
            led_bytes = b"".join(bytes(_) for _ in leds)
            led_bytes = os.urandom(2) + struct.pack(">B", num_configs) + led_bytes
            checksum = self._led_checksum(num_configs, led_bytes)
            led_bytes = VKBDevice.__LED_SET_OP_CODE + checksum + led_bytes
            led_bytes = led_bytes + b"\x00" * (VKBDevice.__LED_REPORT_LEN - len(led_bytes))
            device.send_feature_report(led_bytes)
