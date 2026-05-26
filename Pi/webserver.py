from flask import Flask

from utils import get_config

cfg = get_config()

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world'

if __name__ == '__main__':
    app.run(debug=True, host=cfg["web"]["host"], port=cfg["web"]["port"])