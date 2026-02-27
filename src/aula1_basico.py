import json

post = {
    "titulo": "STJ – Direito Penal – Informativo",
    "ano": 2026,
    "url": "https://www.dizerodireito.com.br/"
}

caminho_arquivo = "data/post_exemplo.json"

with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
    json.dump(post, arquivo, ensure_ascii=False, indent=2)

print("Arquivo salvo em:", caminho_arquivo)
