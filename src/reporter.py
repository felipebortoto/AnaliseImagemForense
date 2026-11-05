"""Módulo gerador de mapa interativo (Folium) e relatórios periciais (JSON e Markdown).

Produz a representação cartográfica cronológica e o laudo de custódia
em conformidade com o Art. 158-A do CPP, com formatação destacada
e espaçamento amplo para os hashes criptográficos SHA-256.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

import folium
from folium import plugins


def generate_folium_map(
    evidence_items: list[dict[str, Any]],
    output_path: Optional[Union[str, Path]] = None,
) -> folium.Map:
    """Gera um mapa interativo Folium contendo marcadores e trajetória cronológica.

    Args:
        evidence_items: Lista de dicionários contendo dados de integridade e metadados.
        output_path: Caminho opcional para salvar o arquivo HTML gerado.

    Returns:
        Instância do mapa Folium configurado.
    """
    # Filtra apenas evidências com dados válidos de GPS
    geo_items = [
        item for item in evidence_items
        if item.get("metadata", {}).get("has_gps")
        and item.get("metadata", {}).get("latitude") is not None
        and item.get("metadata", {}).get("longitude") is not None
    ]

    # Ordena cronologicamente por datetime_iso ou datetime_original
    def _sort_key(item: dict) -> str:
        meta = item.get("metadata", {})
        return meta.get("datetime_iso") or meta.get("datetime_original") or ""

    geo_items.sort(key=_sort_key)

    if geo_items:
        # Centraliza na média dos pontos
        avg_lat = sum(it["metadata"]["latitude"] for it in geo_items) / len(geo_items)
        avg_lon = sum(it["metadata"]["longitude"] for it in geo_items) / len(geo_items)
        fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=14, control_scale=True)
    else:
        # Localização padrão caso nenhuma imagem tenha GPS
        fmap = folium.Map(location=[-15.7801, -47.9292], zoom_start=4, control_scale=True)

    # Cria rota/trajetória cronológica se houver 2 ou mais pontos
    if len(geo_items) >= 2:
        trajectory_points = [
            (it["metadata"]["latitude"], it["metadata"]["longitude"])
            for it in geo_items
        ]
        folium.PolyLine(
            locations=trajectory_points,
            color="#1d4ed8",
            weight=4,
            opacity=0.8,
            dash_array="5, 10",
            tooltip="Trajetória Cronológica de Disparos",
        ).add_to(fmap)

    # Adiciona marcadores numerados para cada evidência
    for idx, item in enumerate(geo_items, start=1):
        meta = item.get("metadata", {})
        integrity = item.get("integrity", {})
        lat = meta["latitude"]
        lon = meta["longitude"]
        filename = item.get("file_name", f"Evidência {idx}")
        dt = meta.get("datetime_original", "Data/Hora não informada")
        status = integrity.get("status", "NÃO VERIFICADO")
        color = "green" if integrity.get("is_intact") else "red"
        sha_preview = integrity.get("initial_hash", "")[:16] + "..."

        popup_html = f"""
        <div style="font-family: sans-serif; width: 240px; font-size: 13px;">
            <h4 style="margin: 0 0 6px 0; color: #1e293b;"><b>Evidência #{idx}:</b> {filename}</h4>
            <p style="margin: 2px 0;"><b>Data/Hora:</b> {dt}</p>
            <p style="margin: 2px 0;"><b>Coordenadas:</b> {lat:.5f}, {lon:.5f}</p>
            <p style="margin: 2px 0;"><b>Status CPP:</b> <span style="color: {color}; font-weight: bold;">{status}</span></p>
            <p style="margin: 2px 0; font-size: 11px; color: #64748b;"><b>SHA-256:</b> <code>{sha_preview}</code></p>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"#{idx} - {filename} ({dt})",
            icon=folium.Icon(color=color, icon="camera", prefix="fa"),
        ).add_to(fmap)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        fmap.save(str(out))

    return fmap


