# Modul 4: Autentikasi, RBAC, dan Pencegahan BOLA
*API Development Training - Hari 1: Bagian 5*

---

## 1. Membedakan Autentikasi (AuthN) dan Otorisasi (AuthZ)

Kegagalan memisahkan kedua konsep ini adalah salah satu penyebab utama kerentanan keamanan pada API modern:

```
[Request Klien]
       |
       v
+-------------------------------+
|    1. AUTENTIKASI (AuthN)     | ---> Apakah token ini sah? Siapa pengguna di balik token ini?
+-------------------------------+      (Jika gagal -> 401 UNAUTHENTICATED)
       | (Identitas Terverifikasi: Alice, role: member, team: A)
       v
+-------------------------------+
|     2. OTORISASI (AuthZ)      | ---> Apakah Alice berhak membaca / mengubah task tsk_123?
+-------------------------------+      (Jika tidak berhak -> 403 FORBIDDEN)
```

> **Ingat:**
> - `401 Unauthenticated` = Server tidak tahu siapa Anda (token tidak ada/salah/expired).
> - `403 Forbidden` = Server tahu persis siapa Anda, tetapi **Anda dilarang** mengakses objek tersebut!

---

## 2. Ancaman Terbesar API: BOLA (Broken Object Level Authorization)

Berdasarkan **OWASP API Security Top 10**, BOLA (dikenal juga sebagai IDOR - Insecure Direct Object Reference) menempati peringkat nomor 1 kerentanan paling sering dieksploitasi.

### Skenario Serangan BOLA:
1. Penyerang (Bob) login secara legal dan mendapatkan token bearer yang sah.
2. Bob melihat task miliknya: `GET /api/v1/tasks/tsk_bob_1`.
3. Bob mengganti ID di URL menjadi milik Alice: `GET /api/v1/tasks/tsk_alice_1`.
4. Jika backend hanya memeriksa apakah token Bob valid tanpa memeriksa **kepemilikan objek**, data rahasia Alice akan bocor ke Bob!

### Mitos UUID:
> *"Kami menggunakan UUID acak yang tidak bisa ditebak, jadi API kami aman."*
> **SALAH BESAR!** UUID hanya mempersulit penebakan berurutan (*enumeration attack*). Jika UUID bocor melalui log, referer header, tautan sharing, atau endpoint listing, siapa pun yang memiliki token valid tetap bisa membuka objek tersebut jika server tidak memverifikasi izin level objek.

---

## 3. Komparasi Metode Autentikasi

| Metode | Karakteristik Kunci | Catatan Keamanan Penting |
| :--- | :--- | :--- |
| **API Key** | Identitas aplikasi/klien berupa string panjang statis. | Jangan pernah ditaruh di URL (terekam di log server) atau di frontend JavaScript publik. |
| **Basic Auth** | Format `Authorization: Basic base64(user:pass)`. | **Base64 BUKAN enkripsi!** Base64 hanyalah representasi teks yang dapat di-decode seketika oleh siapa pun. Wajib dilindungi TLS/HTTPS! |
| **Bearer Opaque** | Token acak berentropi tinggi tanpa isi data (32+ byte). | Hash disimpan di database. Server melakukan lookup ke DB. Sangat mudah di-revoke seketika. |
| **Bearer JWT** | Token mandiri (self-contained) berisi klaim JSON yang ditandatangani secara kriptografis (JWS). | Server dapat memvalidasi signature tanpa query DB. Namun payload base64url dapat dibaca siapa saja, dan proses revoke lebih rumit. |
| **OAuth 2.0 + PKCE**| Kerangka delegasi otorisasi terstandarisasi (RFC 9700). | Wajib menggunakan PKCE (S256) untuk public client (SPA/Mobile) untuk mencegah intersepsi auth code. |

---

## 4. Matriks Otorisasi TaskHub (RBAC + Object-Level)

Di lab TaskHub, kita mendefinisikan 4 aktor dengan batasan hak akses sebagai berikut:

| Aktor | User ID | Role | Tim | Akses Task Alice | Akses Task Bob | Akses Task Manager | Buat Task Baru |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Alice** | `u1` | `member` | `A` | **ALLOW** | **DENY (403)** | **DENY (403)** | **ALLOW** |
| **Bob** | `u2` | `member` | `B` | **DENY (403)** | **ALLOW** | **DENY (403)** | **ALLOW** |
| **Manager** | `u3` | `manager`| `A` | **ALLOW** | **DENY (403)** | **ALLOW** | **ALLOW** |
| **Admin** | `u4` | `admin` | `ALL` | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |

### Implementasi Fungsi `can_access` (Slide 56):
```python
def can_access(con, user: dict, task: dict) -> bool:
    # 1. Admin memiliki hak penuh terhadap seluruh resource
    if user["role"] == "admin":
        return True

    # 2. Pemilik task (Owner) selalu berhak mengakses task miliknya
    if task["owner_id"] == user["id"]:
        return True

    # 3. Manager hanya berhak mengakses task milik anggota dalam tim yang sama
    owner = con.execute("SELECT team FROM users WHERE id=?", (task["owner_id"],)).fetchone()
    if owner and user["role"] == "manager" and owner["team"] == user["team"]:
        return True

    # 4. Selain aturan di atas, tolak akses (Defensive by default)
    return False
```

---

## 5. Scope Koleksi (Collection Scoping)

Proteksi BOLA **tidak hanya berlaku pada endpoint detail** (`GET /tasks/{id}`), tetapi **wajib diterapkan pada endpoint koleksi** (`GET /tasks`):

Jika Alice memanggil `GET /api/v1/tasks`, server **tidak boleh** mengembalikan seluruh task di database lalu menyembunyikannya di antarmuka frontend. Server harus menyaring data di query sehingga task milik Bob dari Tim B tidak pernah terkirim ke jaringan!
Begitu pula nilai `meta.totalItems`, jangan sampai membocorkan jumlah total task milik pihak lain.
