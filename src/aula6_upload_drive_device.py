import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ========= CONFIG =========
OAUTH_CLIENT_PATH = Path("secrets/oauth_client.json")
TOKEN_PATH = Path("secrets/drive_token.json")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

LOCAL_DOWNLOADS = Path("downloads")

DRIVE_ROOT_FOLDER_NAME = "Jurisprudencia"

# >>> AJUSTE IMPORTANTE: agora bate com suas pastas reais em downloads/ <<<
FOLDER_MAP = {
    "Informativos_STF": ("Informativos_STF", True),
    "Informativos_STJ": ("Informativos_STJ", True),
    "Revisoes": ("Revisoes", False),
    "Alteracoes_Legislativas": ("Alteracoes_Legislativas", False),
    "Materiais_Diversos": ("Materiais_Diversos", False),
    "Codigos": ("Codigos", False),
}
# ==========================


def load_oauth_client() -> Tuple[str, str]:
    if not OAUTH_CLIENT_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {OAUTH_CLIENT_PATH}. "
            f"Coloque o oauth_client.json completo (com client_secret) em secrets/."
        )

    data = json.loads(OAUTH_CLIENT_PATH.read_text(encoding="utf-8"))
    root_key = "installed" if "installed" in data else ("web" if "web" in data else None)
    if not root_key:
        raise ValueError("oauth_client.json inválido: esperado 'installed' ou 'web' na raiz.")

    client_id = data[root_key].get("client_id")
    client_secret = data[root_key].get("client_secret")

    if not client_id or not client_secret:
        raise ValueError("oauth_client.json incompleto: precisa conter client_id e client_secret.")

    return client_id, client_secret


def device_flow_get_token() -> Credentials:
    client_id, client_secret = load_oauth_client()

    r = requests.post(
        "https://oauth2.googleapis.com/device/code",
        data={"client_id": client_id, "scope": " ".join(SCOPES)},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()

    verification_url = payload["verification_url"]
    user_code = payload["user_code"]
    device_code = payload["device_code"]
    interval = int(payload.get("interval", 5))

    print("\n=== LOGIN GOOGLE (SEM LOCALHOST) ===")
    print(f"Abra: {verification_url}")
    print(f"Digite o código: {user_code}\n")
    print("Aguardando você autorizar...")

    while True:
        time.sleep(interval)

        tr = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            timeout=30,
        )

        try:
            data = tr.json()
        except Exception:
            data = {"raw": tr.text, "status_code": tr.status_code}

        err = data.get("error")

        if err in ("authorization_pending", "slow_down"):
            if err == "slow_down":
                interval += 2
            continue

        if tr.status_code >= 400:
            raise RuntimeError(f"Falha ao obter token: {data}")

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        if not access_token:
            raise RuntimeError(f"Resposta inesperada do token endpoint: {data}")

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

        print("Autorizado com sucesso. Token salvo em:", TOKEN_PATH)
        return creds


def get_creds() -> Credentials:
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        return creds

    return device_flow_get_token()


def drive_service():
    creds = get_creds()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_folder(service, name: str, parent_id: Optional[str]) -> Optional[str]:
    safe_name = name.replace("'", "\\'")
    q = f"name='{safe_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"

    res = service.files().list(
        q=q,
        spaces="drive",
        fields="files(id,name)",
        pageSize=10,
    ).execute()

    files = res.get("files", [])
    return files[0]["id"] if files else None


def get_or_create_folder(service, name: str, parent_id: Optional[str]) -> str:
    existing = find_folder(service, name, parent_id)
    if existing:
        return existing

    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]

    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def ensure_drive_structure(service) -> Dict[str, str]:
    root_id = get_or_create_folder(service, DRIVE_ROOT_FOLDER_NAME, None)

    base_ids: Dict[str, str] = {}
    for local_key, (folder_name, _) in FOLDER_MAP.items():
        base_ids[local_key] = get_or_create_folder(service, folder_name, root_id)

    return base_ids


def find_file_by_name_in_folder(service, filename: str, parent_id: str) -> Optional[str]:
    safe_name = filename.replace("'", "\\'")
    q = f"name='{safe_name}' and trashed=false and '{parent_id}' in parents"
    res = service.files().list(q=q, spaces="drive", fields="files(id,name)", pageSize=5).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def upload_file(service, local_path: Path, parent_id: str) -> str:
    media = MediaFileUpload(str(local_path), resumable=True)
    body = {"name": local_path.name, "parents": [parent_id]}
    created = service.files().create(body=body, media_body=media, fields="id").execute()
    return created["id"]


def iter_local_files() -> list[Path]:
    if not LOCAL_DOWNLOADS.exists():
        raise FileNotFoundError(f"Pasta '{LOCAL_DOWNLOADS}' não existe.")
    return [p for p in LOCAL_DOWNLOADS.rglob("*") if p.is_file()]


def classify_path(p: Path) -> Tuple[str, Optional[str]]:
    """
    Regra: primeira pasta depois de downloads/ define a categoria.
    Ex:
      downloads/Informativos_STJ/2026/arquivo.pdf -> ("Informativos_STJ", "2026")
      downloads/Revisoes/arquivo.pdf -> ("Revisoes", None)
    """
    rel = p.relative_to(LOCAL_DOWNLOADS)
    parts = rel.parts
    if not parts:
        return ("Materiais_Diversos", None)

    cat = parts[0]
    ano = None

    if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 4:
        ano = parts[1]

    if cat not in FOLDER_MAP:
        cat = "Materiais_Diversos"

    return (cat, ano)


def main():
    print("Iniciando upload para Google Drive (Device Flow)...")
    service = drive_service()
    base_ids = ensure_drive_structure(service)

    year_cache: Dict[Tuple[str, str], str] = {}

    files = iter_local_files()
    print(f"Arquivos locais encontrados em '{LOCAL_DOWNLOADS}': {len(files)}")

    uploaded = 0
    skipped = 0

    for fp in files:
        cat, ano = classify_path(fp)
        base_id = base_ids[cat]
        _, has_year = FOLDER_MAP[cat]

        parent_id = base_id
        if has_year:
            year = ano or "Sem_Ano"
            key = (cat, year)
            if key not in year_cache:
                year_cache[key] = get_or_create_folder(service, year, base_id)
            parent_id = year_cache[key]

        # >>> ANTI-DUPLICATA <<<
        if find_file_by_name_in_folder(service, fp.name, parent_id):
            print(f"[PULO]  {fp.name} (já existe na pasta destino)")
            skipped += 1
            continue

        print(f"[UPLOAD] {fp} -> {cat}{'/' + (ano or 'Sem_Ano') if has_year else ''}")
        file_id = upload_file(service, fp, parent_id)
        print(f"        Drive file_id: {file_id}")
        uploaded += 1

    print("\nConcluído.")
    print("Uploads feitos:", uploaded)
    print("Pulos:", skipped)


if __name__ == "__main__":
    main()
