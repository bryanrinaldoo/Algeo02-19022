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
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
# Membuat hash table
import collections
from copy import deepcopy

# Fungsi-fungsi pembantu

# function FormatString(s : string) → string
# Memformat string dalam 3 langkah
def FormatString(s):
    s = StemmerFactory().create_stemmer().stem(s)
    # Double-check: Ubah string menjadi lowercase
    s = s.lower()
    # Double-check: Hilangkan punctuation
    for char in string.punctuation:
        s = s.replace(char, " ")
    # Double-check: Hilangkan duplicate whitespace, → s
    return " ".join(s.split())

# function FrequencyCounter(s : string) → Counter
# Mengubah string ke dalam Counter, Counter adalah hash table dengan format <key: kata, value: jumlah kemunculan kata pada string>
def FrequencyCounter(s):
    # Ubah string ke dalam list kata demi kata
    s_list = s.split()
    # Ubah list menjadi Counter, → Counter
    return collections.Counter(s_list)

# function GetVal((keytype, valtype)) → valtype
# Mengambil value dari tuple (key, value)
def GetVal(kv):
    return kv[1]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5120 * 5120
app.config["UPLOAD_EXTENSIONS"] = [".txt"]
app.config["UPLOAD_PATH"] = "uploads"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/addfile", methods=["POST"])
def addfile():

    # File yang dikirim mungkin lebih dari satu, loop berikut akan meng-iterasi file-file tersebut satu demi satu
    for txtfile in request.files.getlist("txtfile"):

        # Nama file diset supaya bisa disave di OS Linux
        filename = secure_filename(txtfile.filename)

        # Tidak akan terjadi apa-apa jika nama file tidak valid
        if filename != "":

            # Ambil extension file (.txt), dan kirimkan pesan error 400 ke pengguna jika extension file bukan .txt
            ext = os.path.splitext(filename)[1]
            if ext not in app.config["UPLOAD_EXTENSIONS"]:
                abort(400)

            # Save file ke ./uploads/
            txtfile.save(os.path.join(app.config["UPLOAD_PATH"], filename))
    
    # Refresh web page
    return redirect(url_for("index"))

@app.route("/addurl", methods=["POST"])
def addurl():

    # Ambil link yang dikirim
    link = request.form.get("urlfile")

    # Buka link
    doc = requests.get(link)

    # Ambil kode html dari link yang dikirim
    soup = BeautifulSoup(doc.text, "html.parser")

    # Ambil judul artikel
    title = soup.title.string

    # Web Scraping
    # Saat ini men-support cnnindonesia.com, medcom.id, kompas.com
    # Untuk link cnnindonesia.com
    if "cnnindonesia.com" in link:

        # Ambil body berita
        string_detikdetailtext = soup.find(id="detikdetailtext")

        # Antarpraragraf pada berita dipisahkan oleh <p></p>, buat list yang isinya adalah [paragraf 1, paragraf 2, dst.]
        list_paragraph = string_detikdetailtext.find_all("p")
        paragraph = []
        for i in range(len(list_paragraph)):

            # String formatting: tambahkan \n ke tiap akhir paragraf
            paragraph.append(list_paragraph[i].text.strip() + "\n")

            # String formatting: hilangkan \xa0
            paragraph[i] = paragraph[i].replace(u"\xa0", u" ")

        # Save berita ke file .txt
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w") as f:
            f.write(title + "\n\n")
            f.writelines(paragraph)
    
    # Untuk link medcom.id
    elif "medcom.id" in link:

        # Ambil body berita
        string_articleBody = soup.find(attrs={"class": "text", "itemprop": "articleBody"})

        # medcom.id menaruh advertisement di tengah berita. Ambil advertisementnya
        string_parallax_ads = string_articleBody.find(attrs={"class": "parallax_ads"})

        # Hapus advertisement dari berita,
        # String formatting: hapus \xa0, hapus \r, ganti “ menjadi "
        article = string_articleBody.get_text().replace(string_parallax_ads.get_text(), "").strip().replace(u"\xa0", u" ").replace("\r", "").replace("“", "\"")

        # String formatting: hapus \n berganda
        while "\n\n" in article:
            article = article.replace("\n\n", "\n")

        # Save berita ke file .txt
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w") as f:
            f.write(title + "\n\n")
            f.write(article)
    
    # Untuk link kompas.com
    elif "kompas.com" in link:
        
        # Ambil body berita
        string_read__content = soup.find("div", {"class": "read__content"})

        # Antarpraragraf pada berita dipisahkan oleh <p></p>, buat list yang isinya adalah [paragraf 1, paragraf 2, dst.]
        list_paragraph = string_read__content.find_all("p")
        paragraph = []
        for i in range(len(list_paragraph)):

            # String formatting: tambahkan \n ke tiap akhir paragraf
            paragraph.append(list_paragraph[i].text.strip() + "\n")

            # String formatting: hilangkan \xa0
            paragraph[i] = paragraph[i].replace(u"\xa0", u" ")

        # Save berita ke file .txt
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w") as f:
            f.write(title + "\n\n")
            f.writelines(paragraph)
    
    # Untuk link lainnya, kirim error 400
    else:
        abort(400)

    # Refresh web page
    return redirect(url_for("index"))

