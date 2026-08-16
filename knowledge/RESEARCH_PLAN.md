# Tower 2 — Rekrutmen Analytics · Research Plan & Knowledge Base

Status: **DRAFT untuk direview** · Dibuat 2026-08-16 · Belum ada eksekusi riset.

## 0. Tujuan & ruang lingkup

Membangun **knowledge base untuk seluruh sistem**, bukan cuma bahan bikin database mock.
Riset ini memberi fondasi fakta yang dipakai oleh:

- `mockdb/` — database mock rekrutmen (sedang dibangun)
- Dashboard **prototipe** (rencana: Streamlit dulu) — folder baru, **bukan** `recruitment_dashboard/` yang lama
- Dashboard **produksi** — folder baru lagi, stack non-Streamlit (TBD)
- **Chatbot RAG** — korpus jawaban dari perdir/SK + fakta riset

Dua aset fondasi proyek: **`knowledge/`** (fakta + korpus) dan **`mockdb/out/`** (data).
Semua dashboard = konsumen dari keduanya.

> Kenapa riset dulu sebelum mockdb selesai: data asli (situs rekrutmen + perdir) besar
> kemungkinan **mengubah beberapa aturan** yang sudah kita sepakati (lihat §6). Lebih murah
> mengubah aturan sekarang daripada regenerate seluruh database nanti.

## 1. Arsitektur folder

```
tower2_dashboard/
├─ referensi/            # bahan MENTAH dari manusia (SK PDF, screenshot, chat, reqgathering) — tetap
├─ data sintetis/        # data real, ADA PII (DAPEG) — jangan commit
├─ knowledge/            # ← BARU. Knowledge base sistem, dipisah dari mockdb
│  ├─ RESEARCH_PLAN.md   # dokumen ini
│  ├─ sources/           # hasil tangkapan per sumber (mentah-terstruktur)
│  │  ├─ rekrutmen_pln/  #   R1: programs.csv + detail/*.html + pdf/*.pdf
│  │  ├─ perdir/         #   R2: <nomor>/text.md, chunks.jsonl, summary.md
│  │  ├─ seleksi_pln/    #   R5: schema_notes.md (dari screenshot)
│  │  ├─ web/            #   R3: cache halaman yg di-fetch
│  │  └─ htd_chat/       #   R4: fakta dari chat WA tim HTD
│  ├─ findings.md        # fakta TERSULING lintas sumber (klaim + sitasi + keyakinan + tgl)
│  └─ corpus/            # chunk siap-RAG untuk chatbot (dibuat belakangan)
├─ mockdb/               # konsumen knowledge → hasilkan database mock
│  ├─ rules/  build/  out/  docs/
├─ recruitment_dashboard/# dashboard LAMA (streamlit) — dibiarkan jalan, akan digantikan
└─ (nanti) dashboard-prototipe/  dashboard-produksi/   # folder baru, di luar recruitment_dashboard
```

Nama `knowledge/` gampang di-rename kalau kamu lebih suka `kb/` atau `riset/`.

## 2. Sumber, metode, cara simpan

| # | Sumber | Cara ambil | Disimpan sebagai | Otoritas |
|---|---|---|---|---|
| **R1** | rekrutmen.pln.co.id (publik) | httpx tarik semua listing (paginasi) → tiap halaman detail → unduh PDF brosur. Cek `robots.txt` dulu, rate-limit sopan, cache lokal | `sources/rekrutmen_pln/programs.csv` (judul, jenjang, penempatan, periode, lokasi, kuota, url, pdf) + `pdf/` + `detail/` | Tinggi (data resmi PLN) |
| **R1-login** | akun sendiri (CV + rekap lamaran) | Kamu login manual + captcha di browser Playwright → aku ambil alih sesi. Hanya akunmu | `sources/rekrutmen_pln/akun/` (skema field biodata, bukan data orang lain) | Tinggi |
| **R2** | perdir/SK (PDF) | `pip install pymupdf` → probe teks-vs-scan → ekstrak teks → chunk per pasal | `sources/perdir/<nomor>/text.md` + `chunks.jsonl` + `summary.md`; aturan tersuling → `mockdb/rules/*.yaml` | **Tertinggi** (regulasi) |
| **R3** | Google + web | WebSearch (2–3 frasa) → WebFetch sumber terkuat. On-demand tiap butuh fakta | entri di `findings.md` (klaim, 2–3 URL, keyakinan, tgl) + cache di `sources/web/` | Sedang (verifikasi silang) |
| **R4** | Chat WA tim HTD | Baca export `.txt` / foto (vision) | fakta → `findings.md` tag `sumber=HTD` | **Tertinggi** (pelaksana langsung) |
| **R5** | seleksi.pln.co.id | Baca 3 screenshot yang ada. **Tanpa** bruteforce / data bocor (lihat §4) | `sources/seleksi_pln/schema_notes.md` | Rendah (parsial) |

