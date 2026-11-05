"""Módulo de integridade pericial e garantia da Cadeia de Custódia (Art. 158-A do CPP).

Responsável pelo cálculo criptográfico do hash SHA-256 em blocos binários
e pela verificação estrita de inviolabilidade probatória pré e pós-análise.
"""

from __future__ import annotations

import hashlib
import io
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Union


class CustodyIntegrityError(Exception):
    """Exceção levantada quando há divergência de integridade na evidência digital."""
    pass


@dataclass(frozen=True)
class IntegrityReport:
    """Ateste de integridade pericial de acordo com o Art. 158-A do CPP."""

    target_name: str
    initial_hash: str
    final_hash: str
    is_intact: bool
    status: str
    timestamp_utc: str
    legal_basis: str = "Conformidade com a Cadeia de Custódia (Art. 158-A do Código de Processo Penal)"

    def to_dict(self) -> dict:
        return {
            "target_name": self.target_name,
            "initial_hash": self.initial_hash,
            "final_hash": self.final_hash,
            "is_intact": self.is_intact,
            "status": self.status,
            "timestamp_utc": self.timestamp_utc,
            "legal_basis": self.legal_basis,
        }


def calculate_sha256(
    source: Union[str, Path, BinaryIO, bytes],
    chunk_size: int = 65536,
) -> str:
    """Calcula o hash SHA-256 de um arquivo em disco, buffer binário ou bytes.

    Lê os dados estritamente em modo binário somente-leitura ('rb') em chunks
    de 64KB (65536 bytes) para preservar o arquivo e otimizar memória.

    Args:
        source: Caminho do arquivo (str/Path), stream binário (BinaryIO) ou bytes.
        chunk_size: Tamanho do bloco de leitura em bytes (padrão: 64KB).

    Returns:
        String hexadecimal minúscula de 64 caracteres.
    """
    hasher = hashlib.sha256()

    if isinstance(source, bytes):
        hasher.update(source)
        return hasher.hexdigest().lower()

    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo de evidência não encontrado: {path}")

        with path.open("rb") as stream:
            while chunk := stream.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    if hasattr(source, "read"):
        # Garante início do buffer e restaura após leitura
        initial_pos = source.tell() if hasattr(source, "tell") else None
        if initial_pos is not None and initial_pos != 0:
            source.seek(0)

        while chunk := source.read(chunk_size):
            hasher.update(chunk)

        if initial_pos is not None:
            source.seek(initial_pos)

        return hasher.hexdigest().lower()

    raise TypeError(f"Tipo de fonte não suportado para cálculo de hash: {type(source)}")


def verify_integrity(
    initial_hash: str,
    final_hash: str,
    target_name: str = "evidencia",
    raise_on_divergence: bool = False,
) -> IntegrityReport:
    """Verifica e documenta formalmente a integridade da evidência.

    Compara o hash SHA-256 inicial (fixação pré-análise) com o hash final
    (verificação pós-análise).

    Args:
        initial_hash: Hash SHA-256 calculado na fixação inicial.
        final_hash: Hash SHA-256 calculado após o exame pericial.
        target_name: Identificador ou nome do arquivo.
        raise_on_divergence: Se True, lança CustodyIntegrityError caso divirjam.

    Returns:
        Instância de IntegrityReport com o parecer pericial.
    """
    initial_clean = (initial_hash or "").strip().lower()
    final_clean = (final_hash or "").strip().lower()

    is_intact = bool(initial_clean and final_clean and (initial_clean == final_clean))
    status = "ÍNTEGRO" if is_intact else "VIOLADO"
    now_utc = datetime.now(timezone.utc).isoformat()

    report = IntegrityReport(
        target_name=target_name,
        initial_hash=initial_clean,
        final_hash=final_clean,
        is_intact=is_intact,
        status=status,
        timestamp_utc=now_utc,
    )

    if not is_intact and raise_on_divergence:
        raise CustodyIntegrityError(
            f"Alerta de Cadeia de Custódia: Divergência detectada para '{target_name}'. "
            f"Inicial: {initial_clean} != Final: {final_clean}"
        )

    return report

