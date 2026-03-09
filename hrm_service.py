import asyncio
import threading
import time
from typing import Optional

from bleak import BleakClient, BleakScanner


HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


class HeartRateMonitor:
    """
    Простой сервис для чтения пульса с Garmin HRM-Pro по BLE.
    Запускается в отдельном потоке и пытается переподключаться при обрыве.
    """

    def __init__(self, device_name_substring: str = "HRM-Pro"):
        self.device_name_substring = device_name_substring
        self.current_hr: int = 0
        self.connected: bool = False
        self.last_update_ts: float = 0.0
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        finally:
            self._loop.close()

    async def _main(self) -> None:
        while not self._stop_event.is_set():
            try:
                device = await self._find_device()
                if not device:
                    print("Garmin HRM-Pro не найден, повторный поиск через 5 секунд...")
                    await asyncio.sleep(5)
                    continue

                print(f"Подключение к устройству: {device.name} ({device.address})")
                async with BleakClient(device) as client:
                    self.connected = True
                    print("Подключение установлено")

                    def hr_callback(_, data: bytearray) -> None:
                        # Стандартный формат Heart Rate Measurement
                        if not data:
                            return
                        flags = data[0]
                        hr_value_16bit = flags & 0x01
                        if hr_value_16bit:
                            value = int.from_bytes(data[1:3], byteorder="little")
                        else:
                            value = data[1]
                        self.current_hr = int(value)
                        self.last_update_ts = time.time()

                    await client.start_notify( HEART_RATE_CHAR_UUID, hr_callback)

                    # Ждём, пока соединение активно или пока не попросили остановиться
                    while not self._stop_event.is_set() and client.is_connected:
                        await asyncio.sleep(1)

            except Exception as e:  # noqa: BLE001
                print(f"Ошибка HRM-сервиса: {e}")
                # #region agent log
                try:
                    import json

                    log_entry = {
                        "sessionId": "5c9330",
                        "runId": "run1",
                        "hypothesisId": "H1",
                        "location": "hrm_service.py:_main",
                        "message": "HRM service exception",
                        "data": {"error": str(e)},
                        "timestamp": int(time.time() * 1000),
                    }
                    with open("debug-5c9330.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                except Exception:
                    # не ломаем сервис, если логирование не удалось
                    pass
                # #endregion agent log
            finally:
                self.connected = False
                await asyncio.sleep(5)

    async def _find_device(self):
        print("Поиск пульсометра Garmin HRM-Pro...")
        devices = await BleakScanner.discover()
        for d in devices:
            name = (d.name or "").lower()
            if self.device_name_substring.lower() in name or "garmin" in name:
                print(f"Найдено устройство: {d}")
                return d
        return None

    def get_heart_rate(self) -> int:
        # Если давно не было обновлений, считаем, что данных нет
        if self.last_update_ts and (time.time() - self.last_update_ts > 5):
            return 0
        return self.current_hr

    def get_status(self) -> str:
        if self.connected:
            return "connected"
        if self.last_update_ts == 0:
            return "searching"
        return "disconnected"