def generate_json_report(
    evidence_items: list[dict[str, Any]],
    case_info: Optional[dict[str, Any]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> dict[str, Any]:
    """Gera o relatório pericial estruturado em formato JSON."""
    case_info = case_info or {}
    total = len(evidence_items)
    intact = sum(1 for item in evidence_items if item.get("integrity", {}).get("is_intact"))

    report = {
        "case_info": {
            "title": case_info.get("title", "Exame Pericial de Mídias Digitais"),
            "examiner": case_info.get("examiner", "Perito Responsável"),
            "legal_foundation": "Art. 158-A a 158-F do Código de Processo Penal (Cadeia de Custódia)",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_evidences": total,
            "intact_evidences": intact,
            "custody_preserved": bool(total > 0 and intact == total),
        },
        "evidences": evidence_items,
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return report


def generate_markdown_report(
    evidence_items: list[dict[str, Any]],
    case_info: Optional[dict[str, Any]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> str:
    """Gera o Laudo Pericial em Markdown com espaçamento amplo para conferência de hashes."""
    case_info = case_info or {}
    total = len(evidence_items)
    intact = sum(1 for item in evidence_items if item.get("integrity", {}).get("is_intact"))
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")

    lines: list[str] = [
        "# LAUDO PERICIAL FORENSE DE MÍDIAS DIGITAIS",
        "",
        "## 1. Informações Gerais e Fundamentação Jurídica",
        "",
        f"- **Operação / Caso:** {case_info.get('title', 'Exame de Evidências Digitais')}",
        f"- **Perito / Examinador:** {case_info.get('examiner', 'Laboratório de Computação Forense')}",
        f"- **Data da Emissão:** {now_str}",
        "- **Fundamentação Legal:** Código de Processo Penal, Art. 158-A e seguintes (Lei nº 13.964/2019 - Cadeia de Custódia).",
        f"- **Total de Mídias Examinadas:** {total}",
        f"- **Evidências com Integridade Atestada:** {intact} de {total}",
        "",
        "---",
        "",
        "## 2. Auditoria Criptográfica da Cadeia de Custódia",
        "",
        "Conforme preconiza o Art. 158-A do CPP, todas as mídias tiveram seus hashes criptográficos SHA-256 extraídos imediatamente no recebimento (fixação preliminar) e recalculados após os exames analíticos. A tabela e os cartões a seguir detalham a verificação.",
        "",
    ]

    for idx, item in enumerate(evidence_items, start=1):
        filename = item.get("file_name", f"Evidencia_{idx}")
        integrity = item.get("integrity", {})
        meta = item.get("metadata", {})

        is_intact = integrity.get("is_intact", False)
        status_tag = "ÍNTEGRO (100% PRESERVADO)" if is_intact else "VIOLADO / DIVERGÊNCIA DETECTADA"
        size = meta.get("file_size_bytes", 0)
        size_fmt = f"{size:,} bytes ({size / (1024*1024):.2f} MB)" if size else "Desconhecido"

        init_hash = integrity.get("initial_hash", "N/A")
        final_hash = integrity.get("final_hash", "N/A")

        lines.extend([
            f"### Evidência {idx:02d}: `{filename}`",
            "",
            f"- **Status de Custódia:** `[ {status_tag} ]`",
            f"- **Tamanho do Arquivo:** {size_fmt}",
            f"- **Dispositivo Registrador:** {meta.get('make') or 'N/A'} {meta.get('model') or ''}".strip(),
            f"- **Data/Hora Original de Captura (EXIF):** {meta.get('datetime_original') or 'Ausente'}",
            f"- **Geolocalização (GPS):** Latitude: `{meta.get('latitude') or 'N/A'}` | Longitude: `{meta.get('longitude') or 'N/A'}`",
            "",
            "#### Conferência Criptográfica de Hashes SHA-256 (Art. 158-A CPP):",
            "",
            "> **SHA-256 Pré-Processamento (Fixação Inicial):**",
            ">",
            f"> `{init_hash}`",
            "",
            "> **SHA-256 Pós-Processamento (Verificação Final):**",
            ">",
            f"> `{final_hash}`",
            "",
            f"> **Parecer Técnico:** {'Correspondência exata dos 64 caracteres hexadecimais. Sem alteração física ou lógica da prova.' if is_intact else 'DIVERGÊNCIA DETECTADA. Integridade da evidência comprometida.'}",
            "",
        ])

        if meta.get("notes"):
            lines.extend([
                "**Observações Periciais:**",
                *[f"- {note}" for note in meta["notes"]],
                "",
            ])

        lines.extend(["---", ""])

    lines.extend([
        "## 3. Conclusão Forense",
        "",
        f"Atesta-se para os devidos fins de direito que {'todas as evidências digitais examinadas mantiveram sua integridade probatória inalterada durante todo o procedimento pericial' if intact == total and total > 0 else 'houve irregularidade na integridade de uma ou mais evidências analisadas'}.",
        "",
        "_Documento gerado automaticamente pelo Sistema de Análise de Imagem Forense._",
        "",
    ])

    content = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")

    return content

