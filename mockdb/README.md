# mockdb — database mock rekrutmen PLN Group

Rebuild database mock rekrutmen dari nol, supaya dashboard lebih menggambarkan kondisi
real di lapangan. Terpisah total dari `data mockup/` (mock lama) dan
`recruitment_dashboard/` (dashboard lama).

Semua angka di sini **berjangkar ke riset di `knowledge/findings.md` (49 temuan tersitasi)**.
Tiap aturan di `rules/` mencantumkan temuan rujukannya. Yang tidak punya rujukan ditandai
eksplisit sebagai `turunan` atau `asumsi` — itu justru bahan cerita dashboard
("data apa yang sudah ada vs apa yang masih perlu ditambahkan").

## Keputusan desain

| Hal | Keputusan | Rujukan |
|---|---|---|
| Cakupan | **PLN Group** — holding kaya (unit induk→pelaksana→posisi dari DAPEG), subholding ringkas (nama perusahaan + bidang + jumlah) | DECISION-01, F-002, F-012 |
| Horison | **gelombang 2019–2025**, data sampai **15 Sep 2026**. Semua ukuran kohort berjangkar angka nyata | F-048 |
| Tanggal "sekarang" | **15 September 2026** (semua status dihitung relatif ke tanggal ini) | keputusan user |
| Skala | **penuh 1:1** — ±315rb pendaftaran, ±499rb akun, ±621rb baris tahapan | F-019, F-047 |
| Gelombang 2026 | **tidak ada** — katalog asli berhenti Okt-2025; 2026 = fase perencanaan | keputusan user |
| Jalur | dua: **MANDIRI** (portal PLN) & **PPB/RBB** (FHCI); satu kosakata tahapan, jalur jadi atribut | F-041, F-046 |
| Jalur per tahun | mandiri **2019, 2022, 2023, 2025** · PPB/RBB **2020, 2021, 2024** | F-041, F-048 |
| Penomoran angkatan | **seri paralel per peruntukan** pakai nomor asli (74→2020, 81&86→2023, 91&92→2025) | F-008 |
| Nomor tes | **pakai segmen `ES`** — terpecahkan sebagai kode subholding penempatan, bukan kode misterius | F-009 |
| Level unit | Unit induk → unit pelaksana. **Berhenti di sini secara sadar** — dokumen pagu asli turun sampai unit layanan (ULP), tapi master DAPEG kita (`BusA`) hanya sampai unit pelaksana | keputusan user, F-054 |
| Field fisik | **kelengkapan bertahap** — kosong di kohort lama, makin terisi tiap tahun | keputusan user |
| Nama program | pakai **judul asli** hasil scrape + pemulihan Wayback, bukan karangan | F-001, F-030 |
| Penyimpanan | DuckDB (`out/rekrutmen.duckdb`) + export CSV/Parquet | keputusan user |
| Cara generate | Persona-agent merancang **aturan** (`rules/*.yaml`), generator Python mengeksekusi per-kandidat secara kausal & ber-*seed* | keputusan user |

> **Perubahan dari versi README sebelumnya** (dicatat supaya jejaknya jelas): cakupan
> holding-saja → **PLN Group**; periode 2023+ → **gelombang 2019–2025**; "±2.000
> diterima/tahun" → **angka nyata per tahun (325–1.927)**; penomoran angkatan tebakan
> (S1 70-an/SMA 20-an) → **nomor asli multi-seri dengan lubang dibiarkan kosong**;
> nomor tes tanpa `ES` → **dengan `ES`**. Semua karena riset R1–R7.

## Angka kalibrasi (dari data asli — bukan asumsi)

