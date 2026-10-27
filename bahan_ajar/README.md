# Silabus & Bahan Ajar: API Development Training (Hari 1)
**Fokus: Desain REST, OpenAPI, dan Autentikasi**

Selamat datang di materi pembelajaran resmi **API Development Training - Hari 1**.
Modul ini disusun secara terstruktur dari fondasi arsitektur protokol hingga implementasi pengujian keamanan tingkat tinggi pada API **TaskHub**.

---

## 📚 Daftar Modul Pembelajaran

1. [**Modul 1: Fondasi REST & Semantik HTTP**](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/01_fondasi_rest_http.md)
   - Konsep API sebagai kontrak formal antarperangkat lunak.
   - Enam batasan arsitektur REST (Client-Server, Stateless, Cacheable, Uniform Interface, Layered System, Code-on-Demand).
   - Penamaan resource (kata benda domain vs fungsi RPC).
   - Semantik HTTP Method: Perbedaan mendalam antara *Safe* dan *Idempotent*.

2. [**Modul 2: Desain Kontrak API, Validasi, & Penanganan Error**](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/02_kontrak_dan_validasi.md)
   - Urutan pemrosesan request 6-tahap di server.
   - Pertahanan dari serangan *Mass Assignment* dengan skema allowlist.
   - Mengapa validasi bukan pengganti *Prepared Statements (SQL Parameterization)*.
   - Taksonomi kode status HTTP (200, 201, 204, 400, 401, 403, 404, 409, 413, 415, 422, 500).
   - Kontrol konkurensi dengan *Optimistic Locking (Versioning)*.
   - Standar format error berbasis mesin (`code` & `requestId`).

3. [**Modul 3: OpenAPI 3.1.1 Sebagai Kontrak Teruji**](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/03_openapi_spesifikasi.md)
   - Pendekatan *Contract-First* vs *Code-First*.
   - Bedah struktur berkas `openapi.yaml`: Header, Server, Security Global & Override.
   - Komponen skema yang dapat digunakan ulang (`$ref`).
   - Mencegah *Schema Drift* melalui pengujian kontrak otomatis.

4. [**Modul 4: Autentikasi, RBAC, dan Pencegahan BOLA**](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/04_autentikasi_dan_rbac_bola.md)
   - Membedakan Autentikasi (AuthN) dan Otorisasi (AuthZ).
   - Memahami ancaman BOLA (Broken Object Level Authorization / IDOR).
   - Mengapa UUID bukan pengganti otorisasi objek.
   - Komparasi: API Key, Basic Auth, Bearer Opaque Token, JWT, dan OAuth 2.0 PKCE.
   - Matriks otorisasi 4 aktor: Alice, Bob, Manager Tim A, dan Admin.

5. [**Modul 5: Panduan Praktik Lab & Langkah Hands-on**](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/05_lab_praktik_panduan.md)
   - Arsitektur lab `app.py` menggunakan Python Standard Library murni & SQLite.
   - Panduan pengujian otomatis: `python3 -m unittest -v test_lab test_http`.
   - Langkah demi langkah eksekusi request menggunakan cURL di terminal.
   - Penggunaan koleksi Postman & Insomnia.
   - Solusi masalah umum (*Troubleshooting*).

6. [**Modul 6: Evaluasi, Matriks Keamanan, & Latihan Perluasan**](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/06_evaluasi_dan_latihan.md)
   - Tujuh Poin Kunci yang Wajib Dikuasai peserta pelatihan.
   - 15 Matriks Uji Keamanan API TaskHub.
   - Latihan Kelompok: Memperluas kontrak dengan resource `projects` dan properti `due_date`.
   - Rubrik peer review dan kriteria kelulusan.

---

## 🚀 Menjalankan Lab & Playground Visual

Jalankan satu perintah berikut di terminal:
```bash
python3 app.py
```
Lalu buka browser di:
- **Playground Interaktif & Reader**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Spesifikasi OpenAPI**: [http://127.0.0.1:8000/openapi.yaml](http://127.0.0.1:8000/openapi.yaml)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
