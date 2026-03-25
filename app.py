import threading
import time
import tkinter as tk
from tkinter import ttk

import pyautogui
import pyperclip
from pynput import keyboard, mouse

import config

KAKAO_YELLOW = "#FEE500"
KAKAO_YELLOW_DARK = "#E6CE00"


def _setup_styles(style: ttk.Style) -> None:
    style.theme_use("clam")
    style.configure(
        "Kakao.TButton",
        background=KAKAO_YELLOW,
        foreground="#000000",
        font=("맑은 고딕", 10, "bold"),
        padding=6,
    )
    style.map(
        "Kakao.TButton",
        background=[("active", KAKAO_YELLOW_DARK), ("disabled", "#D0D0D0")],
        foreground=[("disabled", "#888888")],
    )
    style.configure(
        "Header.TLabel",
        background=KAKAO_YELLOW,
        foreground="#000000",
        font=("맑은 고딕", 12, "bold"),
        padding=8,
    )
    style.configure("Status.TLabel", foreground="#555555", font=("맑은 고딕", 9))
    style.configure("Hint.TLabel", foreground="#888888", font=("맑은 고딕", 8))


class BasePage(ttk.Frame):
    """공통 레이아웃 및 동작을 담당하는 기반 페이지.

    하위 클래스는 _build_message_area()와 _start_send_thread()를 구현해야 한다.
    위젯 생성 순서를 보장하기 위해 __init__에서 _build_message_area()를 호출한다.
    """

    def __init__(self, parent, app, default_repeat, title_text):
        super().__init__(parent, padding=12)
        self.app = app
        self.result_x = 0
        self.result_y = 0
        self._mouse_listener = None

        # 헤더
        ttk.Label(self, text=title_text, style="Header.TLabel").pack(fill="x", pady=(0, 12))

        # 좌표 캡쳐
        self.capture_btn = ttk.Button(
            self,
            text="카톡 대화창 좌표 얻기",
            style="Kakao.TButton",
            command=self.enable_click_capture,
        )
        self.capture_btn.pack(pady=(0, 4))

        self.co_text = tk.StringVar(value=f"x : {self.result_x}    y : {self.result_y}")
        ttk.Entry(self, textvariable=self.co_text, width=30, state="readonly").pack(pady=(0, 12))

        # 메시지 영역 (하위 클래스에서 구현)
        self._build_message_area()

        # 반복 횟수
        ttk.Label(self, text="반복 횟수 (최소 1):").pack(anchor="w")
        vcmd = (self.register(self._validate_integer), "%P")
        self.repeat_entry = ttk.Entry(self, width=10, validate="key", validatecommand=vcmd)
        self.repeat_entry.insert(tk.END, str(default_repeat))
        self.repeat_entry.pack(anchor="w", pady=(0, 8))

        # 스페이스바 중단 안내
        ttk.Label(
            self,
            text="※ 전송 중 스페이스바를 누르면 즉시 중단됩니다.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        # 전송 버튼 (좌표 캡처 전까지 비활성)
        self.send_btn = ttk.Button(
            self,
            text="메시지 전송",
            style="Kakao.TButton",
            command=self._start_send_thread,
            state=tk.DISABLED,
        )
        self.send_btn.pack(pady=(0, 8))

        # 상태바
        self.status_var = tk.StringVar(value="대기 중")
        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

    def _build_message_area(self):
        raise NotImplementedError

    def _start_send_thread(self):
        raise NotImplementedError

    def _validate_integer(self, new_value):
        if new_value == "":
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False

    def update_coordinates(self, x, y):
        self.result_x = x
        self.result_y = y
        self.co_text.set(f"x : {x}    y : {y}")
        self.capture_btn.config(text="카톡 대화창 좌표 얻기")
        self.send_btn.config(state=tk.NORMAL)

    def on_click(self, x, y, button, pressed):
        if pressed:
            # 마우스 리스너는 별도 스레드에서 실행되므로 after()로 GUI 업데이트
            self.after(0, lambda: self.update_coordinates(x, y))
            return False

    def enable_click_capture(self):
        if self._mouse_listener is not None and self._mouse_listener.is_alive():
            return
        self.capture_btn.config(text="클릭 대기 중...")
        self._mouse_listener = mouse.Listener(on_click=self.on_click)
        self._mouse_listener.start()

    def get_repeat_count(self):
        try:
            val = int(self.repeat_entry.get())
            if val < 1:
                raise ValueError
            return val
        except ValueError:
            self._set_status("반복 횟수에 1 이상의 정수를 입력하세요.")
            return None

    def focus_chat_window(self):
        pyautogui.moveTo(self.result_x, self.result_y)
        pyautogui.click()
        time.sleep(config.FOCUS_DELAY)

    def _set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def _set_sending(self, is_sending):
        state = tk.DISABLED if is_sending else tk.NORMAL
        self.after(0, lambda: self.send_btn.config(state=state))


# 페이지 1: 단일 메시지 전송
class SingleMessagePage(BasePage):
    def __init__(self, parent, app):
        super().__init__(
            parent, app,
            default_repeat=config.DEFAULT_REPEAT_SINGLE,
            title_text="단일 메시지 전송",
        )

    def _build_message_area(self):
        ttk.Label(self, text="보낼 메시지:").pack(anchor="w")
        self.messages_text = tk.Text(self, width=50, height=8, relief="solid", borderwidth=1)
        self.messages_text.pack(fill="x", pady=(0, 10))

    def _start_send_thread(self):
        repeat_count = self.get_repeat_count()
        if repeat_count is None:
            return

        message = self.messages_text.get("1.0", "end-1c")
        if not message.strip():
            self._set_status("보낼 메시지를 입력하세요.")
            return

        self._set_sending(True)
        threading.Thread(
            target=self._send, args=(message, repeat_count), daemon=True
        ).start()

    def _send(self, message, repeat_count):
        self.focus_chat_window()
        pyperclip.copy(message)

        for i in range(repeat_count):
            if self.app.stop_macro:
                self.app.stop_macro = False
                self._set_status("중단됨")
                self._set_sending(False)
                return
            self._set_status(f"전송 중... ({i + 1}/{repeat_count})")
            pyautogui.hotkey("ctrl", "v", interval=config.HOTKEY_INTERVAL)
            pyautogui.press("enter")
            time.sleep(config.SEND_DELAY)

        self._set_status("완료")
        self._set_sending(False)


# 페이지 2: 다중 메시지 전송 (한 바퀴에 모든 메시지를 전송)
class MultiMessagePage(BasePage):
    def __init__(self, parent, app):
        super().__init__(
            parent, app,
            default_repeat=config.DEFAULT_REPEAT_MULTI,
            title_text="다중 메시지 전송",
        )

    def _build_message_area(self):
        ttk.Label(self, text="보낼 메시지 (줄바꿈으로 구분):").pack(anchor="w")
        self.messages_text = tk.Text(self, width=50, height=8, relief="solid", borderwidth=1)
        self.messages_text.pack(fill="x", pady=(0, 10))

    def _start_send_thread(self):
        repeat_count = self.get_repeat_count()
        if repeat_count is None:
            return

        messages = self.messages_text.get("1.0", "end-1c").splitlines()
        if not any(msg.strip() for msg in messages):
            self._set_status("보낼 메시지를 입력하세요.")
            return

        self._set_sending(True)
        threading.Thread(
            target=self._send, args=(messages, repeat_count), daemon=True
        ).start()

    def _send(self, messages, repeat_count):
        self.focus_chat_window()

        for i in range(repeat_count):
            if self.app.stop_macro:
                self.app.stop_macro = False
                self._set_status("중단됨")
                self._set_sending(False)
                return
            self._set_status(f"전송 중... ({i + 1}/{repeat_count})")
            for msg in messages:
                if msg.strip():
                    pyperclip.copy(msg)
                    pyautogui.hotkey("ctrl", "v", interval=config.HOTKEY_INTERVAL)
                    pyautogui.press("enter")
                    time.sleep(config.SEND_DELAY)

        self._set_status("완료")
        self._set_sending(False)


# 메인 애플리케이션 창
class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.WINDOW_TITLE)
        self.geometry(config.WINDOW_SIZE)

        _setup_styles(ttk.Style(self))

        self.stop_macro = False

        # 키보드 리스너: 스페이스바로 매크로 중단
        self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self._keyboard_listener.start()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        page1 = SingleMessagePage(notebook, app=self)
        page2 = MultiMessagePage(notebook, app=self)

        notebook.add(page1, text="단일 메시지 전송")
        notebook.add(page2, text="다중 메시지 전송")

    def _on_key_press(self, key):
        if key == keyboard.Key.space:
            self.stop_macro = True


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
