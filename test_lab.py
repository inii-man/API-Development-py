#!/usr/bin/env python3
"""
Unit and Persistence Test Suite for TaskHub Lab (Hari 1)
Based on API Development Training Course Specs (Slides 40-43)
"""

import unittest
import tempfile
import os
import secrets
import hashlib
import time

import app

class LabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        app.initialize_db(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def get_users_map(self, con):
        rows = con.execute("SELECT * FROM users").fetchall()
        return {r["username"]: dict(r) for r in rows}

    def test_password(self):
        """Uji hashing password dengan salt acak dan scrypt (Slide 41)."""
        salt = os.urandom(16)
        self.assertEqual(
            app.password_hash("abc", salt),
            app.password_hash("abc", salt)
        )
        self.assertNotEqual(
            app.password_hash("abc", salt),
            app.password_hash("xyz", salt)
        )

    def test_object_authorization(self):
        """Uji otorisasi level objek (BOLA prevention) lintas pengguna (Slide 42 & 49)."""
        with app.get_db(self.db_path) as con:
            users = self.get_users_map(con)
            task = {"owner_id": "u1"} # Alice's task (Tim A)

            # 1. Alice adalah pemilik (Owner) -> Berhak
            self.assertTrue(app.can_access(con, users["alice"], task))

            # 2. Manager tim A adalah atasan tim Alice -> Berhak
            self.assertTrue(app.can_access(con, users["manager"], task))

            # 3. Admin memiliki akses penuh -> Berhak
            self.assertTrue(app.can_access(con, users["admin"], task))

            # 4. Bob berasal dari Tim B -> DITOLAK (403 BOLA defense)
            self.assertFalse(app.can_access(con, users["bob"], task))

    def test_manager_cross_team_authorization(self):
        """Manager Tim A tidak boleh mengakses task milik Bob dari Tim B."""
        with app.get_db(self.db_path) as con:
            users = self.get_users_map(con)
            task_bob = {"owner_id": "u2"} # Bob (Tim B)

            self.assertFalse(app.can_access(con, users["manager"], task_bob))
            self.assertTrue(app.can_access(con, users["bob"], task_bob))
            self.assertTrue(app.can_access(con, users["admin"], task_bob))

    def test_validate_create(self):
        """Uji validasi CreateTask dan penolakan mass assignment (Slide 22 & 57)."""
        # Valid title
        self.assertTrue(app.validate_create({"title": "Review Kontrak API"}))
        self.assertTrue(app.validate_create({"title": "   Spasi di awal dan akhir   "}))

        # Rejection: Injeksi field internal (mass assignment)
        self.assertFalse(app.validate_create({"title": "Review", "owner_id": "u2"}))
        self.assertFalse(app.validate_create({"title": "Review", "role": "admin"}))
        self.assertFalse(app.validate_create({"title": "Review", "version": 2}))

        # Rejection: Panjang title di luar 3 s.d 150
        self.assertFalse(app.validate_create({"title": "ab"})) # < 3
        self.assertFalse(app.validate_create({"title": "   a   "})) # strip < 3
        self.assertFalse(app.validate_create({"title": "x" * 151})) # > 150

        # Rejection: Format salah
        self.assertFalse(app.validate_create("Review"))
        self.assertFalse(app.validate_create(["Review"]))
        self.assertFalse(app.validate_create({}))

    def test_task_optimistic_concurrency(self):
        """Uji optimistic concurrency update versioning (Slide 30 & 58)."""
        with app.get_db(self.db_path) as con:
            # Task awal versi 1
            row = con.execute("SELECT * FROM tasks WHERE id = 'tsk_alice_1'").fetchone()
            self.assertEqual(row["version"], 1)

            # Update pertama dengan version=1 -> Berhasil, naik jadi version 2
            cur = con.execute(
                "UPDATE tasks SET status = ?, version = version + 1 WHERE id = ? AND version = ?",
                ("done", "tsk_alice_1", 1)
            )
            self.assertEqual(cur.rowcount, 1)

            # Update kedua dengan version=1 lama -> GAGAL (0 baris diupdate / conflict 409)
            cur2 = con.execute(
                "UPDATE tasks SET status = ?, version = version + 1 WHERE id = ? AND version = ?",
                ("open", "tsk_alice_1", 1)
            )
            self.assertEqual(cur2.rowcount, 0)

            # Update dengan version=2 yang baru -> Berhasil
            cur3 = con.execute(
                "UPDATE tasks SET status = ?, version = version + 1 WHERE id = ? AND version = ?",
                ("open", "tsk_alice_1", 2)
            )
            self.assertEqual(cur3.rowcount, 1)

    def test_token_expiry_and_hash(self):
        """Uji mekanisme token opaque ber-hash SHA-256 dan validasi kedaluwarsa (Slide 54 & 55)."""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = int(time.time())

        with app.get_db(self.db_path) as con:
            # 1. Simpan token aktif (berlaku 900s)
            con.execute("INSERT INTO tokens VALUES (?, ?, ?)", (token_hash, "u1", now + 900))
            con.commit()

            # Query token aktif
            cur = con.execute(
                "SELECT * FROM tokens WHERE hash = ? AND expires > ?",
                (token_hash, now)
            )
            self.assertIsNotNone(cur.fetchone())

            # 2. Token kadaluwarsa (expired 10 detik yang lalu)
            expired_token = secrets.token_urlsafe(32)
            expired_hash = hashlib.sha256(expired_token.encode("utf-8")).hexdigest()
            con.execute("INSERT INTO tokens VALUES (?, ?, ?)", (expired_hash, "u1", now - 10))
            con.commit()

            cur_exp = con.execute(
                "SELECT * FROM tokens WHERE hash = ? AND expires > ?",
                (expired_hash, now)
            )
            self.assertIsNone(cur_exp.fetchone())

if __name__ == "__main__":
    unittest.main()