**Format `findings.md`** (satu store fakta lintas sumber, sekaligus sitasi data dictionary):

```markdown
### F-012 · Jumlah lokasi tes untuk program S1 se-Indonesia
Klaim: dibuka di 8 kota (Jakarta, Bandung, Surabaya, Medan, Pekanbaru, Pontianak, Denpasar, Makassar).
Sumber: [detik url], [antara url]  · Keyakinan: sedang · Tanggal: 2026-08-16 · Dampak: tabel lokasi_seleksi
```

## 3. Alur login + captcha (human-in-the-loop)

1. Aku jalankan Chromium (Playwright) **headed**, pakai `user_data_dir` persisten.
2. **Kamu** yang login di jendela itu + selesaikan captcha.
3. Aku deteksi sesi sudah masuk → ambil alih navigasi & ekstraksi di sesi yang sama.
4. Cookie tersimpan di profile → run berikutnya reuse login sampai kedaluwarsa.

Aku tidak pernah memegang password atau menyelesaikan captcha. Hanya akunmu, hanya datamu.

## 4. Batas etika (sumber 4)

**Tidak** dilakukan: bruteforce login `seleksi.pln.co.id`, dan berburu/memakai data hasil kebocoran.
Izin membangun dashboard bukan izin menembus sistem HR atau memakai data pribadi bocor.
Jalur yang dipakai: model skema dari screenshot yang ada + (bila perlu data asli) minta lewat
kanal resmi/nota dinas ke VP HTD/HST. Fallback ini sudah disetujui: "lanjut pakai info seadanya".

## 5. Urutan eksekusi (usulan)

1. **R1 publik** — paling siap, risiko rendah, langsung menjawab "pakai program asli?" & holding-vs-group
2. **R2 perdir 0056** (Akuisisi Pegawai) — SOP rekrutmen resmi, paling mengubah aturan
3. **R4** begitu chat WA di-share (primer, cepat)
4. **R3** jalan terus on-demand untuk isi celah
5. **R5** + **R1-login** kapan pun siap (butuh aksimu: login/kredensial/captcha)

## 6. Dampak ke aturan mockdb (kumpulkan dulu, putuskan nanti)

1. ⚠️ **Holding-only vs PLN Group** — program asli semuanya "PLN Group, penempatan subholding".
   Ini yang bikin porsi Pembangkitan di holding kelihatan kecil. Putuskan setelah R1+R2.
2. **Nama & struktur program/angkatan** — kemungkinan ganti ke data asli (R1).
3. **Tahapan seleksi & passing grade** — dari perdir 0056 (R2), bisa beda dari asumsi 6-tahap.
4. **Mapping posisi ↔ jurusan** — dari PDF brosur program (R1), bukan tebakan.

## 7. Yang kubutuhkan dari kamu

- [ ] File **chat WA tim HTD** (export `.txt` paling enak; foto juga bisa) → taruh `referensi/`
- [ ] Saat R1-login: **kamu login manual** di browser yang kubuka (untuk captcha)
- [ ] Konfirmasi nama folder `knowledge/` (atau usul lain)
- [ ] Greenlight mulai R1 setelah review plan ini

## 8. Status log

| Tgl | Kejadian |
|---|---|
| 2026-08-16 | Plan dibuat. Probe R1 sukses (situs server-rendered, bisa di-scrape). Tooling dicek: Playwright+Chromium ADA, library PDF BELUM (perlu pymupdf). Chat WA belum di-share. |
