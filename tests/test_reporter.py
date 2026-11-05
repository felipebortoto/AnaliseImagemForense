import json
from pathlib import Path

from src.reporter import (
    generate_folium_map,
    generate_json_report,
    generate_markdown_report,
)


def test_generate_folium_map(tmp_path: Path):
    items = [
        {
            "file_name": "foto1.jpg",
            "integrity": {
                "initial_hash": "a" * 64,
                "final_hash": "a" * 64,
                "is_intact": True,
                "status": "ÍNTEGRO",
            },
            "metadata": {
                "has_gps": True,
                "latitude": -23.55052,
                "longitude": -46.633408,
                "datetime_original": "2026:11:05 10:00:00",
            },
        },
        {
            "file_name": "foto2.jpg",
            "integrity": {
                "initial_hash": "b" * 64,
                "final_hash": "b" * 64,
                "is_intact": True,
                "status": "ÍNTEGRO",
            },
            "metadata": {
                "has_gps": True,
                "latitude": -23.55500,
                "longitude": -46.638000,
                "datetime_original": "2026:11:05 10:15:00",
            },
        },
    ]

    html_file = tmp_path / "mapa.html"
    fmap = generate_folium_map(items, output_path=html_file)
    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert "leaflet" in content.lower()
    assert "-23.55052" in content


def test_generate_json_and_markdown_reports(tmp_path: Path):
    items = [
        {
            "file_name": "foto1.jpg",
            "integrity": {
                "initial_hash": "c" * 64,
                "final_hash": "c" * 64,
                "is_intact": True,
                "status": "ÍNTEGRO",
            },
            "metadata": {
                "file_size_bytes": 1024,
                "has_gps": False,
                "notes": ["Sem coordenadas"],
            },
        }
    ]

    json_file = tmp_path / "relatorio.json"
    data = generate_json_report(items, case_info={"title": "Caso Teste"}, output_path=json_file)
    assert json_file.exists()
    assert data["case_info"]["custody_preserved"] is True

    md_file = tmp_path / "laudo.md"
    md_content = generate_markdown_report(items, case_info={"title": "Caso Teste"}, output_path=md_file)
    assert md_file.exists()
    assert "Art. 158-A" in md_content
    # Verifica que o hash está em bloco com respiro
    assert f"`{'c'*64}`" in md_content

