import io
from PIL import Image
from PIL.ExifTags import Base, IFD
from src.extractor import (
    convert_dms_to_decimal,
    extract_metadata,
)


def test_convert_dms_to_decimal():
    # Coordenadas de São Paulo: 23° 33' 1.872" S, 46° 38' 0.27" W
    # 23 + 33/60 + 1.872/3600 = 23.55052
    lat = convert_dms_to_decimal((23, 33, 1.872), "S")
    assert lat == -23.55052

    lon = convert_dms_to_decimal((46, 38, 0.27), "W")
    assert lon == -46.633408

    # Hemisfério Norte / Leste
    lat_n = convert_dms_to_decimal((48, 51, 24), "N")
    assert lat_n == 48.856667

    # Entrada inválida
    assert convert_dms_to_decimal(None, "N") is None
    assert convert_dms_to_decimal([], "S") is None


def test_extract_metadata_image_without_exif():
    # Cria uma imagem simples sem EXIF
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    metadata = extract_metadata(data, file_name="imagem_sem_exif.png")
    assert metadata.file_name == "imagem_sem_exif.png"
    assert metadata.file_size_bytes == len(data)
    assert metadata.has_exif is False
    assert metadata.has_gps is False
    assert len(metadata.notes) > 0


def test_extract_metadata_with_exif_and_gps():
    # Cria imagem JPEG com EXIF e GPS
    img = Image.new("RGB", (100, 100), color="red")
    exif = img.getexif()

    # Make, Model, DateTime
    exif[Base.Make] = "PericiaLab Camera"
    exif[Base.Model] = "ForensicMark I"
    exif[Base.DateTime] = "2026:11:05 14:00:00"

    # GPS IFD
    gps_ifd = exif.get_ifd(IFD.GPSInfo)
    gps_ifd[1] = "S"  # GPSLatitudeRef
    gps_ifd[2] = (23, 33, 1.872)  # GPSLatitude
    gps_ifd[3] = "W"  # GPSLongitudeRef
    gps_ifd[4] = (46, 38, 0.27)  # GPSLongitude

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    data = buf.getvalue()

    metadata = extract_metadata(data, file_name="foto_pericial.jpg")
    assert metadata.has_exif is True
    assert metadata.make == "PericiaLab Camera"
    assert metadata.model == "ForensicMark I"
    assert metadata.has_gps is True
    assert metadata.latitude == -23.55052
    assert metadata.longitude == -46.633408

