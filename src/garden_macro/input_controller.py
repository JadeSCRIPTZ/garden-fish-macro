from __future__ import annotations

import time
from typing import Callable

try:
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0
except ImportError:  # pragma: no cover
    pyautogui = None

from .config import KeyBindings, MacroConfig


SleepFn = Callable[[float], None]


class InputController:
    def __init__(self, keys: KeyBindings, sleep: SleepFn) -> None:
        self._keys = keys
        self._sleep = sleep
        self._held: set[str] = set()

    def press(self, key: str) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is not installed.")
        pyautogui.press(key)

    def hold(self, *keys: str) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is not installed.")
        for key in keys:
            if key not in self._held:
                pyautogui.keyDown(key)
                self._held.add(key)

    def release(self, *keys: str) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is not installed.")
        for key in keys:
            if key in self._held:
                pyautogui.keyUp(key)
                self._held.discard(key)

    def release_all(self) -> None:
        movement = {
            self._keys.attack,
            self._keys.right,
            self._keys.left,
            self._keys.forward,
        }
        for key in list(self._held):
            if key in movement:
                self.release(key)

    def release_everything(self) -> None:
        for key in list(self._held):
            self.release(key)

    def hold_farm_right(self) -> None:
        self.release_all()
        self.hold(self._keys.attack, self._keys.right)

    def hold_farm_left(self) -> None:
        self.release_all()
        self.hold(self._keys.attack, self._keys.left)

    def tap_forward(self, duration: float) -> None:
        self.release_all()
        self.hold(self._keys.forward)
        self._sleep(duration)
        self.release(self._keys.forward)

    def fish_collection_sequence(self, config: MacroConfig) -> None:
        keys = config.keys
        self.release_everything()
        self._sleep(0.1)

        self.press(keys.set_home)
        self._sleep(config.tp_delay)

        self.press(keys.tp_plot)
        self._sleep(config.tp_wait)

        pyautogui.mouseDown(button="right")
        try:
            self._sleep(config.vacuum_duration)
        finally:
            pyautogui.mouseUp(button="right")

        self._sleep(0.1)
        self.press(keys.go_home)
        self._sleep(config.home_wait)
