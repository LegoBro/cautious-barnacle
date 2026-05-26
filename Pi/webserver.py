from flask import Flask
from flask import render_template, send_from_directory
import os

from utils import get_config


cfg = get_config()

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world'

@app.route('/listoffiles')
def list_of_files():
     filenames=os.listdir(cfg["recording"]["output_dir"])
     print(os.listdir("."))
     return render_template('contents.html', files=filenames )

@app.route('/listoffiles/<path:filename>')
def read_file(filename):
    return send_from_directory(os.path.abspath(cfg["recording"]["output_dir"]), filename, as_attachment=True)
#here for attachment i went with flase otherwise it gonna download all the contents of the files

if __name__ == '__main__':
    app.run(debug=True, host=cfg["web"]["host"], port=cfg["web"]["port"])


# Credit:
# https://medium.com/@venkatalakshmiundamatla97/flask-tutorial-list-and-view-files-from-a-directory-using-jinja2-templates-48d4c2e620e3