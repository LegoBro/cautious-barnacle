# /home/pi/birdfeeder/webserver.py
from flask import Flask, jsonify, send_from_directory
import os
from utils import load_config, setup_logger

cfg = load_config()
logger = setup_logger("webserver", cfg["logging"]["dir"], cfg["logging"]["level"])

app = Flask(__name__)
RECORD_DIR = cfg["recording"]["output_dir"]

@app.route("/status")
def status():
    try:
        files = sorted(
            os.listdir(RECORD_DIR),
            key=lambda f: os.path.getmtime(os.path.join(RECORD_DIR, f)),
            reverse=True,
        )
    except FileNotFoundError:
        files = []

    return jsonify({
        "status": "ok",
        "files": files[:20],
    })

@app.route("/recordings/<path:filename>")
def recordings(filename):
    return send_from_directory(RECORD_DIR, filename, as_attachment=False)

@app.route("/")
def index():
    return """
    <html>
      <body>
        <h1>Bird Feeder</h1>
        <p><a href="/status">Status JSON</a></p>
        <p>Latest recordings listed in /status, downloadable via /recordings/&lt;filename&gt;</p>
      </body>
    </html>
    """

if __name__ == "__main__":
    host = cfg["web"]["host"]
    port = cfg["web"]["port"]
    logger.info(f"Starting webserver on {host}:{port}")
    app.run(host=host, port=port)
