# HANDOFF — dari fase RISET ke fase BANGUN DATABASE

> **Sesi baru: baca file ini dulu, lalu `knowledge/findings.md`.**
> Riset selesai (54 temuan tersitasi). Fondasi + langkah 01 revisi, 03, 04 & 05 selesai. Tugas berikutnya: generator 06.
> Terakhir diperbarui: 2026-08-17.

---

## 1. Di mana kita sekarang

| Fase | Status |
|---|---|
| Riset 7 sumber (R1–R7) | ✅ **SELESAI** — 54 temuan di `knowledge/findings.md` |
| Master data dari DAPEG | ✅ **SELESAI** — `mockdb/out/master/` (6 file, tervalidasi) |
| Klasifikasi jabatan | ✅ **SELESAI** — 6.148 posisi → bidang/sub-bidang/pembidangan |
| Konsolidasi (README, rules, ERD) | ✅ **SELESAI** — lihat §6 |
| Generator 03 (rumpun jurusan) | ✅ **SELESAI** — 4 keluaran, cakupan 99,8%, memunculkan F-050 |
| Generator 04 (attrition & kekosongan) | ✅ **SELESAI** — identitas headcount tertutup, memunculkan F-051 & F-052 |
| Generator 05 (usulan & pagu) | ✅ **SELESAI** — skema HR asli (F-054), pagu 6.221 = kohort |
| **Generator 06–12** | ⬜ **BELUM — ini tugas sesi baru** |

### Yang selesai di sesi 2026-08-17

- **F-047 ditambahkan** — rasio 1:200 (F-039) **ditolak**, dipakai **1:49** dari F-019.
  F-039 mencampur pembilang cakupan Group dengan penyebut cakupan Induk, dan melanggar
  plafon kumulatif F-019. Ini mengunci seluruh skala database.
- **F-048 & F-049 ditambahkan** setelah SR-2017/2018/2020/2021 diunduh user — runtun
  rekrutmen & headcount mundur ke 2016, jeda pipeline TERKONFIRMASI (keyakinan naik ke
  tinggi), gender per tahun, dan **patahan definisi turnover** yang bisa memunculkan
  lonjakan palsu 10×.
- **`mockdb/README.md` diperbarui** — PLN Group, gelombang 2019–2025, angka kalibrasi baru.
- **9 file `mockdb/rules/*.yaml`** — 49 temuan disuling jadi aturan yang bisa dieksekusi.
- **`mockdb/docs/ERD.md` + `kamus_data.md`** — model data & kamus kolom.
- **`mockdb/build/00_verifikasi_rules.py`** — ±140 cek silang antar file aturan, semua lulus.
- **`mockdb/build/00b_verifikasi_keluaran.py`** — 22 cek atas `out/master/*.csv`. Dibuat setelah
  F-056: 161 cek aturan lulus sementara langkah 05 menaruh 143 orang di jabatan struktural,
  karena tak satu pun cek pernah membuka CSV hasil. **Aturan benar ≠ generator menaatinya.**

**Skala yang disepakati user: penuh 1:1.** ±315rb pendaftaran · ±499rb akun kandidat ·
±621rb baris tahapan · 8.851 lulus seleksi (6.427 sudah ber-SK) · DuckDB ±350 MB.

**Distribusi ke tim: REGENERATE, bukan salin file.** `.duckdb` di-gitignore. Generator
03–12 hanya butuh `out/master/` + `rules/` + CSV di `knowledge/sources/` — semuanya
ter-track dan **tidak** butuh `data sintetis/` yang berisi PII. Syaratnya generator harus
deterministik (seed tunggal di `kohort.yaml`); ini wajib diuji: jalankan dua kali, hash
keluarannya harus sama.

## 2. Keputusan yang SUDAH DIKUNCI (jangan dibuka ulang tanpa alasan baru)

