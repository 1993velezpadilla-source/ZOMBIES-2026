"""Publish the exact APK the owner requested as a direct GitHub download.

The request contains a one-file content key, intentionally released with this
already requested public APK. It is not an account or signing credential, and
the private RSA delivery key never leaves the original build workspace.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def prepare(request,encrypted,target):
    r=json.loads(request.read_text());data=encrypted.read_bytes()
    if data[:8]!=b'AKHDAPK1':raise ValueError('wrong private artifact format')
    n=struct.unpack('>I',data[8:12])[0]
    if not 128<=n<=1024:raise ValueError('bad encrypted envelope')
    key=base64.b64decode(r['apk_content_key_b64'],validate=True)
    result=AESGCM(key).decrypt(data[12+n:24+n],data[24+n:],b'AKHDAPK1')
    digest=hashlib.sha256(result).hexdigest()
    if digest!=r['apk_sha256']:raise ValueError('APK hash differs from the verified build')
    target.write_bytes(result)
    print(json.dumps({'file':target.name,'bytes':len(result),'sha256':digest}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('request',type=Path)
    p.add_argument('encrypted',type=Path);p.add_argument('target',type=Path)
    a=p.parse_args();prepare(a.request,a.encrypted,a.target)
