# HANDOFF — dari fase RISET ke fase BANGUN DATABASE

> **Sesi baru: baca file ini dulu, lalu `knowledge/findings.md`.**
> Riset sudah selesai (45 temuan tersitasi). Tugas berikutnya: konsolidasi + generate database mock.
> Terakhir diperbarui: 2026-08-17.

---

## 1. Di mana kita sekarang

| Fase | Status |
|---|---|
| Riset 7 sumber (R1–R7) | ✅ **SELESAI** — 45 temuan di `knowledge/findings.md` |
| Master data dari DAPEG | ✅ **SELESAI** — `mockdb/out/master/` (5 file, tervalidasi) |
| Klasifikasi jabatan | ✅ **SELESAI** — 6.148 posisi → bidang/sub-bidang/pembidangan |
| **Konsolidasi + generate DB** | ⬜ **BELUM — ini tugas sesi baru** |

## 2. Keputusan yang SUDAH DIKUNCI (jangan dibuka ulang tanpa alasan baru)

| Hal | Keputusan | Rujukan |
|---|---|---|
| **Cakupan** | **PLN Group** — holding kaya (unit induk→pelaksana→posisi dari DAPEG), subholding ringkas (nama perusahaan + bidang + jumlah) | DECISION-01, F-002, F-012 |
| **Horison** | **2020 – 15 Sep 2026**. 2022+ berjangkar penuh; **2020–2021 sengaja "tipis"** (program sedikit, demografi kosong) & ditandai kualitas rendah | F-044 |
| **Tanggal "sekarang"** | **15 September 2026** | keputusan user |
| **Penyimpanan** | **DuckDB** (`mockdb/out/rekrutmen.duckdb`) + export CSV/Parquet | keputusan user |
| **Cara generate** | Persona-agent merancang **aturan** → generator Python eksekusi **per-kandidat secara kausal & ber-seed**. BUKAN subagent per kandidat (200rb+ call, tidak realistis) | keputusan user |
| **Field fisik** | **Kelengkapan bertahap** — kosong di kohort lama, makin terisi tiap tahun | keputusan user |
| **Nama program/angkatan** | Pakai **data asli** hasil scrape, bukan karangan | F-001, F-030 |
| **Dashboard** | Folder **BARU** di luar `recruitment_dashboard/`. Prototipe Streamlit dulu, produksi stack lain (TBD) | keputusan user |

## 3. Angka kalibrasi (dari data asli — jangan pakai asumsi lama)

| Metrik | Nilai | Rujukan |
|---|---|---|
| Kohort/tahun (PLN Induk) | 2021 **337** · 2022 **689** · 2023 **689** · 2024 **1.277** · 2025 **1.098** | F-035 |
| Per angkatan | ±200–400 (batas atas ~500) | F-035 |
| Headcount Induk | 2020 ~44.000ᵈ · 2021 42.755 · 2022 42.151 · 2023 38.542 · 2024 38.289 · 2025 37.423 | F-044 |
| Attrition | **2,7%/thn**, didominasi pensiun; headcount **MENYUSUT** | F-036 |
| ⚠️ Carve-out | Penurunan 2022→2023 (−3.609) = **pemindahan ke subholding, BUKAN attrition** | F-045 |
| Rasio pelamar:diterima | ~1:200 | F-039 |
| Funnel HTD (kumulatif) | 598.395 pelamar → 382.744 lulus adm (64%) → 12.248 lulus wawancara → 2.453 lulus diklat | F-019 |
| Komposisi jenjang | S1 67% · D3 26% · SMK 6% · S2 1% | F-020 |
| No-show | ~44% | F-020 |
| Gender kohort | ~75:25 pria:wanita (prajabatan 2024 bahkan 86:14) | F-038 |

ᵈ = diturunkan lewat identitas terverifikasi `Group = Induk + Anak`.

## 4. Aturan bisnis yang WAJIB dipatuhi generator

1. **Tidak pernah menempatkan pegawai baru ke jabatan struktural** (Team Leader, Assistant Manager,
   Manager, Senior Manager, GM, VP, EVP). Filter pakai `kelompok_jabatan`, **BUKAN** `jenjang` —
   Team Leader juga G2, sama dengan Officer. (F-042)
2. **Grade masuk sesuai jenjang pendidikan**: SMK/D3 → **G1** (Junior Officer/Technician);
   S1/D4 → **G2** (Officer/Technician); S2 → **G3** (Senior Officer). Jangan semua ke Junior. (F-042)
3. **Batas umur & IPK berbeda per jalur**: rekrutmen PLN sendiri S1 ≤27; RBB S1 ≤30; D3 ≤25–27;
   S2 ≤30. IPK min 3,00 (afirmasi/OAP 2,5). (F-022, F-043)
