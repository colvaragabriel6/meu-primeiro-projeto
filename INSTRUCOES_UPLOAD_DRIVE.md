# 📤 INSTRUÇÕES PARA UPLOAD DE INFORMATIVOS AO GOOGLE DRIVE

## Passo 1: Executor o script de upload
```bash
cd /workspaces/meu-primeiro-projeto
python3 src/upload_drive_final.py
```

## Passo 2: O script exibirá uma URL
Uma URL será mostrada assim:
```
https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...
```

## Passo 3: Abra a URL no seu navegador
- Copie a URL completa
- Abra em um novo aba do navegador
- Você será redirecionado para autenticar com sua conta Google

## Passo 4: Autorize o acesso
- Clique em "Autorizar" ou "Permitir" conforme solicitado
- Você receberá um código (algo como: `4/0AGtsvnzH8k...`)

## Passo 5: Copie o código
- Selecione e copie todo o código de autorização
- Volte ao terminal que está executando o script
- Cole o código quando perguntado

## Passo 6: Aguarde o upload
- O script automaticamente criará a pasta "DOD - Informativos" no seu Google Drive
- Criará subpastas para STF e STJ
- Fará upload de todos os 808 PDFs (pode demorar alguns minutos)

---

## Resumo
**808 arquivos serão enviados para:**
- Pasta principal: `DOD - Informativos`
  - Subpasta: `Informativos_STF` (376 PDFs)
  - Subpasta: `Informativos_STJ` (432 PDFs)

**Nota:** Se o arquivo já existir no Drive, será pulado (não será re-enviado).
