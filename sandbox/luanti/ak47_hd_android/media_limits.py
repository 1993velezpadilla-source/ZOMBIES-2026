"""Media budget of the pinned Luanti 5.18.0 network protocol.

Keep in sync with MEDIAFILE_MAX_SIZE in src/network/networkprotocol.h.
The native loader probe also checks that actual engine constant.
"""
MAX_MEDIAFILE_BYTES=32*1024*1024
MAX_MEDIA_TRANSFER_BYTES=16_700_000

def check_media_size(name,size):
    if not 0<size<=MAX_MEDIAFILE_BYTES:
        raise ValueError(f'{name}: {size} bytes exceeds the Luanti media budget '
                         f'of {MAX_MEDIAFILE_BYTES} bytes (or is empty)')
