"""Exercise actual native decoded-file and serialized-packet rejection paths."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from media_limits import MAX_MEDIAFILE_BYTES,MAX_MEDIA_TRANSFER_BYTES

def verify(probe):
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'oversized-media.bin'
        with p.open('wb') as f:f.truncate(MAX_MEDIAFILE_BYTES+1)
        rejected=subprocess.run([str(probe),str(p),'unused'],capture_output=True,text=True)
        if rejected.returncode!=4 or 'SERVER_MEDIA_REJECTED' not in rejected.stderr:
            raise RuntimeError('Native engine must reject decoded files above 32 MiB: '+rejected.stderr)
        # A file inside the decoded budget can still exceed the wire budget.
        p.write_bytes(np.random.default_rng(1729).bytes(MAX_MEDIA_TRANSFER_BYTES+100_000))
        rejected=subprocess.run([str(probe),str(p),'unused'],capture_output=True,text=True)
        if rejected.returncode!=5 or 'SERVER_MEDIA_TRANSFER_REJECTED' not in rejected.stderr:
            raise RuntimeError('Oversized incompressible packets must be rejected before MTP send: '+rejected.stderr)
    print('NATIVE_MEDIA_LIMITS_PASS: >32 MiB decoded file rejected; oversized serialized packet rejected safely')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('probe',type=Path)
    verify(p.parse_args().probe)
