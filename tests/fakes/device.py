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


responses_gestures = [  # the commented-out messages are not used by either the setting or other testing
    Response("4203410141020400320480148C21A301", 0x0400, "0000"),  # items
    Response("A302A11EA30A4105822C852DAD2AAD2B", 0x0400, "0008"),
    Response("8F408F418F434204AF54912282558264", 0x0400, "0010"),
    Response("01000000000000000000000000000000", 0x0400, "0018"),
    Response("01000000000000000000000000000000", 0x0410, "000101"),  # enable
    #    Response("02000000000000000000000000000000", 0x0410, "000102"),
    #    Response("04000000000000000000000000000000", 0x0410, "000104"),
    #    Response("08000000000000000000000000000000", 0x0410, "000108"),
    Response("00000000000000000000000000000000", 0x0410, "000110"),
    #    Response("20000000000000000000000000000000", 0x0410, "000120"),
    #    Response("40000000000000000000000000000000", 0x0410, "000140"),
    #    Response("00000000000000000000000000000000", 0x0410, "000180"),
    #    Response("00000000000000000000000000000000", 0x0410, "010101"),
    #    Response("00000000000000000000000000000000", 0x0410, "010102"),
    #    Response("04000000000000000000000000000000", 0x0410, "010104"),
    #    Response("00000000000000000000000000000000", 0x0410, "010108"),
    Response("6F000000000000000000000000000000", 0x0410, "0001FF"),
    Response("04000000000000000000000000000000", 0x0410, "01010F"),
    Response("00000000000000000000000000000000", 0x0430, "000101"),  # divert
    #    Response("00000000000000000000000000000000", 0x0430, "000102"),
    #    Response("00000000000000000000000000000000", 0x0430, "000104"),
    #    Response("00000000000000000000000000000000", 0x0430, "000108"),
    Response("00000000000000000000000000000000", 0x0430, "000110"),
    #    Response("00000000000000000000000000000000", 0x0430, "000120"),
    #    Response("00000000000000000000000000000000", 0x0430, "000140"),
    #    Response("00000000000000000000000000000000", 0x0430, "000180"),
    #    Response("00000000000000000000000000000000", 0x0430, "010101"),
    #    Response("00000000000000000000000000000000", 0x0430, "010102"),
    Response("00000000000000000000000000000000", 0x0430, "0001FF"),
    Response("00000000000000000000000000000000", 0x0430, "010103"),
    Response("08000000000000000000000000000000", 0x0450, "01FF"),
    Response("08000000000000000000000000000000", 0x0450, "02FF"),
    Response("08000000000000000000000000000000", 0x0450, "03FF"),
    Response("00040000000000000000000000000000", 0x0450, "04FF"),
    Response("5C020000000000000000000000000000", 0x0450, "05FF"),
    Response("01000000000000000000000000000000", 0x0460, "00FF"),
    Response("01000000000000000000000000000000", 0x0470, "00FF"),
    Response("01", 0x0420, "00010101"),  # set index 1
    Response("00", 0x0420, "00010100"),  # unset index 1
    Response("01", 0x0420, "00011010"),  # set index 4
    Response("00", 0x0420, "00011000"),  # unset index 4
    Response("01", 0x0440, "00010101"),  # divert index 1
    Response("00", 0x0440, "00010100"),  # undivert index 1
    Response("000080FF", 0x0480, "000080FF"),  # write param 0
    Response("000180FF", 0x0480, "000180FF"),  # write param 0
]


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
