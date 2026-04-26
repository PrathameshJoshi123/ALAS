import argparse
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate RSA key pair for data encryption at rest."
    )
    parser.add_argument(
        "--out-dir",
        default="keys",
        help="Directory to write private/public PEM files (default: keys)",
    )
    parser.add_argument(
        "--bits",
        type=int,
        default=2048,
        choices=[2048, 3072, 4096],
        help="RSA key size (default: 2048)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    private_key_path = out_dir / "data_rsa_private.pem"
    public_key_path = out_dir / "data_rsa_public.pem"

    if private_key_path.exists() or public_key_path.exists():
        raise RuntimeError(
            f"Refusing to overwrite existing keys in {out_dir}. "
            "Delete old files first if you want to regenerate."
        )

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=args.bits)
    public_key = private_key.public_key()

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_key_path.write_bytes(private_key_pem)
    public_key_path.write_bytes(public_key_pem)

    print("RSA key pair generated successfully")
    print(f"Private key: {private_key_path}")
    print(f"Public key : {public_key_path}")
    print("")
    print("Add these to your backend .env:")
    print(f"DATA_RSA_PRIVATE_KEY_PATH={private_key_path}")
    print(f"DATA_RSA_PUBLIC_KEY_PATH={public_key_path}")


if __name__ == "__main__":
    main()
