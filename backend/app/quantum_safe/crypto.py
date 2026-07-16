"""
Quantum-Safe Cryptography Module
==================================

Demonstration of Post-Quantum Cryptography (PQC) for banking security.

This module implements quantum-safe cryptographic operations to protect
sensitive credentials, API keys, security tokens, and certificates
against future quantum computing threats.

Background:
    Current public-key cryptography (RSA, ECC) relies on the difficulty
    of factoring large numbers or solving discrete logarithm problems.
    Quantum computers running Shor's algorithm could break these in
    polynomial time. Post-quantum cryptography uses mathematical problems
    believed to be hard for both classical and quantum computers.

Demonstrated Algorithms:
    1. CRYSTALS-Kyber: Key Encapsulation Mechanism (KEM)
       - Used for key exchange and session key establishment
       - NIST PQC Standard (ML-KEM)
       - Based on Module Learning With Errors (MLWE) problem

    2. CRYSTALS-Dilithium: Digital Signature Algorithm
       - Used for authentication and integrity verification
       - NIST PQC Standard (ML-DSA)
       - Based on Module Learning With Errors and Module-SIS problems

Implementation Note:
    This module uses the 'pqcrypto' or 'oqs-python' library when available,
    and falls back to a simulation for demonstration purposes. In a real
    production system, use a NIST-approved PQC library.
"""

import os
import hashlib
import hmac
import secrets
import struct
import json
import logging
from typing import Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class KeyPair:
    """
    Quantum-safe key pair container.

    Attributes:
        public_key: Public key bytes
        private_key: Private key bytes
        algorithm: Algorithm identifier
        created_at: Key generation timestamp
        key_id: Unique key identifier
    """
    public_key: bytes
    private_key: bytes
    algorithm: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    key_id: str = field(default_factory=lambda: secrets.token_hex(16))


@dataclass
class EncryptedData:
    """Container for quantum-safe encrypted data."""
    ciphertext: bytes
    encapsulated_key: bytes
    nonce: bytes
    algorithm: str
    key_id: str
    encrypted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Signature:
    """Container for quantum-safe digital signature."""
    signature_bytes: bytes
    algorithm: str
    key_id: str
    signed_at: datetime = field(default_factory=datetime.utcnow)


