# TaskHub API Lab - Hari 1: Desain REST, OpenAPI, dan Autentikasi
**API Development Training**

Repositori ini berisi implementasi lengkap bahan ajar dan interactive playground untuk pelatihan **API Development Training - Hari 1: Desain REST, OpenAPI, dan Autentikasi** (berdasarkan slide materi resmi 1 s.d 68).

---

## 🌟 Fitur Utama Hari 1

1. **Backend REST API TaskHub (`app.py`)**:
   - Dibuat menggunakan **Python 3 Standard Library** murni (`http.server`, `sqlite3`, `hashlib`, `hmac`, `secrets`).
   - Hashing password adaptif menggunakan **`scrypt`** dengan salt acak 16-byte (Slide 53).
   - Otentikasi **Opaque Bearer Token** 32-byte berentropi tinggi, disimpan hash SHA-256 di database SQLite dengan masa berlaku (TTL) 900 detik (Slide 54 & 55).
   - Pencegahan **BOLA / IDOR** (Broken Object Level Authorization) dengan logika `can_access(con, user, task)` memetakan peran Alice (Tim A), Bob (Tim B), Manager (Tim A), dan Admin (Slide 49 & 56).
   - Pertahanan dari serangan **Mass Assignment** pada endpoint pembuatan task (Slide 22 & 57).
   - Kontrol konkurensi **Optimistic Locking** berbasis kolom `version` (mengembalikan `409 VERSION_CONFLICT` saat update tabrakan) (Slide 30 & 58).
   - Paginasi (`page`, `pageSize`) dan filter status (`open`, `done`) dengan batasan ketat (Slide 27 & 59).
   - Format respons error terstandarisasi berbasis mesin (`error.code` & `requestId`) (Slide 29).

2. **Web Playground & Studio Interaktif (`/playground`)**:
   - Terintegrasi langsung di dalam server `app.py` pada alamat: **`http://127.0.0.1:8000/`**.
   - **Persona Switcher**: Tukar peran instan antara Alice, Bob, Manager A, dan Admin dengan 1 klik (otomatis login dan menyematkan token).
   - **Request Composer & Preset Skenario**: 13 skenario uji bawaan yang mendemonstrasikan kasus positif dan negatif dari slide.
   - **Response Inspector**: Status code visual color-coded, response latency counter, headers, dan penampil JSON berwarna.
   - **Bahan Ajar Reader**: Penampil 6 modul materi pembelajaran lengkap dengan diagram dan tabel.
   - **BOLA & RBAC Simulator**: Simulator interaktif yang mendemonstrasikan langkah demi langkah evaluasi izin objek.
   - **Optimistic Concurrency Collision Simulator**: Uji coba tabrakan update 2 tab browser secara simultan.
   - **Live Database Inspector**: Memantau isi tabel `users`, `tokens`, dan `tasks` secara real-time.
   - **OpenAPI Spec Viewer**: Membaca spesifikasi `openapi.yaml`.
   - **Kuis Evaluasi 7 Poin Kunci**: Uji pemahaman mandiri dengan scoring dan pembahasan.