| Metrik | Nilai | Rujukan |
|---|---|---|
| **Rekrutmen Induk/tahun** | 2019 **1.927** · 2020 **1.093** · 2021 **325** · 2022 **689** · 2023 **689** · 2024 **1.277** · 2025 **1.098** | F-048, F-035 |
| Konteks di luar horison | 2017 **4.484** (puncak, era 35.000 MW) | F-048 |
| Headcount Induk | 2017 **46.062** (puncak) · 2020 **44.310** · 2021 42.755 · 2022 42.151 · 2023 38.542 · 2024 38.289 · 2025 37.423 | F-044, F-048 |
| Attrition | **2,7%/thn** (definisi luas), didominasi pensiun; headcount **MENYUSUT** | F-036 |
| ⚠️ Carve-out | Penurunan 2022→2023 (−3.609) = **pemindahan ke subholding, BUKAN attrition** | F-045 |
| ⚠️ Patahan definisi | Turnover SR-2017/2020 = **sempit** (tanpa pensiun, 0,2%) vs SR-2021+ = **luas** (2,7%) | **F-049** |
| Rasio pelamar:diterima | **1:49** (jalur mandiri) · **1:186** (RBB nasional) | F-047 |
| Funnel HTD (kumulatif) | 598.395 pelamar → 382.744 lulus adm (64%) → 12.248 lulus wawancara | F-019 |
| Komposisi jenjang | S1 67% · D3 26% · SMK 6% · S2 1% *(kumulatif; SMK semua dari era ≤2017)* | F-020 |
| No-show | ~44% rata-rata lintas tahapan (tertinggi di tes pertama) | F-020 |
| Gender per tahun | **berayun 65:35 → 86:14** — jangan pakai satu angka tetap | **F-048** |

Ukuran per angkatan **tidak dibatasi ~500**: 2025 hanya punya 2 nomor angkatan untuk ±2.000
diterima Group. Batas kapasitas yang sesungguhnya berlaku di **kelas prajabatan** (30–60 orang
per UPDL), bukan di angkatan.

## Aturan bisnis yang WAJIB dipatuhi generator

1. **Tidak pernah menempatkan pegawai baru ke jabatan struktural.** Filter pakai
   `kelompok_jabatan`, **BUKAN** `jenjang` — Team Leader juga G2, sama dengan Officer. (F-042)
2. **Grade masuk sesuai jenjang pendidikan**: SMK/D3 → G1; S1/D4 → G2; S2 → G3.
   Jangan semua ke Junior. (F-042)
3. **Batas umur & IPK berbeda per jalur**: mandiri S1 ≤27, D3 ≤25, S2 ≤30;
   RBB S1 ≤30, D3 ≤27. IPK min 3,00 (afirmasi/OAP 2,50). (F-022, F-043)
4. **Lokasi tes terkunci** pada yang dipilih saat daftar; tahap awal online, tahap akhir offline. (F-024, F-033)
5. **Akun = lifetime**; satu akun boleh melamar banyak angkatan lintas tahun. (F-025, F-033)
6. **Unit granular pendaftaran = PROFESI**, bukan program (1 program → banyak profesi). (F-010)
7. **Pembidangan berat sebelah**: Pembangkitan di holding cuma 761 pegawai G1+G2 → porsi UPDL
   Suralaya kecil; didominasi Distribusi/Transmisi/Niaga. (langkah 02)
8. **Headcount menyusut**, bukan tumbuh — rekrutmen < attrition. (F-036)

## Dua jalur rekrutmen

```
JALUR MANDIRI  [PLN] administrasi → adaptif → akademik+inggris → psikologi
                     → fisik/MCU → wawancara
                     ↑ per-kandidat sejak tahap pertama

JALUR RBB      [FHCI] adm → TKD/AKHLAK/TWK → inggris/Learning Agility
                     ↑ HANYA di-TRACK: tanggal + jumlah agregat (tanpa nama)
               [PLN] akademik (TKB, tanpa komponen Inggris) → psikologi
                     → fisik/MCU → wawancara
                     ↑ SERAH-TERIMA: nama masuk sistem PLN, lalu mengikuti
                       ALUR & TAHAPAN PLN YANG SAMA

KEDUANYA       ttd kontrak → SAMAPTA → pembidangan → OJT → ujian OJT → SK penempatan
```

**Satu tabel `seleksi_tahap`, satu kosakata tahapan, satu set aturan.** Jalur cukup jadi
atribut (`sumber_rekrutmen`), bukan struktur tabel terpisah. Satu-satunya perbedaan =
**titik masuk**. Tahap FHCI disimpan agregat (tanggal + jumlah) di tabel terpisah — data
per-kandidat memang tidak ada di PLN, dan itu justru temuan yang ditampilkan. (F-046)

## Tiga hal yang HARUS dimodelkan (tidak ada di sumber manapun)

Ini bukan kegagalan riset — justru **gap inilah yang mau ditonjolkan dashboard**:

