from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidTag
from private_delivery import encrypt,decrypt

class DeliveryTests(unittest.TestCase):
    def test_private_payload_round_trip_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            (p/'public').write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
            (p/'private').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            (p/'source').write_bytes(bytes(range(256))*100)
            encrypt(p/'source',p/'encrypted',p/'public');decrypt(p/'encrypted',p/'decoded',p/'private')
            self.assertEqual((p/'decoded').read_bytes(),(p/'source').read_bytes())
            bad=bytearray((p/'encrypted').read_bytes());bad[-1]^=1;(p/'encrypted').write_bytes(bad)
            with self.assertRaises(InvalidTag):decrypt(p/'encrypted',p/'untrusted',p/'private')
            self.assertFalse((p/'untrusted').exists())

if __name__=='__main__':unittest.main()
