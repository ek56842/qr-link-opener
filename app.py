from __future__ import annotations

import ctypes
import json
import os
import sys
import webbrowser
import winreg
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPoint, QRect, Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from qr_utils import decode_qr_png, is_openable_url


APP_NAME = "QR 連結快速開啟"
APP_VERSION = "1.0.1"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "QRLinkOpener"
HOTKEY_ID = 1
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_Q = 0x51


class Settings:
    def __init__(self) -> None:
        appdata = Path(os.environ.get("APPDATA", Path.home())) / "QRLinkOpener"
        try:
            appdata.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Portable builds and locked-down environments may not permit
            # AppData writes. Keep a local fallback rather than failing startup.
            executable_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
            appdata = executable_dir / ".qr-link-opener-data"
            appdata.mkdir(parents=True, exist_ok=True)
        self.path = appdata / "settings.json"
        self.data = {"autostart": True}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                pass

    @property
    def autostart(self) -> bool:
        return bool(self.data.get("autostart", True))

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_autostart(self, enabled: bool) -> None:
        self.data["autostart"] = enabled
        self.save()
        command = startup_command()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, RUN_VALUE)
                    except FileNotFoundError:
                        pass
        except OSError as error:
            raise RuntimeError(f"無法更新開機啟動設定：{error}") from error


def startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    return f'"{Path(sys.executable).resolve()}" "{Path(__file__).resolve()}"'


def pixmap_to_png(pixmap: QPixmap) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(data)


