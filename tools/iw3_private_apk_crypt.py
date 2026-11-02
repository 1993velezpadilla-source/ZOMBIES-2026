#!/usr/bin/env python3
"""Encrypt a PRIVATE, user-supplied IW3 Android APK before any GitHub artifact.

The CI runner uses a recipient public RSA key to encrypt a random AES-256-GCM
file key. Only the matching private RSA key, NEVER in GitHub, can decrypt it.
Upload ONLY the sealed .iw3sealed file, not a ZIP or plaintext .apk.

Format (v1): magic UTF-8 | u32big header length | JSON header |
             AES-256-GCM ciphertext | 16-byte GCM tag.
The header is authenticated AAD, and contains metadata/size/hash but no game
asset bytes. The original APK remains only in ephemeral runner storage.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import struct

from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.exceptions import InvalidTag

MAGIC=b"IW3APK-AESGCM-v1\n"
CHUNK=2*1024*1024
MAX_HEADER=8192


def digest_file(path: Path) -> tuple[int,str]:
    digest=hashlib.sha256()
    size=0
    with path.open("rb") as input_file:
        for piece in iter(lambda:input_file.read(CHUNK),b""):
            digest.update(piece)
            size+=len(piece)
    return size,digest.hexdigest()


def seal(path: Path, output: Path, recipient_pub: Path) -> dict:
    if path.suffix.lower()!=".apk" or not path.is_file():
        raise ValueError("only an existing Android APK may be sealed")
    if output.exists():
        raise FileExistsError("encrypted output already exists: "+str(output))
    size,digest=digest_file(path)
    if size<100000:
        raise ValueError("APK suspiciously small")
    public_key=serialization.load_pem_public_key(recipient_pub.read_bytes())
    aes_key=secrets.token_bytes(32)
    nonce=secrets.token_bytes(12)
    wrapped=public_key.encrypt(aes_key,padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),label=None))
    header={
        "version":1,"cipher":"AES-256-GCM",
        "key_wrap":"RSA-OAEP-SHA256","nonce":base64.b64encode(nonce).decode(),
        "encrypted_aes_key":base64.b64encode(wrapped).decode(),
        "original_filename":path.name,"original_size":size,
        "sha256":digest,
        "warning":"Contains encrypted owner-supplied game resources. Do not redistribute."
    }
    head=json.dumps(header,sort_keys=True,separators=(",",":")).encode()
    if len(head)>MAX_HEADER:
        raise ValueError("header too large")
    encryptor=Cipher(algorithms.AES(aes_key),modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(MAGIC+head)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("xb") as o, path.open("rb") as inp:
        o.write(MAGIC)
        o.write(struct.pack(">I",len(head)))
        o.write(head)
        for chunk in iter(lambda:inp.read(CHUNK),b""):
            o.write(encryptor.update(chunk))
        o.write(encryptor.finalize())
        o.write(encryptor.tag)
    sealed_size=output.stat().st_size
    return {"encrypted_archive":output.name,"encrypted_size":sealed_size,
            "plaintext_sha256":digest,"plaintext_size":size,
            "plaintext_uploaded":False,"recipient_private_key_uploaded":False}


def unseal(source: Path, output: Path, private_pem: Path) -> dict:
    if output.exists():
        raise FileExistsError("refusing to overwrite existing private APK")
    with source.open("rb") as inf:
        magic=inf.read(len(MAGIC))
        if magic!=MAGIC:
            raise ValueError("not an authenticated IW3 encrypted APK")
        raw_len=inf.read(4)
        if len(raw_len)!=4:
            raise ValueError("truncated file header")
        head_size=struct.unpack(">I",raw_len)[0]
        if not 0<head_size<=MAX_HEADER:
            raise ValueError("header too large")
        head=inf.read(head_size)
        if len(head)!=head_size:
            raise ValueError("truncated header")
        metadata=json.loads(head)
        if metadata.get("version")!=1 or metadata.get("cipher")!="AES-256-GCM" or metadata.get("key_wrap")!="RSA-OAEP-SHA256":
            raise ValueError("unsupported encryption")
        private_key=serialization.load_pem_private_key(private_pem.read_bytes(),password=None)
        key=private_key.decrypt(base64.b64decode(metadata["encrypted_aes_key"]),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(),label=None))
        nonce=base64.b64decode(metadata["nonce"])
        if len(nonce)!=12 or len(key)!=32:
            raise ValueError("invalid crypto material")
        start=inf.tell()
        end=source.stat().st_size
        if end-start<16:
            raise ValueError("truncated encrypted data")
        inf.seek(end-16)
        tag=inf.read(16)
        inf.seek(start)
        decryptor=Cipher(algorithms.AES(key),modes.GCM(nonce,tag)).decryptor()
        decryptor.authenticate_additional_data(MAGIC+head)
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("xb") as out:
            try:
                left=end-16-start
                while left:
                    piece=inf.read(min(CHUNK,left))
                    if not piece:
                        raise ValueError("truncated ciphertext")
                    out.write(decryptor.update(piece))
                    left-=len(piece)
                out.write(decryptor.finalize())
                out.flush()
            except Exception:
                output.unlink(missing_ok=True)
                raise
    length,digest=digest_file(output)
    if length!=metadata["original_size"] or digest!=metadata["sha256"]:
        output.unlink(missing_ok=True)
        raise ValueError("checksum mismatch; do not install")
    return {"decrypted_file":output.name,"size":length,"sha256":digest,"authenticated":True}


def main()->None:
    arg=argparse.ArgumentParser(description=__doc__)
    sub=arg.add_subparsers(dest="command",required=True)
    en=sub.add_parser("seal")
    en.add_argument("apk",type=Path);en.add_argument("sealed",type=Path);en.add_argument("public_pem",type=Path)
    de=sub.add_parser("unseal")
    de.add_argument("sealed",type=Path);de.add_argument("apk",type=Path);de.add_argument("private_pem",type=Path)
    opts=arg.parse_args()
    report=seal(opts.apk,opts.sealed,opts.public_pem) if opts.command=="seal" else unseal(opts.sealed,opts.apk,opts.private_pem)
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
