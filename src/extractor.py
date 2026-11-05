"""Engine de extração pericial de metadados e conversão geodésica (Pillow).

Lê metadados EXIF sem adulteração do arquivo, converte coordenadas GPS
(DMS para graus decimais com sinal hemisférico) e trata com resiliência
imagens corrompidas ou sem metadados (stripping por WhatsApp/Telegram).
"""

from __future__ import annotations

import io
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from PIL import ExifTags, Image, UnidentifiedImageError


@dataclass
class EvidenceMetadata:
    """Estrutura pericial padronizada dos metadados extraídos de uma imagem."""

    file_name: str
    file_size_bytes: int
    has_exif: bool = False
    make: Optional[str] = None
    model: Optional[str] = None
    software: Optional[str] = None
    datetime_original: Optional[str] = None
    datetime_iso: Optional[str] = None
    has_gps: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    notes: list[str] = field(default_factory=list)
    raw_tags: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rational_to_float(value: Any) -> float:
    """Converte números IFDRational ou tuplas de frações para float."""
    if isinstance(value, (int, float)):
        return float(value)
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return float(value.numerator) / float(value.denominator) if value.denominator != 0 else 0.0
    if isinstance(value, (tuple, list)) and len(value) == 2:
        num, den = value
        return float(num) / float(den) if den != 0 else 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def convert_dms_to_decimal(dms: Any, ref: Optional[str]) -> Optional[float]:
    """Converte coordenadas em Graus, Minutos e Segundos (DMS) para Graus Decimais.

    Aplica sinal negativo para os hemisférios Sul ('S') e Oeste ('W').

    Args:
        dms: Tupla ou lista (graus, minutos, segundos).
        ref: Referência cardinal ('N', 'S', 'E', 'W').

    Returns:
        Valor float em graus decimais ou None se inválido.
    """
    if not dms or not isinstance(dms, (tuple, list)) or len(dms) < 3:
        return None

    try:
        degrees = _rational_to_float(dms[0])
        minutes = _rational_to_float(dms[1])
        seconds = _rational_to_float(dms[2])

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        if ref and str(ref).strip().upper() in ("S", "W"):
            decimal = -decimal

        return round(decimal, 6)
    except Exception:
        return None


def _parse_iso_datetime(dt_str: Optional[str]) -> Optional[str]:
    """Tenta converter a string EXIF 'YYYY:MM:DD HH:MM:SS' para formato ISO 8601."""
    if not dt_str:
        return None

    dt_str = str(dt_str).strip()
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S%z",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(dt_str, fmt)
            return parsed.isoformat()
        except ValueError:
            continue
    return dt_str


def extract_metadata(
    source: Union[str, Path, BinaryIO, bytes],
    file_name: str = "imagem_evidencia",
) -> EvidenceMetadata:
    """Extrai metadados forenses e dados GPS de uma imagem de forma segura.

    Args:
        source: Caminho para o arquivo, buffer binário ou bytes da imagem.
        file_name: Nome de exibição da evidência.

    Returns:
        Instância de EvidenceMetadata com os dados compilados e normalizados.
    """
    notes: list[str] = []
    size_bytes = 0

    # Determinar tamanho do arquivo
    if isinstance(source, bytes):
        size_bytes = len(source)
        stream = io.BytesIO(source)
    elif isinstance(source, (str, Path)):
        p = Path(source)
        file_name = p.name
        size_bytes = p.stat().st_size if p.exists() else 0
        with p.open("rb") as f:
            stream = io.BytesIO(f.read())
    elif hasattr(source, "read"):
        current_pos = source.tell() if hasattr(source, "tell") else 0
        data = source.read()
        size_bytes = len(data)
        stream = io.BytesIO(data)
        if hasattr(source, "seek"):
            source.seek(current_pos)
    else:
        raise TypeError(f"Fonte de imagem não suportada: {type(source)}")

    result = EvidenceMetadata(
        file_name=file_name,
        file_size_bytes=size_bytes,
        notes=notes,
    )

    try:
        with Image.open(stream) as img:
            raw_exif_dict: dict[str, Any] = {}

            # Obtém EXIF primário
            exif = img.getexif()
            if not exif:
                notes.append("Cabeçalho EXIF ausente (provável compressão ou remoção de metadados).")
                return result

            # Dicionário mapeado com nomes legíveis
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, f"Tag_{tag_id}")
                # Evita strings binárias imensas
                if isinstance(value, bytes) and len(value) > 256:
                    value = f"<Binary Data: {len(value)} bytes>"
                raw_exif_dict[tag_name] = str(value)

            result.has_exif = True
            result.make = raw_exif_dict.get("Make")
            result.model = raw_exif_dict.get("Model")
            result.software = raw_exif_dict.get("Software")

            # DateTimeOriginal costuma residir no IFD EXIF (0x8769)
            exif_ifd = {}
            try:
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
            except Exception:
                pass

            dt_original = None
            if exif_ifd:
                for sub_tag_id, sub_value in exif_ifd.items():
                    sub_tag_name = ExifTags.TAGS.get(sub_tag_id, f"SubTag_{sub_tag_id}")
                    raw_exif_dict[sub_tag_name] = str(sub_value)
                    if sub_tag_name in ("DateTimeOriginal", "DateTimeDigitized") and not dt_original:
                        dt_original = str(sub_value)

            if not dt_original:
                dt_original = raw_exif_dict.get("DateTimeOriginal") or raw_exif_dict.get("DateTime")

            if dt_original:
                result.datetime_original = dt_original
                result.datetime_iso = _parse_iso_datetime(dt_original)

            # Extração de GPS (IFD 0x8825)
            gps_ifd = {}
            try:
                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            except Exception:
                pass

            if gps_ifd:
                gps_data: dict[str, Any] = {}
                for gps_tag_id, val in gps_ifd.items():
                    gps_tag_name = ExifTags.GPSTAGS.get(gps_tag_id, f"GPS_{gps_tag_id}")
                    gps_data[gps_tag_name] = val

                lat = convert_dms_to_decimal(
                    gps_data.get("GPSLatitude"),
                    gps_data.get("GPSLatitudeRef"),
                )
                lon = convert_dms_to_decimal(
                    gps_data.get("GPSLongitude"),
                    gps_data.get("GPSLongitudeRef"),
                )
                alt = None
                if "GPSAltitude" in gps_data:
                    alt = _rational_to_float(gps_data["GPSAltitude"])
                    if gps_data.get("GPSAltitudeRef") == 1:  # 1 = Abaixo do nível do mar
                        alt = -alt

                if lat is not None and lon is not None:
                    result.has_gps = True
                    result.latitude = lat
                    result.longitude = lon
                    result.altitude = alt
                else:
                    notes.append("Dados de GPS parciais ou inválidos no bloco EXIF.")
            else:
                notes.append("Sem coordenadas de GPS registradas no EXIF.")

            result.raw_tags = raw_exif_dict

    except UnidentifiedImageError:
        notes.append("Arquivo não identificado como formato de imagem válido.")
    except Exception as exc:
        notes.append(f"Exceção durante parsing de metadados: {type(exc).__name__} - {exc}")

    return result