| Hal | Keputusan | Rujukan |
|---|---|---|
| **Cakupan** | **PLN Group** — holding kaya (unit induk→pelaksana→posisi dari DAPEG), subholding ringkas (nama perusahaan + bidang + jumlah) | DECISION-01, F-002, F-012 |
| **Horison** | **gelombang 2019–2025**, data sampai **15 Sep 2026**. Semua ukuran kohort berjangkar angka NYATA; 2019–2021 ditandai kualitas rendah | **F-048** |
| **Gelombang 2026** | **tidak ada** — katalog berhenti Okt-2025; 2026 = fase perencanaan | keputusan user |
| **Tanggal "sekarang"** | **15 September 2026** | keputusan user |
| **Penyimpanan** | **DuckDB** (`mockdb/out/rekrutmen.duckdb`) + export CSV/Parquet | keputusan user |
| **Cara generate** | Persona-agent merancang **aturan** → generator Python eksekusi **per-kandidat secara kausal & ber-seed**. BUKAN subagent per kandidat (200rb+ call, tidak realistis) | keputusan user |
| **Field fisik** | **Kelengkapan bertahap** — kosong di kohort lama, makin terisi tiap tahun | keputusan user |
| **Nama program/angkatan** | Pakai **data asli** hasil scrape, bukan karangan | F-001, F-030 |
| **Dashboard** | Folder **BARU** di luar `recruitment_dashboard/`. Prototipe Streamlit dulu, produksi stack lain (TBD) | keputusan user |

## 3. Angka kalibrasi (dari data asli — jangan pakai asumsi lama)

| Metrik | Nilai | Rujukan |
|---|---|---|
| Rekrutmen Induk/tahun | 2019 **1.927** · 2020 **1.093** · 2021 **325** · 2022 **689** · 2023 **689** · 2024 **1.277** · 2025 **1.098** | **F-048** |
| Konteks di luar horison | 2017 **4.484** (puncak, era 35.000 MW) | **F-048** |
| Headcount Induk | 2017 **46.062** (puncak) · 2020 **44.310** · 2021 42.755 · 2022 42.151 · 2023 38.542 · 2024 38.289 · 2025 37.423 | F-044, **F-048** |
| Attrition | **2,7%/thn**, didominasi pensiun; headcount **MENYUSUT** | F-036 |
| ⚠️ Carve-out | Penurunan 2022→2023 (−3.609) = **pemindahan ke subholding, BUKAN attrition** | F-045 |
| Rasio pelamar:diterima | **1:49** mandiri · **1:186** RBB nasional | **F-047** (F-039 ditolak) |
| Funnel HTD (kumulatif) | 598.395 pelamar → 382.744 lulus adm (64%) → 12.248 lulus wawancara → 2.453 lulus diklat | F-019 |
| Komposisi jenjang | S1 67% · D3 26% · SMK 6% · S2 1% *(kumulatif; SMK semua dari era ≤2017, di luar horison)* | F-020 |
| No-show | ~44% | F-020 |
| Gender per tahun | **berayun 65:35 → 86:14** — jangan pakai satu angka tetap | **F-048** |
| ⚠️ Patahan definisi | Turnover SR-2017/2020 **sempit** (tanpa pensiun, 0,2%) vs SR-2021+ **luas** (2,7%) | **F-049** |

Ukuran per angkatan **tidak dibatasi ~500** — 2025 hanya punya 2 nomor angkatan untuk
±2.000 diterima. Batas sesungguhnya ada di kelas prajabatan (30–60/UPDL).

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

### 4b. Tahun jalur PPB/RBB (2020, 2021 & 2024) — modelkan sebagai jalur terpisah

2021 & 2024 kosong di katalog PLN karena rekrutmen lewat **PPB/RBB (FHCI)**, bukan program PLN
sendiri (F-041). **2020 ikut jalur ini juga** — satu-satunya gelombangnya adalah
"REKRUTMEN PPB BUMN KHUSUS PUTRA PUTRI PAPUA" yang buka 30 Des 2020 (F-048). Teknisnya (F-046): **FHCI** mengerjakan administrasi + tes online 1 (TKD/AKHLAK/TWK)
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

## 6. Fondasi — ✅ SELESAI (langkah 1–3)

| Langkah | Hasil |
|---|---|
| 1 — `mockdb/README.md` | ✅ diperbarui ke PLN Group, gelombang 2019–2025, kalibrasi baru |
| 2 — `mockdb/rules/` | ✅ 9 YAML + `rules/README.md` (peta, konvensi, urutan kausal) |
| 3 — `mockdb/docs/` | ✅ `ERD.md` (11 area tabel, diagram mermaid) + `kamus_data.md` |
| — verifikasi aturan | ✅ `build/00_verifikasi_rules.py`, ±160 cek, semua lulus |
| — verifikasi keluaran | ✅ `build/00b_verifikasi_keluaran.py`, 22 cek + penjaga PII, semua lulus |

