# Modul 1: Fondasi REST & Semantik HTTP
*API Development Training - Hari 1: Bagian 2*

---

## 1. API Sebagai Kontrak Antarperangkat Lunak

API (Application Programming Interface) pada dasarnya adalah **kontrak formal** yang mengikat dua sistem independen (klien dan server) untuk saling berkomunikasi tanpa perlu mengetahui implementasi internal masing-masing.

```
+----------------+      Request (Method, Path, Headers, Body)     +----------------+
|                | ---------------------------------------------> |                |
|     Client     |                                                |     Server     |
| (Web/Mobile/CI)| <--------------------------------------------- | (API Engine)   |
+----------------+      Response (Status, Headers, Payload)       +----------------+
```

Klien tidak perlu tahu apakah server ditulis dengan Python, Go, Node.js, atau Java; dan tidak perlu tahu nama tabel di database SQL. Yang wajib disepakati adalah **kontrak antarmukanya**:
- **Operasi**: Kombinasi HTTP Method dan Path (misal: `POST /api/v1/tasks`).
- **Metadata**: HTTP Headers (misal: `Content-Type: application/json`, `Authorization: Bearer <TOKEN>`).
- **Payload**: Representasi resource dalam format terstruktur (JSON).
- **Hasil**: Kode status HTTP yang bermakna dan struktur representasi respons.

---

## 2. Enam Batasan (Constraints) Arsitektur REST

Roy Fielding merumuskan 6 arsitektur constraint yang membuat REST scalable dan andal:

| Constraint | Penjelasan Inti | Penerapan di Lab TaskHub |
| :--- | :--- | :--- |
| **1. Client-Server** | Pemisahan tanggung jawab antarmuka pengguna (klien) dari logika bisnis dan persistensi (server). | Klien (browser, curl, mobile) berinteraksi hanya melalui HTTP; database terisolasi di sisi server. |
| **2. Stateless** | Setiap request dari klien harus membawa seluruh konteks yang diperlukan. Server tidak menyimpan percakapan/sesi di memori server. | Server memverifikasi identitas pengguna pada setiap request via header `Authorization: Bearer <TOKEN>`. |
| **3. Cacheable** | Respons server harus mendeklarasikan secara eksplisit apakah data boleh disimpan (di-cache) oleh klien/perantara. | Header respons menyertakan direktif cache yang tepat untuk data privat maupun publik. |
| **4. Uniform Interface** | Antarmuka interaksi seragam: identifikasi resource via URI, manipulasi lewat representasi, self-descriptive messages, dan hypermedia. | Resource memiliki pola URI konsisten, format JSON baku, dan semantik method standar. |
| **5. Layered System** | Klien tidak dapat mengetahui apakah ia tersambung langsung ke end-server atau melalui proxy, gateway, load balancer, atau CDN. | Header dipertahankan melalui middleware/reverse-proxy tanpa melanggar otentikasi. |
| **6. Code-on-Demand (Opsional)** | Server dapat memperluas fungsi klien dengan mentransfer kode yang dapat dieksekusi (misal script/wasm). | Bersifat opsional; lab TaskHub berfokus pada data exchange REST murni. |

### Prinsip Penting: Stateless Tidak Berarti Tanpa Database!
> **Catatan Kunci:**
> Banyak pengembang keliru mengira *stateless* berarti server tidak boleh menyimpan data.
> *Stateless* berarti **tidak ada percakapan (conversation state) yang disimpan di sesi server**. Server tidak perlu mengingat "langkah sebelumnya" untuk memproses request berikutnya. Semua konteks (siapa pemanggil, token apa, parameter apa) dibawa lengkap di dalam request saat ini.
> Database tetap menyimpan state bisnis (data task, data user, history).

---

## 3. Desain Resource: Kata Benda Domain vs Kata Kerja Fungsi

Dalam REST, URI adalah alamat dari **Resource (Kata Benda)**, sedangkan aksinya ditentukan oleh **HTTP Method (Kata Kerja)**.

### Contoh Pola yang Salah (RPC-style):
- ❌ `POST /getTasks`
- ❌ `POST /createTask`
- ❌ `POST /tasks/updateTask`
- ❌ `GET /deleteTaskById?id=123`

### Contoh Pola yang Benar (RESTful):
- ✅ `GET /api/v1/tasks` (Membaca koleksi task)
- ✅ `POST /api/v1/tasks` (Membuat task baru)
- ✅ `GET /api/v1/tasks/{taskId}` (Membaca spesifik task)
- ✅ `PATCH /api/v1/tasks/{taskId}` (Mengubah sebagian data task)
- ✅ `DELETE /api/v1/tasks/{taskId}` (Menghapus spesifik task)

---

## 4. Relasi Domain: Hierarki (Nesting) vs Query Parameter

Ketika resource memiliki relasi (misalnya: Task berada di dalam Project):
1. **Nesting (Hierarki):**
   Gunakan jika resource anak tidak memiliki eksistensi mandiri di luar induknya:
   ```http
   GET /api/v1/projects/{projectId}/tasks
   ```
2. **Query Parameter:**
   Gunakan jika relasi hanyalah salah satu cara pemfilteran:
   ```http
   GET /api/v1/tasks?project_id=prj_123
   ```
> **Aturan Praktis:** Hindari nesting lebih dari 2 tingkat kedalaman (misal: `/teams/{id}/projects/{id}/tasks/{id}/comments/{id}`) karena membuat URL rapuh dan mempersulit caching serta perutean.

---

## 5. Semantik HTTP Method: Safe vs Idempotent

Dua sifat krusial yang harus dipahami oleh setiap backend engineer:

- **Safe (Aman):** Request **tidak meminta perubahan state bisnis** di database. Request safe aman dipanggil berulang kali, di-cache, di-prefetch oleh browser atau web crawler.
- **Idempotent (Idempoten):** Menjalankan request sebanyak 1 kali atau 100 kali berturut-turut menghasilkan **efek akhir state sistem yang sama**.

| Method | Semantik Utama | Safe? | Idempoten? | Penjelasan Perilaku |
| :--- | :--- | :---: | :---: | :--- |
| **GET** | Membaca representasi resource | **Ya** | **Ya** | Tidak boleh mengubah state di database. |
| **POST** | Membuat resource baru / domain action | **Tidak** | **Tidak** | Menjalankan 2x POST akan membuat 2 resource berbeda. |
| **PUT** | Mengganti representasi secara penuh | **Tidak** | **Ya** | Mengganti seluruh data target; pengulangan menghasilkan target yang sama. |
| **PATCH** | Mengubah sebagian atribut resource | **Tidak** | **Kondisional** | Idempoten jika menetapkan nilai (`status="done"`), tidak idempoten jika increment (`counter=counter+1`). |
| **DELETE** | Menghapus resource | **Tidak** | **Ya** | Panggilan pertama menghapus resource (204). Panggilan berikutnya resource tetap terhapus (404/204). Efek akhirnya sama: resource hilang. |
| **OPTIONS**| Menanyakan kapabilitas / Preflight CORS | **Ya** | **Ya** | Mengambil header allow method/headers tanpa efek samping. |

> **PERINGATAN KERAS:**
> Jangan pernah menggunakan method `GET` untuk menghapus atau menyetujui transaksi (misal: `GET /approve?id=5`)!
> Antivirus proxy, crawler Google, atau browser link prefetching dapat memicu eksekusi endpoint tersebut secara otomatis tanpa persetujuan pengguna!
