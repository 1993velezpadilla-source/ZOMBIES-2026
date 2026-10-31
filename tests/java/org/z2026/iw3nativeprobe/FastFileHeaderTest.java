package org.z2026.iw3nativeprobe;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;

/** Host-JVM regression tests for the exact Java helper used by Android import. */
public final class FastFileHeaderTest {
    private static int checks;

    private static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }

    private static byte[] header(String magic, long version) {
        byte[] bytes = new byte[12];
        byte[] magicBytes = magic.getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        System.arraycopy(magicBytes, 0, bytes, 0, Math.min(8, magicBytes.length));
        bytes[8] = (byte) version;
        bytes[9] = (byte) (version >>> 8);
        bytes[10] = (byte) (version >>> 16);
        bytes[11] = (byte) (version >>> 24);
        return bytes;
    }

    private static void rejects(byte[] bytes, String path, String expectedMessage)
            throws Exception {
        try {
            FastFileHeader.readAndValidate(new ByteArrayInputStream(bytes), path);
            throw new AssertionError("Expected rejection for " + path);
        } catch (IOException expected) {
            check(expected.getMessage().contains(expectedMessage),
                    "Unexpected rejection message for " + path + ": " + expected.getMessage());
        }
    }

    private static final class SparseReadStream extends InputStream {
        private final ByteArrayInputStream delegate;
        private boolean returnZero = true;

        SparseReadStream(byte[] bytes) { delegate = new ByteArrayInputStream(bytes); }

        @Override public int read() { return delegate.read(); }

        @Override public int read(byte[] target, int offset, int length) {
            if (returnZero) {
                returnZero = false;
                return 0;
            }
            return delegate.read(target, offset, Math.min(1, length));
        }
    }

    public static void main(String[] args) throws Exception {
        byte[] expected = header("IWffu100", 5);
        byte[] withPayload = Arrays.copyOf(expected, expected.length + 3);
        withPayload[12] = 0x11;
        withPayload[13] = 0x22;
        withPayload[14] = 0x33;

        ByteArrayInputStream valid = new ByteArrayInputStream(withPayload);
        byte[] actual = FastFileHeader.readAndValidate(valid, "zone/english/code_post_gfx.ff");
        check(Arrays.equals(actual, expected), "Validated header bytes must be returned unchanged");
        check(valid.read() == 0x11, "Header validation must not consume FastFile payload");

        byte[] sparse = FastFileHeader.readAndValidate(
                new SparseReadStream(withPayload), "zone/english/common.ff");
        check(Arrays.equals(sparse, expected), "Short/zero reads must be handled without corrupting header");

        rejects(header("IWff0100", 5), "zone/english/secure.ff", "Unsupported IW3 FastFile magic");
        rejects(header("IWffu100", 4), "zone/english/old.ff", "version 4");
        rejects(Arrays.copyOf(expected, 11), "zone/english/truncated.ff", "Truncated IW3 FastFile header");
        rejects(header("NOTIW3!!", 5), "zone/english/fake.ff", "Unsupported IW3 FastFile magic");

        check(true, "All assertions reached");
        System.out.println("IW3_FASTFILE_HEADER_TESTS_PASS checks=" + checks);
    }
}
