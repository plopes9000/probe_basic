import os

import linuxcnc

# Workarround for nvidia propietary drivers

import ctypes
import ctypes.util

ctypes.CDLL(ctypes.util.find_library("GL"), mode=ctypes.RTLD_GLOBAL)

# end of Workarround


from qtpy.QtCore import Property, Signal, Slot, QUrl, QTimer
from qtpy.QtQuickWidgets import QQuickWidget

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)
STATUS = getPlugin('status')
TOOLTABLE = getPlugin('tooltable')
IN_DESIGNER = os.getenv('DESIGNER', False)
WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))
INIFILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))

class DynATC(QQuickWidget):
    pocketSig = Signal(int, int, int, arguments=['first_pocket', 'first_pocket_pos', 'pockets'])
    rotateSig = Signal(int, int, arguments=['steps', 'direction'])

    showToolSig = Signal(int, int, arguments=['pocket', 'tool_num'])
    hideToolSig = Signal(int, arguments=['pocket'])

    homeMsgSig = Signal(str, arguments=["message"])

    def __init__(self, parent=None):
        super(DynATC, self).__init__(parent)

        if IN_DESIGNER:
            return

        self._IniFilePrefix = ""
        self.atc_position = 0
        self.pocket = 1
        self.home = 0
        self.homing = 0

        self.engine().rootContext().setContextProperty("atc_spiner", self)
        qml_path = os.path.join(WIDGET_PATH, "atc.qml")
        url = QUrl.fromLocalFile(qml_path)

        self.setSource(url)  # Fixme fails on qtdesigner

        self.tool_table = None
        self.status_tool_table = None
        self.pockets = dict()
        self.tools = None
        self.pocket_slots = 0
        self.start_pocket = 1
        self.start_pocket_pos = 90

        self.iniFilePrefix = ""

    def hideEvent(self, *args, **kwargs):
        pass  # hack to prevent animation glitch when we are on another tab FIXME

    def load_tools(self):
        # print("load_tools")
        for i in range(1, self.pocket_slots+1):
            self.hideToolSig.emit(i)

        for pocket, tool in self.pockets.items():
            if tool != 0:
                self.showToolSig.emit(pocket, tool)
            else:
                self.hideToolSig.emit(pocket)

    def store_tool(self, pocket, tool_num):
        self.pockets[pocket] = tool_num
        #
        # print(type(pocket), pocket)
        # print(type(tool_num), tool_num)
        if tool_num != 0:
            # print("show tool {} at pocket {}".format(tool_num, pocket))
            self.showToolSig.emit(pocket, tool_num)
        else:
            # print("Hide tool at pocket {}".format(pocket))
            self.hideToolSig.emit(pocket)

    def atc_message(self, msg=""):
        self.homeMsgSig.emit(msg)

    def rotate(self, steps, direction):
        if direction == "cw":
            self.rotateSig.emit(steps, 1)
        elif direction == "ccw":
            self.rotateSig.emit(steps, -1)

    # ini file prefix
    @Property(str)
    def iniFilePrefix(self):
        return self._IniFilePrefix
    @iniFilePrefix.setter
    def iniFilePrefix(self, _IniFilePrefix):
        self._IniFilePrefix = _IniFilePrefix or ""
        self.pocket_slots = int(INIFILE.find("ATC", self._IniFilePrefix + "POCKETS") or 12)
        self.start_pocket = int(INIFILE.find("ATC", self._IniFilePrefix + "START_POCKET") or 1)
        self.start_pocket_pos = int(INIFILE.find("ATC", self._IniFilePrefix + "START_POCKET_POS") or 90)
        self.pocketSig.emit(self.start_pocket, self.start_pocket_pos, self.pocket_slots)
        for pocket in range(self.start_pocket, self.start_pocket+self.pocket_slots):
            self.hideToolSig.emit(pocket)


