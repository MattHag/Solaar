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

from gi.repository import GLib

from solaar.ui.pairing.model import PairingModel

if typing.TYPE_CHECKING:
    from solaar.ui.pairing.view import PairingView

logger = logging.getLogger(__name__)

STATUS_CHECK_MILLISECONDS = 500

# _hidpp10_constants.DEVICE_KIND.keyboard = 0x01
DEVICE_KIND_KEYBOARD = 0x01


class Presenter:
    def __init__(self, model: PairingModel, view: PairingView) -> None:
        self.model = model
        self.view = view

    def run(self) -> None:
        self.model.reset_pairing()  # clear out any information on previous pairing

        title = self.model.create_page_title()
        text = self.model.create_page_text()
        ready_for_pairing = self.model.prepare()

        self.view.init_ui(self, ready_for_pairing, title, text)

        if ready_for_pairing:
            GLib.timeout_add(STATUS_CHECK_MILLISECONDS, self.check_lock_state, self.model.receiver)

        self.view.mainloop()

    def check_lock_state(self, receiver, count=2):
        if not self.view.is_drawable():
            # if logger.isEnabledFor(logging.DEBUG):
            #     logger.debug("assistant %s destroyed, bailing out", assistant)
            return False
        return self._check_lock_state(receiver, count, self.check_lock_state)

    def _check_lock_state(self, receiver, count, check_lock_state_func):
        if receiver.pairing.error:
            self.view.pairing_failed(receiver, receiver.pairing.error)
            return False
        elif receiver.pairing.new_device:
            receiver.remaining_pairings(False)  # Update remaining pairings
            self.view.pairing_succeeded(receiver, receiver.pairing.new_device)
            return False
        elif not receiver.pairing.lock_open and not receiver.pairing.discovering:
            if count > 0:
                # the actual device notification may arrive later so have a little patience
                GLib.timeout_add(STATUS_CHECK_MILLISECONDS, check_lock_state_func, receiver, count - 1)
                # self.model.run_command_with_timeout(check_lock_state_func, receiver, count - 1)
            else:
                self.view.pairing_failed(receiver, "failed to open pairing lock")
            return False
        elif receiver.pairing.lock_open and receiver.pairing.device_passkey:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("%s show passkey: %s", receiver, receiver.pairing.device_passkey)
            device_name = receiver.pairing.device_name
            authentication = receiver.pairing.device_authentication
            receiver_name = receiver.name
            passkey = receiver.pairing.device_passkey
            self.view.show_passcode(device_name, authentication, receiver_name, passkey)
            return True
        elif receiver.pairing.discovering and receiver.pairing.device_address and receiver.pairing.device_name:
            add = receiver.pairing.device_address
            ent = 20 if receiver.pairing.device_kind == DEVICE_KIND_KEYBOARD else 10
            if receiver.pair_device(address=add, authentication=receiver.pairing.device_authentication, entropy=ent):
                return True
            else:
                self.view.pairing_failed(receiver, "failed to open pairing lock")
                return False
        return True

    def handle_finish(self, _assistant):
        self.view.finish_destroy_assistant()
        self.model.handle_finish()
