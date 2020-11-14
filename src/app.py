# Backend Website
from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
# Append nama file
import os
# Web Scraping
import requests
from bs4 import BeautifulSoup
# String formatting
import string
# Membuat hash table
import collections
from copy import deepcopy

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
    return redirect(url_for("index"))

@app.route("/addurl", methods=["POST"])
def addurl():
    link = request.form.get("urlfile")
    doc = requests.get(link)
    soup = BeautifulSoup(doc.text, "html.parser")
    title = soup.title.string
    if "cnnindonesia.com" in link:
        string_detikdetailtext = soup.find(id="detikdetailtext")
        list_paragraph = string_detikdetailtext.find_all("p")
        paragraph = []
        for i in range(len(list_paragraph)):
            paragraph.append(list_paragraph[i].text.strip() + "\n")
            paragraph[i] = paragraph[i].replace(u"\xa0", u" ")
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w") as f:
            f.write(title + "\n\n")
            f.writelines(paragraph)
    elif "medcom.id" in link:
        string_articleBody = soup.find(attrs = {"class": "text", "itemprop": "articleBody"})
        string_parallax_ads = string_articleBody.find(attrs = {"class": "parallax_ads"})
        article = string_articleBody.get_text().replace(string_parallax_ads.get_text(), "").strip().replace(u"\xa0", u" ").replace("\r", "").replace("“", "\"")
        while "\n\n" in article:
            article = article.replace("\n\n", "\n")
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w") as f:
            f.write(title + "\n\n")
            f.write(article)
    else:
        abort(400)
    return redirect(url_for("index"))

@app.route("/search")
def search():
    query_string = request.args.get("q").lower()
    for char in string.punctuation:
        query_string = query_string.replace(char, "")
    query_list = query_string.split()
    query_vector = collections.Counter(query_list)
    vectors = {}
    vectors["query"] = query_vector
    cosine_similarity = {}
    for filename in os.listdir(os.path.join(os.getcwd(), app.config["UPLOAD_PATH"])):
        with open(os.path.join(app.config["UPLOAD_PATH"], filename), "r") as f:
            f_string = f.read().lower()
            for char in string.punctuation:
                f_string = f_string.replace(char, "")
            f_list = f_string.split()
            f_vector = collections.Counter(f_list)
            vectors["%s" % filename] = f_vector
            cosine_similarity["%s" % filename] = 0
    origin_vector = collections.Counter([])
    for vector in vectors:
        origin_vector += vectors[vector]
    origin_vector.subtract(origin_vector)
    for vector in vectors:
        vectors[vector].update(origin_vector)
    # Hitung cosine similarity
    query_mag = 0
    for term in vectors["query"]:
        query_mag += (vectors["query"][term] ** 2)
    query_mag **= 0.5
    for filename in cosine_similarity:
        file_mag = 0
        for term in vectors[filename]:
            file_mag += (vectors[filename][term] ** 2)
        file_mag **= 0.5
        cross = 0
        for term in vectors[filename]:
            cross += (vectors["query"][term] * vectors[filename][term])
        cosine_similarity[filename] = cross / (query_mag * file_mag)
    return render_template("search.html", query=query_string)