4. **Lokasi tes terkunci** pada yang dipilih saat daftar; tahap awal online, tahap akhir offline. (F-024, F-033)
5. **Akun = lifetime**; satu akun boleh melamar banyak angkatan lintas tahun. (F-025, F-033)
6. **Unit granular pendaftaran = PROFESI**, bukan program (1 program → banyak profesi). (F-010)
7. **Pembidangan berat sebelah**: Pembangkitan di holding cuma 761 pegawai G1+G2 → porsi UPDL
   Suralaya kecil; didominasi Distribusi/Transmisi/Niaga. (langkah 02 mockdb)

### 4b. Tahun jalur RBB (2021 & 2024) — modelkan sebagai jalur terpisah

2021 & 2024 kosong di katalog PLN karena rekrutmen lewat **PPB/RBB (FHCI)**, bukan program PLN
sendiri (F-041). Teknisnya (F-046): **FHCI** mengerjakan administrasi + tes online 1 (TKD/AKHLAK/TWK)
+ tes online 2 (Inggris/Learning Agility); **PLN baru masuk di Tahap 3/TKB** (kompetensi bidang +
psikotes + wawancara + MCU). PLN hanya menetapkan syarat di tahap awal.

→ Modelkan RBB sebagai **jalur (`sumber_rekrutmen`) terpisah** dengan pipeline PLN lebih pendek.
Ini memberi dashboard perbandingan antar-jalur (*recruitment source effectiveness*, ReqGathering#3)
sekaligus memperkuat tema "data apa yang ada vs belum".

**Model yang disepakati user (2026-08-17):**

```
JALUR MANDIRI  [PLN] administrasi → adaptif → akademik+inggris → psikologi
                     → fisik/MCU → wawancara
                     ↑ per-kandidat sejak tahap pertama

JALUR RBB      [FHCI] adm → TKD/AKHLAK/TWK → inggris/Learning Agility
                     ↑ HANYA di-TRACK: tanggal + jumlah agregat (tanpa nama)
               [PLN] tes bidang (TKB) → psikologi → MCU → wawancara
                     ↑ SERAH-TERIMA: nama masuk sistem PLN, lalu mengikuti
                       ALUR & TAHAPAN PLN YANG SAMA (tiap tes = tahap sendiri,
                       tanggal sendiri — bukan sehari borongan)

KEDUANYA       ttd kontrak → SAMAPTA → pembidangan → OJT → ujian OJT → SK penempatan
```

Tiga ketentuan:
1. **Tahap FHCI = tanggal + jumlah agregat**, bukan tanggal saja. PLN pasti tahu berapa orang yang
   diserahkan ke TKB. Tanpa angka ini funnel tahun RBB kosong dan tak bisa dibandingkan antar-jalur.
   Data per-kandidat memang tidak ada — itu faktanya, dan justru jadi temuan yang ditampilkan.
2. **Setelah serah-terima, RBB memakai pipeline PLN yang identik.** Bukan "bundel TKB" yang perlu
   diurai: kandidat RBB langsung masuk tabel tahapan yang sama dengan jalur mandiri dan menjalani
   urutan tes PLN seperti biasa. **Satu-satunya perbedaan = titik masuk** (RBB melewatkan
   administrasi/adaptif/akademik-inggris karena sudah dikerjakan FHCI).
   → Konsekuensi teknis: **satu tabel `seleksi_tahap`, satu kosakata tahapan, satu set aturan.**
     Jalur cukup jadi atribut (`sumber_rekrutmen`), bukan struktur tabel terpisah.
3. **Pengumuman berlaku untuk kedua jalur** — PLN tetap menyebarkan info RBB ke kanal sendiri
   (website, socmed, job fair; lih. F-029).

⚠️ Keyakinan **sedang** (sumber pemberitaan). 3 pertanyaan terbuka untuk tim HTD tercatat di F-046 —
terutama apakah kandidat RBB tercatat di `rekrutmen.pln.co.id` dan apakah skor FHCI diserahkan ke PLN.

## 5. Tiga hal yang HARUS dimodelkan (tidak ada di sumber manapun)

Ini bukan kegagalan riset — justru **gap inilah yang mau ditonjolkan dashboard**
("apa yang sudah ada vs apa yang masih perlu ditambahkan", sesuai ReqGathering):

1. **Kuota/kebutuhan per posisi** → turunkan dari gap FTK + attrition (F-017, F-027, F-043)
2. **Passing grade tiap tahap** → tidak ada di perdir 0056/0050/0048 (F-028)
3. **Skor tes mentah** → sistem hanya menyimpan lulus/gagal (F-017)

## 6. Tugas sesi baru — rencana konsolidasi

**Langkah 1 — perbarui `mockdb/README.md`**
Masih tertulis "holding saja" & "±2.000/tahun". Ganti ke: PLN Group, horison 2020–2026,
angka kalibrasi bagian §3 di atas.

**Langkah 2 — susun `mockdb/rules/`** (suling 45 temuan jadi aturan eksekusi)

| File | Isi | Temuan |
|---|---|---|
| `administrasi.yaml` | umur & IPK per jalur, berkas wajib | F-022, F-043, F-034 |
| `tahapan.yaml` | 7 tahap, mode online/offline, kota terkunci, no-show 44% | F-023, F-024, F-029 |
| `funnel.yaml` | konversi per tahap, rasio 1:200, komposisi jenjang | F-019, F-020, F-039 |
| `kohort.yaml` | ukuran per tahun, 3–4 angkatan/thn, jeda pipeline | F-035, F-026 |
| `attrition.yaml` | 2,7%/thn + **carve-out terpisah** | F-036, F-045, F-015 |
| `jabatan.yaml` | non-struktural saja + grade per pendidikan | F-042 |
| `angkatan.yaml` | seri paralel, kode profesi, nomor tes ber-`ES` | F-008, F-009 |
| `demografi.yaml` | gender 75:25, sebaran pendidikan & usia | F-038 |
| `kelengkapan.yaml` | field fisik terisi bertahap | keputusan user |

**Langkah 3 — revisi ERD** (`mockdb/docs/`)
- Program → **profesi** (2 level)
- Kandidat: alamat **domisili vs asal**, blok **fisik/visus** (BMI, visus, tato, lingkar perut),
  kontak keluarga, pendidikan wajib SD/SMP/SMA — semua dari skema asli (F-034)
- Tahapan: `mode`, `kota`, `sumber_sistem`, `pemilik_proses`, `hadir`
- Tandai eksplisit field yang **tidak ada di sistem asli**

**Langkah 4 — generate bertahap**: unit ✅ → kebutuhan/pagu → program/angkatan → vendor & lokasi →
kandidat & pendaftaran → tahapan seleksi → kontrak/prajabatan/OJT → penempatan → load DuckDB.

## 7. Peta file penting

```
knowledge/
  HANDOFF.md            <- file ini
  findings.md           <- 45 temuan tersitasi. SUMBER KEBENARAN.
  RESEARCH_PLAN.md      <- rencana & status riset, arsitektur folder
  build/                <- skrip riset (r1 scrape, r1c wayback, r1d login, r7 rbb)
  sources/
    rekrutmen_pln/      programs.csv (31) · profesi.csv (128) · wayback/programs_historis.csv (111)
                        akun/skema_form.md  <- SKEMA BIODATA ASLI (penting utk tabel kandidat)
    laporan_pln/        ringkasan_hc.md · ringkasan_hc_2022_2023.md
    rbb_fhci/           lowongan_pln_rbb.csv (20 lowongan RBB 2024)
    perdir/             0056 & 0050 & 0048 (teks, GITIGNORED)
    htd_chat/           notes.md (GITIGNORED)
mockdb/
  README.md             <- PERLU DIPERBARUI (masih "holding saja")
  build/01_extract_master.py · 02_klasifikasi_jabatan.py
  rules/bidang_jabatan.csv
  out/master/           unit_induk(48) · unit_pelaksana(357) · jabatan_katalog(6.148) ·
                        jabatan_klasifikasi · posisi_unit_induk · posisi_unit_pelaksana
data sintetis/          SUMBER ASLI + PII (DAPEG 37rb pegawai). GITIGNORED. Jangan commit.
referensi/              perdir PDF, chat WA, screenshot. GITIGNORED.
```

## 8. Catatan lingkungan

- Python: `recruitment_dashboard/.venv/Scripts/python.exe`
  (sudah ada: httpx, bs4, lxml, pymupdf, playwright+chromium, pandas, duckdb)
- Pola hibrida yang disukai user: **subagent Sonnet untuk kerja mekanis, Opus untuk analisis/keputusan**
- Ritme kerja user: **diskusi → konfirmasi → implementasi → verifikasi → commit saat diminta**
- **Jangan commit PII.** `.gitignore` sudah menjaga; verifikasi sebelum commit.

## 9. Item terbuka (opsional, tidak memblokir)

- **PPB 2021 & RBB non-2024** — status belum diketahui; archive.org membalas **HTTP 503**
  (gangguan layanan, bukan rate limit/ketiadaan arsip). Coba ulang `knowledge/build/r7_rbb_fhci.py`
  + CDX untuk `ppb.fhcibumn.id*`, `rekrutmenbersama2022/2023/2025`. Nilai rendah (RBB di luar cakupan inti).
- **SR-2022** gagal diunduh (server abaikan HTTP Range). Sudah tertutup lewat identitas turunan.
- **Statistik PLN 2025** gagal diunduh (server). Tertutup oleh SR-2025.
- **0171 Direktori Kompetensi** (1110 hal) sengaja ditunda → bahan korpus RAG chatbot.
