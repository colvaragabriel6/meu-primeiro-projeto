import json

caminho_arquivo = "data/posts.txt"
registros = []

with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        linha = linha.strip()
        if not linha:
            continue

        registro = {
            "url": linha,
            "status": "pendente",
        }
        registros.append(registro)

caminho_saida = "data/posts_index.json"

with open(caminho_saida, "w", encoding="utf-8") as saida:
    json.dump(registros, saida, ensure_ascii=False, indent=2)

print("Índice criado em:", caminho_saida)
