package org.z2026.iw3nativeprobe;

import java.io.IOException;
import java.io.InputStream;

/**
 * Bounded preflight for the exact FastFile header contract in KisakCOD IW3.
 *
 * The original DB_LoadXFileInternal accepts "IWffu100" at version 5. It also
 * recognizes "IWff0100", but classifies that variant as authenticated/secure;
 * this vendored loader explicitly rejects authenticated FastFiles. This helper
 * only validates the header before import. It does NOT load or mount a FastFile.
 */
final class FastFileHeader {
    private static final String SUPPORTED_MAGIC = "IWffu100";
    private static final int SUPPORTED_VERSION = 5;
    private static final int HEADER_BYTES = 12;

    private FastFileHeader() {}

    /**
     * Reads and validates the 8-byte magic and little-endian uint32 version.
     * Returns the consumed bytes so the caller can copy them without reopening
     * the SAF stream. Never accepts a truncated header or secure/unsupported
     * variant, and never reads beyond the fixed 12-byte header.
     */
    static byte[] readAndValidate(InputStream input, String relativePath) throws IOException {
        if (input == null) throw new IOException("FastFile stream unavailable: " + relativePath);

        byte[] header = new byte[HEADER_BYTES];
        int offset = 0;
        while (offset < header.length) {
            int count = input.read(header, offset, header.length - offset);
            if (count < 0) {
                throw new IOException("Truncated IW3 FastFile header: " + relativePath);
            }
            if (count == 0) {
                // Be defensive about unusual provider streams that return zero
                // for a non-empty read request; guarantee forward progress.
                int one = input.read();
                if (one < 0) {
                    throw new IOException("Truncated IW3 FastFile header: " + relativePath);
                }
                header[offset++] = (byte) one;
            } else {
                offset += count;
            }
        }

        for (int i = 0; i < SUPPORTED_MAGIC.length(); i++) {
            if ((header[i] & 0xff) != SUPPORTED_MAGIC.charAt(i)) {
                throw new IOException("Unsupported IW3 FastFile magic: " + relativePath);
            }
        }

        long version = (header[8] & 0xffL)
                | ((header[9] & 0xffL) << 8)
                | ((header[10] & 0xffL) << 16)
                | ((header[11] & 0xffL) << 24);
        if (version != SUPPORTED_VERSION) {
            throw new IOException("Unsupported IW3 FastFile version " + version
                    + " (expected " + SUPPORTED_VERSION + "): " + relativePath);
        }
        return header;
    }
}
