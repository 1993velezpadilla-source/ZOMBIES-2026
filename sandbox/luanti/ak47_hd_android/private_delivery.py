"""Authenticated encrypted build handoff. Only a public key reaches CI."""
import argparse
import os
from pathlib import Path
import struct
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC=b'AKHDAPK1'

def encrypt(source,target,public_key):
    pub=serialization.load_pem_public_key(public_key.read_bytes())
    key=AESGCM.generate_key(bit_length=256);nonce=os.urandom(12)
    wrapped=pub.encrypt(key,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=MAGIC))
    data=AESGCM(key).encrypt(nonce,source.read_bytes(),MAGIC)
    target.write_bytes(MAGIC+struct.pack('>I',len(wrapped))+wrapped+nonce+data)

def decrypt(source,target,private_key):
    data=source.read_bytes()
    if data[:8]!=MAGIC:raise ValueError('bad delivery envelope')
    n=struct.unpack('>I',data[8:12])[0]
    if n>1024 or len(data)<n+40:raise ValueError('bad encrypted key length')
    priv=serialization.load_pem_private_key(private_key.read_bytes(),password=None)
    key=priv.decrypt(data[12:12+n],padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=MAGIC))
    target.write_bytes(AESGCM(key).decrypt(data[12+n:24+n],data[24+n:],MAGIC))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['encrypt','decrypt'])
    p.add_argument('source',type=Path);p.add_argument('target',type=Path);p.add_argument('key',type=Path)
    a=p.parse_args();(encrypt if a.mode=='encrypt' else decrypt)(a.source,a.target,a.key)
