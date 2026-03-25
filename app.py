import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import pyperclip
import time
from pynput import mouse, keyboard

# 전역 변수: 매크로 중단 여부 체크
stop_macro = False


def on_key_press(key):
    global stop_macro
    if key == keyboard.Key.space:
        stop_macro = True


# 전역 키 리스너 시작 (백그라운드에서 실행됨)
keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()


# 페이지 1: 단일 메시지 전송 기능
class SingleMessagePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.result_x = 0
        self.result_y = 0

        # 좌표 캡쳐 버튼과 결과 표시
        self.button1 = tk.Button(
            self, text="카톡 대화창 좌표 얻기", command=self.enable_click_capture
        )
        self.button1.pack(pady=10)

        self.coText = tk.StringVar(value=f"x : {self.result_x}    y : {self.result_y}")
        self.coordEntry = tk.Entry(self, textvariable=self.coText, width=30)
        self.coordEntry.pack(pady=10)

        # 보낼 메시지 입력 (단일 메시지)
        self.messageLabel = tk.Label(self, text="보낼 메시지:")
        self.messageLabel.pack(pady=(10, 0))
        self.messagesText = tk.Text(self, width=50, height=10)
        self.messagesText.pack(pady=(0, 10))

        # 반복 횟수 입력
        self.repeatLabel = tk.Label(self, text="반복 횟수:")
        self.repeatLabel.pack(pady=(10, 0))
        self.vcmd = (self.register(self.validate_integer), "%P")
        self.repeatEntry = tk.Entry(
            self, width=10, validate="key", validatecommand=self.vcmd
        )
        self.repeatEntry.insert(tk.END, "2")
        self.repeatEntry.pack(pady=(0, 10))

        # 시작 버튼
        self.sendButton = tk.Button(
            self,
            text="메시지 전송",
            command=self.send_single_message,
            state=tk.DISABLED,
        )
        self.sendButton.pack(pady=10)

    def validate_integer(self, new_value):
        """반복횟수가 정수인지 확인"""
        if new_value == "":
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False

    def update_coordinates(self, x, y):
        """클릭된 좌표 업데이트 및 시작 버튼 활성화"""
        self.result_x = x
        self.result_y = y
        self.coText.set(f"x : {x}    y : {y}")
        self.sendButton.config(state=tk.NORMAL)

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.update_coordinates(x, y)
            return False

    def enable_click_capture(self):
        listener = mouse.Listener(on_click=self.on_click)
        listener.start()

    def send_single_message(self):
        global stop_macro
        try:
            repeat_count = int(self.repeatEntry.get())
        except ValueError:
            messagebox.showerror("오류", "반복 횟수에 올바른 정수를 입력하세요.")
            return

        message = self.messagesText.get("1.0", "end-1c")
        if not message:
            messagebox.showerror("오류", "보낼 메시지를 입력하세요.")
            return

        # 지정된 좌표로 이동 후 클릭하여 대화창 선택
        pyautogui.moveTo(self.result_x, self.result_y)
        pyautogui.click()
        time.sleep(0.1)

        pyperclip.copy(message)

        for _ in range(repeat_count):
            if stop_macro:
                stop_macro = False  # 중단 후 초기화
                return
            pyautogui.hotkey("ctrl", "v", interval=0.01)
            pyautogui.press("enter")
            time.sleep(0.1)  # 각 전송 사이에 잠깐의 지연


# 페이지 2: 다중 메시지 전송 기능 (한 바퀴에 모든 메시지를 전송)
class MultiMessagePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.result_x = 0
        self.result_y = 0

        # 좌표 캡쳐 버튼과 결과 표시
        self.button1 = tk.Button(
            self, text="카톡 대화창 좌표 얻기", command=self.enable_click_capture
        )
        self.button1.pack(pady=10)

        self.coText = tk.StringVar(value=f"x : {self.result_x}    y : {self.result_y}")
        self.coordEntry = tk.Entry(self, textvariable=self.coText, width=30)
        self.coordEntry.pack(pady=10)

        # 보낼 메시지들 입력 (다중 메시지, 줄바꿈으로 구분)
        self.messagesLabel = tk.Label(self, text="보낼 메시지 (줄바꿈으로 구분):")
        self.messagesLabel.pack(pady=(10, 0))
        self.messagesText = tk.Text(self, width=50, height=10)
        self.messagesText.pack(pady=(0, 10))

        # 반복 횟수 입력 (한 바퀴당 모든 메시지를 전송)
        self.repeatLabel = tk.Label(self, text="반복 횟수:")
        self.repeatLabel.pack(pady=(10, 0))
        self.vcmd = (self.register(self.validate_integer), "%P")
        self.repeatEntry = tk.Entry(
            self, width=10, validate="key", validatecommand=self.vcmd
        )
        self.repeatEntry.insert(tk.END, "1")
        self.repeatEntry.pack(pady=(0, 10))

        # 시작 버튼
        self.sendButton = tk.Button(
            self,
            text="메시지 전송",
            command=self.send_multi_messages,
            state=tk.DISABLED,
        )
        self.sendButton.pack(pady=10)

    def validate_integer(self, new_value):
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
        self.coText.set(f"x : {x}    y : {y}")
        self.sendButton.config(state=tk.NORMAL)

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.update_coordinates(x, y)
            return False

    def enable_click_capture(self):
        listener = mouse.Listener(on_click=self.on_click)
        listener.start()

    def send_multi_messages(self):
        global stop_macro
        try:
            repeat_count = int(self.repeatEntry.get())
        except ValueError:
            messagebox.showerror("오류", "반복 횟수에 올바른 정수를 입력하세요.")
            return

        messages = self.messagesText.get("1.0", "end-1c").splitlines()
        if not any(msg.strip() for msg in messages):
            messagebox.showerror("오류", "보낼 메시지를 입력하세요.")
            return

        pyautogui.moveTo(self.result_x, self.result_y)
        pyautogui.click()
        time.sleep(0.1)

        for _ in range(repeat_count):
            if stop_macro:
                stop_macro = False
                return
            for msg in messages:
                if msg.strip():
                    pyperclip.copy(msg)
                    pyautogui.hotkey("ctrl", "v", interval=0.01)
                    pyautogui.press("enter")
                    time.sleep(0.1)


# 메인 애플리케이션 창
class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("카톡 매크로 & 메시지 전송")
        self.geometry("800x700")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        page1 = SingleMessagePage(notebook)
        page2 = MultiMessagePage(notebook)

        notebook.add(page1, text="단일 메시지 전송")
        notebook.add(page2, text="다중 메시지 전송")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