@app.route("/search")
def search():

    # Inisialisasi hash table untuk daftar vektor dan cosine similarity

    # vectors {key: string, value: Counter()}
    vectors = {}
    # Cara penambahan elemen: vectors["key"] = FrequencyCounter(s) di mana s adalah string yang ingin diubah ke dalam vektor frekuensi kata

    # cosine_similarity {key: string, value: float}
    cosine_similarity = {}
    # Cara penambahan elemen: cosine_similarity["key"] = f : float
    
    # Ambil query
    query_string = FormatString(request.args.get("q"))

    # Tambahkan query ke dalam daftar vektor
    vectors["query"] = FrequencyCounter(query_string)

    # Tidak ada lagi yang bisa kita lakukan dengan query. Sekarang kita buat dulu vektor frekuensi kata dari tiap-tiap berita
    # Iterasi berita satu demi satu
    for filename in os.listdir(os.path.join(os.getcwd(), app.config["UPLOAD_PATH"])):

        # Ubah berita ke dalam bentuk string
        with open(os.path.join(app.config["UPLOAD_PATH"], filename), "r") as f:
            f_string = FormatString(f.read())

        # Tambahkan berita ke dalam daftar vektor
        vectors["%s" % filename] = FrequencyCounter(f_string)

        # Tambahkan berita ke dalam daftar cosine similarity
        cosine_similarity["%s" % filename] = 0

    # Samakan dimensi semua vektor

    # Buat vektor nol berdimensi n, n = jumlah kata unik pada query maupun berita-berita
    origin_vector = collections.Counter([])
    for vector in vectors:
        origin_vector += vectors[vector]
    origin_vector.subtract(origin_vector)

    # Translasi semua vektor ke dalam dimensi n
    for vector in vectors:
        vectors[vector].update(origin_vector)

    
    # Hitung cosine similarity
    # Jika q = vektor query dan d = vektor dokumen, maka
    # cosine_similarity(q, d) = (q • d) / (||q|| ||d||)

    # Hitung ||q||
    query_mag = 0
    for term in vectors["query"]:
        query_mag += (vectors["query"][term] ** 2)
    query_mag **= 0.5

    # Hitung ||d|| dan q • d
    for filename in cosine_similarity:
        
        # ||d||
        file_mag = 0
        for term in vectors[filename]:
            file_mag += (vectors[filename][term] ** 2)
        file_mag **= 0.5

        # q • d
        cross = 0
        for term in vectors[filename]:
            cross += (vectors["query"][term] * vectors[filename][term])
        
        # Tambahkan hasil perhitungan ke dalam daftar cosine similarity
        cosine_similarity[filename] = cross / (query_mag * file_mag)
    
    # Ubah cosine similarity ke dalam bentuk list dengan [(k1, v1), (k2, v2), dst.], v1 ≥ v2 ≥ v3 dst.
    cosine_similarity_list = list(cosine_similarity.items()).sort(reverse=True, key=GetVal)

    return render_template("search.html", query=query_string)