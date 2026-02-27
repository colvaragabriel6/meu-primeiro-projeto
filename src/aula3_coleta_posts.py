import requests
from bs4 import BeautifulSoup

url = "https://www.dizerodireito.com.br/2026/"

resposta = requests.get(url)
resposta.raise_for_status()

soup = BeautifulSoup(resposta.text, "html.parser")

posts = []

for a in soup.find_all("a"):
    href = a.get("href")
    if href and "/2026/" in href:
        if href.startswith("https://www.dizerodireito.com.br/"):
            posts.append(href)

posts = list(dict.fromkeys(posts))

caminho_saida = "data/posts.txt"

with open(caminho_saida, "w", encoding="utf-8") as arquivo:
    for post in posts:
        arquivo.write(post + "\n")

print("Arquivo posts.txt gerado com", len(posts), "links")
