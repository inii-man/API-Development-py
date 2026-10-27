#!/usr/bin/env python3
"""
TaskHub API - Hari 1: Desain REST, OpenAPI, dan Autentikasi
Training API Development
Standard Library Implementation (http.server + sqlite3)
"""

import http.server
import json
import os
import sys
import time
import secrets
import hashlib
import hmac
import sqlite3
import urllib.parse
from pathlib import Path

# Database path (configurable via environment for tests)
DB_PATH = os.environ.get("TASKHUB_DB", "taskhub.db")
PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = Path(__file__).resolve().parent

def get_db(db_path=None):
    target = db_path or DB_PATH
    con = sqlite3.connect(target)
    con.row_factory = sqlite3.Row
    return con

def password_hash(password: str, salt: bytes) -> str:
    """Hash password menggunakan scrypt sesuai slide 53."""
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1
    ).hex()

def initialize_db(db_path=None):
    """Membuat tabel dan seed pengguna default sesuai slide 52 & 53."""
    with get_db(db_path) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                hash TEXT NOT NULL,
                role TEXT NOT NULL,
                team TEXT NOT NULL
            );
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('open', 'done')),
                owner_id TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Cek apakah seed sudah ada
        cur = con.execute("SELECT COUNT(*) as count FROM users")
        if cur.fetchone()["count"] == 0:
            demo_password = "Lab-Only-123!"
            seeds = [
                ("u1", "alice", "member", "A"),
                ("u2", "bob", "member", "B"),
                ("u3", "manager", "manager", "A"),
                ("u4", "admin", "admin", "ALL"),
            ]
            for uid, uname, role, team in seeds:
                salt = secrets.token_bytes(16)
                p_hash = password_hash(demo_password, salt)
                con.execute(
                    "INSERT INTO users (id, username, salt, hash, role, team) VALUES (?, ?, ?, ?, ?, ?)",
                    (uid, uname, salt.hex(), p_hash, role, team)
                )

            # Tambahkan task awal untuk demonstrasi
            con.execute(
                "INSERT INTO tasks (id, title, status, owner_id, version) VALUES (?, ?, ?, ?, ?)",
                ("tsk_alice_1", "Review Kontrak OpenAPI TaskHub", "open", "u1", 1)
            )
            con.execute(
                "INSERT INTO tasks (id, title, status, owner_id, version) VALUES (?, ?, ?, ?, ?)",
                ("tsk_bob_1", "Setup Repository Microservice Tim B", "open", "u2", 1)
            )
        con.commit()

def can_access(con, user: dict, task: dict) -> bool:
    """
    Otorisasi level objek (BOLA prevention) sesuai slide 8, 49, 56.
    - Admin: selalu diizinkan
    - Owner: pemilik task diizinkan
    - Manager: hanya jika tim manager sama dengan tim pemilik task
    - Member lain: ditolak
    """
    if user["role"] == "admin" or task["owner_id"] == user["id"]:
        return True

    owner = con.execute("SELECT team FROM users WHERE id=?", (task["owner_id"],)).fetchone()
    if not owner:
        return False

    return user["role"] == "manager" and owner["team"] == user["team"]

def validate_create(body) -> bool:
    """
    Validasi CreateTask sesuai slide 22 & 57:
    - Harus dictionary
    - Hanya memperbolehkan field 'title' (tolak mass assignment owner_id, role, etc.)
    - Title bertipe string, panjang 3 s.d 150 karakter setelah trim
    """
    if not isinstance(body, dict):
        return False
    if set(body.keys()) - {"title"}:
        return False
    title = body.get("title")
    if not isinstance(title, str):
        return False
    cleaned = title.strip()
    return 3 <= len(cleaned) <= 150


