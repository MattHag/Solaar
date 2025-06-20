from __future__ import annotations

import threading

from dataclasses import dataclass
from dataclasses import field
from struct import pack
from typing import Any
from typing import Optional

from logitech_receiver import device
from logitech_receiver import hidpp20
from solaar import configuration


@dataclass
class Response:
    response: str | float
    id: int
    params: str = ""
    handle: int = 0x11
    devnumber: int = 0xFF
    no_reply: bool = False


@dataclass
class FakeDevice:
    """Device instance.

    A fake device that uses provided data (responses) to respond to
    HID++ commands. Some methods from the real device are used to set
    up data structures needed for settings.
    """

    name: str = "TESTD"
    online: bool = True
    protocol: float = 2.0
    responses: Any = field(default_factory=list)
    codename: str = "TESTC"
    feature: Optional[int] = None
    offset: Optional[int] = 4
    version: Optional[int] = 0
    wpid: Optional[str] = "0000"
    setting_callback: Any = None
    sliding = profiles = _backlight = _keys = _remap_keys = _led_effects = _gestures = None
    _gestures_lock = threading.Lock()
    number = "d1"
    present = True

    read_register = device.Device.read_register
    write_register = device.Device.write_register
    backlight = device.Device.backlight
    keys = device.Device.keys
    remap_keys = device.Device.remap_keys
    led_effects = device.Device.led_effects
    gestures = device.Device.gestures
    __hash__ = device.Device.__hash__
    feature_request = device.Device.feature_request

    def __post_init__(self):
        self._name = self.name
        self._protocol = self.protocol
        self.persister = configuration._DeviceEntry()
        self.features = hidpp20.FeaturesArray(self)
        self.settings = []
        self.receiver = []
        if self.feature is not None:
            self.features = hidpp20.FeaturesArray(self)
            self.responses = [
                Response("010001", 0x0000, "0001"),
                Response("20", 0x0100),
            ] + self.responses
            self.responses.append(
                Response(
                    f"{int(self.offset):0>2X}00{int(self.version):0>2X}",
                    0x0000,
                    f"{int(self.feature):0>4X}",
                )
            )
        if self.setting_callback is None:
            self.setting_callback = lambda x, y, z: None
        self.add_notification_handler = lambda x, y: None

    def request(self, id, *params, no_reply=False, long_message=False, protocol=2.0):
        params = b"".join(pack("B", p) if isinstance(p, int) else p for p in params)
        print("REQUEST ", self._name, hex(id), params.hex().upper())
        for r in self.responses:
            if id == r.id and params == bytes.fromhex(r.params):
                print("RESPONSE", self._name, hex(r.id), r.params, r.response)
                return bytes.fromhex(r.response) if isinstance(r.response, str) else r.response
        print("RESPONSE", self._name, None)

    def ping(self, handle=None, devnumber=None, long_message=False):
        print("PING", self._protocol)
        return self._protocol

    def handle_notification(self, handle):
        pass

    def changed(self, *args, **kwargs):
        pass

    def set_battery_info(self, *args, **kwargs):
        pass

    def status_string(self):
        pass
