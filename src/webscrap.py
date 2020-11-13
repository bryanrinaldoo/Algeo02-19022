from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup

my_url = input("Masukkan URL dari CNN : ")

uClient = uReq(my_url)
page_html = uClient.read()
uClient.close()

page_soup = soup(page_html, "html.parser")

containers = page_soup.findAll("div",{"class":"content_detail"})
judul = containers[0].h1.text.strip()
print(judul)
paragraf_container = containers[0].findAll("p")

f = open('../test/'+judul+'.txt',"w")
#pake len 
for i in range (len(containers[0].findAll("p"))):
    paragraf = paragraf_container[i].text.strip()
    print(paragraf)
    f.write(paragraf)
f.close()
    
