# mockdb — database mock rekrutmen PLN Holding

Rebuild database mock rekrutmen dari nol, supaya dashboard lebih menggambarkan kondisi
real di lapangan. Terpisah total dari `data mockup/` (mock lama) dan
`recruitment_dashboard/` (dashboard lama).

## Keputusan desain

| Hal | Keputusan |
|---|---|
| Cakupan | **PLN Holding saja** (tanpa subholding / anak perusahaan) |
| Tanggal "sekarang" | **15 September 2026** (semua status angkatan dihitung relatif ke tanggal ini) |
| Periode | 2023 – September 2026, ±30 angkatan |
| Penomoran angkatan | seri terpisah per jenjang: D3/D4/S1 di **70-an**, SMA/D1 di **20-an**, S2/Pro Hire di **belasan** |
| SMA/D1 | tetap ada, tapi kebutuhannya **mengecil tiap tahun** (pelaksana makin banyak direkrut lewat PLN Group) |
| Vendor | pakai nama **real** (Prodia, Kimia Farma, LPT UI, UPAC PLN, dll) |
| Nomor tes | tanpa segmen `ES` — artinya belum diketahui, dihilangkan dulu |
| Skala penerimaan | ±2.000/tahun, maks ±500 per angkatan (rekor historis 800) → ±8.000 total |
| Level unit | Unit induk → unit pelaksana. **Tidak** sampai unit layanan |
| Penyimpanan | DuckDB (`out/rekrutmen.duckdb`) + export CSV/Parquet |
| Cara generate | Persona-agent merancang **aturan**, generator Python mengeksekusi per-kandidat secara kausal & ber-*seed* |

## Struktur folder

```
mockdb/
  build/     skrip generator (dijalankan berurutan: 01_, 02_, ...)
  rules/     file aturan hasil persona-agent (YAML/JSON) — input generator
  out/
    master/  master data hasil ekstraksi dari sumber real
  docs/      ERD & data dictionary
```

## ⚠️ Catatan PII

`data sintetis/Sample-03-Realisasi Pemenuhan FTK_April 2026.xlsx` sheet `Sheet1`
berisi **DAPEG asli: 37.073 nama pegawai + NIP**. Skrip ekstraksi sengaja hanya
mengeluarkan agregat struktural — tidak ada satu pun kolom identitas orang yang
ditulis ke `out/`. Jangan ubah perilaku ini.

Folder `data sintetis/` sebaiknya masuk `.gitignore`.

## Status

### ✅ 01 — Master data (`build/01_extract_master.py`)

Diturunkan dari data real, bukan tebakan. Jalankan: `python mockdb/build/01_extract_master.py`

| File | Baris | Isi |
|---|---:|---|
| `out/master/unit_induk.csv` | 48 | Unit induk + FTK 2024/2025 + realisasi Des-2025 & Apr-2026 |
| `out/master/unit_pelaksana.csv` | 357 | Unit pelaksana + induknya + jumlah pegawai |
| `out/master/jabatan_katalog.csv` | 6.148 | Nama posisi unik + jenjang utama + sebaran |
| `out/master/posisi_unit_induk.csv` | 11.781 | Jumlah pegawai per (unit induk × posisi × jenjang) |
| `out/master/posisi_unit_pelaksana.csv` | 20.271 | Idem, sampai unit pelaksana |

**Validasi:** total FTK 2025 = 37.854 (persis sama dengan baris `TOTAL HOLDING`
di sheet sumber); total realisasi Des-2025 = 37.067; 48/48 unit induk ter-match;
tidak ada baris FTK yang terpakai dobel.

Komposisi unit induk: KP 1, UID 18, UIP 11, UIW 5, PUSAT 5, UIT 3, UIP3B 3, UIP2B 1, UIK 1.
Unit pelaksana: UP3 167, UPP 58, UPT 41, kantor induk 28, UP2D 18, UP2B 15,
**UPDL 11** (lokasi pembidangan), UPKIT 7, sisanya UP2W/UP3B/UPMK/UPS/UPMLEB/UPAC.

