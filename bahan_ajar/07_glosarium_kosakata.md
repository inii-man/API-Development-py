# Modul 7: Glosarium & Kamus Istilah API Development
*Kamus Istilah Teknis, Konsep Keamanan, Arsitektur, dan Protokol API*

Dokumen ini memuat penjelasan mendalam mengenai kosakata, singkatan, protokol, dan konsep-konsep kunci yang digunakan di seluruh materi pelatihan **API Development Training**. Setiap istilah dijelaskan secara komprehensif mulai dari definisi, latar belakang masalah, cara kerja, hingga contoh penerapannya.

---

## 📑 Daftar Isi Istilah

1. [PKCE (Proof Key for Code Exchange)](#1-pkce-proof-key-for-code-exchange)
2. [BOLA / IDOR (Broken Object Level Authorization)](#2-bola--idor-broken-object-level-authorization)
3. [AuthN vs AuthZ (Authentication vs Authorization)](#3-authn-vs-authz-otentikasi-vs-otorisasi)
4. [Opaque Token vs JWT (JSON Web Token)](#4-opaque-token-vs-jwt-json-web-token)
5. [RBAC vs ABAC (Role-Based vs Attribute-Based Access Control)](#5-rbac-vs-abac)
6. [Mass Assignment (Over-Posting Vulnerability)](#6-mass-assignment-over-posting)
7. [Optimistic Concurrency Control (OCC) & Lost Update](#7-optimistic-concurrency-control-occ--lost-update)
8. [Scrypt & Password Hashing vs Fast Hash](#8-scrypt--password-hashing-vs-fast-hash)
9. [Salt Kriptografis & Rainbow Table](#9-salt-kriptografis--rainbow-table)
10. [Timing Attack & Constant-Time Comparison](#10-timing-attack--constant-time-comparison)
11. [Idempotency vs Safety pada HTTP](#11-idempotency-vs-safety-pada-http)
12. [Stateless dalam Arsitektur REST](#12-stateless-dalam-arsitektur-rest)
13. [OpenAPI 3.1 & Schema Drift](#13-openapi-31--schema-drift)
14. [CORS (Cross-Origin Resource Sharing) & Preflight](#14-cors-cross-origin-resource-sharing--preflight)
15. [Prepared Statement / Parameterized Query](#15-prepared-statement--parameterized-query)
16. [RFC 9700 (OAuth 2.0 Security Best Current Practice)](#16-rfc-9700-oauth-20-security-best-current-practice)

---

## 1. PKCE (Proof Key for Code Exchange)

- **Pelafalan**: *"pixy"* (`/ˈpɪk.si/`)
- **Standar RFC**: [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636) & diwajibkan secara tegas di [RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700).

### Latar Belakang Masalah
Pada alur otorisasi OAuth 2.0 standar (*Authorization Code Flow*), server otentikasi memberikan *Authorization Code* sekali-pakai ke aplikasi klien melalui redirect URL di browser. Aplikasi klien kemudian menukar kode ini dengan *Access Token* bersama `client_secret`.
Namun, pada **Public Client** (seperti Single Page Application / SPA berbasis React/Vue atau aplikasi Mobile iOS/Android):
1. Kode sumber klien berjalan di perangkat pengguna dan dapat dibongkar (*reverse engineered*).
2. Public client **tidak dapat menyimpan `client_secret` secara aman**.
3. Aplikasi berbahaya lain di perangkat yang sama dapat menyadap redirect URI dan mencuri *Authorization Code* tersebut (*Authorization Code Interception Attack*).

### Solusi PKCE
PKCE menghilangkan kebutuhan menyimpan `client_secret` di public client dengan menciptakan **kunci rahasia dinamis sekali-pakai** untuk setiap sesi transaksi login:

```
[Klien / Browser]                                      [Authorization Server]
       |                                                         |
 1. Buat code_verifier (acak)                                    |
    Hitung code_challenge = SHA256(verifier)                     |
       |                                                         |
 2. GET /authorize?code_challenge=...&method=S256 -------------> | (Simpan code_challenge)
       |                                                         |
 3. <-- Redirect kembali membawa Authorization Code ------------ |
       |                                                         |
 4. POST /token (bawa Authorization Code + code_verifier) -----> | Verifikasi: SHA256(verifier)
       |                                                         | == challenge awal?
 5. <-- Berikan Access Token jika cocok ------------------------ |
```

### 3 Komponen Inti PKCE:
1. **`code_verifier`**: String acak dengan entropi tinggi (43 s.d 128 karakter) yang dibuat oleh browser secara lokal saat tombol login diklik.
2. **`code_challenge`**: Turunan dari verifier. Dibuat dengan rumus:
   $$\text{code\_challenge} = \text{base64url}(\text{SHA-256}(\text{code\_verifier}))$$
3. **`code_challenge_method`**: Wajib menggunakan `S256` (SHA-256). Hindari metode `plain` karena tidak aman.

> **Poin Kunci RFC 9700**: PKCE kini **wajib** untuk semua Public Client dan **sangat direkomendasikan** bahkan untuk Confidential Client (backend-to-backend) untuk mencegah serangan injection auth code.

---

## 2. BOLA / IDOR (Broken Object Level Authorization)

- **Kepanjangan**: *Broken Object Level Authorization* (dikenal juga sebagai *Insecure Direct Object Reference* / IDOR).
- **Status**: Kerentanan nomor #1 di daftar **OWASP API Security Top 10**.

### Definisi
Kerentanan yang terjadi ketika endpoint API menerima referensi ID objek secara langsung (misal: `/api/v1/tasks/{taskId}`) dan mempercayai pemanggil yang memiliki token valid tanpa memeriksa apakah pengguna tersebut **memiliki hak akses** atas objek spesifik tersebut.

### Contoh Skenario di Lab TaskHub:
- Alice (User `u1`, Tim A) membuat task dengan ID: `tsk_alice_1`.
- Bob (User `u2`, Tim B) berhasil login secara legal dan memiliki token resmi.
- Bob mengirim request:
  ```http
  GET /api/v1/tasks/tsk_alice_1
  Authorization: Bearer <TOKEN_BOB_YANG_VALID>
  ```
- **Jika Server Rentan BOLA**: Server melihat token Bob valid, lalu langsung menjalankan `SELECT * FROM tasks WHERE id = 'tsk_alice_1'`, sehingga data rahasia Alice bocor ke Bob!
- **Server Kebal BOLA (Pertahanan TaskHub)**: Server mengecek fungsi otorisasi objek:
  ```python
  if not can_access(con, user, task):
      return 403, {"error": {"code": "FORBIDDEN"}}
  ```

> **Mitos UUID**: Mengganti ID berurutan (`1, 2, 3`) dengan UUID acak (`a8b3...`) **BUKAN** proteksi BOLA! UUID hanya mencegah penyerang menebak ID secara berurutan, namun jika UUID bocor (dari log, URL sharing, atau browser history), siapa pun tetap dapat membukanya jika otorisasi objek di server tidak diimplementasikan.

---

## 3. AuthN vs AuthZ (Otentikasi vs Otorisasi)

Sering tertukar, padahal merupakan dua tahap gerbang keamanan yang sama sekali berbeda:

| Aspek | Authentication (AuthN / Otentikasi) | Authorization (AuthZ / Otorisasi) |
| :--- | :--- | :--- |
| **Pertanyaan Inti** | *"Siapa Anda?"* (Membuktikan identitas) | *"Bolehkan Anda mengakses objek/aksi ini?"* (Memeriksa izin) |
| **Mekanisme** | Password, OTP, Biometrik, Bearer Token, API Key. | Role, Permissions, Access Control List, Policy domain. |
| **Kode Error HTTP**| `401 Unauthenticated` (Token salah/expired). | `403 Forbidden` (Identitas sah tapi izin ditolak). |
| **Urutan Server** | Dijalankan **pertama kali** sebelum logika bisnis. | Dijalankan **setelah** objek diambil dari database. |

---

## 4. Opaque Token vs JWT (JSON Web Token)

Dua format token bearer yang paling banyak digunakan di industri:

```
Opaque Token:  "s8F9j2K_e3W7qL1xZ0vB4nC8mP5tY6uI9oE2wQ..."  (Hanya string acak)
JWT:           "eyJhbGciOi... . eyJzdWIiOi... . TJVA95Or..."  (Header . Payload . Signature)
```

| Fitur | Opaque Token (Dipakai di Lab TaskHub) | JWT (JSON Web Token) |
| :--- | :--- | :--- |
| **Struktur** | String acak berentropi tinggi tanpa arti bagi klien (*by-reference*). | 3 bagian base64url: Header, Payload data, Signature kriptografis (*by-value*). |
| **Penyimpanan Server** | Server menyimpan hash SHA-256 token di database. | Server tidak perlu menyimpan token; verifikasi dilakukan dengan memvalidasi signature kriptografis. |
| **Pencabutan (Revocation)** | **Sangat Cepat & Mudah**: Cukup hapus baris token dari tabel database. | **Rumit**: Token tetap valid sampai masa `exp` habis, kecuali server mengelola *blocklist* / *revocation list*. |
| **Kerahasiaan Payload** | Tidak membawa data apa pun di dalam token. | **Dapat dibaca siapa saja**: Payload JWT hanya di-encode base64, **bukan dienkripsi**! Dilarang menaruh password, NIK, atau secret di payload JWT. |

---

## 5. RBAC vs ABAC

Dua paradigma utama dalam perancangan otorisasi sistem:

### RBAC (Role-Based Access Control)
Hak akses ditentukan semata-mata berdasarkan **Peran (Role)** pengguna:
- Contoh: Role `admin` boleh menghapus task, Role `member` hanya boleh membaca.
- **Kelemahan RBAC Murni**: Tidak bisa menangani kepemilikan objek. Jika Alice dan Bob sama-sama memiliki role `member`, RBAC murni mengizinkan Bob mengedit task milik Alice karena role mereka identik.

### ABAC (Attribute-Based Access Control) / Policy-Based
Hak akses dievaluasi secara dinamis berdasarkan **Atribut** dari subjek, resource, dan lingkungan:
- Atribut Subjek: `user.id`, `user.role`, `user.team`.
- Atribut Resource: `task.owner_id`, `task.status`, `task.created_at`.
- Atribut Lingkungan: Jam akses, IP subnet, lokasi kantor.
- **Penerapan di Lab TaskHub**: Logika `can_access(con, user, task)` menggabungkan RBAC dan ABAC:
  1. Jika `user.role == 'admin'` -> Izinkan.
  2. Jika `task.owner_id == user.id` -> Izinkan (Kepemilikan).
  3. Jika `user.role == 'manager'` dan `owner.team == user.team` -> Izinkan (Atribut Relasi Tim).

---

## 6. Mass Assignment (Over-Posting)

### Definisi
Kerentanan di mana backend secara membabi-buta mengikat (*bind*) seluruh data payload JSON dari klien langsung ke model database tanpa memfilter properti internal.

### Contoh Kasus di Lab TaskHub:
Klien seharusnya hanya boleh mengirim:
```json
{ "title": "Setup Server" }
```
Namun penyerang mengirimkan field tambahan:
```json
{
  "title": "Setup Server",
  "owner_id": "u2",        // <-- Mencoba mengalihkan kepemilikan
  "role": "admin",         // <-- Mencoba eskalasi privilege
  "version": 99            // <-- Mencoba merusak konkurensi
}
```
Jika backend langsung melakukan `INSERT INTO tasks ... VALUES (**body)`, penyerang berhasil membajak hak akses.

### Mitigasi:
Gunakan **Allowlist Skema Keras**. Di OpenAPI 3.1:
```yaml
CreateTask:
  type: object
  additionalProperties: false   # Tolak segala properti di luar allowlist
  required: [title]
```
Di Python backend:
```python
if set(body.keys()) - {"title"}:
    return 422, {"error": {"code": "INVALID_PAYLOAD"}}
```

---

## 7. Optimistic Concurrency Control (OCC) & Lost Update

### Fenomena Lost Update
Terjadi saat dua pengguna membaca data pada versi yang sama dan melakukan update hampir bersamaan. Perubahan pengguna yang pertama disimpan akan ditimpa dan hilang tertelan oleh pengguna kedua tanpa disadari.

```
Klien 1 (baca v1) -------------------------> UPDATE -> Sukses (Versi jadi 2)
                                                 |
Klien 2 (baca v1) ------------> [Lambat] ----> UPDATE -> Sukses (Menimpa perubahan Klien 1!)
```

### Cara Kerja Optimistic Locking
Kita menambahkan kolom integer `version` pada setiap baris data di database. Klien wajib menyertakan versi terakhir yang dibacanya:

```sql
UPDATE tasks
SET status = ?, version = version + 1
WHERE id = ? AND version = ?;
```

1. **Klien 1**: Mengirim `version: 1`. Query memeriksa `WHERE version = 1`. Cocok! Data diubah dan versi dinaikkan menjadi `2` (`rowcount = 1`).
2. **Klien 2**: Mengirim `version: 1`. Query memeriksa `WHERE version = 1`. Tidak cocok karena versi di database sudah `2`! `rowcount = 0`.
3. Server mendeteksi tabrakan ini dan segera mengembalikan:
   ```http
   HTTP/1.1 409 Conflict
   {"error": {"code": "VERSION_CONFLICT"}}
   ```
4. Klien 2 dipaksa membaca ulang state terbaru sebelum memutuskan perubahan berikutnya.

---

## 8. Scrypt & Password Hashing vs Fast Hash

Mengapa kita menggunakan **scrypt** di Lab TaskHub dan bukan MD5 atau SHA-256 biasa?

| Kategori | Fast Hash (MD5, SHA-1, SHA-256 murni) | Password Hash Adaptif (scrypt, Argon2id, bcrypt) |
| :--- | :--- | :--- |
| **Tujuan Awal**| Integritas data & checksum cepat (jutaan hash/detik). | Penyimpanan password yang sengaja dibuat komputasinya mahal (*slow-hash*). |
| **Resistensi GPU/ASIC**| **Nol**. Hacker dengan 1 GPU RTX modern bisa mencoba 100 miliar tebakan password per detik. | **Sangat Kuat**. Menggunakan memori besar (*memory-hard*), sehingga GPU dan chip penambang ASIC kehabisan RAM. |
| **Parameter Biaya** | Tetap / tidak bisa diatur. | Bisa diatur parameter biayanya ($N=16384, r=8, p=1$) seiring kemajuan teknologi hardware. |

> **Aturan Emas**: Jangan pernah menggunakan SHA-256 biasa untuk menyimpan password pengguna!

---

## 9. Salt Kriptografis & Rainbow Table

- **Salt**: Rangkaian byte acak dengan entropi tinggi (di lab kita memakai `secrets.token_bytes(16)`) yang digabungkan ke password sebelum dilakukan proses hashing.

### Mengapa Salt Wajib?
1. **Mencegah Rainbow Table**: Rainbow table adalah tabel kamus raksasa berisi miliaran pasangan teks password umum beserta hasil hash-nya yang sudah dihitung sebelumnya (*precomputed*). Dengan salt acak yang unik untuk setiap pengguna, serangan kamus precomputed ini menjadi tidak berguna.
2. **Mencegah Pola Identik**: Jika Alice dan Bob kebetulan memiliki password yang sama (`Lab-Only-123!`), nilai hash di database mereka akan tetap **sama sekali berbeda** karena salt mereka berbeda.

---

## 10. Timing Attack & Constant-Time Comparison

### Apa itu Timing Attack?
Penyerang mengirimkan jutaan request uji coba ke server dan mengukur selisih waktu respons dalam hitungan nanodetik.

Pada pembandingan string biasa (`if check == secret`):
- Komputer membandingkan karakter demi karakter dari kiri ke kanan.
- Jika karakter pertama salah, komputer langsung berhenti (*short-circuit*).
- Jika 5 karakter pertama benar dan baru karakter ke-6 salah, komputer membutuhkan waktu sedikit lebih lama sebelum berhenti.
- Dari grafik selisih nanodetik tersebut, penyerang dapat menebak password atau secret tanda tangan satu demi satu karakter!

### Solusinya: Constant-Time Comparison
Fungsi `hmac.compare_digest(a, b)` di Python membandingkan seluruh panjang karakter tanpa *short-circuit*, sehingga waktu eksekusi selalu konstan terlepas dari di mana posisi karakter yang salah berada.

---

## 11. Idempotency vs Safety pada HTTP

Dua konsep semantik HTTP yang sering disalahartikan:

- **Safe Method (Aman)**:
  Operasi yang **tidak meminta perubahan state bisnis** pada resource. Contoh: `GET`, `HEAD`, `OPTIONS`. Klien tidak bertanggung jawab atas efek samping pemanggilan safe method. Web crawler aman melakukan pre-fetching pada method safe.
- **Idempotent Method (Idempoten)**:
  Operasi yang jika dieksekusi 1 kali atau 10 kali berturut-turut menghasilkan **efek state akhir yang persis sama pada sistem**.
  - Contoh Idempoten: `DELETE /tasks/1`. Request pertama menghapus task (state: hilang). Request kedua menemukan task sudah tidak ada (state: tetap hilang).
  - Contoh Non-Idempoten: `POST /tasks`. Setiap request baru akan membuat baris baru di database (state bertambah terus).

---

## 12. Stateless dalam Arsitektur REST

- Salah satu batasan inti yang dirumuskan Roy Fielding.
- **Arti Sebenarnya**: Server tidak menyimpan status sesi interaksi (*conversation state*) antara klien dan server. Setiap request yang dikirimkan klien harus membawa seluruh data, token otentikasi, dan parameter yang dibutuhkan agar server dapat memprosesnya secara mandiri.
- **Stateless BUKAN berarti tanpa Database**: Database tetap menyimpan data persisten bisnis (tasks, users, orders). Yang dilarang adalah server menyimpan variabel sesi pengguna di RAM server yang membuat klien harus selalu terikat ke satu mesin server fisik yang sama (*sticky session*).

---

## 13. OpenAPI 3.1 & Schema Drift

- **OpenAPI 3.1**: Standar spesifikasi API deskriptif berbasis JSON/YAML yang menyelaraskan dirinya secara 100% dengan standar [JSON Schema 2020-12](https://json-schema.org/).
- **Schema Drift**: Fenomena berbahaya di mana kode aktual backend terus berubah (misal field diganti namanya atau validasi diubah) sementara dokumentasi OpenAPI tidak pernah diperbarui, sehingga terjadi jurang perbedaan antara janji kontrak dan kenyataan implementasi.
- **Contract-First**: Pendekatan merancang berkas `openapi.yaml` terlebih dahulu, melakukan peer review bersama tim klien, dan menggunakan pengujian kontrak otomatis (*conformance testing*) untuk memastikan tidak terjadi schema drift.

---

## 14. CORS (Cross-Origin Resource Sharing) & Preflight

### Kebijakan Keamanan Browser
CORS adalah mekanisme keamanan **di dalam browser** (bukan firewall di server) yang mengatur apakah halaman web dari Domain A (misal: `http://localhost:3000`) diizinkan membaca respons data yang diambil dari Domain B (misal: `http://127.0.0.1:8000`).

### Origin
Origin ditentukan oleh 3 serangkai: **Scheme + Host + Port**. Jika salah satu berbeda, maka terhitung *Cross-Origin*.

### Preflight Request (OPTIONS)
Untuk request yang mengubah data (`POST`, `PATCH`, `DELETE`) atau membawa header kustom (`Authorization`), browser secara otomatis mengirimkan request `OPTIONS` terlebih dahulu (*Preflight*) untuk bertanya kepada server: *"Apakah saya diizinkan mengirim Authorization header ke endpoint ini?"*. Server harus merespons dengan header `Access-Control-Allow-*`.

---

## 15. Prepared Statement / Parameterized Query

Teknik utama pencegahan celah **SQL Injection (SQLi)**:

```python
# ❌ SANGAT RENTAN SQL INJECTION (String Concatenation):
sql = f"SELECT * FROM tasks WHERE id = '{task_id}'"
con.execute(sql)
# Jika task_id berisi: "tsk_1' OR '1'='1" -> Seluruh data database bocor!

# ✅ SANGAT AMAN (Prepared Statement / Parameterized):
con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
```

Ketika menggunakan placeholder tanda tanya (`?`), database engine mengompilasi struktur perintah SQL terlebih dahulu, kemudian menganggap nilai parameter murni sebagai data literal biasa. Karakter kutip (`'`) atau sintaks SQL apapun yang dikirim penyerang tidak akan pernah dieksekusi sebagai perintah.

---

## 16. RFC 9700 (OAuth 2.0 Security Best Current Practice)

- **Judul Resmi**: *OAuth 2.0 Security Best Current Practice* (diterbitkan IETF).
- **Inti Aturan Modern**:
  1. **Hapuskan Implicit Flow**: Implicit Grant yang mengembalikan access token langsung di hash fragment URL browser telah resmi ditinggalkan karena rentan disadap.
  2. **Wajibkan PKCE**: Alur Authorization Code wajib menggunakan ekstensi PKCE (S256).
  3. **Hapuskan Resource Owner Password Credentials Grant (ROPC)**: Klien dilarang meminta dan mengumpulkan username/password pengguna secara langsung; pengguna harus login di halaman resmi Authorization Server.
  4. **Exact Redirect URI Matching**: Authorization server wajib memvalidasi redirect URI secara persis karakter demi karakter (*exact match*), tanpa wildcard.
