# Garmin HRM-Pro Kiosk для Raspberry Pi Zero 2 W

Простое приложение для Raspberry Pi, которое:

- **подключается к нагрудному пульсометру Garmin HRM-Pro по BLE**;
- **показывает пульс в браузере** в стиле экрана Garmin;
- **дает кнопку "Выключить Raspberry Pi"** прямо со страницы;
- автоматически **запускается при старте системы** в браузере Midori в полноэкранном режиме.

Разработано под **Raspberry Pi OS 32-bit**, Raspberry Pi Zero 2 W.

---

## 1. Установка (локально / перед заливкой на GitHub)

Проект уже содержит все нужные файлы:

- `app.py` — Flask-приложение (HTTP API + веб-страница);
- `hrm_service.py` — фоновый сервис BLE для чтения пульса с HRM-Pro;
- `templates/index.html` и `static/css/style.css` — интерфейс в стиле Garmin;
- `requirements.txt` — зависимости Python;
- `hrm-web.service` — пример юнита systemd для автозапуска сервера;
- `.gitignore` — чтобы не коммитить `venv` и кэш.

Чтобы выложить на GitHub:

```bash
cd firstapp
git init
git add .
git commit -m "Initial Garmin HRM-Pro kiosk"
git branch -M main
git remote add origin git@github.com:ВАШ_АККАУНТ/ВАШ_РЕПОЗИТОРИЙ.git
git push -u origin main
```

После этого на Raspberry Pi можно будет просто делать `git clone`.

---

## 2. Установка на Raspberry Pi (через SSH и GitHub)

### 2.1. Подготовка системы

```bash
sudo apt update
sudo apt upgrade -y

sudo apt install -y python3-pip python3-venv bluez midori git
```

Убедитесь, что Bluetooth включен и работает (`bluetoothctl` не выдаёт ошибок).

### 2.2. Клонирование репозитория

```bash
cd /home/pi
git clone git@github.com:ВАШ_АККАУНТ/ВАШ_РЕПОЗИТОРИЙ.git firstapp
cd firstapp
```

### 2.3. Python-окружение и зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Можно проверить запуск вручную:

```bash
python app.py
```

Открыть в браузере Raspberry Pi:

- адрес: `http://localhost:5000`

Остановить сервер `Ctrl + C`.

---

## 3. Настройка выключения без пароля

Чтобы кнопка "Выключить Pi" работала без ввода пароля, нужно разрешить пользователю `pi`
выполнять `shutdown` без пароля.

```bash
sudo visudo
```

Добавьте строку (если имя пользователя другое — замените `pi`):

```text
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

Сохраните и выйдите.

---

## 4. Автозапуск сервера через systemd

Файл `hrm-web.service` уже есть в репозитории. Скопируйте его в `/etc/systemd/system/`:

```bash
sudo cp /home/pi/firstapp/hrm-web.service /etc/systemd/system/hrm-web.service
sudo systemctl daemon-reload
sudo systemctl enable hrm-web.service
sudo systemctl start hrm-web.service
```

Проверить статус:

```bash
sudo systemctl status hrm-web.service
```

Если всё ок, сервер слушает порт `5000` всегда после загрузки.

> При необходимости отредактируйте пути в `hrm-web.service`, если вы положили проект не в `/home/pi/firstapp`.

---

## 5. Автозапуск Midori в полноэкранном режиме

Для стандартного окружения LXDE (Raspberry Pi OS с графикой):

```bash
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart
```

Добавьте строку:

```text
@midori -e Fullscreen -a http://localhost:5000
```

Перезагрузите Raspberry Pi:

```bash
sudo reboot
```

После загрузки:

- сначала поднимется сервис `hrm-web.service` (Flask + BLE),
- затем автоматически запустится LXDE и Midori в режиме киоска с вашим приложением.

---

## 6. Как это работает

- `hrm_service.py`:
  - ищет BLE-устройство, имя которого содержит `HRM-Pro` или `Garmin`;
  - подключается к **Heart Rate Service (UUID: 0x180D)**;
  - подписывается на характеристику **Heart Rate Measurement (UUID: 0x2A37)**;
  - сохраняет текущий пульс и статус подключения, пытается переподключаться при обрыве.

- `app.py` (Flask):
  - маршрут `/` — отдает HTML-интерфейс (крупные зеленые цифры в стиле Garmin);
  - `/api/heart_rate` — JSON с текущим пульсом и статусом (`connected`, `searching`, `disconnected`);
  - `/api/shutdown` — POST-запрос, который вызывает `sudo /sbin/shutdown -h now`.

Интерфейс нарисован под **полноэкранный режим**, поэтому удобно запускать в киоске.

---

## 7. Частые вопросы / отладка

- **Датчик не находится**
  - Убедитесь, что `HRM-Pro` "проснулся" (надет на тело, влажные электроды).
  - Запустите `bluetoothctl`, выполните `scan on` и посмотрите, как именно называется устройство.
  - Если имя отличается, поменяйте строку `device_name_substring="HRM-Pro"` в `app.py` / `hrm_service.py`.

- **Автовыключение не срабатывает**
  - Проверьте, что в `sudo visudo` добавлена строка с `NOPASSWD`.
  - Убедитесь, что путь к `shutdown` `/sbin/shutdown` валиден (`which shutdown`).

Если хочешь, могу добавить:

- логирование в файл для диагностики;
- отдельную страницу/индикатор "нет связи с датчиком" перед стартом тренировки.

