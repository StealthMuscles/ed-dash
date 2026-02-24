# ed-dash
Monitor Elite Dangerous status.json file updates in order to set VKB HID device LEDs.

This is hard-coded for my preferences and equipment (VKB Gladiator NXT EVO + GNX SEM), but might make a useful example for other VKB peripheral owners to play around with.

Borrows some re-worked code from [pyvkb](https://github.com/ventorvar/pyvkb)

Requires binaries from [hidapi](https://github.com/libusb/hidapi) (pre-compiled Windows binaries are available for download from project Releases)

```
python .\ed_dash.py --help
usage: ed_dash.py [-h] [N]

Monitor Elite Dangerous status.json updates and set VKB HID LEDs

positional arguments:
  N                     path to status.json file

options:
  -h, --help            show this help message and exit
```
