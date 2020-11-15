# Backend Website
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from werkzeug.utils import secure_filename
# File handling
import os
import shutil
# Web Scraping
import requests
from bs4 import BeautifulSoup
# String formatting
import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
# Membuat hash table
import collections
from copy import deepcopy

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5120 * 5120
app.config["UPLOAD_EXTENSIONS"] = [".txt"]
app.config["UPLOAD_PATH"] = "../test"
app.config["CUSTOM_STATIC_PATH"] = "../test"

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

# function GetCosineSimilarity((k : keytype, v : [f : float, i : integer, s : string])) → f
# Mengambil f dari tuple (k, v)
def GetCosineSimilarity(kv):
    return kv[1][1]

# function GetFilenames() → array of string
# Mengembalikan array yang berisi daftar filename pada direktori ../test
def GetFilenames():
    items = os.listdir(app.config["UPLOAD_PATH"])
    for item in items:
        if os.path.isdir(os.path.join(app.config["UPLOAD_PATH"], item)):
            items.remove(item)
    return items

# procedure UpdateDatabase()
# Meng-update variabel-variabel global
def UpdateDatabase():

    # Ambil daftar dokumen/berita
    FILENAMES = GetFilenames()

    # Iterasi berita satu demi satu
    for filename in FILENAMES:

        # Cek apakah file sudah pernah dimasukkan ke database
        if filename not in SEARCH_RESULTS:

            # Tambahkan berita ke dalam daftar hasil pencarian
            SEARCH_RESULTS["%s" % filename] = ["*", 0.0, 0, "*"]
                
            # Ubah berita ke dalam bentuk string
            with open(os.path.join(app.config["UPLOAD_PATH"], filename), "r", encoding="utf-8") as f:
                f_string = f.read()

                # Tambahkan judul berita ke dalam hasil pencarian
                f.seek(0)
                SEARCH_RESULTS["%s" % filename][0] = f.readline()

            # Tambahkan kalimat pertama berita ke dalam hasil pencarian
            # Ada 6 kemungkinan separator kalimat pertama: ". ", ".\n", "? ", "?\n", "! ", dan "!\n"
            # Pilih yang paling pendek sebagai kalimat utama
            s2 = []
            s2.append(f_string.split(". ", 1)[0] + ".")
            s2.append(f_string.split(".\n", 1)[0] + ".")
            s2.append(f_string.split("? ", 1)[0] + "?")
            s2.append(f_string.split("?\n", 1)[0] + "?")
            s2.append(f_string.split("! ", 1)[0] + "!")
            s2.append(f_string.split("!\n", 1)[0] + "!")
            if len(s2[0]) == len(s2[1]) == len(s2[2]) == len(s2[3]) == len(s2[4]) == len(s2[5]):
                SEARCH_RESULTS["%s" % filename][3] = s2[0][:-1]
            else:
                SEARCH_RESULTS["%s" % filename][3] = min(s2, key=len)

            # Format isi berita agar bisa dibuat vektornya
            f_formattedstring = FormatString(f_string)

            # Tambahkan berita ke dalam daftar vektor
            VECTORS["%s" % filename] = FrequencyCounter(f_formattedstring)

            # Tambahkan jumlah kata pada berita ke dalam hasil pencarian
            SEARCH_RESULTS["%s" % filename][2] = sum(VECTORS["%s" % filename].values())

# Variabel-variabel global / database

# FILENAMES : array of string
# Daftar file yang ada pada database
FILENAMES = GetFilenames()

# VECTORS : {key: string, value: Counter()}
# Daftar vektor yang akan dipakai ketika perhitungan (akan dikirim ke frontend untuk membuat tabel)
VECTORS = {}
# Cara penambahan elemen: VECTORS["key"] = FrequencyCounter(s : string) di mana s adalah string yang ingin diubah ke dalam vektor frekuensi kata

# SEARCH_RESULTS : {key: string, value: [s1 : string, f : float, i : integer, s2 : string]}
# Data yang akan dikirim kembali ke frontend, berisi informasi mengenai hasil pencarian
SEARCH_RESULTS = {}
# key = nama file berita
# s1 = judul berita
# f = hasil cosine similarity berita
# i = jumlah kata pada berita
# s2 = kalimat pertama pada berita
# Cara penambahan elemen: search_results["key"] = [s1 : string, f : float, i : integer, s2 : string]

# Inisialisasi database
UpdateDatabase()

@app.route("/")
def index():
    FILENAMES = GetFilenames()
    return render_template("index.html", FILENAMES=FILENAMES)