1. **Kuota/kebutuhan per posisi** → turunkan dari gap FTK + attrition (F-017, F-027, F-043)
2. **Passing grade tiap tahap** → tidak ada di perdir 0056/0050/0048 (F-028)
3. **Skor tes mentah** → sistem asli hanya menyimpan lulus/gagal (F-017)

Semua kolom hasil pemodelan ini diberi tanda `sumber_sistem = 'DIMODELKAN'` supaya
dashboard bisa membedakan mana yang nyata dan mana yang direka.

## Struktur folder

```
mockdb/
  build/     skrip generator (dijalankan berurutan: 01_, 02_, ...)
  rules/     file aturan — input generator, boleh diedit tangan tanpa nyentuh kode
  docs/      ERD & kamus data
  out/
    master/  master data hasil ekstraksi dari sumber real
    csv/     export tabel hasil generate
    rekrutmen.duckdb
```

## ⚠️ Catatan PII

`data sintetis/Sample-03-Realisasi Pemenuhan FTK_April 2026.xlsx` sheet `Sheet1`
berisi **DAPEG asli: 37.073 nama pegawai + NIP**. Skrip ekstraksi sengaja hanya
mengeluarkan agregat struktural — tidak ada satu pun kolom identitas orang yang
ditulis ke `out/`. **Jangan ubah perilaku ini.**

Nama kandidat di database mock **100% sintetis** (dibangkitkan dari daftar nama Indonesia
umum + seed), tidak diambil dari DAPEG maupun dump area member.

## Status

### ✅ 01 — Master data (`build/01_extract_master.py`)

Diturunkan dari data real, bukan tebakan. Jalankan: `python mockdb/build/01_extract_master.py`

| File | Baris | Isi |
|---|---:|---|
| `out/master/unit_induk.csv` | 48 | Unit induk + FTK 2024/2025 + realisasi Des-2025 & **Mar-2026** |
| `out/master/realisasi_bulanan.csv` | 665 | **13 titik realisasi bulanan per unit** (Des-2024 → Mar-2026) |
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

### ✅ Fondasi aturan (`rules/*.yaml`) & ERD (`docs/`)

9 file aturan hasil penyulingan 49 temuan. Lihat `rules/README.md` untuk peta isinya,
`docs/ERD.md` untuk model datanya, dan `docs/kamus_data.md` untuk rincian kolom.

**Verifikasi silang:** `python mockdb/build/00_verifikasi_rules.py`

Aturannya tersebar di 9 file dan saling bergantung — mengubah ukuran kohort tanpa
menyetel laju funnel akan merusak seluruh volume database tanpa memunculkan error.
Skrip ini menjalankan ±160 cek: rantai perkalian funnel harus mendarat persis di jangkar
F-019, total kohort harus cocok antar file, semua sebaran harus berjumlah 1, kosakata
tahapan harus identik antara `tahapan.yaml` dan `funnel.yaml`, nomor angkatan harus
memuat semua jangkar asli, dan kurva kelengkapan tidak boleh menurun.
**Jalankan setiap kali menyentuh `rules/`.**

**Verifikasi keluaran:** `python mockdb/build/00b_verifikasi_keluaran.py`

Skrip di atas membaca `rules/`; yang ini membaca `out/master/*.csv`. Perbedaan itu penting —
**aturan yang benar tidak menjamin generator menaatinya.** Kekosongan inilah yang membiarkan
langkah 05 menaruh 143 orang di jabatan struktural sementara seluruh 161 cek aturan lulus,
karena tak satu pun di antaranya pernah membuka CSV hasil.

22 cek: larangan struktural di pagu & usulan, `kode_grade` harus cocok dengan jenjang
pendidikan menurut `jabatan.yaml`, total pagu harus mendarat persis di kohort tiap tahun,
setiap unit yang dirujuk harus ada di master, `nama_jabatan + sebutan_jabatan` harus bisa
dirangkai balik jadi jabatan utuh, `usulan = kekosongan + gap_ftk`, proyeksi rinci harus
sama dengan ringkasannya, dan **penjaga PII** — tidak boleh ada kolom atau nilai berbau
orang (NIP/NIK/email) di seluruh `out/master/`.

Cek-nya sudah diuji-negatif: lima cacat disuntikkan sengaja (Team Leader diselundupkan,
D3 dinaikkan ke G2, satu orang dihilangkan dari total, level pro hire dimunculkan lagi,
struktural di usulan) — kelimanya tertangkap, kontrol tanpa mutasi tetap lulus.
**Jalankan setiap kali menyentuh `build/`.**

