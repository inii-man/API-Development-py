#!/usr/bin/env python3
"""
HTTP Integration Test Suite for TaskHub Lab (Hari 1)
Based on API Development Training Course Specs (Slides 44-45 & 48)
Tests live HTTP server running on random dynamic port (port 0).
"""

import unittest
import http.server
import threading
import urllib.request
import urllib.error
import json
import tempfile
import os

import app

class TestTaskHubHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Database temporary untuk server integration test
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp.name, "test_http.db")
        app.initialize_db(cls.db_path)

        class CustomHandler(app.TaskHubHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, db_path=cls.db_path, **kwargs)

        # Port 0 memilih port dinamis yang belum terpakai (Slide 44)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CustomHandler)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def call(self, method: str, path: str, body: dict = None, token: str = None, headers: dict = None, raw_body: bytes = None):
        """Helper HTTP request untuk test runner."""
        url = self.base + path
        req_headers = {}
        if token:
            req_headers["Authorization"] = f"Bearer {token}"
        if headers:
            req_headers.update(headers)

        data = None
        if raw_body is not None:
            data = raw_body
        elif body is not None:
            req_headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, method=method, headers=req_headers)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                resp_headers = dict(resp.headers)
                resp_body_bytes = resp.read()
                try:
                    resp_body = json.loads(resp_body_bytes.decode("utf-8")) if resp_body_bytes else {}
                except Exception:
                    resp_body = resp_body_bytes.decode("utf-8")
                return status, resp_body, resp_headers
        except urllib.error.HTTPError as exc:
            err_body_bytes = exc.read()
            try:
                err_body = json.loads(err_body_bytes.decode("utf-8")) if err_body_bytes else {}
            except Exception:
                err_body = err_body_bytes.decode("utf-8")
            return exc.code, err_body, dict(exc.headers)

    def login(self, username: str, password: str = "Lab-Only-123!") -> str:
        status, body, _ = self.call("POST", "/api/v1/auth/token", {"username": username, "password": password})
        if status == 200 and isinstance(body, dict):
            return body.get("token")
        return None

    def test_full_lifecycle_cross_user(self):
        """Alur lintas user sesuai slide 45."""
        a = self.login("alice")
        b = self.login("bob")
        self.assertIsNotNone(a, "Login alice harus sukses")
        self.assertIsNotNone(b, "Login bob harus sukses")

        # 1. Alice membuat task -> 201 Created dengan header Location
        status, body, headers = self.call("POST", "/api/v1/tasks", {"title": "Review API"}, token=a)
        self.assertEqual(status, 201)
        self.assertIn("Location", headers)
        path = headers["Location"]
        task_id = body["data"]["id"]
        self.assertEqual(path, f"/api/v1/tasks/{task_id}")

        # 2. Bob mencoba mengakses task milik Alice -> 403 Forbidden (BOLA Defense)
        status_b, _, _ = self.call("GET", path, token=b)
        self.assertEqual(status_b, 403)

        # 3. Alice membaca task miliknya sendiri -> 200 OK
        status_a, task_detail, _ = self.call("GET", path, token=a)
        self.assertEqual(status_a, 200)
        self.assertEqual(task_detail["data"]["version"], 1)

        # 4. Alice mengupdate task dari versi 1 -> 200 OK (versi naik jadi 2)
        status_patch1, patch1_body, _ = self.call("PATCH", path, {"status": "done", "version": 1}, token=a)
        self.assertEqual(status_patch1, 200)
        self.assertEqual(patch1_body["data"]["version"], 2)

        # 5. Alice mengupdate lagi tapi memakai versi 1 lama -> 409 VERSION_CONFLICT (Optimistic Concurrency)
        status_patch2, err_patch, _ = self.call("PATCH", path, {"status": "open", "version": 1}, token=a)
        self.assertEqual(status_patch2, 409)
        self.assertEqual(err_patch["error"]["code"], "VERSION_CONFLICT")

        # 6. Pagination validation: page=0 tidak diizinkan -> 422
        status_page0, err_page, _ = self.call("GET", "/api/v1/tasks?page=0", token=a)
        self.assertEqual(status_page0, 422)

        # 7. Alice menghapus task miliknya -> 204 No Content
        status_del, _, _ = self.call("DELETE", path, token=a)
        self.assertEqual(status_del, 204)

        # 8. Alice mencoba membaca task yang sudah dihapus -> 404 Not Found
        status_after_del, _, _ = self.call("GET", path, token=a)
        self.assertEqual(status_after_del, 404)

    def test_manager_role_access(self):
        """Manager Tim A dapat melihat task Alice, tapi tidak dapat melihat task Bob."""
        a = self.login("alice")
        b = self.login("bob")
        mgr = self.login("manager")

        # Alice (Tim A) buat task
        _, body_a, _ = self.call("POST", "/api/v1/tasks", {"title": "Task Tim A"}, token=a)
        task_a_path = f"/api/v1/tasks/{body_a['data']['id']}"

        # Bob (Tim B) buat task
        _, body_b, _ = self.call("POST", "/api/v1/tasks", {"title": "Task Tim B"}, token=b)
        task_b_path = f"/api/v1/tasks/{body_b['data']['id']}"

        # Manager Tim A akses task Alice -> 200 OK
        status_mgr_a, _, _ = self.call("GET", task_a_path, token=mgr)
        self.assertEqual(status_mgr_a, 200)

        # Manager Tim A akses task Bob -> 403 Forbidden
        status_mgr_b, _, _ = self.call("GET", task_b_path, token=mgr)
        self.assertEqual(status_mgr_b, 403)

    def test_admin_role_access(self):
        """Admin dapat mengakses semua task dari tim manapun."""
        a = self.login("alice")
        admin = self.login("admin")

        _, body_a, _ = self.call("POST", "/api/v1/tasks", {"title": "Admin Inspection Task"}, token=a)
        task_path = f"/api/v1/tasks/{body_a['data']['id']}"

        status_admin, _, _ = self.call("GET", task_path, token=admin)
        self.assertEqual(status_admin, 200)

    def test_security_matrix_scenarios(self):
        """Uji 15 matriks keamanan sesuai Slide 48."""
        a = self.login("alice")

        # 1. Tanpa token / token random -> 401
        self.assertEqual(self.call("GET", "/api/v1/tasks")[0], 401)
        self.assertEqual(self.call("GET", "/api/v1/tasks", token="random_bogus_token")[0], 401)

        # 2. Password salah -> 401 tanpa bocor detail
        s_wrong_pw, err_pw, _ = self.call("POST", "/api/v1/auth/token", {"username": "alice", "password": "WrongPassword!"})
        self.assertEqual(s_wrong_pw, 401)
        self.assertEqual(err_pw["error"]["code"], "INVALID_CREDENTIALS")

        # 3. Injeksi owner_id pada create -> 422
        s_owner, err_owner, _ = self.call("POST", "/api/v1/tasks", {"title": "Exploit", "owner_id": "u2"}, token=a)
        self.assertEqual(s_owner, 422)
        self.assertEqual(err_owner["error"]["code"], "INVALID_PAYLOAD")

        # 4. JSON rusak -> 400
        s_bad_json, _, _ = self.call("POST", "/api/v1/tasks", raw_body=b"{title: not json}", token=a, headers={"Content-Type": "application/json"})
        self.assertEqual(s_bad_json, 400)

        # 5. Content-Type tak didukung -> 415
        s_ct, _, _ = self.call("POST", "/api/v1/tasks", raw_body=b"title=formdata", token=a, headers={"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(s_ct, 415)

        # 6. Body melebihi batas 65536 byte -> 413
        huge_title = "x" * 70000
        huge_payload = json.dumps({"title": huge_title}).encode("utf-8")
        s_huge, _, _ = self.call("POST", "/api/v1/tasks", raw_body=huge_payload, token=a, headers={"Content-Type": "application/json"})
        self.assertEqual(s_huge, 413)

        # 7. CORS check: Origin localhost mendapat header, origin asing tidak
        s_cors_ok, _, h_cors_ok = self.call("GET", "/api/v1/tasks", token=a, headers={"Origin": "http://localhost:3000"})
        self.assertEqual(s_cors_ok, 200)
        self.assertEqual(h_cors_ok.get("Access-Control-Allow-Origin"), "http://localhost:3000")

        s_cors_ext, _, h_cors_ext = self.call("GET", "/api/v1/tasks", token=a, headers={"Origin": "https://attacker.site"})
        self.assertEqual(s_cors_ext, 200)
        self.assertNotIn("Access-Control-Allow-Origin", h_cors_ext)

if __name__ == "__main__":
    unittest.main()
