import logging

from typing import Optional

from solaar.i18n import _
from solaar.i18n import ngettext

STATUS_CHECK_MILLISECONDS = 500
PAIRING_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


class PairingModel:
    def __init__(self, receiver):
        self.receiver = receiver

    # def run_command_with_timeout(self, command, *args):
    #     GLib.timeout_add(STATUS_CHECK_MILLISECONDS, command, *args)

    def reset_pairing(self):
        self.receiver.reset_pairing()

    def prepare(self):
        if self.receiver.receiver_kind == "bolt":
            if self.receiver.discover(timeout=PAIRING_TIMEOUT_SECONDS):
                return True
            else:
                self.receiver.pairing.error = "discovery did not start"
                return False
        elif self.receiver.set_lock(False, timeout=PAIRING_TIMEOUT_SECONDS):
            return True
        else:
            self.receiver.pairing.error = "the pairing lock did not open"
            return False

    def create_page_title(self) -> str:
        return _("%(receiver_name)s: pair new device") % {"receiver_name": self.receiver.name}

    def create_page_text(self):
        receiver_kind = self.receiver.receiver_kind
        remaining_pairings = self.receiver.remaining_pairings()
        return _create_pairing_page_text(receiver_kind, remaining_pairings)

    def handle_finish(self):
        self.receiver.pairing.new_device = None
        if self.receiver.pairing.lock_open:
            if self.receiver.receiver_kind == "bolt":
                self.receiver.pair_device("cancel")
            else:
                self.receiver.set_lock()
        if self.receiver.pairing.discovering:
            self.receiver.discover(True)
        if not self.receiver.pairing.lock_open and not self.receiver.pairing.discovering:
            self.receiver.pairing.error = None


def _create_pairing_page_text(receiver_kind: str, remaining_pairings: Optional[int] = None) -> str:
    if receiver_kind == "bolt":
        text = _("Bolt receivers are only compatible with Bolt devices.")
        text += "\n\n"
        text += _("Press a pairing button or key until the pairing light flashes quickly.")
    else:
        if receiver_kind == "unifying":
            text = _("Unifying receivers are only compatible with Unifying devices.")
        else:
            text = _("Other receivers are only compatible with a few devices.")
        text += "\n\n"
        text += _("Turn on the device you want to pair.")
        text += _("The device must not be paired with a nearby powered-on receiver.")
        text += "\n"
        text += _("If the device is already turned on, turn it off and on again.")
    if remaining_pairings and remaining_pairings >= 0:
        text += (
            ngettext(
                "\n\nThis receiver has %d pairing remaining.",
                "\n\nThis receiver has %d pairings remaining.",
                remaining_pairings,
            )
            % remaining_pairings
        )
        text += _("\nCancelling at this point will not use up a pairing.")
    return text