def tray_icon() -> QIcon:
    """Create a small, dependency-free QR-like icon for the notification area."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("#ffffff"))
    painter = QPainter(pixmap)
    painter.setBrush(QColor("#1769aa"))
    painter.setPen(Qt.PenStyle.NoPen)
    for x, y in ((6, 6), (38, 6), (6, 38)):
        painter.drawRect(x, y, 20, 20)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(x + 5, y + 5, 10, 10)
        painter.setBrush(QColor("#1769aa"))
    for x, y in ((38, 38), (48, 38), (38, 48), (50, 50)):
        painter.drawRect(x, y, 7, 7)
    painter.end()
    return QIcon(pixmap)


def capture_virtual_desktop() -> tuple[QPixmap, QRect]:
    """Stitch all screens into a virtual-desktop pixmap before showing the overlay."""
    screens = QApplication.screens()
    geometry = screens[0].geometry()
    for screen in screens[1:]:
        geometry = geometry.united(screen.geometry())

    image = QPixmap(geometry.size())
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    for screen in screens:
        point = screen.geometry().topLeft() - geometry.topLeft()
        painter.drawPixmap(point, screen.grabWindow(0))
    painter.end()
    return image, geometry


class CaptureOverlay(QWidget):
    def __init__(self, screenshot: QPixmap, geometry: QRect, finished) -> None:
        super().__init__()
        self.screenshot = screenshot
        self.finished = finished
        self.start: QPoint | None = None
        self.end: QPoint | None = None
        self.setGeometry(geometry)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # Let Windows show the real desktop through the overlay; only the
        # painted layer is dimmed, like the Windows snipping interface.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def selection(self) -> QRect:
        if self.start is None or self.end is None:
            return QRect()
        return QRect(self.start, self.end).normalized()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 82))
        selected = self.selection()
        if not selected.isNull():
            # Clear only the selection to reveal the unmodified desktop.
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selected, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.fillRect(selected, QColor(255, 255, 255, 24))
            painter.setPen(QPen(QColor("#4fc3f7"), 2))
            painter.drawRect(selected)
        painter.setPen(QColor("white"))
        painter.drawText(18, 32, "拖曳框選一個 QR Code，按 Esc 取消")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.start = event.position().toPoint()
            self.end = self.start
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.start is not None:
            self.end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.start is not None:
            self.end = event.position().toPoint()
            selected = self.selection()
            self.close()
            if selected.width() >= 8 and selected.height() >= 8:
                self.finished(self.screenshot.copy(selected))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class ResultDialog(QDialog):
    def __init__(self, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.value = value
        self.setWindowTitle(APP_NAME)
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        is_url = is_openable_url(value)
        heading = "已讀取網址，請確認後再開啟" if is_url else "已讀取 QR Code 內容"
        layout.addWidget(QLabel(heading))
        content = QLabel(value)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content.setStyleSheet("padding: 10px; background: #f3f5f7; border-radius: 6px;")
        layout.addWidget(content)
        if not is_url:
            layout.addWidget(QLabel("此內容不是網址，工具不會嘗試執行或連線。"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy_button = QPushButton("複製")
        copy_button.clicked.connect(self.copy_value)
        buttons.addButton(copy_button, QDialogButtonBox.ButtonRole.ActionRole)
        if is_url:
            open_button = QPushButton("開啟連結")
            open_button.setDefault(True)
            open_button.clicked.connect(self.open_value)
            buttons.addButton(open_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def copy_value(self) -> None:
        QApplication.clipboard().setText(self.value)

    def open_value(self) -> None:
        # QDesktopServices delegates line:// and web URLs to Windows defaults.
        if not QDesktopServices.openUrl(QUrl(self.value)):
            webbrowser.open(self.value)
        self.accept()


class HotkeyListener(QWidget):
    """Receive WM_HOTKEY using a native Qt window."""
    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.winId()

    def nativeEvent(self, event_type, message):
        if bytes(event_type) == b"windows_generic_MSG":
            class MSG(ctypes.Structure):
                _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT), ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM), ("time", wintypes.DWORD), ("pt", wintypes.POINT)]
            msg = MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.callback()
                return True, 0
        return super().nativeEvent(event_type, message)


class QRLinkOpener:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.settings = Settings()
        self.overlay: CaptureOverlay | None = None
        self.listener = HotkeyListener(self.start_capture)
        self.listener.hide()
        self.tray = QSystemTrayIcon(tray_icon(), app)
        self.tray.setToolTip(APP_NAME)
        self.menu = QMenu()
        scan = QAction("立即掃描 QR Code", self.menu)
        scan.triggered.connect(self.start_capture)
        self.menu.addAction(scan)
        self.autostart_action = QAction("開機自動啟動", self.menu, checkable=True)
        self.autostart_action.setChecked(self.settings.autostart)
        self.autostart_action.triggered.connect(self.update_autostart)
        self.menu.addAction(self.autostart_action)
        self.menu.addSeparator()
        quit_action = QAction("結束程式", self.menu)
        quit_action.triggered.connect(self.quit)
        self.menu.addAction(quit_action)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(lambda reason: self.start_capture() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()
        self.register_hotkey()
        if self.settings.autostart:
            try:
                self.settings.set_autostart(True)
            except RuntimeError as error:
                self.tray.showMessage(APP_NAME, str(error), QSystemTrayIcon.MessageIcon.Warning)

    def register_hotkey(self) -> None:
        success = ctypes.windll.user32.RegisterHotKey(int(self.listener.winId()), HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_Q)
        if not success:
            self.tray.showMessage(APP_NAME, "Ctrl + Shift + Q 已被其他程式使用；請從通知區選單選擇「立即掃描 QR Code」。", QSystemTrayIcon.MessageIcon.Warning, 9000)

    def update_autostart(self, checked: bool) -> None:
        try:
            self.settings.set_autostart(checked)
        except RuntimeError as error:
            self.autostart_action.setChecked(not checked)
            QMessageBox.warning(None, APP_NAME, str(error))

    def start_capture(self) -> None:
        if self.overlay is not None and self.overlay.isVisible():
            return
        screenshot, geometry = capture_virtual_desktop()
        self.overlay = CaptureOverlay(screenshot, geometry, self.decode_selection)
        self.overlay.show()
        self.overlay.activateWindow()
        self.overlay.setFocus()

    def decode_selection(self, pixmap: QPixmap) -> None:
        values = decode_qr_png(pixmap_to_png(pixmap))
        if len(values) == 0:
            self.tray.showMessage(APP_NAME, "找不到 QR Code，請重新框選。", QSystemTrayIcon.MessageIcon.Information)
        elif len(values) > 1:
            self.tray.showMessage(APP_NAME, "偵測到多個 QR Code，請一次只框選一個。", QSystemTrayIcon.MessageIcon.Warning)
        else:
            ResultDialog(values[0]).exec()

    def quit(self) -> None:
        ctypes.windll.user32.UnregisterHotKey(int(self.listener.winId()), HOTKEY_ID)
        self.tray.hide()
        self.app.quit()


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("此工具僅支援 Windows。")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # Keep the controller alive for the entire Qt event loop; otherwise Python
    # can collect the tray icon and hotkey listener immediately after startup.
    controller = QRLinkOpener(app)
    app.controller = controller
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
