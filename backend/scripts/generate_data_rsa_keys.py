import argparse
import base64
import secrets
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate AES-256 key for data encryption at rest."
    )
    parser.add_argument(
        "--out-file",
        default="keys/data_aes256.key",
        help="Path to write base64-encoded AES-256 key (default: keys/data_aes256.key)",
    )
    args = parser.parse_args()

    out_file = Path(args.out_file).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    if out_file.exists():
        raise RuntimeError(
            f"Refusing to overwrite existing key file at {out_file}. "
            "Delete old file first if you want to regenerate."
        )

    key = secrets.token_bytes(32)
    key_b64 = base64.urlsafe_b64encode(key).decode("utf-8")
    out_file.write_text(key_b64, encoding="utf-8")

    print("AES-256 key generated successfully")
    print(f"Key file: {out_file}")
    print("")
    print("Add these to your backend .env:")
    print(f"DATA_AES256_KEY_PATH={out_file}")
    print("or")
    print(f"DATA_AES256_KEY_B64={key_b64}")


if __name__ == "__main__":
    main()