### ✅ 03 — Rumpun jurusan & jembatan jurusan↔jabatan (`build/03_rumpun_jurusan.py`)

Menutup mata rantai antara **sisi pelamar** (punya program studi) dan **sisi kursi**
(posisi punya sub bidang). Tanpa ini generator penempatan cuma bisa mengundi, dan
lulusan Hukum bisa mendarat di Pemeliharaan Distribusi.

Tiga file aturan, semuanya bisa diedit tangan: `rules/rumpun_jurusan.csv` (kata kunci
→ rumpun, *first-match-wins*), `rules/rumpun_subbidang.csv` (rumpun → sub bidang + bobot),
`rules/minat_profesi.csv` (minat profesi → sub bidang).

| File | Baris | Isi |
|---|---:|---|
| `out/master/program_studi.csv` | 546 | tiap prodi → rumpun + bidang + kata kunci pemicu |
| `out/master/rumpun_jurusan.csv` | 18 | ringkasan rumpun + porsi permintaan |
| `out/master/rumpun_subbidang.csv` | 68 | bobot rumpun × sub bidang |
| `out/master/minat_profesi.csv` | 34 | minat profesi asli → sub bidang |

**Cakupan:** 42/42 prodi inti (100%), 545/546 lintas semua sumber (99,8%). Rumpun payung
"Lainnya Teknik/Non-Teknik" **tidak ditulis tangan** — porsinya mengikuti sebaran kursi nyata.

> ⚠️ **Temuan F-050 — bauran jurusan yang diundang tidak cocok dengan bauran kursi.**
> Distribusi punya **27,8%** kursi G1+G2 tapi cuma **13,0%** pasokan (−14,8 poin);
> Transmisi & GI 16,2% vs 9,9% (−6,3). Sebabnya konsisten dengan F-031 + F-042: kursi itu
> didominasi Junior Technician yang dulu diisi lewat rekrutmen SMK per kota, dan rekrutmen
> itu berhenti setelah 2019.
> **Konsekuensi:** langkah 11 JANGAN memaksa pengisian proporsional — kandidat sah untuk
> Distribusi akan habis. Kekurangannya dilaporkan sebagai keluaran, bukan ditutupi.

### ✅ 04 — Attrition, kaskade promosi & proyeksi kekosongan (`build/04_attrition_proyeksi.py`)

Menjawab ReqGathering#1: kebutuhan rekrutmen sebagai **fungsi** dari pensiun + APS +
mutasi, bukan angka sporadis. Rantai sebabnya dimodelkan penuh — kekosongan di jenjang
atas diisi promosi dari bawahnya, dan kaskadenya berujung di jenjang masuk.

| File | Baris | Isi |
|---|---:|---|
| `out/master/proyeksi_kekosongan.csv` | 92.928 | unit × posisi × tahun × sebab |
| `out/master/kekosongan_ringkas.csv` | 384 | unit × tahun — masukan langkah 05 |
| `out/master/profil_usia.csv` | 8 | sebaran usia sintetis per jenjang |

**Validasi:** 37.066/37.066 kursi terpetakan. Identitas headcount
`awal + direkrut − keluar − carve-out` tertutup dengan residu rata-rata **0,52%**,
dan **persis nol untuk 2023**.

> ⭐ **Temuan F-052.** Besaran carve-out 2023 diturunkan dari identitas = **3.138 orang**,
> lalu tervalidasi silang oleh kenaikan Anak Perusahaan **+3.377** (selisih 239 = rekrutmen
> subholding sendiri). Dua jalur perhitungan terpisah mendarat berdekatan.
>
> Dan: **kekosongan tidak pernah terisi penuh** — kohort cuma 24% (2021), 53%, 59% dari
> kebutuhan sampai 2023. Itulah penjelasan aritmetis penyusutan headcount, bukan sekadar
> "kebijakan efisiensi". Titik baliknya **2024** (124%) & 2025 (108%), tapi efeknya belum
> masuk headcount karena jeda SK.
>
> Kaskade tidak mengubah JUMLAH kebutuhan (= jumlah keluar, secara identik), hanya
> **sebaran jenjangnya**: L1 36% · L2 41% · L3 20% · L4 3%. Pecahan inilah yang menentukan
> berapa lowongan D3 vs S1/D4 vs S2 dibuka.