3. **Dokumen Bahan Ajar Terstruktur (`/bahan_ajar/`)**:
   - [Modul 1: Fondasi REST & Semantik HTTP](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/01_fondasi_rest_http.md)
   - [Modul 2: Desain Kontrak API, Validasi, & Penanganan Error](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/02_kontrak_dan_validasi.md)
   - [Modul 3: OpenAPI 3.1.1 Sebagai Kontrak Teruji](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/03_openapi_spesifikasi.md)
   - [Modul 4: Autentikasi, RBAC, dan Pencegahan BOLA](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/04_autentikasi_dan_rbac_bola.md)
   - [Modul 5: Panduan Praktik Lab & Langkah Hands-on](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/05_lab_praktik_panduan.md)
   - [Modul 6: Evaluasi, Matriks Keamanan, & Latihan Perluasan](file:///Users/sulaimansaleh/Documents/API-Development/bahan_ajar/06_evaluasi_dan_latihan.md)

4. **Kontrak & Koleksi Testing**:
   - `openapi.yaml`: Kontrak OpenAPI 3.1.1 valid.
   - `test_lab.py`: Unit test suite (scrypt, BOLA, concurrency, validation).
   - `test_http.py`: End-to-end integration test suite pada port dinamis (15 matriks keamanan).
   - `postman_collection.json` & `postman_environment.json`: Koleksi Postman siap pakai.

---

## 🎯 Prasyarat Belajar (Prerequisites)

Sebelum memulai lab dan materi pelatihan ini, peserta diharapkan mempersiapkan:
1. **Konseptual**: Memahami dasar protokol HTTP (*request/response, method, status code*), format data JSON, serta dasar database relasional & query SQL (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
2. **Tooling**: Terbiasa menggunakan Terminal (CLI dasar & *environment variable*) dan HTTP client (`curl`, Postman, atau Insomnia).
3. **Lingkungan**: Python 3.9+ (dengan modul bawaan `sqlite3` dan `hashlib.scrypt`) serta Web Browser modern (Chrome/Safari/Firefox/Edge).
4. **Bebas Dependensi (Zero-Dependency)**: Tidak memerlukan instalasi database server eksternal dan tidak memerlukan `pip install` library tambahan.

---

## 📦 Panduan Instalasi & Setup Langkah demi Langkah

Repositori ini dirancang **Zero-Dependency (100% Python Standard Library)**, sehingga proses setup sangat cepat tanpa perlu melakukan `pip install` library eksternal atau konfigurasi database server terpisah.

### Langkah 1: Kloning atau Unduh Repositori
Buka terminal dan clone repositori ini:
```bash
git clone https://github.com/inii-man/API-Development-py.git
cd API-Development-py
```
*(Atau masuk ke direktori tempat Anda mengekstrak berkas ZIP proyek ini).*

---

### Langkah 2: Verifikasi Versi Python
Pastikan Python versi **3.9 atau yang lebih baru** telah terpasang:
```bash
# macOS / Linux
python3 --version

# Windows
python --version
```
> **Catatan Windows**: Jika perintah `python3` tidak dikenali, gunakan `python`.

---

### Langkah 3: Siapkan Virtual Environment (Opsional tapi Direkomendasikan)
Meskipun lab ini menggunakan pustaka standar, membuat virtual environment merupakan *best practice* untuk mengisolasi lingkungan kerja:

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt / CMD)
python -m venv venv
.\venv\Scripts\activate.bat
```

---

### Langkah 4: Verifikasi Instalasi dengan Menjalankan Automated Test
Jalankan pengujian otomatis bawaan untuk memastikan interpreter Python Anda mendukung modul `sqlite3` dan algoritma `scrypt`:
```bash
# macOS / Linux
python3 -m unittest -v test_lab test_http

# Windows
python -m unittest -v test_lab test_http
```
Jika melihat output **`Ran 10 tests ... OK`**, instalasi Anda 100% valid dan siap digunakan!

---

### Langkah 5: Jalankan Server API & Interactive Playground
Nyalakan server lab:
```bash
# macOS / Linux
python3 app.py

# Windows
python app.py
```
Saat server menyala, database `taskhub.db` akan dibuat dan di-seed secara otomatis. Buka browser dan navigasikan ke:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

### ⚙️ Menjalankan pada Port Kustom (Jika Port 8000 Terpakai)
Jika port 8000 sedang digunakan oleh aplikasi lain, gunakan *environment variable* `PORT`:
```bash
# macOS / Linux
PORT=8080 python3 app.py

# Windows (PowerShell)
$env:PORT="8080"; python app.py

# Windows (CMD)
set PORT=8080 && python app.py
```

---

## ⚡ Panduan Cepat Menjalankan

### 1. Menjalankan Seluruh Pengujian Otomatis
```bash
python3 -m unittest -v test_lab test_http
```
*Output: 10 test lulus (100% OK).*

### 2. Menjalankan Server API & Web Playground
```bash
python3 app.py
```
Akses di browser Anda:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 👥 Akun Uji Coba Bawaan (Seed)
Semua akun memiliki password demo: **`Lab-Only-123!`**
- **`alice`**: Member (Tim A)
- **`bob`**: Member (Tim B)
- **`manager`**: Manager (Tim A)
- **`admin`**: Administrator (Semua Tim)
