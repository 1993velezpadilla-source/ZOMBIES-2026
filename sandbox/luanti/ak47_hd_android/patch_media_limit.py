"""Raise the decoded media budget while keeping the existing MTP wire limits."""
import argparse
from pathlib import Path
from patch_engine import checked

def patch(root):
    checked(root/'src/network/networkprotocol.h',
        '// Due to our network protocol the maximum window size determines the maximum\n'
        '// media size we can safely allow. See the comment and check in Connection::Send().\n'
        '// This is a bit lower to include safety margin.\n'
        '#define MEDIAFILE_MAX_SIZE (16700000U)',
        '// Decoded media may be larger than a reliable network payload. Protocol 48+\n'
        '// compresses each file before sending; sendRequestedMedia checks the final\n'
        '// packet against the unchanged MTP transfer budget before Connection::Send.\n'
        '#define MEDIAFILE_MAX_SIZE (32U * 1024U * 1024U)\n'
        '#define MEDIAFILE_TRANSFER_MAX_SIZE (16700000U)')
    checked(root/'src/server.cpp',
        '\t\tbunch.clear(); // free memory early\n\n\t\tverbosestream',
        '\t\tbunch.clear(); // free memory early\n\n'
        '\t\t// Bound the serialized wire packet, not the decoded model. Never pass\n'
        '\t\t// an oversized reliable payload into the MTP fatal-error path.\n'
        '\t\tif (pkt.getSize() > MEDIAFILE_TRANSFER_MAX_SIZE) {\n'
        '\t\t\twarningstream << "Server: media packet exceeds transfer budget for peer "\n'
        '\t\t\t\t<< peer_id << ": " << pkt.getSize() << std::endl;\n'
        '\t\t\tDenyAccess(peer_id, SERVER_ACCESSDENIED_CUSTOM_STRING,\n'
        '\t\t\t\t"Media transfer is too large. A client with compressed media support is required.");\n'
        '\t\t\treturn;\n'
        '\t\t}\n\n\t\tverbosestream')
    print('Decoded media limit: 32 MiB; serialized MTP packet budget unchanged and guarded')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path)
    patch(p.parse_args().root)
