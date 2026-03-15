# Profile Image Upload

A zero-dependency Python 3 HTTP server that lets users upload and serve profile images, with client-side and server-side validation.

## Features

- **Image-type validation** — uses magic-byte sniffing (not just MIME type or extension) to verify the file is a real JPEG, PNG, GIF, or WEBP image.
- **Size cap** — rejects files larger than 5 MB.
- **Path-traversal protection** — `GET /uploads/<name>` rejects filenames containing `..`, `/`, or `\`.
- **JSON API** — all `POST /upload` responses are JSON with a consistent `{message, filename, url, size}` or `{error}` shape.
- **Built-in web UI** — `GET /` serves `index.html` which shows a live avatar preview, upload-progress bar, and status feedback.

## Requirements

- Python 3.8+
- No third-party packages

## Usage

```bash
# Start the server on the default port (8080)
python3 upload_server.py

# Start on a custom port
python3 upload_server.py 9000
```

Then open <http://localhost:8080> in your browser.

## API Reference

### `POST /upload`

Upload a profile image.

**Request:** `multipart/form-data` with a single field named `image`.

**Success (200)**
```json
{
  "message": "Profile image uploaded successfully",
  "filename": "3f2a1b4c...d9.jpg",
  "url": "/uploads/3f2a1b4c...d9.jpg",
  "size": 42312
}
```

**Error responses**

| Status | Reason |
|--------|--------|
| 400 | Wrong `Content-Type`, missing `image` field, or no file selected |
| 413 | File exceeds 5 MB |
| 415 | File is not a recognised image (JPEG, PNG, GIF, WEBP) |

### `GET /uploads/<filename>`

Retrieve a previously uploaded image by its server-assigned filename.

### `GET /`

Serves the web UI (`index.html`).

## Example session

```bash
# Upload with curl
curl -F "image=@/path/to/photo.jpg" http://localhost:8080/upload
# {"message":"Profile image uploaded successfully","filename":"abc123.jpg","url":"/uploads/abc123.jpg","size":85210}

# Fetch the uploaded image
curl http://localhost:8080/uploads/abc123.jpg -o saved.jpg
```

## Running the tests

```bash
cd profile-image-upload
python3 -m pytest test_upload_server.py -v
# or without pytest:
python3 -m unittest test_upload_server -v
```

The test suite spins up a real HTTP server on a random port and covers:
- Happy-path uploads (JPEG, PNG, GIF, WEBP)
- Saved file integrity
- File-type rejection (ZIP, PDF, spoofed extension)
- Oversized-file rejection
- Boundary condition (file at exactly 5 MB accepted)
- Missing / malformed request fields
- `GET /` serving the web UI
- `GET /uploads/<filename>` serving uploaded files
- Path-traversal blocked

## File layout

```
profile-image-upload/
├── upload_server.py        # HTTP server + validation logic
├── index.html              # Web UI (avatar preview, progress bar)
├── test_upload_server.py   # Unit / integration tests
├── README.md               # This file
└── uploads/                # Created at runtime; not committed
```
