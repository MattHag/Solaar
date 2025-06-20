from logitech_receiver.hidpp10_constants import Registers


class FakeReceiver:
    handle = 1
    isDevice = False

    def read_register(self, register, *args):
        return 0 if register == Registers.RECEIVER_INFO else b"\x01\x03"