@app.route("/addfile", methods=["POST"])
def addfile():
    
    # Update daftar file
    FILENAMES = GetFilenames()

    # File yang dikirim mungkin lebih dari satu, loop berikut akan meng-iterasi file-file tersebut satu demi satu
    for txtfile in request.files.getlist("txtfile"):

        # Nama file diset supaya bisa disave di OS Linux
        filename = secure_filename(txtfile.filename)

        # Tidak akan terjadi apa-apa jika nama file tidak valid
        if filename != "":

            # Save file yang diupload dengan nama sementara
            txtfile.save(os.path.join(app.config["UPLOAD_PATH"], ".tmp/temp.txt"))
            
            # File akan disave
            # Mungkin file tersebut merupakan duplikat, mungkin file tersebut unik tapi namanya sudah dipakai oleh file lain pada database
            # Perlu dilakukan penanganan khusus untuk kasus-kasus ini
            i = 1
            isSaved = False
            while not isSaved:
            
                # Cek apakah file sudah ada di database
                if filename not in FILENAMES:

                    # Pastikan loop tidak akan diulang
                    isSaved = True
                    
                    # Ambil extension file (.txt), dan kirimkan pesan error 400 ke pengguna jika extension file bukan .txt
                    ext = os.path.splitext(filename)[1]
                    if ext not in app.config["UPLOAD_EXTENSIONS"]:
                        abort(400)

                    # Move file ke ../test/
                    shutil.move((os.path.join(app.config["UPLOAD_PATH"], ".tmp/temp.txt")), (os.path.join(app.config["UPLOAD_PATH"], filename)))

                    # Update database
                    UpdateDatabase()

                # Jika file bernama sama sudah ada,
                else:

                    # Buka kedua file
                    with open(os.path.join(app.config["UPLOAD_PATH"], ".tmp/temp.txt")) as newfile:
                        newtxt = newfile.read()
                    with open(os.path.join(app.config["UPLOAD_PATH"], filename)) as existingfile:
                        existingtxt = existingfile.read()

                    # Cek apakah file yang sudah diupload merupakan file duplikat. Jika ya, file tidak akan disave
                    if newtxt == existingtxt:
                        isSaved = True
                        os.remove(os.path.join(app.config["UPLOAD_PATH"], ".tmp/temp.txt"))

                    # Jika tidak, rename file yang diupload, cek lagi apakah file yang sudah direname ini juga memiliki duplikat
                    else:
                        filename = secure_filename(os.path.splitext(txtfile.filename)[0] + "_" + str(i) + os.path.splitext(txtfile.filename)[1])
                        i += 1
    
    # Refresh web page
    return redirect(url_for("index"))

