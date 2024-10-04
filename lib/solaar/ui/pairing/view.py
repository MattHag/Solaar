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

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk

from solaar.i18n import _
from solaar.ui import icons as _icons

if typing.TYPE_CHECKING:
    from solaar.ui.pairing.presenter import Presenter

logger = logging.getLogger(__name__)

STATUS_CHECK_MILLISECONDS = 500


class PairingView:
    def __init__(self, window: Gtk.Window) -> None:
        self.window = window
        self.assistant: typing.Union[Gtk.Assistant, None] = None

    def init_ui(self, presenter: Presenter, ready_for_pairing: bool, page_title: str, page_text: str) -> None:
        self.assistant = Gtk.Assistant()
        self.assistant.set_title(page_title)
        self.assistant.set_icon_name("list-add")
        self.assistant.set_size_request(400, 240)
        self.assistant.set_resizable(False)
        self.assistant.set_role("pair-device")
        self.assistant.set_transient_for(self.window)
        self.assistant.set_destroy_with_parent(True)
        self.assistant.set_modal(True)
        self.assistant.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.assistant.set_position(Gtk.WindowPosition.CENTER)

        logger.debug("ready_for_pairing: %s", ready_for_pairing)
        if ready_for_pairing:
            page_intro = self.create_page(
                Gtk.AssistantPageType.PROGRESS, page_title, "preferences-desktop-peripherals", page_text
            )
            spinner = Gtk.Spinner()
            spinner.set_visible(True)
            spinner.start()
            page_intro.pack_end(spinner, True, True, 24)
            self.assistant.set_page_complete(page_intro, True)
        else:
            # error = receiver.pairing.error
            error = "discovery did not start"
            page_intro = self._create_failure_page(self.assistant, error)

        self.assistant.connect("cancel", presenter.handle_finish)
        self.assistant.connect("close", presenter.handle_finish)

    def show_passcode(self, device_name: str, authentication: int, receiver_name, passkey):
        intro_text = _("%(receiver_name)s: pair new device") % {"receiver_name": receiver_name}
        page_text = create_passcode_text(authentication, device_name, passkey)

        page = self.create_page(Gtk.AssistantPageType.PROGRESS, intro_text, "preferences-desktop-peripherals", page_text)
        self.assistant.set_page_complete(page, True)
        self.assistant.next_page()

    def pairing_failed(self, error, _assistant):
        self.assistant.remove_page(0)  # needed to reset the window size
        # if logger.isEnabledFor(logging.DEBUG):
        #     logger.debug("%s fail: %s", receiver, error)
        self._create_failure_page(self.assistant, error)

    def pairing_succeeded(self, device, _assistant):
        self.assistant.remove_page(0)  # needed to reset the window size
        # if logger.isEnabledFor(logging.DEBUG):
        #     logger.debug("%s success: %s", receiver, device)
        self._create_success_page(self.assistant, device)

    def _create_success_page(self, assistant, device):
        def _check_encrypted(device, assistant, hbox):
            if assistant.is_drawable() and device.link_encrypted is False:
                hbox.pack_start(Gtk.Image.new_from_icon_name("security-low", Gtk.IconSize.MENU), False, False, 0)
                hbox.pack_start(Gtk.Label(label=_("The wireless link is not encrypted")), False, False, 0)
                hbox.show_all()
            return False

        page = self.create_page(Gtk.AssistantPageType.SUMMARY)
        header = Gtk.Label(label=_("Found a new device:"))
        page.pack_start(header, False, False, 0)
        device_icon = Gtk.Image()
        icon_name = _icons.device_icon_name(device.name, device.kind)
        device_icon.set_from_icon_name(icon_name, _icons.LARGE_SIZE)
        page.pack_start(device_icon, True, True, 0)
        device_label = Gtk.Label()
        device_label.set_markup(f"<b>{device.name}</b>")
        page.pack_start(device_label, True, True, 0)
        hbox = Gtk.HBox(homogeneous=False, spacing=8)
        hbox.pack_start(Gtk.Label(label=" "), False, False, 0)
        hbox.set_property("expand", False)
        hbox.set_property("halign", Gtk.Align.CENTER)
        page.pack_start(hbox, False, False, 0)
        GLib.timeout_add(
            STATUS_CHECK_MILLISECONDS, _check_encrypted, device, assistant, hbox
        )  # wait a bit to check link status
        page.show_all()
        assistant.next_page()
        assistant.commit()

    def _create_failure_page(self, assistant, error):
        header = _("Pairing failed") + ": " + _(str(error)) + "."
        if "timeout" in str(error):
            text = _("Make sure your device is within range, and has a decent battery charge.")
        elif str(error) == "device not supported":
            text = _("A new device was detected, but it is not compatible with this receiver.")
        elif "many" in str(error):
            text = _("More paired devices than receiver can support.")
        else:
            text = _("No further details are available about the error.")
        self.create_page(Gtk.AssistantPageType.SUMMARY, header, "dialog-error", text)
        assistant.next_page()
        assistant.commit()

    def finish_destroy_assistant(self):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("finish %s", self.assistant)
        self.assistant.destroy()

    def create_page(self, kind, header=None, icon_name=None, text=None):
        p = Gtk.VBox(homogeneous=False, spacing=8)
        self.assistant.append_page(p)
        self.assistant.set_page_type(p, kind)
        if header:
            item = Gtk.HBox(homogeneous=False, spacing=16)
            p.pack_start(item, False, True, 0)
            label = Gtk.Label(label=header)
            label.set_line_wrap(True)
            item.pack_start(label, True, True, 0)
            if icon_name:
                icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
                item.pack_start(icon, False, False, 0)
        if text:
            label = Gtk.Label(label=text)
            label.set_line_wrap(True)
            p.pack_start(label, False, False, 0)
        p.show_all()
        return p

    def is_drawable(self) -> bool:
        return self.assistant.is_drawable()

    def mainloop(self) -> None:
        self.assistant.present()


def create_passcode_text(authentication: int, device_name: str, passkey: str) -> str:
    page_text = _("Enter passcode on %(name)s.") % {"name": device_name}
    page_text += "\n"
    if authentication & 0x01:
        page_text += _("Type %(passcode)s and then press the enter key.") % {"passcode": passkey}
    else:
        passcode = ", ".join([_("right") if bit == "1" else _("left") for bit in f"{int(passkey):010b}"])
        page_text += _("Press %(code)s\nand then press left and right buttons simultaneously.") % {"code": passcode}
    return page_text
