## Copyright (C) Solaar Contributors
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program; if not, write to the Free Software Foundation, Inc.,
## 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import annotations

import logging
import typing

from typing import Optional

from solaar.i18n import _
from solaar.i18n import ngettext

if typing.TYPE_CHECKING:
    from logitech_receiver.receiver import Receiver

STATUS_CHECK_MILLISECONDS = 500
PAIRING_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


class PairingModel:
    def __init__(self, receiver: Receiver):
        self.receiver = receiver

    def reset_pairing(self) -> None:
        self.receiver.reset_pairing()

    def prepare(self) -> bool:
        if self.receiver.receiver_kind == "bolt":
            if self.receiver.discover(timeout=PAIRING_TIMEOUT_SECONDS):
                return True
            else:
                self.receiver.pairing.error = "discovery did not start"
                return False
        elif self.receiver.set_lock(False, timeout=PAIRING_TIMEOUT_SECONDS):
            return True
        self.receiver.pairing.error = "the pairing lock did not open"
        return False

    def create_page_title(self) -> str:
        return _("%(receiver_name)s: pair new device") % {"receiver_name": self.receiver.name}

    def create_page_text(self) -> str:
        receiver_kind = self.receiver.receiver_kind
        remaining_pairings = self.receiver.remaining_pairings()
        return _create_pairing_page_text(receiver_kind, remaining_pairings)

    def handle_finish(self) -> None:
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
