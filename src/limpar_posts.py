import re

# padrão de URL de post do blog (ano/mês)
PADRAO_POST = re.compile(r"^https://www\.dizerodireito\.com\.br/\d{4}/\d{2}/")

entrada = "data/posts.txt"
saida = "data/posts_limpos.txt"

urls_ok = []

with open(entrada, "r", encoding="utf-8") as f:
    for linha in f:
        url = linha.strip()
        if not url:
            continue
        if PADRAO_POST.search(url):
            urls_ok.append(url)

# remove duplicados preservando a ordem
urls_ok = list(dict.fromkeys(urls_ok))

with open(saida, "w", encoding="utf-8") as f:
    for url in urls_ok:
        f.write(url + "\n")

print("Total de URLs originais:", sum(1 for _ in open(entrada, encoding="utf-8")))
print("Total de posts válidos:", len(urls_ok))
print("Arquivo gerado:", saida)