class TaskHubHandler(http.server.BaseHTTPRequestHandler):
    server_version = "TaskHub-Lab/1.0"

    def __init__(self, *args, db_path=None, **kwargs):
        self.custom_db_path = db_path
        super().__init__(*args, **kwargs)

    def db(self):
        return get_db(self.custom_db_path)

    def send_json(self, status: int, data: dict, extra_headers: dict = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # Security headers
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        # CORS lab headers for local exploration
        origin = self.headers.get("Origin")
        if origin and ("localhost" in origin or "127.0.0.1" in origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
            self.send_header("Vary", "Origin")

        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_error_response(self, status: int, code: str, message: str = None):
        """Format error mesin stabil sesuai slide 29."""
        req_id = f"req_{secrets.token_hex(6)}"
        payload = {
            "error": {
                "code": code,
                "requestId": req_id
            }
        }
        if message:
            payload["error"]["message"] = message
        self.send_json(status, payload)

    def read_json_body(self, max_bytes: int = 65536):
        """Membaca body JSON dengan validasi ukuran & format sesuai slide 13 & 22."""
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return None, (400, "INVALID_REQUEST", "Content-Length header is required")

        try:
            length = int(content_length)
        except ValueError:
            return None, (400, "INVALID_REQUEST", "Invalid Content-Length")

        if length > max_bytes:
            return None, (413, "PAYLOAD_TOO_LARGE", f"Body exceeds {max_bytes} bytes")

        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return None, (415, "UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json")

        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
            return parsed, None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, (400, "INVALID_JSON", "Malformed JSON body")

    def get_authenticated_user(self):
        """
        Validasi opaque bearer token sesuai slide 54-55.
        Tolak jika tidak ada atau expired -> return None.
        """
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token_value = auth_header[7:].strip()
        if not token_value:
            return None

        digest = hashlib.sha256(token_value.encode("utf-8")).hexdigest()
        now = int(time.time())

        with self.db() as con:
            cur = con.execute("""
                SELECT u.id, u.username, u.role, u.team
                FROM users u
                JOIN tokens t ON u.id = t.user_id
                WHERE t.hash = ? AND t.expires > ?
            """, (digest, now))
            row = cur.fetchone()
            if row:
                return dict(row)
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        origin = self.headers.get("Origin")
        if origin and ("localhost" in origin or "127.0.0.1" in origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
            self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Health endpoint
        if path == "/health":
            return self.send_json(200, {"status": "pass", "time": int(time.time())})

        # Serve openapi.yaml
        if path == "/openapi.yaml":
            yaml_path = BASE_DIR / "openapi.yaml"
            if yaml_path.exists():
                content = yaml_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/yaml; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                return self.send_error_response(404, "NOT_FOUND", "openapi.yaml not found")

        # Debug endpoint for Playground DB inspector
        if path == "/api/v1/debug/db":
            with self.db() as con:
                users = [dict(r) for r in con.execute("SELECT id, username, role, team, salt, substr(hash, 1, 16) || '...' as hash_preview FROM users").fetchall()]
                now = int(time.time())
                tokens = [dict(r) for r in con.execute("SELECT substr(hash, 1, 16) || '...' as hash_preview, user_id, expires, (expires - ?) as ttl_sec FROM tokens", (now,)).fetchall()]
                tasks = [dict(r) for r in con.execute("SELECT id, title, status, owner_id, version FROM tasks").fetchall()]
                return self.send_json(200, {
                    "users": users,
                    "tokens": tokens,
                    "tasks": tasks,
                    "server_time": now
                })

        # Static file serving for Playground UI
        if path == "/" or path == "/playground" or path == "/playground/":
            return self.serve_static_file(BASE_DIR / "playground" / "index.html", "text/html")
        if path.startswith("/playground/"):
            rel_file = path[len("/playground/"):]
            file_path = BASE_DIR / "playground" / rel_file
            content_type = "text/plain"
            if rel_file.endswith(".html"): content_type = "text/html"
            elif rel_file.endswith(".css"): content_type = "text/css"
            elif rel_file.endswith(".js"): content_type = "application/javascript"
            elif rel_file.endswith(".json"): content_type = "application/json"
            elif rel_file.endswith(".svg"): content_type = "image/svg+xml"
            return self.serve_static_file(file_path, content_type)

        # GET /api/v1/tasks
        if path == "/api/v1/tasks":
            user = self.get_authenticated_user()
            if not user:
                return self.send_error_response(401, "UNAUTHENTICATED", "Valid Bearer token required")

            # Parse query params (page, pageSize, status)
            page_val = query.get("page", ["1"])[0]
            page_size_val = query.get("pageSize", ["20"])[0]
            status_filter = query.get("status", [None])[0]

            try:
                page = int(page_val)
                page_size = int(page_size_val)
            except ValueError:
                return self.send_error_response(422, "VALIDATION_ERROR", "page and pageSize must be integers")

            if page < 1:
                return self.send_error_response(422, "VALIDATION_ERROR", "page must be >= 1")
            if not (1 <= page_size <= 100):
                return self.send_error_response(422, "VALIDATION_ERROR", "pageSize must be between 1 and 100")

            if status_filter and status_filter not in ("open", "done"):
                return self.send_error_response(422, "VALIDATION_ERROR", "status must be 'open' or 'done'")

            with self.db() as con:
                # Ambil semua task lalu saring dengan can_access (Slide 42 & 59)
                query_sql = "SELECT * FROM tasks"
                params = []
                if status_filter:
                    query_sql += " WHERE status = ?"
                    params.append(status_filter)

                all_rows = [dict(r) for r in con.execute(query_sql, params).fetchall()]
                # Saring hanya task yang boleh diakses pengguna ini (Slide 42)
                authorized_tasks = [t for t in all_rows if can_access(con, user, t)]

                total_items = len(authorized_tasks)
                total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1

                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_items = authorized_tasks[start_idx:end_idx]

                return self.send_json(200, {
                    "data": paginated_items,
                    "meta": {
                        "page": page,
                        "pageSize": page_size,
                        "totalItems": total_items,
                        "totalPages": total_pages
                    }
                })

        # GET /api/v1/tasks/{taskId}
        if path.startswith("/api/v1/tasks/"):
            task_id = path[len("/api/v1/tasks/"):]
            if "/" in task_id or not task_id:
                return self.send_error_response(404, "NOT_FOUND", "Task not found")

            user = self.get_authenticated_user()
            if not user:
                return self.send_error_response(401, "UNAUTHENTICATED", "Valid Bearer token required")

            with self.db() as con:
                task_row = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                if not task_row:
                    return self.send_error_response(404, "NOT_FOUND", f"Task '{task_id}' not found")

                task = dict(task_row)
                # Object Authorization Check (BOLA)
                if not can_access(con, user, task):
                    return self.send_error_response(403, "FORBIDDEN", "You do not have permission to view this task")

                return self.send_json(200, {"data": task})

        return self.send_error_response(404, "NOT_FOUND", f"Endpoint '{path}' not found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Debug endpoint for resetting DB to seed state
        if path == "/api/v1/debug/reset":
            if os.path.exists(self.custom_db_path or DB_PATH):
                os.remove(self.custom_db_path or DB_PATH)
            initialize_db(self.custom_db_path)
            return self.send_json(200, {"message": "Database reset to initial seed state successfully."})

        # POST /api/v1/auth/token (Login)
        if path == "/api/v1/auth/token":
            body, err = self.read_json_body()
            if err:
                status, code, msg = err
                return self.send_error_response(status, code, msg)

            if not isinstance(body, dict):
                return self.send_error_response(422, "VALIDATION_ERROR", "Body must be a JSON object")

            username = body.get("username")
            password = body.get("password")

            if not isinstance(username, str) or not isinstance(password, str):
                return self.send_error_response(422, "VALIDATION_ERROR", "username and password are required strings")

            with self.db() as con:
                user_row = con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
                user = dict(user_row) if user_row else None

                # Anti timing attack (Slide 54): tetap hitung hash meskipun user tidak ditemukan
                salt = bytes.fromhex(user["salt"]) if user else bytes(16)
                check = password_hash(password, salt)

                if not user or not hmac.compare_digest(check, user["hash"]):
                    return self.send_error_response(401, "INVALID_CREDENTIALS", "Username or password incorrect")

                # Generate high-entropy opaque bearer token (Slide 54)
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
                now = int(time.time())
                expires = now + 900  # 15 minutes (Slide 54 & 64)

                con.execute(
                    "INSERT INTO tokens (hash, user_id, expires) VALUES (?, ?, ?)",
                    (token_hash, user["id"], expires)
                )
                con.commit()

                return self.send_json(200, {
                    "token": token,
                    "token_type": "Bearer",
                    "expires_in": 900,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                        "team": user["team"]
                    }
                })

        # POST /api/v1/tasks (Create Task)
        if path == "/api/v1/tasks":
            user = self.get_authenticated_user()
            if not user:
                return self.send_error_response(401, "UNAUTHENTICATED", "Valid Bearer token required")

            body, err = self.read_json_body()
            if err:
                status, code, msg = err
                return self.send_error_response(status, code, msg)

            # Strict validation against Mass Assignment (Slide 22 & 57)
            if not validate_create(body):
                return self.send_error_response(
                    422,
                    "INVALID_PAYLOAD",
                    "Only 'title' is allowed (length 3-150). Internal fields such as owner_id or role cannot be set by client."
                )

            task_id = f"tsk_{secrets.token_hex(4)}"
            title = body["title"].strip()
            owner_id = user["id"]  # Owner must be determined by server from token (Slide 8 & 22)
            version = 1

            with self.db() as con:
                con.execute(
                    "INSERT INTO tasks (id, title, status, owner_id, version) VALUES (?, ?, 'open', ?, ?)",
                    (task_id, title, owner_id, version)
                )
                con.commit()

            location = f"/api/v1/tasks/{task_id}"
            created_data = {
                "id": task_id,
                "title": title,
                "status": "open",
                "owner_id": owner_id,
                "version": version
            }
            # Return 201 Created with Location header (Slide 24 & 57)
            return self.send_json(201, {"data": created_data}, extra_headers={"Location": location})

        return self.send_error_response(404, "NOT_FOUND", f"Endpoint '{path}' not found")

    def do_PATCH(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # PATCH /api/v1/tasks/{taskId}
        if path.startswith("/api/v1/tasks/"):
            task_id = path[len("/api/v1/tasks/"):]
            if "/" in task_id or not task_id:
                return self.send_error_response(404, "NOT_FOUND", "Task not found")

            user = self.get_authenticated_user()
            if not user:
                return self.send_error_response(401, "UNAUTHENTICATED", "Valid Bearer token required")

            body, err = self.read_json_body()
            if err:
                status, code, msg = err
                return self.send_error_response(status, code, msg)

            # Body harus tepat {status, version} (Slide 58)
            if not isinstance(body, dict) or set(body.keys()) - {"status", "version"}:
                return self.send_error_response(422, "INVALID_PAYLOAD", "Payload must contain only 'status' and 'version'")

            status = body.get("status")
            version = body.get("version")

            if status not in ("open", "done"):
                return self.send_error_response(422, "INVALID_PAYLOAD", "status must be 'open' or 'done'")
            if not isinstance(version, int):
                return self.send_error_response(422, "INVALID_PAYLOAD", "version must be an integer")

            with self.db() as con:
                # 1. Cek existence: 404 jika tidak ditemukan (Slide 58)
                row = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                if not row:
                    return self.send_error_response(404, "NOT_FOUND", f"Task '{task_id}' not found")
                task = dict(row)

                # 2. Cek authorization: 403 jika tidak berhak (Slide 58)
                if not can_access(con, user, task):
                    return self.send_error_response(403, "FORBIDDEN", "You do not have permission to update this task")

                # 3. Optimistic concurrency control (Slide 30 & 58)
                cur = con.execute(
                    "UPDATE tasks SET status = ?, version = version + 1 WHERE id = ? AND version = ?",
                    (status, task_id, version)
                )
                if cur.rowcount == 0:
                    return self.send_error_response(409, "VERSION_CONFLICT", "Task has been modified by another request. Please reload.")

                con.commit()
                updated_row = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                return self.send_json(200, {"data": dict(updated_row)})

        return self.send_error_response(404, "NOT_FOUND", f"Endpoint '{path}' not found")

    def do_DELETE(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # DELETE /api/v1/tasks/{taskId}
        if path.startswith("/api/v1/tasks/"):
            task_id = path[len("/api/v1/tasks/"):]
            if "/" in task_id or not task_id:
                return self.send_error_response(404, "NOT_FOUND", "Task not found")

            user = self.get_authenticated_user()
            if not user:
                return self.send_error_response(401, "UNAUTHENTICATED", "Valid Bearer token required")

            with self.db() as con:
                # 1. Cek existence (Slide 58)
                row = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                if not row:
                    return self.send_error_response(404, "NOT_FOUND", f"Task '{task_id}' not found")
                task = dict(row)

                # 2. Cek authorization (Slide 58)
                if not can_access(con, user, task):
                    return self.send_error_response(403, "FORBIDDEN", "You do not have permission to delete this task")

                # 3. Delete task
                con.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                con.commit()

                # 204 No Content (Sukses tanpa body, Slide 25 & 26)
                self.send_response(204)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                return

        return self.send_error_response(404, "NOT_FOUND", f"Endpoint '{path}' not found")

    def serve_static_file(self, path: Path, content_type: str):
        if not path.exists() or not path.is_file():
            return self.send_error_response(404, "NOT_FOUND", "File not found")

        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        # Structured, clean logging without leaking tokens or sensitive bodies (Slide 52 Hari 3)
        sys.stderr.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} - {format % args}\n")


def run_server(port=PORT, db_path=None):
    initialize_db(db_path)
    server_address = ("127.0.0.1", port)
    
    class CustomServerHandler(TaskHubHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, db_path=db_path, **kwargs)

    httpd = http.server.ThreadingHTTPServer(server_address, CustomServerHandler)
    print(f"===============================================================")
    print(f"🚀 TaskHub API Lab Server (Hari 1) is running!")
    print(f"📍 Address: http://127.0.0.1:{port}")
    print(f"🌐 Interactive Playground: http://127.0.0.1:{port}/")
    print(f"📜 OpenAPI Specification: http://127.0.0.1:{port}/openapi.yaml")
    print(f"===============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
