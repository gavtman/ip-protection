"""Unit tests for upload_server.py"""

from __future__ import annotations

import io
import json
import struct
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zlib
from http.server import HTTPServer
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the module under test. UPLOADS_DIR will be patched per-test-run
# inside _TestServer.__init__ before the first request is made.
# ---------------------------------------------------------------------------
import upload_server  # noqa: E402  (local import is intentional)

# ---------------------------------------------------------------------------
# Image-building helpers
# ---------------------------------------------------------------------------

def _make_jpeg(width: int = 1, height: int = 1) -> bytes:
    """Return a minimal valid JPEG file (1×1 white pixel)."""
    # SOI + minimal APP0 + quantization table stubs + SOF0 + DHT stubs + SOS
    # Easiest: just use the JPEG magic bytes + enough content to pass sniffing.
    # For magic-byte detection, only the first 3 bytes matter.
    # We build the smallest structurally valid JPEG that Python's imghdr can
    # recognise, but for our purposes the magic bytes are sufficient.
    return (
        b"\xff\xd8\xff\xe0"          # SOI + APP0 marker
        b"\x00\x10JFIF\x00"          # APP0 length + identifier
        b"\x01\x01\x00\x00\x01\x00\x01\x00\x00"  # version, units, density
        b"\xff\xd9"                   # EOI
    )


