from __future__ import annotations

import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import pbkdf2_hmac
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> str:
    # Mantém o DB dentro do projeto (facilita entregar o trabalho).
    # Pode ser sobrescrito com MERCADINHO_DB_PATH.
    return os.getenv("MERCADINHO_DB_PATH", os.path.abspath("mercadinho.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                sobrenome TEXT NOT NULL,
                senha_salt BLOB NOT NULL,
                senha_hash BLOB NOT NULL,
                criado_em TEXT NOT NULL,
                ultimo_login_em TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _hash_senha(senha: str, salt: bytes) -> bytes:
    return pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 120_000)


def criar_usuario(email: str, senha: str, nome: str, sobrenome: str) -> dict[str, Any]:
    init_db()
    uid = f"usr-{uuid.uuid4()}"
    salt = os.urandom(16)
    h = _hash_senha(senha, salt)
    agora = _utc_now_iso()

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO usuarios (id, email, nome, sobrenome, senha_salt, senha_hash, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (uid, email.lower().strip(), nome.strip(), sobrenome.strip(), salt, h, agora),
        )
        conn.commit()
        return {"id": uid, "email": email.lower().strip(), "nome": nome.strip(), "sobrenome": sobrenome.strip()}
    finally:
        conn.close()


def obter_usuario_por_email(email: str) -> dict[str, Any] | None:
    init_db()
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def marcar_login(usuario_id: str) -> None:
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE usuarios SET ultimo_login_em = ? WHERE id = ?",
            (_utc_now_iso(), usuario_id),
        )
        conn.commit()
    finally:
        conn.close()


def validar_credenciais(email: str, senha: str) -> dict[str, Any] | None:
    u = obter_usuario_por_email(email)
    if not u:
        return None
    salt = u["senha_salt"]
    esperado = u["senha_hash"]
    atual = _hash_senha(senha, salt)
    if atual != esperado:
        return None
    marcar_login(u["id"])
    return u

