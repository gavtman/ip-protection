"""
Profile Image Upload Server
============================
Zero-dependency Python 3 HTTP server that accepts profile image uploads.

Endpoints
---------
GET  /            Serves index.html
GET  /uploads/<filename>  Serves a previously uploaded file
POST /upload      Accepts multipart/form-data with field "image"

Validation
----------
- Allowed MIME types / magic bytes: JPEG, PNG, GIF, WEBP
- Maximum file size: 5 MB

Usage
-----
    python3 upload_server.py            # listens on 0.0.0.0:8080
    python3 upload_server.py 9000       # custom port
"""

from __future__ import annotations

import email
import email.policy
import io
import json
import mimetypes
import sys
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# (magic-bytes prefix, canonical extension)
ALLOWED_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"RIFF", ".webp"),   # full check includes bytes[8:12] == b"WEBP"
]

SCRIPT_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = SCRIPT_DIR / "uploads"
INDEX_HTML = SCRIPT_DIR / "index.html"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_image_ext(data: bytes) -> str | None:
    """Return the canonical file extension if *data* starts with a known
    image magic-byte sequence, otherwise return *None*.

    For WEBP files, the RIFF header alone is not sufficient — bytes 8–11
    must also equal ``WEBP`` (the FourCC that distinguishes RIFF/WEBP from
    other RIFF containers such as WAV or AVI)."""
    for sig, ext in ALLOWED_SIGNATURES:
        if data[:len(sig)] == sig:
            if ext == ".webp":
                # RIFF....WEBP — bytes 8-12 must be "WEBP"
                if len(data) >= 12 and data[8:12] == b"WEBP":
                    return ext
                continue
            return ext
    return None


def _json_response(handler: BaseHTTPRequestHandler,
                   status: int,
                   payload: dict) -> None:
    body = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class ProfileUploadHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt: str, *args) -> None:  # pragma: no cover
        pass  # silence default access log; tests capture output separately

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            self._serve_file(INDEX_HTML, "text/html; charset=utf-8")
            return

        if path.startswith("/uploads/"):
            filename = path[len("/uploads/"):]
            # Reject path traversal
            if ".." in filename or "/" in filename or "\\" in filename:
                self.send_error(400, "Bad filename")
                return
            file_path = UPLOADS_DIR / filename
            self._serve_file(file_path)
            return

        self.send_error(404, "Not found")

    def _serve_file(self, file_path: Path,
                    content_type: str | None = None) -> None:
        try:
            data = file_path.read_bytes()
        except FileNotFoundError:
            self.send_error(404, "Not found")
            return
        if content_type is None:
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ------------------------------------------------------------------
    # POST /upload
    # ------------------------------------------------------------------

    def do_POST(self) -> None:
        if self.path.split("?")[0] != "/upload":
            self.send_error(404, "Not found")
            return

        content_type_header = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type_header:
            _json_response(self, 400,
                           {"error": "Content-Type must be multipart/form-data"})
            return

        # Parse multipart body using the email package (zero external deps,
        # avoids the deprecated cgi.FieldStorage which is removed in Python 3.13)
        body_bytes = self.rfile.read(
            int(self.headers.get("Content-Length", 0))
        )
        # Reconstruct a full MIME message so email.message_from_bytes can
        # parse the individual parts.
        mime_msg = email.message_from_bytes(
            b"Content-Type: " + content_type_header.encode() + b"\r\n\r\n"
            + body_bytes,
            policy=email.policy.compat32,
        )

        image_data: bytes | None = None
        found_filename: str | None = None
        for part in mime_msg.get_payload():
            disposition = part.get("Content-Disposition", "")
            if 'name="image"' in disposition:
                # Extract the filename from Content-Disposition if present
                for token in disposition.split(";"):
                    token = token.strip()
                    if token.startswith("filename="):
                        found_filename = token[9:].strip().strip('"')
                image_data = part.get_payload(decode=True)
                break

        if image_data is None:
            _json_response(self, 400, {"error": "No 'image' field in request"})
            return

        if not found_filename:
            _json_response(self, 400, {"error": "No file selected"})
            return

        # Size check
        if len(image_data) > MAX_FILE_SIZE:
            _json_response(
                self, 413,
                {"error": f"File too large. Maximum size is "
                           f"{MAX_FILE_SIZE // (1024 * 1024)} MB"}
            )
            return

        # Type check via magic bytes
        ext = _detect_image_ext(image_data)
        if ext is None:
            _json_response(
                self, 415,
                {"error": "Unsupported file type. "
                           "Allowed types: JPEG, PNG, GIF, WEBP"}
            )
            return

        # Save file
        UPLOADS_DIR.mkdir(exist_ok=True)
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = UPLOADS_DIR / filename
        dest.write_bytes(image_data)

        _json_response(self, 200, {
            "message": "Profile image uploaded successfully",
            "filename": filename,
            "url": f"/uploads/{filename}",
            "size": len(image_data),
        })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(port: int = 8080, *, bind: str = "0.0.0.0") -> None:  # pragma: no cover
    server = HTTPServer((bind, port), ProfileUploadHandler)
    print(f"Profile Image Upload Server running on http://{bind}:{port}")
    print(f"Uploads directory: {UPLOADS_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":  # pragma: no cover
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(port)
