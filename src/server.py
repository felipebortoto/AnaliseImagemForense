"""Servidor Web FastAPI para Análise Forense de Imagens Digitais.

Disponibiliza interface moderna em Tailwind CSS para upload drag & drop
de até 25 mídias, exibição do mapa interativo Folium e download de laudo.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from src.extractor import extract_metadata
from src.integrity import calculate_sha256, verify_integrity
from src.reporter import (
    generate_folium_map,
    generate_json_report,
    generate_markdown_report,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
INDEX_FILE = TEMPLATES_DIR / "index.html"

app = FastAPI(
    title="Análise Forense de Mídias Digitais",
    description="Sistema pericial de extração EXIF e Cadeia de Custódia (Art. 158-A CPP)",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse)
async def index_page():
    """Página inicial com dashboard de upload e análise pericial."""
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Template não encontrado.")
    return HTMLResponse(content=INDEX_FILE.read_text(encoding="utf-8"))


@app.post("/api/analyze")
async def analyze_images(files: list[UploadFile] = File(...)):
    """Recebe até 25 imagens, calcula hashes de custódia e extrai metadados."""
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    if len(files) > 25:
        raise HTTPException(
            status_code=400,
            detail="Limite excedido: máximo de 25 imagens por lote pericial.",
        )

    results: list[dict[str, Any]] = []

    for upload_file in files:
        content = await upload_file.read()
        filename = upload_file.filename or "evidencia"

        # 1. Fixação do Hash Inicial (Pré-processamento)
        pre_hash = calculate_sha256(content)

        # 2. Extração segura de metadados
        metadata = extract_metadata(content, file_name=filename)

        # 3. Recálculo e verificação da integridade
        post_hash = calculate_sha256(content)
        integrity = verify_integrity(
            initial_hash=pre_hash,
            final_hash=post_hash,
            target_name=filename,
        )

        results.append({
            "file_name": filename,
            "integrity": integrity.to_dict(),
            "metadata": metadata.to_dict(),
        })

    # Gera mapa Folium em memória
    fmap = generate_folium_map(results)
    map_html = fmap.get_root().render()

    case_info = {
        "title": "Exame Pericial Web",
        "examiner": "Laboratório de Perícia Digital",
    }
    json_report = generate_json_report(results, case_info=case_info)
    markdown_report = generate_markdown_report(results, case_info=case_info)

    return {
        "summary": json_report["case_info"],
        "evidences": results,
        "map_html": map_html,
        "markdown_report": markdown_report,
    }

