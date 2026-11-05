from pathlib import Path
from PIL import Image
from PIL.ExifTags import Base, IFD
from main import main, run_forensic_pipeline


def _create_sample_image(path: Path, with_gps: bool = False):
    img = Image.new("RGB", (64, 64), color="green")
    if with_gps:
        exif = img.getexif()
        exif[Base.Make] = "PericiaLab"
        exif[Base.Model] = "ModelX"
        exif[Base.DateTime] = "2026:11:05 12:00:00"

        gps_ifd = exif.get_ifd(IFD.GPSInfo)
        gps_ifd[1] = "S"
        gps_ifd[2] = (23, 33, 1.8)
        gps_ifd[3] = "W"
        gps_ifd[4] = (46, 38, 0.2)
        img.save(path, format="JPEG", exif=exif)
    else:
        img.save(path, format="PNG")


def test_cli_pipeline_execution(tmp_path: Path):
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.png"
    _create_sample_image(img1, with_gps=True)
    _create_sample_image(img2, with_gps=False)

    out_dir = tmp_path / "out"
    code = main([
        "--image", str(img1), str(img2),
        "--output", str(out_dir),
        "--title", "Caso Teste Integracao",
    ])

    assert code == 0
    assert (out_dir / "mapa_evidencias.html").exists()
    assert (out_dir / "relatorio_pericial.json").exists()
    assert (out_dir / "laudo_pericial.md").exists()


def test_cli_missing_image(capsys):
    code = main([])
    assert code == 1