⚠️ Semua angka **usia** DIREKA (DAPEG tidak punya kolom usia, dan ekstraksi sengaja hanya
mengeluarkan agregat). Yang nyata: jumlah pensiun & keluar per tahun, headcount per tahun,
dan sebaran posisi per unit.

### ✅ 05 — Usulan kebutuhan & penetapan pagu (`build/05_usulan_pagu.py`)

Keluarannya **mengikuti skema asli dokumen HR** `Sample-04-Penetapan Pagu Rekrutmen_2026.xlsx`
(F-054): `NO · HOLDING/AP SH · HOLDING/SUBHOLDING · UNIT PELAKSANA · JABATAN ·
JURUSAN PENDIDIKAN · JUMLAH · PENDIDIKAN · KETERANGAN`, ditambah tiga kolom dari
**Sample-02** (F-055): `NAMA JABATAN · SEBUTAN JABATAN · JENJANG JABATAN`.

| File | Baris | Isi |
|---|---:|---|
| `out/master/usulan_kebutuhan.csv` | 34.006 | usulan unit sebelum dipotong |
| `out/master/pagu_rekrutmen.csv` | 4.975 | pagu ditetapkan, skema HR — total **6.221** orang |

**Nama jabatan dipecah tiga, mengikuti Sample-02.** Master menyimpannya tergabung
(`OFFICER KINERJA DAN ADMINISTRASI LAYANAN PELANGGAN`); keluaran memecahnya kembali jadi
`nama_jabatan` = OFFICER, `sebutan_jabatan` = KINERJA DAN ADMINISTRASI LAYANAN PELANGGAN,
`kode_grade` = G2 — persis tiga kolom yang dipakai dokumen formasi HR.

**Baris berformasi nol dipertahankan** (27.317 dari 34.006 baris usulan, 80%). Sebelumnya
baris ber-nilai < 0,01 dibuang sebagai "debu numerik"; itu keliru. Sample-02 mempertahankan
baris ber-FTK 0, dan memang harus: *"posisi ini ada di unit tapi formasinya nol tahun ini"*
adalah cerita yang berbeda dari *"posisi ini tidak ada di unit ini"*. Kalau dibuang, dashboard
tidak bisa membedakan keduanya.

**Faktor penyesuaian DIHITUNG, bukan diasumsikan.** Pagu dijangkar ke ukuran kohort nyata,
jadi faktornya jatuh sendiri: 0,35 (2019) · **0,13 (2020)** · 0,29 · 0,33 · 0,69 · 0,62 ·
**0,83 (2025)**. Jauh lebih rendah & lebih berayun dari asumsi awal 0,62 — dan tren
naiknya adalah cerita pemulihan yang nyata.

**Dua kalibrasi silang yang sekarang saling menguji:**

| Uji | Hasil | Target |
|---|---|---|
| Bauran pendidikan pagu vs `demografi.yaml` | D3 28,7% · S1 68,0% · S2 3,3% | 28,7% · 67,9% · 3,4% |
| Total pagu vs kohort induk | 6.221 | 6.221 |

⚠️ **Jabatan struktural dikeluarkan dari sasaran rekrutmen** — dan ini pernah bocor.
Versi pertama langkah 05 menyaring pakai `level`, bukan `kelompok_jabatan`, sehingga
**143 orang** masuk ke jabatan TEAM LEADER & ASSISTANT MANAGER. Persis jebakan yang
diperingatkan `jabatan.yaml`: TEAM LEADER bergrade **G2** (sama dengan OFFICER) dan
ASSISTANT MANAGER bergrade **G3** (sama dengan SENIOR OFFICER), jadi saringan berbasis
grade memang tidak bisa memisahkan keduanya. Level 4 (SPC/SSP) juga dikeluarkan: satu-satunya
jalur masuk ke sana adalah pro hire, yang di luar cakupan. Kekosongan di jabatan struktural
**tetap dihitung** dan tetap masuk kaskade promosi — yang dilarang cuma menjadikannya
tujuan rekrutmen dari luar.

Peluang promosi di `attrition.yaml` disetel lewat pencarian grid sampai bauran pendidikan
pagu cocok dengan demografi kohort — jadi kedua file itu kini saling mengunci, bukan
sekadar bertetangga.

