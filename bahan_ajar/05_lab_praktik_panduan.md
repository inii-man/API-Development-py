# Modul 5: Panduan Praktik Lab & Langkah Hands-on
*API Development Training - Hari 1: Bagian 6 & 7*

---

## 1. Arsitektur Lab TaskHub

Lab Hari 1 dirancang menggunakan **Python Standard Library** murni (`http.server`, `sqlite3`, `hashlib`, `hmac`, `secrets`) tanpa dependensi pihak ketiga yang rumit, sehingga portabel dan mudah dipelajari secara mendalam.

```
/API-Development/
├── app.py                   <- Server API & Static Server Playground (Port 8000)
├── test_lab.py              <- 6 Unit & Persistence Tests (SQLite Temporary)
├── test_http.py             <- 4 Integration Tests (Server nyata di port acak)
├── openapi.yaml             <- Spesifikasi Kontrak OpenAPI 3.1.1
├── postman_collection.json  <- Test suite Postman dengan test script
├── postman_environment.json <- Environment variabel baseUrl & token
└── playground/              <- Antarmuka interaktif visual & web playground
```

---

## 2. Persiapan & Menjalankan Lab

### A. Menjalankan Unit & Integration Test
Pastikan semua kontrol logika dan keamanan lulus pengujian otomatis:
```bash
python3 -m unittest -v test_lab test_http
```
*Hasil yang diharapkan: 10 tests passed (OK).*

### B. Menjalankan Server Lokal
```bash
python3 app.py
```
Server akan menginisialisasi database `taskhub.db` dengan seed 4 pengguna:
- `alice` (password: `Lab-Only-123!`, role: `member`, team: `A`)
- `bob` (password: `Lab-Only-123!`, role: `member`, team: `B`)
- `manager` (password: `Lab-Only-123!`, role: `manager`, team: `A`)
- `admin` (password: `Lab-Only-123!`, role: `admin`, team: `ALL`)

Server dapat diakses di `http://127.0.0.1:8000/`.

---

## 3. Langkah Demi Langkah Menggunakan cURL

### Langkah 1: Login Alice & Simpan Token
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "Lab-Only-123!"}'
```
*Expected Status: `200 OK`.* Salin nilai `token` dari respons JSON. Simpan ke shell variable:
```bash
export ALICE_TOKEN="<isi-token-alice>"
```

---

### Langkah 2: Alice Membuat Task Baru
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Review Kontrak API TaskHub"}'
```
*Expected Status: `201 Created`.*
Perhatikan header respons: `Location: /api/v1/tasks/tsk_...`.
Salin ID task tersebut:
```bash
export TASK_ID="tsk_..."
```

---

### Langkah 3: Alice Membaca Task Sendiri
```bash
curl -i http://127.0.0.1:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $ALICE_TOKEN"
```
*Expected Status: `200 OK`.*

---

### Langkah 4: Login Bob (Pengguna Tim B)
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "Lab-Only-123!"}'
```
Simpan token Bob:
```bash
export BOB_TOKEN="<isi-token-bob>"
```

---

### Langkah 5: Pembuktian BOLA Defense (Bob Mengakses Task Alice)
```bash
curl -i http://127.0.0.1:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $BOB_TOKEN"
```
*Expected Status: `403 Forbidden`.*
```json
{
  "error": {
    "code": "FORBIDDEN",
    "requestId": "req_...",
    "message": "You do not have permission to view this task"
  }
}
```

---

### Langkah 6: Alice Mengupdate Task (Optimistic Concurrency)
```bash
curl -i -X PATCH http://127.0.0.1:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done", "version": 1}'
```
*Expected Status: `200 OK`.* Field `version` pada respons sekarang bernilai `2`.

---

### Langkah 7: Pengujian Konflik Versi (Versi Lama)
Ulangi request yang sama dengan `version: 1`:
```bash
curl -i -X PATCH http://127.0.0.1:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "open", "version": 1}'
```
*Expected Status: `409 Conflict` (`VERSION_CONFLICT`).*

---

### Langkah 8: Pengujian Mass Assignment Defense
Coba kirim request pembuatan task yang menyisipkan `owner_id`:
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Eksploitasi Owner", "owner_id": "u2"}'
```
*Expected Status: `422 Unprocessable Entity` (`INVALID_PAYLOAD`).*

---

### Langkah 9: Alice Menghapus Task
```bash
curl -i -X DELETE http://127.0.0.1:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $ALICE_TOKEN"
```
*Expected Status: `204 No Content` (tanpa body).*

---

### Langkah 10: Membaca Kembali Task yang Sudah Dihapus
```bash
curl -i http://127.0.0.1:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $ALICE_TOKEN"
```
*Expected Status: `404 Not Found`.*

---

## 4. Panduan Troubleshooting

| Masalah | Kemungkinan Penyebab | Tindakan Solusi |
| :--- | :--- | :--- |
| `Address already in use` | Port 8000 sedang dipakai proses lain. | Matikan proses yang memakai port 8000 (`lsof -i :8000` lalu `kill <PID>`), atau jalankan pada port lain: `PORT=8080 python3 app.py`. |
| Login gagal (`401 INVALID_CREDENTIALS`) | Password atau username salah ketik. | Gunakan username `alice` dan password persis `Lab-Only-123!`. |
| Semua request task menghasilkan `401 UNAUTHENTICATED` | Token sudah melewati TTL 900 detik (15 menit). | Jalankan kembali langkah login untuk memperoleh token baru. |
| Ingin mereset database ke awal | Banyak data uji coba yang kotor. | Hapus file `taskhub.db` lalu restart server, atau klik tombol "Reset DB" di Playground. |
