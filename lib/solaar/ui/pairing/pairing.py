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

import typing

from solaar.ui.pairing.model import PairingModel
from solaar.ui.pairing.presenter import Presenter
from solaar.ui.pairing.view import PairingView

if typing.TYPE_CHECKING:
    from gi.overrides import Gtk
    from logitech_receiver.receiver import Receiver


def show_window(
    window: Gtk.Window,
    receiver: Receiver,
    model: PairingModel = None,
    view: PairingView = None,
):
    if model is None:
        model = PairingModel(receiver)
    if view is None:
        view = PairingView(window)
    presenter = Presenter(model, view)
    presenter.run()