def _make_png(width: int = 1, height: int = 1) -> bytes:
    """Return a minimal valid 1×1 PNG (RGBA white pixel)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return length + tag + data + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)
    raw_row = b"\x00" + b"\xff\xff\xff" * width  # filter byte + RGB pixels
    compressed = zlib.compress(raw_row * height)
    idat = chunk(b"IDAT", compressed)
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def _make_gif() -> bytes:
    """Return a minimal valid GIF89a file."""
    return (
        b"GIF89a"
        b"\x01\x00\x01\x00\x80\x00\x00"   # width=1, height=1, GCT flag
        b"\xff\xff\xff\x00\x00\x00"         # GCT: two colours
        b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00"  # image descriptor
        b"\x02\x02\x4c\x01\x00"             # LZW data
        b"\x3b"                              # trailer
    )


def _make_webp() -> bytes:
    """Return minimal RIFF/WEBP magic bytes (sufficient for sniffing tests;
    the payload bytes are minimal padding, not valid VP8-encoded image data)."""
    payload = b"\x57\x45\x42\x50" + b"\x00" * 20  # "WEBP" + dummy VP8 data
    size = struct.pack("<I", len(payload))
    return b"RIFF" + size + payload


def _make_multipart(field: str, filename: str, data: bytes,
                    content_type: str = "application/octet-stream") -> tuple[bytes, str]:
    """Build a multipart/form-data body. Returns (body, boundary)."""
    boundary = "TestBoundary1234567890"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return body, boundary


# ---------------------------------------------------------------------------
# Test helper: spin up a real server on a random port in a thread
# ---------------------------------------------------------------------------

class _TestServer:
    def __init__(self, uploads_dir: Path):
        upload_server.UPLOADS_DIR = uploads_dir
        self.server = HTTPServer(("127.0.0.1", 0), upload_server.ProfileUploadHandler)
        self.port = self.server.server_address[1]
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        self.server.shutdown()

    def url(self, path: str = "") -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def post_upload(self, data: bytes, filename: str,
                    content_type: str = "image/jpeg") -> tuple[int, dict]:
        body, boundary = _make_multipart("image", filename, data, content_type)
        req = urllib.request.Request(
            self.url("/upload"),
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDetectImageExt(unittest.TestCase):
    def test_jpeg(self):
        self.assertEqual(upload_server._detect_image_ext(_make_jpeg()), ".jpg")

    def test_png(self):
        self.assertEqual(upload_server._detect_image_ext(_make_png()), ".png")

    def test_gif89a(self):
        self.assertEqual(upload_server._detect_image_ext(_make_gif()), ".gif")

    def test_gif87a(self):
        data = b"GIF87a" + b"\x00" * 10
        self.assertEqual(upload_server._detect_image_ext(data), ".gif")

    def test_webp(self):
        self.assertEqual(upload_server._detect_image_ext(_make_webp()), ".webp")

    def test_unknown(self):
        self.assertIsNone(upload_server._detect_image_ext(b"\x00\x01\x02\x03"))

    def test_empty(self):
        self.assertIsNone(upload_server._detect_image_ext(b""))

    def test_riff_not_webp(self):
        # RIFF but not WEBP — should not match
        data = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"\x00" * 10
        self.assertIsNone(upload_server._detect_image_ext(data))


class TestUploadServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._uploads = Path(cls._tmpdir.name) / "uploads"
        cls._server = _TestServer(cls._uploads)

    @classmethod
    def tearDownClass(cls):
        cls._server.stop()
        cls._tmpdir.cleanup()

    # ------------------------------------------------------------------
    # Happy-path uploads
    # ------------------------------------------------------------------

    def test_upload_jpeg(self):
        status, body = self._server.post_upload(
            _make_jpeg(), "avatar.jpg", "image/jpeg"
        )
        self.assertEqual(status, 200)
        self.assertIn("filename", body)
        self.assertTrue(body["filename"].endswith(".jpg"))
        self.assertIn("url", body)

    def test_upload_png(self):
        status, body = self._server.post_upload(
            _make_png(), "avatar.png", "image/png"
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["filename"].endswith(".png"))

    def test_upload_gif(self):
        status, body = self._server.post_upload(
            _make_gif(), "anim.gif", "image/gif"
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["filename"].endswith(".gif"))

    def test_upload_webp(self):
        status, body = self._server.post_upload(
            _make_webp(), "photo.webp", "image/webp"
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["filename"].endswith(".webp"))

    def test_uploaded_file_exists(self):
        status, body = self._server.post_upload(
            _make_png(), "check.png", "image/png"
        )
        self.assertEqual(status, 200)
        saved = self._uploads / body["filename"]
        self.assertTrue(saved.exists())
        self.assertEqual(saved.read_bytes(), _make_png())

    def test_response_contains_size(self):
        data = _make_jpeg()
        status, body = self._server.post_upload(data, "x.jpg", "image/jpeg")
        self.assertEqual(status, 200)
        self.assertEqual(body["size"], len(data))

    # ------------------------------------------------------------------
    # File-type rejection
    # ------------------------------------------------------------------

    def test_reject_non_image_bytes(self):
        status, body = self._server.post_upload(
            b"PK\x03\x04" + b"\x00" * 20, "evil.zip", "application/zip"
        )
        self.assertEqual(status, 415)
        self.assertIn("error", body)

    def test_reject_pdf_magic(self):
        status, body = self._server.post_upload(
            b"%PDF-1.4" + b"\x00" * 20, "doc.pdf", "application/pdf"
        )
        self.assertEqual(status, 415)

    def test_reject_jpeg_extension_with_wrong_bytes(self):
        # .jpg extension but content is actually a ZIP — magic bytes should win
        status, body = self._server.post_upload(
            b"PK\x03\x04" + b"\x00" * 20, "tricky.jpg", "image/jpeg"
        )
        self.assertEqual(status, 415)

    # ------------------------------------------------------------------
    # Size rejection
    # ------------------------------------------------------------------

    def test_reject_oversized_file(self):
        big = _make_jpeg() + b"\x00" * (upload_server.MAX_FILE_SIZE + 1)
        status, body = self._server.post_upload(big, "big.jpg", "image/jpeg")
        self.assertEqual(status, 413)
        self.assertIn("error", body)

    def test_accept_file_at_size_limit(self):
        # Fill up to exactly MAX_FILE_SIZE with JPEG data
        base = _make_jpeg()
        padding = b"\x00" * (upload_server.MAX_FILE_SIZE - len(base))
        data = base + padding
        status, _ = self._server.post_upload(data, "limit.jpg", "image/jpeg")
        self.assertEqual(status, 200)

    # ------------------------------------------------------------------
    # Missing / malformed field
    # ------------------------------------------------------------------

    def test_reject_wrong_content_type(self):
        req = urllib.request.Request(
            self._server.url("/upload"),
            data=b"hello",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status, body = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            status, body = exc.code, json.loads(exc.read())
        self.assertEqual(status, 400)

    def test_reject_missing_image_field(self):
        boundary = "B"
        body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"other\"\r\n\r\nval\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            self._server.url("/upload"),
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        self.assertEqual(status, 400)

    # ------------------------------------------------------------------
    # GET requests
    # ------------------------------------------------------------------

    def test_get_index(self):
        with urllib.request.urlopen(self._server.url("/")) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn(b"Profile", resp.read())

    def test_get_uploaded_file(self):
        data = _make_png()
        _, upload_body = self._server.post_upload(data, "serve_me.png", "image/png")
        url = self._server.url(upload_body["url"])
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), data)

    def test_get_nonexistent_file(self):
        try:
            urllib.request.urlopen(self._server.url("/uploads/does_not_exist.jpg"))
            self.fail("Expected 404")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)

    def test_get_path_traversal_blocked(self):
        try:
            urllib.request.urlopen(self._server.url("/uploads/../secret"))
            self.fail("Expected 400")
        except urllib.error.HTTPError as exc:
            self.assertIn(exc.code, (400, 404))

    def test_get_unknown_path(self):
        try:
            urllib.request.urlopen(self._server.url("/not-a-route"))
            self.fail("Expected 404")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)


if __name__ == "__main__":
    unittest.main()