### ✅ 02 — Klasifikasi jabatan (`build/02_klasifikasi_jabatan.py`)

Aturannya ada di `rules/bidang_jabatan.csv` (109 kata kunci, *first-match-wins*,
boleh diedit tangan tanpa nyentuh kode). Output: `out/master/jabatan_klasifikasi.csv`.

Tiap posisi dapat: `kelompok_jabatan`, `fungsi`, `bidang` (TEKNIK/NON-TEKNIK),
`sub_bidang` (15 kelas), `bidang_pembidangan` (9 kelas resmi sesuai
`referensi/pembidangan PLN.txt`), dan `is_entry_level`.

Cakupan: **91,1%** kena aturan kata kunci; 8,9% sisanya jatuh ke fallback
(hampir semuanya jabatan manajerial dengan fungsi niche, bukan sasaran rekrutmen).

Entry level (G1): **383 posisi / 6.166 pegawai**.
Sebaran pegawai G1+G2 per bidang pembidangan:
Distribusi 7.709 · Transmisi & GI 4.021 · Niaga 3.919 · Konstruksi & Pengadaan 2.963 ·
Keuangan 2.811 · SDM 2.428 · Perencanaan Sistem 990 · **Pembangkitan 761** · Proteksi & Kontrol 402.

> **Konsekuensi penting:** di holding, Pembangkitan tinggal 761 pegawai G1+G2 (cuma
> UIK Tanjung Jati B) karena pembangkitan sudah pindah ke subholding. Jadi porsi
> pembidangan Pembangkitan (UPDL Suralaya) harus kecil — didominasi
> Distribusi, Transmisi & GI, dan Niaga.

### ⬜ Berikutnya
03 rumpun jurusan & mapping posisi↔jurusan · 04 attrition & proyeksi kosong ·
05 usulan kebutuhan & penetapan pagu · 06 program rekrutmen (angkatan) ·
07 vendor & lokasi seleksi · 08 kandidat & pendaftaran · 09 tahapan seleksi ·
10 kontrak, prajabatan, OJT · 11 penempatan · 12 load ke DuckDB

## Skema penilaian tiap tahap (disepakati)

| Tahap | Yang dinilai | Keputusan |
|---|---|---|
| Administrasi | umur, status nikah, IPK/NEM, jurusan, kelengkapan KTP/akta/ijazah/transkrip | LULUS / GAGAL per kriteria |
| Akademik & Inggris | benar/salah/kosong → skor akademik + skor inggris → total | ambang total per program |
| Adaptif | abstract + verbal + numerical reasoning → total, kategori I–V | total ≥ ambang **dan** tidak ada subskor di bawah minimum |
| MCU | flag per kelompok: fisik, mata, gigi, jantung/EKG, paru, lab darah-urin, audiometri | FIT / FIT WITH NOTE / UNFIT |
| Wawancara | 4 aspek skor 1–5: motivasi, komunikasi, penguasaan bidang, kesesuaian nilai PLN | DISARANKAN / DISARANKAN DENGAN PERTIMBANGAN / TIDAK DISARANKAN |

## Kuirks sumber data yang sudah ditangani

- `CoCd` **bukan** kunci unit induk — CoCd `5200` dipakai bersama UID Jateng dan
  UID Yogyakarta (unit baru, FTK 144, realisasi 0). Kunci yang benar: `Organisasi 2`.
- `Organisasi 3` **bukan** unit pelaksana untuk pegawai kantor induk — di situ isinya
  `BIDANG ...` / `DIREKTORAT ...`. Kunci unit pelaksana yang benar: `BusA`.
- Sheet FTK: baris `TOTAL HOLDING` (37.073) ≠ `JUMLAH UNIT` + Kantor Pusat (37.067).
  Selisih 6 orang ini ada di file sumbernya sendiri. Yang dipakai: jumlah baris per-unit.
- 1 baris DAPEG punya unit induk `#N/A` → dibuang.
