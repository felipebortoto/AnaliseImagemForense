"""Interface de Linha de Comando (CLI) para Análise de Imagem Forense.

Conformidade estrita com a Cadeia de Custódia (Art. 158-A do CPP).
Executa o fluxo completo:
1. Fixação de Hash SHA-256 pré-leitura.
2. Extração segura de metadados EXIF e geolocalização.
3. Verificação pós-leitura de integridade probatória.
4. Geração de Mapa Interativo (Folium), Relatório JSON e Laudo Pericial (.md).
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path
from typing import Sequence

from src.extractor import extract_metadata
from src.integrity import calculate_sha256, verify_integrity
from src.reporter import (
    generate_folium_map,
    generate_json_report,
    generate_markdown_report,
)


def run_forensic_pipeline(
    image_paths: list[Path],
    output_dir: Path,
    case_title: str = "Exame Forense de Mídias",
    examiner: str = "Perito Forense",
    strict: bool = False,
) -> dict:
    """Executa o pipeline forense completo para uma lista de imagens."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    print("\n" + "=" * 70)
    print(" INICIANDO EXAME FORENSE DE MÍDIAS DIGITAIS (Art. 158-A CPP)")
    print("=" * 70)
    print(f"Total de arquivos a examinar: {len(image_paths)}")
    print(f"Diretório de saída: {output_dir.resolve()}\n")

    for idx, img_path in enumerate(image_paths, start=1):
        if not img_path.is_file():
            print(f"[-] [{idx}/{len(image_paths)}] Arquivo não encontrado: {img_path}")
            continue

        filename = img_path.name
        print(f"[*] [{idx}/{len(image_paths)}] Processando: {filename}")

        # 1. Fixação do Hash Inicial (Pré-processamento)
        pre_hash = calculate_sha256(img_path)
        print(f"    -> SHA-256 Pré : {pre_hash}")

        # 2. Extração segura de metadados
        metadata = extract_metadata(img_path, file_name=filename)
        if metadata.has_exif:
            print(f"    -> EXIF        : Detectado ({metadata.make or 'Marca desconhecida'} {metadata.model or ''})")
            if metadata.has_gps:
                print(f"    -> GPS         : Lat {metadata.latitude}, Lon {metadata.longitude}")
            else:
                print("    -> GPS         : Não identificado")
        else:
            print("    -> EXIF        : Ausente ou removido")

        # 3. Recálculo e Verificação do Hash Final (Pós-processamento)
        post_hash = calculate_sha256(img_path)
        print(f"    -> SHA-256 Pós : {post_hash}")

        integrity = verify_integrity(
            initial_hash=pre_hash,
            final_hash=post_hash,
            target_name=filename,
            raise_on_divergence=strict,
        )

        status_symbol = "[✓] ÍNTEGRO" if integrity.is_intact else "[✗] VIOLADO"
        print(f"    -> Status CPP  : {status_symbol}\n")

        results.append({
            "file_name": filename,
            "source_path": str(img_path.resolve()),
            "integrity": integrity.to_dict(),
            "metadata": metadata.to_dict(),
        })

    if not results:
        print("[!] Nenhuma evidência válida foi processada.")
        return {"evidences": []}

    case_info = {
        "title": case_title,
        "examiner": examiner,
    }

    # 4. Geração dos entregáveis forenses
    map_path = output_dir / "mapa_evidencias.html"
    json_path = output_dir / "relatorio_pericial.json"
    md_path = output_dir / "laudo_pericial.md"

    generate_folium_map(results, output_path=map_path)
    generate_json_report(results, case_info=case_info, output_path=json_path)
    generate_markdown_report(results, case_info=case_info, output_path=md_path)

    print("=" * 70)
    print(" EXAME CONCLUÍDO COM SUCESSO")
    print("=" * 70)
    print(f"-> Mapa Interativo HTML : {map_path.resolve()}")
    print(f"-> Relatório JSON       : {json_path.resolve()}")
    print(f"-> Laudo em Markdown    : {md_path.resolve()}")
    print("=" * 70 + "\n")

    return {
        "evidences": results,
        "map_path": str(map_path),
        "json_path": str(json_path),
        "md_path": str(md_path),
    }


def resolve_image_patterns(patterns: list[str]) -> list[Path]:
    """Resolve caminhos literais ou padrões glob de imagens."""
    resolved: list[Path] = []
    for pat in patterns:
        matched = glob.glob(pat, recursive=True)
        if matched:
            resolved.extend([Path(m) for m in matched if Path(m).is_file()])
        else:
            p = Path(pat)
            if p.is_file():
                resolved.append(p)
    return list(dict.fromkeys(resolved))  # Remove duplicatas preservando ordem


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        prog="analise-forense",
        description="Sistema de Extração de Metadados Forenses e Cadeia de Custódia (Art. 158-A CPP)",
    )
    parser.add_argument(
        "-i",
        "--image",
        nargs="+",
        required=False,
        help="Caminho(s) de imagem ou padrão glob (ex: --image foto1.jpg fotos/*.jpg)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Diretório onde os laudos e mapas serão gravados (padrão: output/)",
    )
    parser.add_argument(
        "--title",
        default="Exame Pericial de Evidências Digitais",
        help="Título da investigação ou operação pericial",
    )
    parser.add_argument(
        "--examiner",
        default="Laboratório de Computação Forense",
        help="Nome do perito responsável ou examinador",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Interrompe com erro caso haja divergência no hash pré/pós",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Inicia o servidor web interativo FastAPI com interface Tailwind CSS",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta para o servidor web (padrão: 8000)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada da CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.web:
        import uvicorn
        print(f"[*] Iniciando servidor web pericial em http://127.0.0.1:{args.port} ...")
        uvicorn.run("src.server:app", host="127.0.0.1", port=args.port, reload=False)
        return 0

    if not args.image:
        parser.print_help()
        print("\n[!] Informe ao menos uma imagem através de --image ou utilize --web para iniciar a interface gráfica.")
        return 1

    images = resolve_image_patterns(args.image)
    if not images:
        print(f"[!] Nenhuma imagem válida localizada com o padrão: {args.image}")
        return 1

    try:
        run_forensic_pipeline(
            image_paths=images,
            output_dir=Path(args.output),
            case_title=args.title,
            examiner=args.examiner,
            strict=args.strict,
        )
        return 0
    except Exception as exc:
        print(f"\n[ERRO CRÍTICO] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