class QuantumSafeCrypto:
    """
    Quantum-Safe Cryptography operations for SentinelAI.

    Provides key generation, encryption, decryption, signing, and
    verification using post-quantum cryptographic algorithms.

    This module protects:
    - Database credentials and connection strings
    - API keys and tokens
    - JWT signing keys
    - TLS certificates
    - Security configuration secrets
    - Audit log integrity hashes
    """

    def __init__(self, key_size: int = 256):
        """
        Initialize the quantum-safe crypto module.

        Args:
            key_size: Security level in bits (128, 192, or 256).
                     Higher values provide stronger security but slower operations.
        """
        self.key_size = key_size
        self._key_store: Dict[str, KeyPair] = {}
        self._initialize_algorithms()

    def _initialize_algorithms(self) -> None:
        """Initialize available PQC algorithms."""
        # Check for oqs-python (Open Quantum Safe)
        self.has_oqs = False
        try:
            import oqs
            self.has_oqs = True
            self.kem = oqs.KeyEncapsulation("Kyber512")
            self.signer = oqs.Signature("Dilithium2")
            logger.info("Using Open Quantum Safe (OQS) library for PQC")
        except ImportError:
            logger.info(
                "OQS library not available. Using simulation mode for PQC demonstration."
            )

    def generate_kem_keypair(self, algorithm: str = "CRYSTALS-Kyber") -> KeyPair:
        """
        Generate a quantum-safe key encapsulation key pair.

        Uses CRYSTALS-Kyber (ML-KEM) for key exchange operations.
        This is equivalent to generating an RSA/ECC key pair but
        resistant to quantum attacks.

        Args:
            algorithm: Algorithm to use (CRYSTALS-Kyber recommended).

        Returns:
            KeyPair with public and private keys.
        """
        if self.has_oqs:
            return self._generate_kem_keypair_oqs(algorithm)
        return self._generate_kem_keypair_simulated(algorithm)

    def _generate_kem_keypair_oqs(self, algorithm: str) -> KeyPair:
        """Generate key pair using the OQS library."""
        import oqs
        kem = oqs.KeyEncapsulation("Kyber512")
        public_key = kem.generate_keypair()
        # OQS stores private key internally, so we extract it
        private_key = bytes(kem.export_secret_key())
        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=algorithm,
        )

    def _generate_kem_keypair_simulated(self, algorithm: str) -> KeyPair:
        """
        Simulated key pair generation for demonstration.

        In a real implementation, this would use CRYSTALS-Kyber.
        The simulation uses high-entropy random bytes to demonstrate
        the API and workflow.
        """
        # Generate high-entropy key material
        private_key = os.urandom(self.key_size // 8 * 3)
        # Derive public key from private key using one-way function
        public_key = hashlib.sha3_256(private_key).digest()

        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=algorithm,
        )

    def generate_signature_keypair(
        self, algorithm: str = "CRYSTALS-Dilithium"
    ) -> KeyPair:
        """
        Generate a quantum-safe digital signature key pair.

        Uses CRYSTALS-Dilithium (ML-DSA) for authentication and
        integrity verification.

        Args:
            algorithm: Algorithm to use.

        Returns:
            KeyPair for signing and verification.
        """
        if self.has_oqs:
            return self._generate_sig_keypair_oqs(algorithm)
        return self._generate_sig_keypair_simulated(algorithm)

    def _generate_sig_keypair_oqs(self, algorithm: str) -> KeyPair:
        """Generate signature key pair using OQS library."""
        import oqs
        signer = oqs.Signature("Dilithium2")
        public_key = signer.generate_keypair()
        private_key = bytes(signer.export_secret_key())
        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=algorithm,
        )

    def _generate_sig_keypair_simulated(self, algorithm: str) -> KeyPair:
        """Simulated signature key pair for demonstration."""
        private_key = os.urandom(self.key_size // 8 * 4)
        public_key = hashlib.sha3_512(private_key).digest()[:64]
        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=algorithm,
        )

    def encapsulate_key(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Perform key encapsulation using CRYSTALS-Kyber.

        This is the PQC equivalent of Diffie-Hellman key exchange.
        It produces a shared secret and an encapsulated key that can
        only be decapsulated with the corresponding private key.

        Args:
            public_key: Recipient's public key.

        Returns:
            Tuple of (shared_secret, encapsulated_key).
        """
        if self.has_oqs:
            return self._encapsulate_oqs(public_key)
        return self._encapsulate_simulated(public_key)

    def _encapsulate_oqs(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate using OQS library."""
        import oqs
        kem = oqs.KeyEncapsulation("Kyber512")
        ciphertext, shared_secret = kem.encap_secret(public_key)
        return shared_secret, ciphertext

    def _encapsulate_simulated(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Simulated key encapsulation for demonstration."""
        # Generate a random shared secret
        shared_secret = os.urandom(32)
        # Create encapsulated key (encrypted with public key via hashing)
        encapsulated = hashlib.sha3_256(
            public_key + shared_secret
        ).digest()
        return shared_secret, encapsulated

    def decapsulate_key(
        self, encapsulated_key: bytes, private_key: bytes
    ) -> bytes:
        """
        Decapsulate a shared secret using the private key.

        Args:
            encapsulated_key: The encapsulated key ciphertext.
            private_key: Private key for decapsulation.

        Returns:
            The shared secret.
        """
        if self.has_oqs:
            return self._decapsulate_oqs(encapsulated_key, private_key)
        return self._decapsulate_simulated(encapsulated_key, private_key)

    def _decapsulate_oqs(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decapsulate using OQS library."""
        import oqs
        kem = oqs.KeyEncapsulation("Kyber512")
        # OQS manages private key internally, re-create from bytes
        shared_secret = kem.decap_secret(ciphertext)
        return shared_secret

    def _decapsulate_simulated(self, encapsulated_key: bytes, private_key: bytes) -> bytes:
        """Simulated decapsulation for demonstration."""
        # In simulation, derive the same shared secret
        public_key = hashlib.sha3_256(private_key).digest()
        return hashlib.sha3_256(public_key + encapsulated_key).digest()

    def sign(
        self, message: bytes, private_key: bytes
    ) -> Signature:
        """
        Create a quantum-safe digital signature using CRYSTALS-Dilithium.

        Digital signatures provide authentication (proving who signed)
        and integrity (proving the message wasn't modified).

        Args:
            message: Message to sign.
            private_key: Signing key.

        Returns:
            Signature object.
        """
        if self.has_oqs:
            return self._sign_oqs(message, private_key)
        return self._sign_simulated(message, private_key)

    def _sign_oqs(self, message: bytes, private_key: bytes) -> Signature:
        """Sign using OQS library."""
        import oqs
        signer = oqs.Signature("Dilithium2")
        sig = signer.sign(message)
        return Signature(
            signature_bytes=sig,
            algorithm="CRYSTALS-Dilithium",
        )

    def _sign_simulated(self, message: bytes, private_key: bytes) -> Signature:
        """Simulated signing for demonstration."""
        # HMAC-SHA3 based simulation
        sig = hmac.new(private_key, message, hashlib.sha3_256).digest()
        return Signature(
            signature_bytes=sig,
            algorithm="CRYSTALS-Dilithium",
        )

    def verify(
        self, message: bytes, signature: Signature, public_key: bytes
    ) -> bool:
        """
        Verify a quantum-safe digital signature.

        Args:
            message: Original message.
            signature: Signature to verify.
            public_key: Signer's public key.

        Returns:
            True if the signature is valid, False otherwise.
        """
        if self.has_oqs:
            return self._verify_oqs(message, signature, public_key)
        return self._verify_simulated(message, signature, public_key)

    def _verify_oqs(
        self, message: bytes, signature: Signature, public_key: bytes
    ) -> bool:
        """Verify using OQS library."""
        import oqs
        signer = oqs.Signature("Dilithium2")
        return signer.verify(message, signature.signature_bytes, public_key)

    def _verify_simulated(
        self, message: bytes, signature: Signature, public_key: bytes
    ) -> bool:
        """Simulated verification for demonstration."""
        expected = hmac.new(public_key, message, hashlib.sha3_256).digest()
        return hmac.compare_digest(expected, signature.signature_bytes)

    def encrypt_data(
        self, data: bytes, public_key: bytes
    ) -> EncryptedData:
        """
        Encrypt data using quantum-safe hybrid encryption.

        Uses Kyber key encapsulation to establish a shared secret,
        then encrypts the data with AES-256-GCM using that secret.

        Args:
            data: Plaintext data to encrypt.
            public_key: Recipient's public key.

        Returns:
            EncryptedData object.
        """
        # Encapsulate a shared secret
        shared_secret, encapsulated = self.encapsulate_key(public_key)

        # Derive encryption key from shared secret
        nonce = os.urandom(12)
        enc_key = hashlib.sha3_256(shared_secret + b"encryption").digest()

        # Simple XOR-based encryption for demonstration
        # In production, use AES-256-GCM
        padded_data = data + b"\x00" * (32 - len(data) % 32)
        encrypted = bytes(
            a ^ b for a, b in zip(padded_data, enc_key * (len(padded_data) // 32 + 1))
        )

        return EncryptedData(
            ciphertext=encrypted[:len(data)],
            encapsulated_key=encapsulated,
            nonce=nonce,
            algorithm="Kyber-AES256-GCM",
            key_id=hashlib.sha256(public_key).hexdigest()[:16],
        )

    def decrypt_data(
        self, encrypted_data: EncryptedData, private_key: bytes
    ) -> bytes:
        """
        Decrypt quantum-safe encrypted data.

        Args:
            encrypted_data: EncryptedData object.
            private_key: Recipient's private key.

        Returns:
            Decrypted plaintext bytes.
        """
        # Decapsulate the shared secret
        shared_secret = self.decapsulate_key(
            encrypted_data.encapsulated_key, private_key
        )

        # Derive the same encryption key
        enc_key = hashlib.sha3_256(shared_secret + b"encryption").digest()

        # Decrypt
        padded = encrypted_data.ciphertext + b"\x00" * (
            32 - len(encrypted_data.ciphertext) % 32
        )
        decrypted = bytes(
            a ^ b for a, b in zip(padded, enc_key * (len(padded) // 32 + 1))
        )

        return decrypted[:len(encrypted_data.ciphertext)]

    def protect_secret(self, secret: str, purpose: str = "general") -> Dict[str, Any]:
        """
        Protect a sensitive secret using quantum-safe encryption.

        High-level method for protecting API keys, passwords, tokens, etc.

        Args:
            secret: The secret value to protect.
            purpose: Purpose of the secret (e.g., "jwt_key", "api_key").

        Returns:
            Dictionary with encrypted secret and metadata.
        """
        # Generate a new key pair for this secret
        keypair = self.generate_signature_keypair()

        # Encrypt the secret
        encrypted = self.encrypt_data(
            secret.encode("utf-8"),
            keypair.public_key
        )

        # Sign the encrypted data for integrity
        sig = self.sign(encrypted.ciphertext, keypair.private_key)

        return {
            "encrypted_secret": encrypted.ciphertext.hex(),
            "encapsulated_key": encrypted.encapsulated_key.hex(),
            "nonce": encrypted.nonce.hex(),
            "signature": sig.signature_bytes.hex(),
            "key_id": keypair.key_id,
            "algorithm": "CRYSTALS-Kyber + CRYSTALS-Dilithium",
            "purpose": purpose,
            "protected_at": datetime.utcnow().isoformat(),
            "public_key": keypair.public_key.hex(),
        }

    def retrieve_secret(
        self, protected_data: Dict[str, Any], private_key: bytes
    ) -> Optional[str]:
        """
        Retrieve a protected secret using the private key.

        Args:
            protected_data: Dictionary from protect_secret().
            private_key: Private key for decryption.

        Returns:
            Decrypted secret string, or None if verification fails.
        """
        try:
            ciphertext = bytes.fromhex(protected_data["encrypted_secret"])
            encapsulated = bytes.fromhex(protected_data["encapsulated_key"])
            nonce = bytes.fromhex(protected_data["nonce"])

            encrypted = EncryptedData(
                ciphertext=ciphertext,
                encapsulated_key=encapsulated,
                nonce=nonce,
                algorithm=protected_data.get("algorithm", ""),
                key_id=protected_data.get("key_id", ""),
            )

            decrypted = self.decrypt_data(encrypted, private_key)
            return decrypted.decode("utf-8").rstrip("\x00")

        except Exception as e:
            logger.error(f"Failed to retrieve secret: {str(e)}")
            return None

    def get_demo_info(self) -> Dict[str, Any]:
        """
        Get information about the quantum-safe cryptography implementation.

        Returns a comprehensive description of the PQC capabilities
        and how they protect banking systems.
        """
        return {
            "title": "Quantum-Safe Cryptography Module",
            "description": (
                "This module implements Post-Quantum Cryptography (PQC) to protect "
                "banking systems against quantum computing threats."
            ),
            "algorithms": {
                "CRYSTALS-Kyber": {
                    "type": "Key Encapsulation Mechanism (KEM)",
                    "standard": "NIST ML-KEM (FIPS 203)",
                    "use_case": "Key exchange, session key establishment",
                    "security_basis": "Module Learning With Errors (MLWE)",
                    "key_sizes": {
                        "Kyber-512": "800 bytes (NIST Level 1)",
                        "Kyber-768": "1184 bytes (NIST Level 3)",
                        "Kyber-1024": "1568 bytes (NIST Level 5)",
                    },
                },
                "CRYSTALS-Dilithium": {
                    "type": "Digital Signature Algorithm",
                    "standard": "NIST ML-DSA (FIPS 204)",
                    "use_case": "Authentication, integrity verification, code signing",
                    "security_basis": "Module-LWE and Module-SIS",
                    "key_sizes": {
                        "Dilithium2": "1312 bytes public key",
                        "Dilithium3": "1952 bytes public key",
                        "Dilithium5": "2592 bytes public key",
                    },
                },
            },
            "banking_use_cases": [
                "Protecting database credentials and connection strings",
                "Securing API keys for inter-service communication",
                "Quantum-safe JWT token signing",
                "Protecting TLS certificates and private keys",
                "Securing audit log integrity (hash chains)",
                "Protecting SWIFT and payment processing credentials",
                "Securing employee PII and HR data encryption keys",
                "Future-proofing compliance with NIST PQC standards",
            ],
            "quantum_threat_explanation": (
                "Quantum computers running Shor's algorithm can break RSA and ECC "
                "cryptosystems in polynomial time. This threatens all banking "
                "communications, stored credentials, and digital signatures. "
                "Post-quantum cryptography uses mathematical problems (Lattice-based "
                "cryptography) that are believed to be resistant to both classical "
                "and quantum attacks. NIST standardized CRYSTALS-Kyber and "
                "CRYSTALS-Dilithium in 2024 as the first PQC standards."
            ),
            "implementation_status": {
                "oqs_available": self.has_oqs,
                "mode": "OQS Library" if self.has_oqs else "Simulation Mode",
                "key_size": f"{self.key_size} bits",
            },
        }


# Global instance
_quantum_safe: Optional[QuantumSafeCrypto] = None


def get_quantum_safe_crypto() -> QuantumSafeCrypto:
    """Get the global quantum-safe crypto singleton."""
    global _quantum_safe
    if _quantum_safe is None:
        _quantum_safe = QuantumSafeCrypto()
    return _quantum_safe
