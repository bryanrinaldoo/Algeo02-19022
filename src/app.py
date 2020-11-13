from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5120 * 5120
app.config["UPLOAD_EXTENSIONS"] = [".txt"]
app.config["UPLOAD_PATH"] = "uploads"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/addfile", methods=["POST"])
def addfile():
    for txtfile in request.files.getlist("txtfile"):
        filename = secure_filename(txtfile.filename)
        if filename != "":
            ext = os.path.splitext(filename)[1]
            if ext not in app.config["UPLOAD_EXTENSIONS"]:
                abort(400)
            txtfile.save(os.path.join(app.config["UPLOAD_PATH"], filename))
    return redirect(url_for('index'))

@app.route("/addurl")
def addurl():
    return True

@app.route("/search")
def search():
    return True
