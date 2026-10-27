# Modul 6: Evaluasi, Matriks Keamanan, & Latihan Perluasan
*API Development Training - Hari 1: Bagian 8*

---

## 1. Tujuh Poin Kunci yang Wajib Dikuasai (Slide 67)

Setelah menyelesaikan materi Hari 1, setiap peserta wajib menguasai 7 prinsip fundamental ini:

1. **Stateless tidak melarang database**:
   Stateless berarti setiap request membawa kredensial dan konteks lengkap tanpa bergantung pada state sesi percakapan di memori server. Database tetap persisten menyimpan data bisnis.
2. **401 dan 403 menguji hal yang berbeda**:
   `401 Unauthenticated` menguji keabsahan identitas (siapa Anda). `403 Forbidden` menguji izin hak akses pada objek (apakah Anda berhak atas data ini).
3. **Token/JWT valid bukan jaminan izin atas objek**:
   Hanya karena token memiliki tanda tangan yang sah dan belum expired, bukan berarti pengguna tersebut berhak membaca atau mengubah data milik pengguna lain (BOLA).
4. **UUID bukan pengganti otorisasi objek**:
   Penggunaan UUID hanya menghentikan enumeration attack, bukan otorisasi. Otorisasi harus diverifikasi di server setiap kali objek diakses.
5. **Basic Auth / Base64 bukan enkripsi**:
   Base64 hanyalah algoritma encoding teks dua arah tanpa kunci rahasia. Siapa pun dapat men-decode kredensial jika tidak diamankan TLS/HTTPS.
6. **OAuth 2.0 bisa memakai Opaque Token atau JWT**:
   OAuth adalah protokol delegasi otorisasi, bukan format token. Server otorisasi bebas menerbitkan token berwujud string acak opaque atau token mandiri bertanda tangan JWT.
7. **Dokumentasi kontrak lengkap mendefinisikan semua skema dan respons error**:
   OpenAPI yang baik tidak hanya mendokumentasikan respons sukses `200`, tetapi merinci skema validasi, batasan karakter, format error `4xx/5xx`, dan skema keamanan.

---

## 2. Matriks Pengujian Keamanan Hari 1 (Slide 48)

| No | Skenario Pengujian | Hasil yang Diharapkan | Catatan Pembuktian |
| :---: | :--- | :---: | :--- |
| 1 | Request tanpa header `Authorization` | `401` | Server menolak sebelum masuk ke logika bisnis. |
| 2 | Token acak / tidak valid / kedaluwarsa | `401` | Lookup SHA-256 token di DB menghasilkan 0 row. |
| 3 | Login dengan password salah | `401` | Pesan generik tanpa membocorkan apakah username ada. |
| 4 | Bob membaca task milik Alice | `403` | Otorisasi objek mendeteksi `task.owner_id != user.id`. |
| 5 | Manager Tim A membaca task milik Bob (Tim B) | `403` | Otorisasi objek mendeteksi tim owner berbeda dengan tim manager. |
| 6 | Manager Tim A membaca task milik Alice (Tim A) | `200` | Diizinkan karena satu tim. |
| 7 | Injeksi `owner_id` pada pembuatan task | `422` | Server menolak mass assignment. |
| 8 | Injeksi field ilegal `role: admin` | `422` | Allowlist schema menolak properti tak dikenal. |
| 9 | Request body dengan JSON rusak / malformed | `400` | Parser JSON gagal sebelum proses validasi. |
| 10| Header `Content-Type` bukan `application/json` | `415` | Media type rejection. |
| 11| Request body melebihi batas 64 KB | `413` | Perlindungan DoS / payload too large. |
| 12| PATCH task menggunakan nomor versi lama | `409` | Optimistic lock collision terdeteksi. |
| 13| Query parameter `page=0` atau `pageSize=500` | `422` | Boundary validation error. |
| 14| Request dari Origin asing (`https://evil.site`) | No CORS | Tidak menyertakan header `Access-Control-Allow-Origin`. |
| 15| Membaca task yang sudah dihapus | `404` | Resource tidak lagi ditemukan di database. |

---

## 3. Latihan Kelompok: Memperluas Kontrak dengan Resource `projects` dan `due_date` (Slide 66)

### Skenario Bisnis:
Tim bisnis TaskHub ingin menambahkan manajemen proyek (`projects`) dan tenggat waktu task (`due_date`).

### Tugas Peserta:
1. **Desain Skema**:
   - Tentukan field untuk `Project`: `id`, `name`, `description`, `owner_id`, `team`.
   - Tambahkan field `project_id` dan `due_date` (ISO-8601 date-time string) pada model `Task`.
2. **Aturan Hak Akses**:
   - Siapa yang boleh membuat project? (Misal: hanya role `manager` dan `admin`).
   - Apakah member tim B boleh menambahkan task ke dalam project tim A? (Wajib ditolak `403`).
3. **Analisis Breaking Change**:
   - Jika field `due_date` bersifat opsional di `POST /tasks`, apakah ini breaking change? (Non-breaking).
   - Jika `due_date` diwajibkan (*required*), apakah ini breaking change? (Ya, breaking change bagi klien lama).
4. **Perluasan OpenAPI**:
   - Tuliskan path `/api/v1/projects` dan `/api/v1/projects/{projectId}/tasks` pada `openapi.yaml`.
   - Lengkapi dengan skema request body dan respons status.