⚠️ **Jangan jumlahkan selisih usulan-vs-pagu lintas tahun sebagai "defisit pegawai".**
Gap FTK adalah **stok** kursi kosong yang diusulkan ulang tiap tahun, jadi ia terhitung
berkali-kali. Yang boleh dideret lintas tahun hanya komponen kekosongan (aliran).

### ✅ 06 — Gelombang, program & profesi (`build/06_gelombang_program_profesi.py`)

Tiga level menurut `angkatan.yaml`: **gelombang** (satu nomor angkatan) → **program** (entri
penempatan per subholding/kota) → **profesi** (unit granular pendaftaran, F-010).

| File | Baris | Isi |
|---|---:|---|
| `out/master/gelombang.csv` | 19 | 16 seri utama + 3 seri khusus |
| `out/master/program.csv` | 97 | entri penempatan — **judul asli semua** |
| `out/master/profesi.csv` | 289 | + syarat IPK, batas umur, kuota |
| `out/master/profesi_prodi.csv` | 427 | IPK minimal per program studi |

⚠️ **Tidak ada judul program yang dikarang** — aturan paling keras di langkah ini, dan kini
ditegakkan otomatis oleh `00b`: setiap judul harus terlacak balik ke `programs.csv` (31),
`programs_historis.csv` (42 dipakai, arsip Wayback), atau `lowongan_pln_rbb.csv` (20).
Empat gelombang yang tidak punya judul sama sekali memakai penanda eksplisit
*"(tidak terekam di katalog PLN)"*.

**Total diterima mendarat persis di 8.851** (kohort Group), dan bauran pendidikan tiap tahun
mengikuti `demografi.yaml` — mis. 2022: D3 27% / S1 64% / S2 9%, tepat sasaran.

⚠️ **`pertama_terlihat` di arsip Wayback adalah tanggal SNAPSHOT, bukan tanggal program dibuka** —
ia cuma batas *atas*. Jebakan ini menggigit **dua kali**:

1. Menyaring dengannya menyeret 12 program SMK 2017 dan 4 program 2018 ke gelombang 2019 — dan SMK
   justru dinyatakan tidak dimodelkan di horison ini. → yang menentukan **tahun di judul**.
2. Judul *tanpa* tahun tetap lolos. 21 judul berpenamaan lama `REKRUTMEN UMUM` (konvensi 2017–2019,
   F-032) menumpuk di gelombang 70 dan menggelembungkannya jadi "~19 kota". Di dalamnya ada **kota
   berulang dalam tiga gaya penulisan** — Manado, Pekanbaru, Lampung, Kupang masing-masing dua kali
   — ciri beberapa tahun rekrutmen yang mengendap di katalog, bukan satu gelombang. → judul tak
   bertahun **dan** berpenamaan lama sekarang dibuang sebagai tak-bertanggal.

Hasilnya 2019 menyusut dari 42 ke **21 program**, dan bentuknya jadi cocok dengan bukti luar:
gelombang 72 menghasilkan **tepat 7 kota** (Medan, Palembang, Kupang, Banjarmasin, Jakarta,
Yogyakarta, Makassar) — persis siaran pers *"PLN Buka Rekrutmen di 7 Kota"* (F-063), dari dua
sumber yang tidak saling bergantung.

**Kursi induk & subholding dibagi di kolam terpisah.** `sub_diterima` di `kohort.yaml`
*diturunkan dari* jumlah entri penempatan subholding per gelombang (F-003) — jadi kursi itu
harus kembali ke gelombang yang punya entri tersebut. Tanpa pemisahan ini, angkatan 92 (2025)
menerima 542 orang padahal 950 kursi subholding tahun itu berasal dari lima entri
penempatannya sendiri: gelombang menerima lebih sedikit daripada angka yang diturunkan
darinya. Setelah dipisah, 91 → 979 dan 92 → 1.021. Tahun tanpa entri subholding sama sekali
(2019, 2023) kursinya dilebur ke kolam induk.

⚠️ **Sisa yang BELUM selesai:** di dalam kolam induk, porsi masih dibagi menurut jumlah baris
profesi — dan jumlah baris itu ukuran cakupan geografis, bukan jumlah orang. Afirmasi pecah
per kota (Papua 2025 = 6 kota × 5 = 30 baris), reguler nasional cukup menulis "Seluruh
Indonesia" (12 baris). Akibatnya angkatan 91 masih menyerap 979 dari 1.050 kursi induk 2025,
sementara pagu langkah 05 hanya mengalokasikan **38 kursi** ke unit Papua. Belum diperbaiki
karena beririsan dengan ketegangan 2023 (gender 86:14 NYATA menuntut afirmasi besar, pagu
menuntut kecil) yang masih terbuka.

