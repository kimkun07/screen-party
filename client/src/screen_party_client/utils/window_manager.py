"""Windows window management using pywin32"""

import platform
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WindowInfo:
    """Window information"""

    handle: int  # hwnd on Windows
    title: str  # Window title
    process_name: str  # Process name (e.g., "notepad.exe")
    x: int  # Position
    y: int
    width: int  # Size
    height: int

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """Returns (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)


class WindowManager:
    """
    Windows window manager using pywin32.

    Note: This class only works on Windows.
    """

    def __init__(self):
        """Initialize window manager"""
        if platform.system() != "Windows":
            raise NotImplementedError(
                "WindowManager is only supported on Windows. "
                "Current platform: " + platform.system()
            )

        # Import pywin32 modules (only available on Windows)
        try:
            import win32gui  # noqa: F401
            import win32process  # noqa: F401

            self.win32gui = win32gui
            self.win32process = win32process
        except ImportError as e:
            raise ImportError(
                "pywin32 is required for WindowManager. "
                "Please install: pip install pywin32"
            ) from e

    def get_window_list(self) -> List[WindowInfo]:
        """Get list of all visible windows"""
        windows = []

        def enum_callback(hwnd, results):
            """Callback for EnumWindows"""
            # Skip invisible windows
            if not self.win32gui.IsWindowVisible(hwnd):
                return

            # Skip windows without title
            title = self.win32gui.GetWindowText(hwnd)
            if not title:
                return

            # Get window position and size
            try:
                rect = self.win32gui.GetWindowRect(hwnd)
                x, y, right, bottom = rect
                width = right - x
                height = bottom - y

                # Skip very small windows (likely system windows)
                if width < 100 or height < 100:
                    return

                # Get process name
                _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
                try:
                    import psutil

                    process = psutil.Process(pid)
                    process_name = process.name()
                except Exception:
                    process_name = "Unknown"

                window_info = WindowInfo(
                    handle=hwnd,
                    title=title,
                    process_name=process_name,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                )
                results.append(window_info)
            except Exception:
                # Skip windows with errors
                pass

        self.win32gui.EnumWindows(enum_callback, windows)
        return windows

    def get_window_info(self, handle: int) -> Optional[WindowInfo]:
        """Get information about a specific window"""
        try:
            if not self.win32gui.IsWindow(handle):
                return None

            title = self.win32gui.GetWindowText(handle)
            rect = self.win32gui.GetWindowRect(handle)
            x, y, right, bottom = rect

            _, pid = self.win32process.GetWindowThreadProcessId(handle)
            try:
                import psutil

                process = psutil.Process(pid)
                process_name = process.name()
            except Exception:
                process_name = "Unknown"

            return WindowInfo(
                handle=handle,
                title=title,
                process_name=process_name,
                x=x,
                y=y,
                width=right - x,
                height=bottom - y,
            )
        except Exception:
            return None

    def is_window_minimized(self, handle: int) -> bool:
        """Check if window is minimized"""
        try:
            return self.win32gui.IsIconic(handle)
        except Exception:
            return False

    def is_window_visible(self, handle: int) -> bool:
        """Check if window is visible"""
        try:
            return self.win32gui.IsWindowVisible(handle)
        except Exception:
            return False

    def window_exists(self, handle: int) -> bool:
        """Check if window exists"""
        try:
            return self.win32gui.IsWindow(handle)
        except Exception:
            return False
