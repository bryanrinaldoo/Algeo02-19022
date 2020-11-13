from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
import os
import requests
from bs4 import BeautifulSoup
import unicodedata

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

@app.route("/addurl", methods=["POST"])
def addurl():
    link = request.form.get("urlfile")
    doc = requests.get(link)
    soup = BeautifulSoup(doc.text, "html.parser")
    title = soup.title.string
    list_contentdetail = soup.find_all("div", "content_detail")
    list_paragraph = list_contentdetail[0].find_all("p")
    paragraph = []
    for i in range(len(list_paragraph)):
        paragraph.append(list_paragraph[i].text.strip() + "\n")
        paragraph[i] = paragraph[i].replace(u"\xa0", u" ")
    with open("./uploads/" + secure_filename(title) + ".txt", "w") as f:
        f.write(title + "\n\n")
        f.writelines(paragraph)
    return redirect(url_for('index'))

@app.route("/search")
def search():
    return True