@app.route("/addurl", methods=["POST"])
def addurl():

    # Update daftar file
    FILENAMES = GetFilenames()
    
    # Ambil link yang dikirim
    link = request.form.get("urlfile")

    # Buka link
    doc = requests.get(link)

    # Ambil kode html dari link yang dikirim
    soup = BeautifulSoup(doc.text, "html.parser")

    # Web Scraping
    # Saat ini men-support cnnindonesia.com, medcom.id, kompas.com
    # Untuk link cnnindonesia.com
    if "cnnindonesia.com" in link:

        # Ambil elemen berita
        content_detail = soup.find("div", {"class": "content_detail"})

        # Ambil judul berita
        title = content_detail.find("h1", {"class": "title"}).get_text().strip()

        # Ambil info berita
        date = content_detail.find("div", {"class": "date"}).get_text().strip()
        
        # Ambil body berita
        detikdetailtext = content_detail.find(id="detikdetailtext")

        # Antarpraragraf pada berita dipisahkan oleh <p></p>, buat list yang isinya adalah [paragraf 1, paragraf 2, dst.]
        list_paragraph = detikdetailtext.find_all("p")
        paragraph = []
        for i in range(len(list_paragraph)):

            # String formatting: tambahkan \n ke tiap akhir paragraf
            paragraph.append(list_paragraph[i].text.strip() + "\n")

            # String formatting: hilangkan \xa0
            paragraph[i] = paragraph[i].replace(u"\xa0", u" ")

        # Save berita ke file .txt
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w", encoding="utf-8") as f:
            f.write(title + "\n")
            f.write(date + "\n\n")
            f.writelines(paragraph)
    
    # Untuk link medcom.id
    elif "medcom.id" in link:

        # Ambil elemen berita
        article_ct = soup.find("div", {"class": "article_ct"})

        # Ambil judul berita
        title = article_ct.find("h1").get_text().strip()

        # Ambil info berita
        info_ct = article_ct.find("div", {"class": "info_ct"}).get_text().strip()
        
        # Ambil body berita
        articleBody = article_ct.find(attrs={"class": "text", "itemprop": "articleBody"})

        # medcom.id menaruh advertisement di tengah berita. Ambil advertisementnya
        parallax_ads = articleBody.find(attrs={"class": "parallax_ads"})

        # Hapus advertisement dari berita,
        # String formatting: hapus \xa0, hapus \r, ganti “ menjadi "
        article = articleBody.get_text().replace(parallax_ads.get_text(), "").strip().replace(u"\xa0", u" ").replace("\r", "").replace("“", "\"")

        # String formatting: hapus \n berganda
        while "\n\n" in article:
            article = article.replace("\n\n", "\n")

        # Save berita ke file .txt
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(title)) + ".txt", "w", encoding="utf-8") as f:
            f.write(title + "\n")
            f.write(info_ct + "\n\n")
            f.write(article)
    
    # Untuk link kompas.com
    elif "kompas.com" in link:
        
        # Ambil elemen berita
        container_clearfix = soup.find("div", {"class": "container clearfix"})

        # Ambil judul berita
        read__title = container_clearfix.find("h1", {"class": "read__title"}).get_text().strip()

        # Ambil info berita
        read__time = container_clearfix.find("div", {"class": "read__time"}).get_text().strip()

        # Ambil body berita
        read__content = container_clearfix.find("div", {"class": "read__content"})

        # Antarpraragraf pada berita dipisahkan oleh <p></p>, buat list yang isinya adalah [paragraf 1, paragraf 2, dst.]
        list_paragraph = read__content.find_all("p")
        paragraph = []
        for i in range(len(list_paragraph)):

            # String formatting: tambahkan \n ke tiap akhir paragraf
            paragraph.append(list_paragraph[i].text.strip() + "\n")

            # String formatting: hilangkan \xa0
            paragraph[i] = paragraph[i].replace(u"\xa0", u" ")

        # Save berita ke file .txt
        with open(os.path.join(app.config["UPLOAD_PATH"], secure_filename(read__title)) + ".txt", "w", encoding="utf-8") as f:
            f.write(read__title + "\n")
            f.write(read__time + "\n\n")
            f.writelines(paragraph)
    
    # Untuk link lainnya, kirim error 400
    else:
        abort(400)

    # Update database
    UpdateDatabase()
    
    # Refresh web page
    return redirect(url_for("index"))

@app.route("/search", methods=["GET"])
def search():

    # Ambil query
    query_string = FormatString(request.args.get("q"))

    # Tangani kasus khusus (query kosong)
    if not query_string:
        return render_template("index.html", FILENAMES=FILENAMES)
    else:

        # Tambahkan query ke dalam daftar vektor
        VECTORS["query"] = FrequencyCounter(query_string)
        
        # Cosine similarity
        # Jika q = vektor query dan d = vektor dokumen, maka
        # cosine_similarity(q, d) = (q • d) / (||q|| ||d||)

        # Hitung ||q||
        query_mag = 0
        for term in VECTORS["query"]:
            query_mag += (VECTORS["query"][term] ** 2)
        query_mag **= 0.5

        # Hitung ||d|| dan q • d
        for filename in SEARCH_RESULTS:
            
            # ||d||
            file_mag = 0
            for term in VECTORS[filename]:
                file_mag += (VECTORS[filename][term] ** 2)
            file_mag **= 0.5

            # q • d
            cross = 0
            for term in VECTORS["query"]:
                if term in VECTORS[filename]:
                    cross += (VECTORS["query"][term] * VECTORS[filename][term])
            
            # Hitung cosine similarity (dalam %), tambahkan ke dalam hasil pencarian
            SEARCH_RESULTS[filename][1] = (cross / (query_mag * file_mag)) * 100
        
        # Ubah cosine similarity ke dalam bentuk list dengan [(k1, [s11, f1, i1, s21]), (k2, [s12, f2, i2, s22]), dst.], f1 ≥ f2 ≥ f3 dst.
        results = list(SEARCH_RESULTS.items())
        results.sort(reverse=True, key=GetCosineSimilarity)

        # Untuk pembuatan tabel, perlu dibuat suatu urutan term
        order = VECTORS["query"].most_common()

        return render_template("search.html", FILENAMES=FILENAMES, query=query_string, results=results, VECTORS=VECTORS, order=order)

@app.route("/uploads/<path:filename>")
def display_result(filename):
    return send_from_directory(app.config["UPLOAD_PATH"], filename)
    
@app.route("/konsep")
def konsep():
    return render_template("konsep.html")

@app.route("/howtouse")
def howtouse():
    return render_template("howtouse.html")

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")