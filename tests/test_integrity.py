import hashlib
import io
from pathlib import Path

import pytest
from src.integrity import (
    CustodyIntegrityError,
    calculate_sha256,
    verify_integrity,
)


def test_calculate_sha256_bytes_and_stream(tmp_path: Path):
    data = b"Evidencia Forense Digital - CPP Art. 158-A"
    expected_hash = hashlib.sha256(data).hexdigest().lower()

    # Teste com bytes brutos
    assert calculate_sha256(data) == expected_hash

    # Teste com BytesIO
    buf = io.BytesIO(data)
    assert calculate_sha256(buf) == expected_hash
    # Garante que a posição do stream foi preservada
    assert buf.tell() == 0

    # Teste com arquivo em disco
    file_path = tmp_path / "teste_evidencia.bin"
    file_path.write_bytes(data)
    assert calculate_sha256(file_path) == expected_hash


def test_verify_integrity_success():
    dummy_hash = "a" * 64
    report = verify_integrity(dummy_hash, dummy_hash, target_name="foto1.jpg")

    assert report.is_intact is True
    assert report.status == "ÍNTEGRO"
    assert "Art. 158-A" in report.legal_basis
    assert report.initial_hash == dummy_hash
    assert report.final_hash == dummy_hash


def test_verify_integrity_divergence():
    hash_1 = "a" * 64
    hash_2 = "b" * 64

    report = verify_integrity(hash_1, hash_2, target_name="foto1.jpg")
    assert report.is_intact is False
    assert report.status == "VIOLADO"

    with pytest.raises(CustodyIntegrityError):
        verify_integrity(hash_1, hash_2, target_name="foto1.jpg", raise_on_divergence=True)

