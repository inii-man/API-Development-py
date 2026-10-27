# Modul 2: Desain Kontrak API, Validasi, & Penanganan Error
*API Development Training - Hari 1: Bagian 3*

---

## 1. Urutan Pemrosesan Request di Sisi Server

Setiap request HTTP yang masuk ke server wajib melalui 6 tahap verifikasi ketat sebelum perubahan disimpan:

```
[01. Terima]  --> [02. Identitas] --> [03. Izin]    --> [04. Validasi] --> [05. Operasi] --> [06. Respons]
Periksa ukuran    Otentikasi          Otorisasi         Validasi skema    Eksekusi query     Susun kode
& Content-Type    (Bearer Token)      (BOLA & RBAC)     & tipe data       & transaksi DB     status & JSON
```

---

## 2. Validasi Input & Pencegahan Serangan Mass Assignment

Dalam pembuatan resource, klien seringkali mencoba mengirim field sensitif yang seharusnya hanya boleh ditentukan oleh server. Kerentanan ini dikenal sebagai **Mass Assignment**.

### Bahaya Injeksi Field Internal:
```json
// PAYLOAD BERBAHAYA DARI PENYERANG:
{
  "title": "Review Keamanan API",
  "owner_id": "u2",        // <- Mencoba mengalihkan kepemilikan ke user lain!
  "role": "admin",         // <- Mencoba eskalasi privilege!
  "is_approved": true      // <- Mencoba bypass verifikasi!
}
```

### Aturan Pertahanan Server:
1. **Gunakan Skema Allowlist**: Hanya izinkan field yang eksplisit terdaftar pada kontrak (`CreateTask` hanya mengizinkan `title`).
2. **Tolak Input Ilegal**: Jika ada field tambahan di luar allowlist, tolak dengan status `422 Unprocessable Entity` (atau bersihkan secara ketat).
3. **Owner Diambil dari Konteks Otentikasi**: Server wajib mengambil `owner_id` dari identitas token pengguna yang sedang login, **bukan** dari payload body!

```python
def validate_create(body):
    if not isinstance(body, dict):
        return False
    # Tolak jika ada kunci selain 'title'
    if set(body.keys()) - {"title"}:
        return False
    title = body.get("title")
    return isinstance(title, str) and 3 <= len(title.strip()) <= 150
```

---

## 3. Validasi Bukan Pengganti Query Parameterization

Meskipun input sudah divalidasi format dan panjang karakternya, **selalu gunakan Prepared Statements (Parameterized Queries)** ketika berinteraksi dengan database:

```python
# SANGAT AMAN (Placeholder memisahkan perintah SQL dari data pengguna):
con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))

# SANGAT BERBAHAYA (Rentan SQL Injection):
# con.execute("SELECT * FROM tasks WHERE id = '" + task_id + "'")
```

---

## 4. Taksonomi Kode Status HTTP yang Wajib Dikuasai

Jangan pernah mengembalikan `200 OK` dengan pesan error di dalam body (pola anti-REST `{"status": 200, "error": "Unauthorized"}`). Gunakan kode status yang semantik:

### Sukses (2xx):
- **`200 OK`**: Berhasil mengambil atau memperbarui representasi data.
- **`201 Created`**: Berhasil membuat resource baru. Wajib menyertakan header `Location: /api/v1/tasks/{id}` yang mengarahkan ke URI resource baru tersebut.
- **`202 Accepted`**: Request diterima untuk diproses secara asinkron (belum selesai).
- **`204 No Content`**: Sukses mengeksekusi operasi (misal DELETE), **tanpa body respons**.

### Error Klien (4xx):
- **`400 Bad Request`**: Request tidak dapat di-parse (misal: JSON rusak atau sintaks HTTP tidak valid).
- **`401 Unauthenticated`**: Identitas pemanggil tidak diketahui (kredensial login salah, token tidak ada, atau token kedaluwarsa).
- **`403 Forbidden`**: Identitas pemanggil dikenali, tetapi **tidak memiliki izin** untuk mengakses resource tersebut (misal: BOLA defense).
- **`404 Not Found`**: Resource yang diminta tidak ditemukan di database.
- **`409 Conflict`**: Terjadi konflik state resource (misal: Optimistic Lock collision / versi usang).
- **`413 Payload Too Large`**: Ukuran body melebihi batas yang diizinkan server (misal > 64 KB).
- **`415 Unsupported Media Type`**: Klien tidak menyertakan `Content-Type: application/json`.
- **`422 Unprocessable Entity`**: Format JSON valid, namun gagal pada aturan validasi bisnis (misal: title terlalu pendek, page < 1).
- **`429 Too Many Requests`**: Melebihi kuota rate limit.

### Error Server (5xx):
- **`500 Internal Server Error`**: Kegagalan tak terduga pada server. Jangan bocorkan stack trace ke klien!

---

## 5. Kontrol Konkurensi: Optimistic Locking dengan Versioning

Ketika dua pengguna atau proses memperbarui data yang sama secara bersamaan, masalah **Lost Update** akan terjadi jika tidak ada kontrol konkurensi.

```
Client A (baca v1) ------------------------> PATCH (v1 -> v2) [200 OK] (Menang)
                                                 |
Client B (baca v1) --------> [Waktu lambat] ---> PATCH (v1) ----> [409 Conflict] (Kalah)
```

### Implementasi SQL Optimistic Concurrency:
```sql
UPDATE tasks
SET status = ?, version = version + 1
WHERE id = ? AND version = ?;
```

Jika `cur.rowcount == 0`, berarti record dengan `id` tersebut sudah berubah ke versi yang lebih tinggi oleh transaksi lain. Server langsung mengembalikan:
```json
{
  "error": {
    "code": "VERSION_CONFLICT",
    "requestId": "req_8a7d3f",
    "message": "Task has been modified by another request. Please reload."
  }
}
```

---

## 6. Standar Penanganan Error Berbasis Mesin

Klien programatik membutuhkan kode error yang stabil untuk percabangan logika aplikasi, bukan bergantung pada kalimat bahasa manusia yang bisa berubah sewaktu-waktu.

```json
{
  "error": {
    "code": "VERSION_CONFLICT",
    "requestId": "req_9921ef4"
  }
}
```

- **`code`**: Identifier string konsisten (misal: `UNAUTHENTICATED`, `FORBIDDEN`, `INVALID_PAYLOAD`, `VERSION_CONFLICT`).
- **`requestId`**: ID pelacakan unik untuk korelasi audit di server tanpa membocorkan data sensitif.
