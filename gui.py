import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time

from hrm_service import HeartRateMonitor


class HeartRateApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Garmin HRM-Pro Plus")
        self.root.configure(bg="#000000")

        # Полноэкранный режим
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", self._exit_fullscreen)

        # Инициализация мониторинга пульса
        self.hrm = HeartRateMonitor(
            device_name_substring="HRM-Pro Plus",
            device_address="FB:6F:43:CE:9A:6A",
        )
        self.hrm.start()

        self._build_ui()
        self._schedule_update()

    def _exit_fullscreen(self, event=None) -> None:  # noqa: D401, ANN001
        """Выход из полноэкранного режима по Esc (на случай отладки)."""
        self.root.attributes("-fullscreen", False)

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self.root, bg="#000000")
        main_frame.pack(expand=True, fill="both")

        # Верхняя строка статуса
        status_frame = tk.Frame(main_frame, bg="#000000")
        status_frame.pack(side="top", pady=20)

        self.status_dot = tk.Canvas(status_frame, width=14, height=14, bg="#000000", highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8))
        self.dot_id = self.status_dot.create_oval(2, 2, 12, 12, fill="#444444", outline="#444444")

        self.status_label = tk.Label(
            status_frame,
            text="Поиск HRM-Pro Plus…",
            fg="#cccccc",
            bg="#000000",
            font=("Segoe UI", 16),
        )
        self.status_label.pack(side="left")

        # Центр — крупный пульс
        center_frame = tk.Frame(main_frame, bg="#000000")
        center_frame.pack(expand=True)

        self.hr_label = tk.Label(
            center_frame,
            text="ПУЛЬС",
            fg="#aaaaaa",
            bg="#000000",
            font=("Segoe UI", 18),
        )
        self.hr_label.pack(pady=(0, 10))

        self.hr_value_label = tk.Label(
            center_frame,
            text="--",
            fg="#00ff55",
            bg="#000000",
            font=("Segoe UI", 120, "bold"),
        )
        self.hr_value_label.pack()

        self.hr_unit_label = tk.Label(
            center_frame,
            text="BPM",
            fg="#888888",
            bg="#000000",
            font=("Segoe UI", 22),
        )
        self.hr_unit_label.pack(pady=(10, 0))

        # Низ — кнопка выключения
        bottom_frame = tk.Frame(main_frame, bg="#000000")
        bottom_frame.pack(side="bottom", pady=30)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Shutdown.TButton",
            font=("Segoe UI", 18, "bold"),
            padding=10,
            foreground="#ffffff",
            background="#b00020",
        )

        self.shutdown_button = ttk.Button(
            bottom_frame,
            text="ВЫКЛЮЧИТЬ PI",
            style="Shutdown.TButton",
            command=self._on_shutdown_click,
        )
        self.shutdown_button.pack()

    def _set_status(self, status: str) -> None:
        if status == "connected":
            color = "#00ff66"
            text = "Подключено к HRM-Pro Plus"
        elif status == "disconnected":
            color = "#ffaa00"
            text = "Нет сигнала · наденьте ремень"
        else:
            color = "#00b7ff"
            text = "Поиск HRM-Pro Plus…"

        self.status_dot.itemconfig(self.dot_id, fill=color, outline=color)
        self.status_label.config(text=text)

    def _schedule_update(self) -> None:
        self._update_values()
        self.root.after(1000, self._schedule_update)

    def _update_values(self) -> None:
        hr = self.hrm.get_heart_rate()
        status = self.hrm.get_status()

        if hr > 0:
            self.hr_value_label.config(text=str(hr))
        else:
            self.hr_value_label.config(text="--")

        self._set_status(status)

    def _on_shutdown_click(self) -> None:
        # Выполняем выключение в отдельном потоке, чтобы не подвесить UI
        def _shutdown():
            subprocess.Popen(["sudo", "/sbin/shutdown", "-h", "now"])

        threading.Thread(target=_shutdown, daemon=True).start()


def main() -> None:
    root = tk.Tk()
    app = HeartRateApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