**Keputusan pemodelan baru yang diambil di langkah 1–3** (semua tercatat lengkap di
file aturannya masing-masing, dengan alasan & cara membatalkannya):

1. **Jeda pipeline 1 tahun — TERKONFIRMASI (keyakinan tinggi).** F-048 mencocokkan bentuk
   gelombang dengan rekrutmen tahun berikutnya, dan tiga titik ekstrem jatuh pas:
   program 2019 (~30 entri, masif) → masuk 2020 = 1.093; program 2020 (HANYA PPB Papua,
   buka 30 Des) → masuk 2021 = **325**, terkecil; program 2023 (OAP + Maluku + Diaspora)
   → masuk 2024 = **1.277**, terbesar.
   Batalkan lewat `kohort.yaml → jeda_pipeline.jeda_bulan: 0`.
2. **Batas "±500 per angkatan" DILEPAS.** Itu angka turunan (kohort ÷ 3–4), dan data asli
   membantahnya: 2025 cuma punya 2 nomor angkatan untuk ±2.000 diterima Group. Batas
   kapasitas yang sesungguhnya berlaku di **kelas prajabatan** (30–60 orang per UPDL).
3. **Titik masuk RBB = `akademik_inggris` varian TKB-saja**, bukan tahap "TKB" tersendiri —
   F-023 sendiri menyebut akademik = "TKB per rumpun jurusan". Jadi kosakata tahapan
   benar-benar tunggal, sesuai kesepakatan.
4. **2020 dikoreksi jadi jalur PPB, bukan mandiri.** Katalog 2020 cuma memuat dua hal:
   Pro Hire VP Pengelolaan Pajak (jabatan STRUKTURAL — dikeluarkan dari cakupan) dan
   PPB BUMN Papua (buka 30 Des). Jadi 2020 bukan tahun rekrutmen mandiri.
5. **Lubang nomor angkatan DIBIARKAN kosong** (76, 77, 79, 80, 83, 84, 85, 89, 90).
   Deret aslinya melompat 74 → 78 → 81 → 86 → 91, dan lompatan itu bukti katalog publik
   tidak lengkap (F-021: 222 rekrutmen di sistem vs 31 tampil publik). Mengisinya dengan
   nomor karangan akan menghapus bukti itu. Kolom `sumber_nomor` memisahkan 8 nomor nyata
   dari yang diperkirakan.
6. **SMK tidak dimodelkan** — katalog 2019–2025 memuat nol program SMK. Daftar program
   di SR-2017/2020/2021 yang menyebut "rekrutmen SMA/SMK oleh unit" muncul VERBATIM SAMA
   di ketiga edisi, jadi boilerplate, bukan bukti pelaksanaan.
7. **TIDAK ADA gelombang 2026** — keputusan user: ikuti data asli. Katalog berhenti di
   gelombang 01–05 Okt 2025, pola PLN buka Q4, jadi per 15 Sep 2026 belum ada yang dibuka.
   2026 diisi **fase perencanaan** (proyeksi kekosongan → usulan → pagu), berjangkar ke
   gap nyata `ftk_2025` (37.854) vs `realisasi_mar_2026` (37.153).
   ⚠️ Kolom April-2026 TIDAK dipakai — cuma terisi 2 dari 49 baris di sumbernya (F-053).
   → **Yang berjalan pada tanggal potong ternyata kohort 2025**, dihitung dari tanggal
   asli: tutup 5 Okt 2025 → wawancara Feb-2026 → ttd kontrak Mar-2026 → SAMAPTA & pembidangan
   Apr-2026 → **OJT 18 Apr–15 Okt 2026 (sedang jalan, ±83%)** → ujian OJT 20 Okt →
   **SK 9 Nov 2026**. Jadi ±1.905 orang sudah berkontrak tapi **belum ber-SK** pada
   tanggal potong. Gelombang berjalan didapat **tanpa mengarang apa pun**.
   ⚠️ Konsekuensi yang wajib dipegang dashboard: **"diterima" ≠ "sudah jadi pegawai"**.
## 6b. Tugas sesi baru — generator (langkah 4)

Generate bertahap: unit ✅ → rumpun jurusan ✅ → attrition & kekosongan ✅ →
usulan & pagu ✅ → **06 program/angkatan & profesi** → 06 program/angkatan & profesi → 07 vendor & lokasi →
08 kandidat & pendaftaran → 09 tahapan seleksi → 10 kontrak/prajabatan/OJT →
11 penempatan → 12 load ke DuckDB.