**Dua lubang angkatan diisi: 79 & 80 (2022).** Katalog 2022 hanya memuat tiga program dan dua
di antaranya S2 — nol kursi D3, padahal tahun itu menerima 1.109 orang. Tanpa gelombang ini 88%
kursi menumpuk di satu program Icon Plus. Pegawai masuk tanpa rekrutmen sebelumnya lebih janggal
daripada nomor angkatan yang kosong. Kronologinya sah: 78 buka 7 Okt 2022, 81 buka 22 Mei 2023.
Tujuh lubang lain **tetap kosong** — alasan per nomor ada di `angkatan.yaml` →
`kapan_lubang_DIISI`.

### ⬜ Berikutnya

07 vendor & lokasi seleksi · 08 kandidat & pendaftaran · 09 tahapan seleksi ·
10 kontrak/prajabatan/OJT · 11 penempatan · 12 load ke DuckDB

## Skema penilaian tiap tahap (disepakati)

⚠️ Seluruh **skor mentah & passing grade di bawah ini DIMODELKAN** — sistem asli hanya
menyimpan lulus/gagal (F-017) dan tidak ada regulasi PLN yang memuat passing grade (F-028).

| Tahap | Yang dinilai | Keputusan |
|---|---|---|
| Administrasi | umur, status nikah, IPK/NEM, jurusan, kelengkapan KTP/akta/ijazah/transkrip | LULUS / GAGAL per kriteria |
| Adaptif | abstract + verbal + numerical reasoning → total, kategori I–V | total ≥ ambang **dan** tidak ada subskor di bawah minimum |
| Akademik & Inggris | benar/salah/kosong → skor akademik (TKB) + skor inggris → total | ambang total per program |
| Psikologi | Wartegg, Pauli/Kraepelin → kesimpulan | DISARANKAN / PERTIMBANGAN / TIDAK |
| Fisik & MCU | flag per kelompok: fisik/BMI, mata (visus & buta warna), gigi, jantung/EKG, paru, lab darah-urin, audiometri | FIT / FIT WITH NOTE / UNFIT |
| Wawancara | 4 aspek skor 1–5: motivasi, komunikasi, penguasaan bidang, kesesuaian nilai AKHLAK | DISARANKAN / PERTIMBANGAN / TIDAK |

## Kuirks sumber data yang sudah ditangani

- `CoCd` **bukan** kunci unit induk — CoCd `5200` dipakai bersama UID Jateng dan
  UID Yogyakarta (unit baru, FTK 144, realisasi 0). Kunci yang benar: `Organisasi 2`.
- `Organisasi 3` **bukan** unit pelaksana untuk pegawai kantor induk — di situ isinya
  `BIDANG ...` / `DIREKTORAT ...`. Kunci unit pelaksana yang benar: `BusA`.
- Sheet FTK: baris `TOTAL HOLDING` (37.073) ≠ `JUMLAH UNIT` + Kantor Pusat (37.067).
  Selisih 6 orang ini ada di file sumbernya sendiri. Yang dipakai: jumlah baris per-unit.
- 1 baris DAPEG punya unit induk `#N/A` → dibuang.
- **Kolom `Realisasi April 2026` rusak di sumbernya** — hanya 2 dari 49 baris numerik,
  47 sisanya `#VALUE!`. Realisasi termutakhir yang bisa dipakai adalah **Maret 2026**
  (49/49 lengkap). Rujukan yang salah kolom sudah diperbaiki di seluruh aturan (F-053).
- **Runtun bulanan tidak boleh dijumlah tanpa cek jumlah unit pelapor.** Kantor Pusat
  kosong Jan–Agt 2025 (`#REF!` di sumber), sehingga total anjlok −3.947 lalu melonjak
  +3.607 — terbaca sebagai PHK massal lalu rekrutmen massal, padahal tidak terjadi
  apa-apa. September & Oktober 2025 bahkan tidak punya kolom sama sekali.
- Laporan resmi PLN sendiri punya ≥6 ketidakcocokan angka internal (F-040) → untuk tiap
  metrik dipilih **satu** sumber dan pilihannya dicatat di `rules/`.
