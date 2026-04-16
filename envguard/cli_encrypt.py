"""CLI sub-commands: encrypt and decrypt env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.encryptor import encrypt_env, decrypt_env
from envguard.parser import parse_env_file
from envguard.exporter import export_dotenv


def build_encrypt_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("encrypt", help="Encrypt sensitive values in an .env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--passphrase", required=True, help="Encryption passphrase")
    p.add_argument("--all", dest="all_keys", action="store_true", help="Encrypt all values")
    p.add_argument("--output", help="Write result to file instead of stdout")
    p.set_defaults(func=_run_encrypt)

    d = sub.add_parser("decrypt", help="Decrypt values in an encrypted .env file")
    d.add_argument("file", help="Path to encrypted .env file")
    d.add_argument("--passphrase", required=True, help="Decryption passphrase")
    d.add_argument("--all", dest="all_keys", action="store_true", help="Decrypt all values")
    d.add_argument("--output", help="Write result to file instead of stdout")
    d.set_defaults(func=_run_decrypt)


def _run_encrypt(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    env = parse_env_file(path)
    result = encrypt_env(env, args.passphrase, all_keys=args.all_keys)
    content = export_dotenv(result.encrypted)
    if args.output:
        Path(args.output).write_text(content)
        print(result.summary())
    else:
        print(content)
    return 0


def _run_decrypt(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    env = parse_env_file(path)
    decrypted = decrypt_env(env, args.passphrase, all_keys=args.all_keys)
    content = export_dotenv(decrypted)
    if args.output:
        Path(args.output).write_text(content)
        print("Decryption complete.")
    else:
        print(content)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="envguard-encrypt")
    sub = parser.add_subparsers(dest="command")
    build_encrypt_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
