"""
Quantum-Safe Security Routes
==============================

API endpoints for demonstrating quantum-safe cryptography.

Endpoints:
    GET  /demo          - Get PQC demonstration information
    POST /generate-keys - Generate quantum-safe key pairs
    POST /encrypt       - Encrypt data with quantum-safe encryption
    POST /decrypt       - Decrypt quantum-safe encrypted data
    POST /sign          - Create a quantum-safe digital signature
    POST /verify        - Verify a quantum-safe signature
    POST /protect-secret - Protect a secret with PQC
"""
import logging
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.quantum_safe.crypto import get_quantum_safe_crypto

logger = logging.getLogger(__name__)
router = APIRouter()


class KeyGenRequest(BaseModel):
    algorithm: str = "CRYSTALS-Kyber"


class EncryptRequest(BaseModel):
    data: str
    public_key_hex: str


class DecryptRequest(BaseModel):
    ciphertext_hex: str
    encapsulated_key_hex: str
    nonce_hex: str
    private_key_hex: str


class SignRequest(BaseModel):
    message: str
    private_key_hex: str


class VerifyRequest(BaseModel):
    message: str
    signature_hex: str
    public_key_hex: str


class ProtectSecretRequest(BaseModel):
    secret: str
    purpose: str = "general"


@router.get("/demo")
async def get_pqc_demo(
    current_user: User = Depends(get_current_user),
):
    """Get quantum-safe cryptography demonstration information."""
    crypto = get_quantum_safe_crypto()
    return crypto.get_demo_info()


@router.post("/generate-keys")
async def generate_keys(
    request: KeyGenRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate quantum-safe key pairs."""
    crypto = get_quantum_safe_crypto()

    if "Kyber" in request.algorithm:
        keypair = crypto.generate_kem_keypair(request.algorithm)
    else:
        keypair = crypto.generate_signature_keypair(request.algorithm)

    return {
        "key_id": keypair.key_id,
        "algorithm": keypair.algorithm,
        "public_key": keypair.public_key.hex(),
        "private_key": keypair.private_key.hex(),
        "created_at": keypair.created_at.isoformat(),
        "message": (
            f"Generated {keypair.algorithm} key pair. "
            f"In production, the private key would be stored in an HSM "
            f"and never exposed. This demonstration shows both keys for verification."
        ),
    }


@router.post("/encrypt")
async def encrypt_data(
    request: EncryptRequest,
    current_user: User = Depends(get_current_user),
):
    """Encrypt data using quantum-safe encryption."""
    crypto = get_quantum_safe_crypto()
    public_key = bytes.fromhex(request.public_key_hex)
    encrypted = crypto.encrypt_data(request.data.encode("utf-8"), public_key)

    return {
        "ciphertext": encrypted.ciphertext.hex(),
        "encapsulated_key": encrypted.encapsulated_key.hex(),
        "nonce": encrypted.nonce.hex(),
        "algorithm": encrypted.algorithm,
        "message": "Data encrypted using Kyber key encapsulation + AES encryption",
    }


@router.post("/decrypt")
async def decrypt_data(
    request: DecryptRequest,
    current_user: User = Depends(get_current_user),
):
    """Decrypt quantum-safe encrypted data."""
    from app.quantum_safe.crypto import EncryptedData
    crypto = get_quantum_safe_crypto()
    private_key = bytes.fromhex(request.private_key_hex)

    encrypted = EncryptedData(
        ciphertext=bytes.fromhex(request.ciphertext_hex),
        encapsulated_key=bytes.fromhex(request.encapsulated_key_hex),
        nonce=bytes.fromhex(request.nonce_hex),
        algorithm="Kyber-AES256-GCM",
        key_id="",
    )

    decrypted = crypto.decrypt_data(encrypted, private_key)
    return {"plaintext": decrypted.decode("utf-8").rstrip("\x00")}


@router.post("/sign")
async def sign_message(
    request: SignRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a quantum-safe digital signature."""
    crypto = get_quantum_safe_crypto()
    private_key = bytes.fromhex(request.private_key_hex)
    sig = crypto.sign(request.message.encode("utf-8"), private_key)
    return {
        "signature": sig.signature_bytes.hex(),
        "algorithm": sig.algorithm,
        "message": "Message signed using CRYSTALS-Dilithium",
    }


@router.post("/verify")
async def verify_signature(
    request: VerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a quantum-safe digital signature."""
    from app.quantum_safe.crypto import Signature
    crypto = get_quantum_safe_crypto()
    public_key = bytes.fromhex(request.public_key_hex)
    sig = Signature(
        signature_bytes=bytes.fromhex(request.signature_hex),
        algorithm="CRYSTALS-Dilithium",
    )
    is_valid = crypto.verify(request.message.encode("utf-8"), sig, public_key)
    return {"is_valid": is_valid, "message": "Signature is valid" if is_valid else "Signature is INVALID"}


@router.post("/protect-secret")
async def protect_secret(
    request: ProtectSecretRequest,
    current_user: User = Depends(get_current_user),
):
    """Protect a sensitive secret using quantum-safe encryption."""
    crypto = get_quantum_safe_crypto()
    protected = crypto.protect_secret(request.secret, request.purpose)
    return {
        **protected,
        "message": (
            "Secret protected using CRYSTALS-Kyber encryption + CRYSTALS-Dilithium signing. "
            "This ensures the secret remains secure even against quantum computer attacks."
        ),
    }
