# Modul 3: OpenAPI 3.1.1 Sebagai Kontrak Teruji
*API Development Training - Hari 1: Bagian 4*

---

## 1. OpenAPI: Lebih Dari Sekadar Tampilan Swagger UI

Banyak tim pengembang menganggap OpenAPI/Swagger hanyalah hiasan visual dokumentasi. Padahal, peran sejati OpenAPI adalah **Single Source of Truth** yang menjadi kontrak pengikat antara tim Frontend, Backend, QA, dan Third-Party Integrator.

```
                  +-------------------------+
                  |   OpenAPI 3.1.1 Spec    |
                  |     (openapi.yaml)      |
                  +-------------------------+
                               |
      +------------------------+------------------------+
      |                        |                        |
      v                        v                        v
[Mock Server]           [Backend Engine]         [Contract Tests]
Frontend mulai coding   Mengimplementasikan      Memverifikasi apakah
tanpa menunggu backend  skema & aturan bisnis    respons sesuai spek
```

### Keunggulan Pendekatan Contract-First:
1. **Parallel Development**: Tim frontend dapat membuat mock server instan menggunakan spek OpenAPI sebelum kode backend selesai dibuat.
2. **Contract Testing**: Automated test dapat memeriksa apakah respons backend menyimpang dari dokumen (menghindari *schema drift*).
3. **Deterministic SDK Generation**: Client SDK untuk mobile/web dapat di-generate secara otomatis.

---

## 2. Bedah Struktur `openapi.yaml` TaskHub Lab

### A. Bagian Header & Security Global (Slide 35)
```yaml
openapi: 3.1.1
info:
  title: TaskHub Local Lab
  version: 1.0.0
servers:
  - url: http://127.0.0.1:8000
security:
  - bearerAuth: []
```
- **`openapi: 3.1.1`**: Versi standar spesifikasi OpenAPI terbaru dengan dukungan penuh JSON Schema 2020-12.
- **`info.version`**: Menandai versi dokumen API kita, bukan versi spesifikasi OpenAPI.
- **`security: [bearerAuth: []]`**: Mendeklarasikan bahwa **secara default seluruh endpoint API terkunci** dan membutuhkan Bearer Token.

---

### B. Override Security Publik untuk Login (Slide 36)
```yaml
paths:
  /api/v1/auth/token:
    post:
      summary: 'Login lab: opaque bearer, bukan OAuth server'
      security: []  # <-- Meng-override security global secara eksplisit!
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200': ...
        '401': ...
```
Dengan menulis `security: []`, kita menyatakan bahwa endpoint login dapat diakses tanpa token otentikasi.

---

### C. Komponen Skema yang Dapat Digunakan Ulang (Reusable Components) (Slide 38)

Mendefinisikan skema di bawah `components/schemas` mencegah duplikasi definisi field dan memastikan konsistensi:

```yaml
components:
  schemas:
    Task:
      type: object
      required: [id, title, status, owner_id, version]
      properties:
        id:
          type: string
        title:
          type: string
        status:
          type: string
          enum: [open, done]
        owner_id:
          type: string
        version:
          type: integer

    CreateTask:
      type: object
      additionalProperties: false  # <-- Mencegah injeksi field ilegal (Mass Assignment)!
      required: [title]
      properties:
        title:
          type: string
          minLength: 3
          maxLength: 150

    PatchTask:
      type: object
      additionalProperties: false
      required: [status, version]
      properties:
        status:
          type: string
          enum: [open, done]
        version:
          type: integer
```

---

## 3. Latihan Membaca Kontrak & Mendeteksi Drift

Sebelum menulis kode atau menjalankan pengujian:
1. **Periksa `$ref`**: Pastikan tidak ada referensi komponen yang rusak (`broken ref`).
2. **Periksa Parameter Wajib**: Pastikan `{taskId}` ditandai `required: true`.
3. **Bandingkan Respons Aktual**: Cocokkan kode status dan struktur JSON yang dihasilkan server terhadap model di dokumen.
