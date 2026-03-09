from pathlib import Path
import subprocess

from flask import Flask, jsonify, render_template

from hrm_service import HeartRateMonitor


BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

hrm = HeartRateMonitor(device_name_substring="HRM-Pro")
hrm.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/heart_rate")
def api_heart_rate():
    return jsonify({"hr": hrm.get_heart_rate(), "status": hrm.get_status()})


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    # ВАЖНО: нужно настроить sudoers, чтобы shutdown не спрашивал пароль
    # см. README.md
    subprocess.Popen(["sudo", "/sbin/shutdown", "-h", "now"])
    return ("OK", 200)


def main():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()