⚠️ **Bawa F-050 ke langkah 11.** Bauran jurusan yang diundang kurang memasok Distribusi
(−14,8 poin) & Transmisi (−6,3). Penempatan JANGAN dipaksa proporsional — kandidat sah
akan habis di tengah jalan. Isi dengan pelonggaran eksplisit dan laporkan kekurangannya.

Baca `mockdb/rules/README.md` dulu — di situ ada **urutan kausal** yang wajib diikuti
(diterima adalah jangkar, pendaftar adalah hasil — bukan sebaliknya) dan **tiga hal yang
tidak boleh dilupakan** (jangan isi mundur; jangan saring jabatan pakai `jenjang`; jangan
tafsirkan penurunan headcount 2023 sebagai attrition).

### ⚠️ 6c. Kalau mentok di langkah 05/06 dengan "jumlah pendaftar/kebutuhan unit/gender saling
bertentangan" (sudah pernah terjadi — kasus Papua 2023/2025) — baca **F-064** dulu sebelum
membongkar aturan apa pun. Ringkasnya, ini DUA sumbu berbeda yang kebetulan muncul bersamaan:

1. **Volume pendaftar per tahap per gelombang** — funnel tunggal dipaksa ke semua gelombang.
   **Resolusi (data sudah ada, R8):** pecah `funnel.yaml` per arketipe laju eliminasi —
   `nasional_mandiri` (eliminasi berat tiap tahap, lihat F-061 funnel 6-tahap Medan 2015) vs
   `afirmasi_remote` (nyaris tanpa eliminasi setelah administrasi, F-058 Biak/Nabire). Jangkar
   nasional F-019 jadi rata-rata TERTIMBANG, bukan aturan per-gelombang.
2. **Kebutuhan unit (pagu) vs bauran jurusan/gender historis gelombang** — dua sumber kebenaran
   independen (pagu bottom-up dari attrition; bauran gelombang REAL dari `angkatan.yaml`) dipaksa
   cocok persis. **Resolusi (prinsip sudah dikunci sejak langkah 03, F-050):** bauran gelombang
   nyata adalah kebenaran tak-bisa-dinegosiasi; `pagu_rekrutmen.csv`/`usulan_kebutuhan.csv`
   diperlakukan sebagai **indikator gap untuk dilaporkan** ("kebutuhan vs realisasi"), BUKAN
   target keras yang harus dipenuhi persis oleh generator. Gender per tahun harus MUNCUL dari
   bauran program × gender-per-bidang, bukan dipaksa ke kandidat (`demografi.yaml` §1).

Kalau kode langkah 06 mencoba memuaskan pagu DAN bauran gelombang nyata secara bersamaan sebagai
dua constraint keras, itu bug-nya — bukan kurang data. Detail lengkap + tabel & sitasi: F-064
(sintesis), F-050 (akar sumbu 2), F-058/F-061 (akar sumbu 1).

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
  README.md             <- ✅ diperbarui (PLN Group, 2020-2026, kalibrasi baru)
  build/00_verifikasi_rules.py  <- JALANKAN tiap kali menyentuh rules/
       00b_verifikasi_keluaran.py <- JALANKAN tiap kali menyentuh build/
       01_extract_master.py · 02_klasifikasi_jabatan.py
  rules/README.md       <- peta aturan, konvensi status_sumber, URUTAN KAUSAL
       kohort.yaml · funnel.yaml · administrasi.yaml · tahapan.yaml · angkatan.yaml ·
       demografi.yaml · jabatan.yaml · attrition.yaml · kelengkapan.yaml ·
       bidang_jabatan.csv
  docs/ERD.md · kamus_data.md
  out/master/           unit_induk(48) · unit_pelaksana(357) · jabatan_katalog(6.148) ·
                        jabatan_klasifikasi · posisi_unit_induk · posisi_unit_pelaksana
data sintetis/          SUMBER ASLI + PII (DAPEG 37rb pegawai). GITIGNORED. Jangan commit.
referensi/              perdir PDF, chat WA, screenshot. GITIGNORED.
```

## 8. Catatan lingkungan

- Python: `recruitment_dashboard/.venv/Scripts/python.exe`
  (sudah ada: httpx, bs4, lxml, pymupdf, playwright+chromium, pandas, duckdb, **pyyaml**)
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
