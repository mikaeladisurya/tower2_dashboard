# Findings — Riset Rekrutmen PLN

Store fakta tersuling lintas sumber. Format tiap entri: klaim · sumber · keyakinan · tanggal · dampak.
Sumber: **R1** situs rekrutmen, **R2** perdir, **R3** web, **R4** chat HTD, **R5** seleksi.

---

### F-001 · Katalog program rekrutmen bisa diambil utuh & asli
Klaim: `rekrutmen.pln.co.id/vacancy/site/index` memuat **31 program** (2020–2025), server-rendered,
4 halaman. Tiap program: judul, jenjang, lokasi tes, minat profesi, program studi, tgl buka/tutup,
status, + PDF brosur. Semua field terisi 31/31.
Sumber: R1 (scrape 2026-08-16, `sources/rekrutmen_pln/programs.csv`) · Keyakinan: **tinggi** · Dampak: **nama & struktur program/angkatan pakai data asli, bukan karangan.**
> **⚠️ DIPERBARUI setelah R1c/R4:** 31 itu hanya yang **masih tampil publik**. Katalog sebenarnya
> jauh lebih besar: **111 judul** pulih dari arsip (F-030) dan **222 rekrutmen** tercatat di sistem
> HTD (F-021). Jangan pakai angka 31 sebagai jumlah angkatan historis.

### F-002 · Rekrutmen PLN itu PLN GROUP, bukan Holding saja ⚠️
Klaim: SEMUA program berlabel "PLN GROUP" dengan **penempatan ke subholding/AP**:
PT PLN Indonesia Power, PLN Nusantara Power, PLN Nusa Daya, PLN Energi Primer Indonesia (EPI),
PLN Electricity Services (PLN ES), PLN Icon Plus (Indonesia Comnets Plus).
Sumber: R1 (kolom `minat_profesi`, judul) · Keyakinan: **tinggi** · Dampak: **bertentangan dengan keputusan "holding-only" kita.** Perlu diputuskan ulang (lihat DECISION-01).

### F-003 · Satu "program" di situs = gelombang × penempatan/lokasi
Klaim: satu gelombang rekrutmen dipecah jadi banyak entri. Contoh: Rekrutmen S1/D4/D3 2025
= 6–7 entri per subholding penempatan; OAP 2023 = 8 entri per kota (Manokwari, Jayapura, Merauke,
Nabire, Biak, Sorong, Timika, Wamena). Jadi "angkatan" = pengelompokan beberapa entri ini.
Sumber: R1 · Keyakinan: tinggi · Dampak: model tabel `program` perlu 2 level (gelombang → entri penempatan).

### F-004 · Daftar jurusan (program studi) asli yang direkrut
Klaim: **49 prodi unik** lintas program. Terbanyak: Teknik Elektro (23), Teknik Mesin (22),
Teknik Industri (22), Akuntansi (22), Manajemen (20), Teknik Sipil (19), Manajemen Bisnis (17),
Manajemen Pemasaran (14), Hukum (10), K3 (8), Komunikasi (8), Psikologi (8). Ada kategori
payung "PROGRAM STUDI LAINNYA TEKNIK / NON TEKNIK".
Sumber: R1 (`programs.csv` kolom `program_studi`) · Keyakinan: tinggi · Dampak: **langsung jadi master rumpun jurusan mockdb** (menggantikan tebakan).

### F-005 · "Minat Profesi" selaras dengan klasifikasi bidang kita
Klaim: nilai minat profesi = Enjiniring Distribusi/Transmisi & GI/Pembangkitan, Pemeliharaan
(Distribusi/Transmisi & GI/Pembangkitan), Perencanaan Pembangkitan, Niaga, Pemasaran & Pelayanan
Pelanggan, Akuntansi, Manajemen Keuangan, Manajemen Konstruksi, Hukum, Data Analitik, Manajemen Digital.
Sumber: R1 · Keyakinan: tinggi · Dampak: validasi silang untuk `mockdb/rules/bidang_jabatan.csv`;
bisa jadi label bidang yang dipakai kandidat saat mendaftar.

### F-006 · Jalur afirmasi 3T dibuka per-kota
Klaim: program afirmasi = OAP (Orang Asli Papua) 2023 & Putra-Putri Papua 2025 (per kota:
Merauke, Wamena, Timika, Biak, Sorong, Nabire, Jayapura, Manokwari), Putra-Putri Maluku & Nusa
Tenggara 2023, PPB BUMN Khusus Putra-Putri Papua 2020.
Sumber: R1 · Keyakinan: tinggi · Dampak: tabel program afirmasi = per kota, bukan per unit induk.

### F-007 · Jendela pendaftaran pendek & jenis program
Klaim: pendaftaran ~5–14 hari (2025 Nasional: 01–05 Okt; 2023 Diaspora: 03–17 Jul).
Jenis yang muncul: Reguler S1/D4/D3, S2 Fresh Graduate & Pro Hire (ICE 2022), S1/S2 Diaspora
(Fresh Graduate & Experienced), Bidang khusus (Matematika, Hukum), Afirmasi 3T.
Tahun yang muncul di situs: 2020, 2022, 2023, 2025 (2021 & 2024 tidak muncul).
Sumber: R1 · Keyakinan: sedang · Dampak: kalibrasi tanggal & jumlah angkatan per tahun.
> **✅ TERJAWAB (lihat F-041):** kekosongan 2021 & 2024 nyata — arsip Wayback tidak memuat satu pun
> judul program baru di kedua tahun itu (padahal cakupan arsip 2021 bagus: 32 snapshot). Penjelasannya:
> tahun-tahun itu PLN merekrut lewat **jalur PPB/RBB (Rekrutmen Bersama BUMN)** yang pengumumannya
> ada di situs FHCI, bukan situs PLN.

### F-008 · Nomor angkatan ASLI = seri paralel per peruntukan
Klaim: penomoran angkatan = **beberapa seri paralel per peruntukan**, bukan satu seri global.
Cross-tab angkatan × tahun × jenis (dari `profesi.csv`) + info tim (user angkatan 57 = S1 thn 2016;
teman angkatan 15 = SMA thn 2016):
- **Seri utama** (reguler S1/D3/D4, **termasuk afirmasi Papua/Maluku & bidang khusus**):
  57 (2016) → 74 (2020) → 81 & 86 (2023) → 91 & 92 (2025). Laju ~3–4 angkatan/tahun.
  Afirmasi ikut seri ini (Papua 2023=81, Maluku 2023=86, Papua 2025=91), **bukan** seri sendiri.
- **Seri terpisah kecil**: Pro Hire S2 = 9 (2022); Icon Plus/subholding = 8 (2022);
  historis SMA/D1 = ~15 (2016). S2 reguler=78 (2022) — kemungkinan masih di seri utama.
Sumber: R1 + info HTD informal · Keyakinan: sedang-tinggi (aturan pasti perlu konfirmasi R4) ·
Dampak: **mockdb pakai nomor angkatan asli & model multi-seri**, bukan tebakan "S1 70an/SMA 20an/S2 belasan".

### F-009 · Struktur kode profesi
Klaim: profesi 2025 berkode `{SUBHOLDING}.{TIPE}.{JENJANG}[.varian]`:
SUBHOLDING = IP (Indonesia Power), NP (Nusantara Power), ND (Nusa Daya), ES (Electricity Services),
ICON (Icon Plus), PLN (PLN Persero); TIPE = UM (Umum), OAP (Orang Asli Papua), HK (Hukum),
S2EX (S2 Experienced). Contoh: IP.UM.D3, ND.UM.S1, PLN.OAP.S1, S2EX.HK. Program lama (2022–23)
pakai kode numerik `{n}.{m}` (4.8, 3.1, ICON.14).
Sumber: R1 · Keyakinan: tinggi · Dampak: skema `kode_profesi` mockdb + konfirmasi daftar subholding penempatan.
> **✅ Menjawab pertanyaan lama soal nomor tes.** Format Sample-05 `2511/ES/92/D3-ELE/135615`:
> segmen **`ES` = PLN Electricity Services** (subholding penempatan) — bukan kode misterius.
> Jadi nomor tes = `{YYMM}/{kode subholding}/{angkatan}/{jenjang-jurusan}/{nomor urut}`.
> Konsekuensi: segmen itu **tidak perlu dihilangkan** seperti keputusan sebelumnya — justru bermakna
> dan sebaiknya dipakai di mock.

### F-010 · Granularitas: 1 program → banyak profesi
Klaim: 31 program → **128 profesi**. Tiap profesi = (jenjang × rumpun jurusan × penempatan) dengan
tanggal, kota, angkatan, kode, program studi, dan **minimal IPK per jurusan** sendiri (mis. Teknik
min 3, non-teknik/OAP min 2.5). Data di `profesi.csv`.
Sumber: R1 · Keyakinan: tinggi · Dampak: unit granular pendaftaran = profesi, bukan program. Min IPK per jurusan → rules administrasi mockdb.

### F-011 · Angkatan lama dihapus dari web — ✅ TERJAWAB
Hipotesis awal (usul user): katalog situs (31 program) tidak lengkap karena pengumuman angkatan
dihapus setelah selesai; 2021 & 2024 kosong di situs. Rencana verifikasi semula: telusuri socmed PLN.
**Status: TERBUKTI** — diverifikasi bukan lewat socmed melainkan **Wayback Machine** (lihat **F-030**):
153 snapshot arsip 2017–2026 memulihkan 111 judul program, **80 di antaranya tidak ada di web live**.
Diperkuat **F-021** (sistem HTD mencatat 222 rekrutmen vs 31 tampil publik).
Sumber: usul user → dieksekusi via R1c · Keyakinan: tinggi · Dampak: daftar angkatan historis mock
pakai judul asli hasil pemulihan. Penelusuran socmed jadi **tidak perlu** (nilai tambahnya kecil).

### F-012 · Cakupan resmi = PLN Group (PLN + Anak Perusahaan) [R2]
Klaim: Perdir 0056.E-DIR-2023 def 1.5.17 "PLN Group adalah PLN dan Anak Perusahaan"; 1.5.1 Anak
Perusahaan = perusahaan >50% saham dimiliki PLN. Rekrutmen (1.5.21) = mencari orang internal/eksternal
untuk mengisi FJ. Jadi akuisisi pegawai resmi dilakukan untuk **PLN Group**, bukan holding saja.
Sumber: R2 (`sources/perdir/0056-E-DIR-2023/text.md`) · Keyakinan: tinggi · Dampak: mengarahkan DECISION-01 ke PLN Group.

### F-013 · Proses akuisisi resmi (makro) [R2]
Klaim: BAB III 0056 — 4 tahap makro: **3.1 Rekrutmen → 3.2 Seleksi → 3.3 Pengangkatan,
Penandatanganan Perjanjian & Penempatan → 3.4 Onboarding**. Rincian tahapan tes (administrasi,
akademik & Inggris, adaptif, MCU, wawancara) bersifat operasional — tidak dienumerasi eksplisit di
0056; kemungkinan di Juknis 0048-2025 (hasil scan) atau ditetapkan per-program.
Sumber: R2 · Keyakinan: tinggi (makro), sedang (rincian tes dari R1/web) · Dampak: struktur tabel tahapan.

### F-014 · Triage 9 dokumen peraturan (relevansi & kekinian) [R2]
| Dok | Hal | Bisa baca | Status | Untuk |
|---|---|---|---|---|
| **0056.E-DIR-2023** Akuisisi Pegawai | 31 | teks ✓ | **berlaku, inti** | SOP rekrutmen (sudah diekstrak) |
| 0050.E-DIR-2023 Manajemen Talenta & Pegawai | 93 | teks ✓ | berlaku | rotasi/mutasi/karier → attrition |
| 0171.K-DIR-2024 Direktori Kompetensi | 1110 | teks ✓ | berlaku | kompetensi per jabatan (ekstrak tertarget) |
| 0060.P-DIR-2023 OTK Dit Legal & HC | 85 | teks ✓ | **kemungkinan SUPERSEDED** oleh 0035-2024 | org (skip) |
| 0027.P-DIR-2025 (ubah 0035-2024 OTK) | 106 | teks ✓ | berlaku (amандемен org) | org struktur, sekunder |
| 0052.P-DIR-2018 Kewenangan Bidang | 8 | teks ✓ | mungkin usang | rendah |
| 090.K-DIR-2006 | 8 | **scan** | usang (2006) | skip |
| 264.K-DIR-2008 | 8 | **scan** | usang (2008) | skip |
| 0048.PTs-DIR-2025 Juknis | 34 | **scan** | terbaru (Des-2025) | judul belum jelas — perlu OCR/konfirmasi |
Sumber: R2 · Dampak: fokus ekstraksi ke 0056 (✓), lalu 0050 & 0171 (tertarget); sisanya skip/defer.

### F-015 · Mekanisme pergerakan pegawai = pemicu kekosongan (dasar attrition) [R2b]
Klaim: Perdir 0050.E-DIR-2023 (Manajemen Talenta & Pegawai, 93 hal, diekstrak) memuat mekanisme
yang menciptakan/mengisi kekosongan FJ: **Mutasi** (68×), **Tugas Karya** (114×), **APS/Atas
Permintaan Sendiri** (29×), **Pensiun** (26×), Rotasi (7×), Promosi (3×), Demosi (2×). Cocok dengan
permintaan Bu Dewi (ReqGathering#1): kebutuhan rekrutmen = fungsi dari pensiun + APS + mutasi +
tugas karya, bukan angka sporadis.
Sumber: R2b (`sources/perdir/0050-E-DIR-2023/text.md`) · Keyakinan: tinggi · Dampak: model attrition
mockdb pakai mekanisme bernama ini (bukan random), lalu FTK−realisasi jadi kalibrasi.

### F-016 · Direktori Kompetensi = bahan RAG, bukan data inti [R2b]
Klaim: 0171.K-DIR-2024 (1110 hal, teks) = kamus kompetensi (Edisi IX 2024), ~510 unit kompetensi
teknis + soft competency, berupa deskripsi kompetensi. Bukan tabel jabatan→kompetensi siap-pakai.
Sumber: R2b (probe struktur) · Keyakinan: tinggi · Dampak: **tidak diekstrak penuh sekarang**;
disimpan untuk korpus RAG chatbot (jawab "kompetensi jabatan X apa") & fitur kecocokan kandidat nanti.

### F-017 · Peta ketersediaan data (apa yg ADA vs TIDAK) [R4] ⭐
Klaim: dari docx beranotasi Willy — TIDAK tersedia di web rekrutmen: (a) **seluruh Data Kebutuhan
Rekrutmen** (jabatan/unit peminta/jumlah/lokasi/kompetensi — ini domain HST), (b) **Score tes**
(hanya pass/fail yang ada). Tersedia: angkatan, master kandidat, tahapan seleksi, hasil pass/fail.
Prajabatan/OJT ada di aplikasi Pusdiklat terpisah.
Sumber: R4 (`sources/htd_chat/notes.md`) · Keyakinan: tinggi · Dampak: **gap ini justru insight utama
dashboard** (kebutuhan HST vs pelaksanaan HTD; skor tak tersedia). Mock harus merefleksikan gap ini.

### F-018 · Kepemilikan proses & 2 sistem [R4]
Klaim: HTD mengawal **administrasi → wawancara**; lalu **Pusdiklat** (prajabatan + uji akhir); hasil
balik ke **HTD** untuk review → **SK Pengangkatan**. Sistem: rekrutmen.pln.co.id = pendaftaran +
perjalanan peserta + hasil pass/fail; seleksi.pln.co.id = **hanya tes akademik & Inggris**;
Pusdiklat = aplikasi prajabatan terpisah. Hasil tes download manual → upload, bisa per angkatan.
Sumber: R4 · Keyakinan: tinggi · Dampak: alur & pemilik tiap tahap di model data.

### F-019 · Angka skala ASLI + funnel end-to-end [R4]
Klaim (screenshot admin 01-Jul-2026, kumulatif semua angkatan): 1.282.833 akun member; 601.373
berkas lengkap; **598.395 pelamar** → 382.744 lulus adm (64%) / 214.014 gagal → **12.248 lulus
wawancara** → **2.453 lulus diklat**. Total **222 rekrutmen**, **43 kota penyelenggara**.
Sumber: R4 · Keyakinan: tinggi · Dampak: rasio konversi & rasio pelamar:diterima nyata untuk kalibrasi
mock (di skala berapa pun yang dipilih).

### F-020 · Komposisi jenjang & kehadiran ASLI [R4]
Klaim: donut kehadiran per jenjang: **S1 67% · D3 26% · SMK 6% · S2 1%**. Kehadiran total
566.774/1.015.830 ≈ **56%** (no-show ~44% lintas tahapan).
Sumber: R4 · Keyakinan: tinggi · Dampak: distribusi jenjang pelamar + rate no-show mock. Konfirmasi
SMA/D1 kecil & S1 dominan (F-007).

### F-021 · Web publik ≠ histori penuh [R4] (menguatkan F-011)
Klaim: sistem HTD mencatat **222 rekrutmen** tapi web publik hanya menampilkan **31**. ~191 gelombang
sudah diarsip/dihapus dari tampilan publik.
Sumber: R4 · Keyakinan: tinggi · Dampak: kalau mau histori lengkap → butuh data internal / socmed (F-011);
untuk mock, 222 & 43 kota jadi acuan skala jumlah angkatan & lokasi.

### F-022 · Penamaan jabatan & syarat administrasi [R3/R5]
Klaim: (a) "Analyst/Analis Logistik" **bukan** jabatan PLN — PLN menerima *lulusan* logistik/SCM,
tapi *posisi* bergaya Officer/Technician (cocok DAPEG: "Officer Logistik"; judul "Analyst/Engineer"
di mock lama keliru untuk holding). (b) Syarat umum: **D3 ≤ 25 th, S1/D4 ≤ 27 th, IPK ≥ 3.0**
(afirmasi/OAP IPK ≥ 2.5 per `profesi.csv`).
Sumber: R3 (WebSearch analyst logistik pln; money.kompas 2025) + R5 · Keyakinan: sedang-tinggi ·
Dampak: aturan tahap Administrasi mockdb (umur & IPK per jenjang) + validasi penamaan jabatan.

### F-023 · Rincian 7 tahapan seleksi [R3-Gemini] (isi celah 0056)
Klaim: 1) Administrasi (KTP/ijazah/transkrip, IPK≥3.0, umur ≤25 D3 / ≤27 S1D4) → 2) Tes Inteligensia
& **Tes Adaptif PLN (TAP)** — GAT (logika/verbal/numerik) + Karakter/Budaya AKHLAK → 3) Akademik (TKB
per rumpun jurusan) & Bahasa Inggris (TOEFL/TOEIC) → 4) **Psikologi** (Wartegg, Pauli/Kraepelin) →
5) **Fisik & Kesehatan Awal** (BMI, THT, gigi, tensi, **buta warna** wajib utk teknis) → 6) **MCU**
(darah, urine/narkoba, rontgen paru, EKG, USG) → 7) Wawancara (User & HR) → Diklat Prajabatan.
Sumber: R3 (Gemini, ada disclaimer LLM) · Keyakinan: **sedang** (urutan beda dgn data pipeline lama
yg menaruh akademik sebelum adaptif; ReqGathering#4 bilang urutan bisa berubah) · Dampak: kandidat
tahapan seleksi mock; urutan final perlu dikunci dari Juknis 0048 / data asli.

### F-024 · Teknis online→offline (drop point) [R3-Gemini]
Klaim: tahap awal (TAP, akademik, Inggris) **online** dari rumah dgn proctoring kamera; tahap akhir
(fisik, MCU, wawancara) **offline** di Kota Rekrutmen (Jakarta, Medan, Surabaya, Makassar, Palembang,
Balikpapan, dll). Pelamar pilih 1 kota saat daftar, tak bisa diubah.
Sumber: R3 · Keyakinan: sedang-tinggi (cocok dgn F-019 "43 kota" & lokasi tes di R1) · Dampak: atribut
`mode` (online/offline) & `kota` per tahap di model tahapan seleksi.

### F-025 · "Satu Akun Selamanya" (lifetime membership) [R3-Gemini]
Klaim: akun rekrutmen.pln.co.id = lifetime; gagal tahun ini tak perlu isi ulang, cukup update dokumen
& lamar formasi baru tahun berikutnya.
Sumber: R3 · Keyakinan: tinggi (menjelaskan F-019: 1,28jt akun kumulatif ≫ pelamar) · Dampak: model
mock — kandidat = akun persisten lintas angkatan; 1 akun bisa daftar banyak angkatan (sesuai aturan
"daftar lagi di angkatan berikutnya" yg kamu sebut).

### F-026 · Frekuensi & jenis rekrutmen [R3-Gemini]
Klaim: 1–2×/tahun. Mandiri (Nasional PLN Group) ~1×/th di Q3/Q4 (Sep–Okt); RBB (Rekrutmen Bersama
BUMN via FHCI) ~1×/th; plus kondisional (SMK/pelaksana, putra-putri daerah, S2 khusus spt hukum).
Sumber: R3 · Keyakinan: sedang-tinggi · Dampak: kalibrasi jumlah & jadwal angkatan/tahun di mock.

### F-027 · Brosur: mapping jurusan→profesi ada, kuota TIDAK [R1b]
Klaim: 30 PDF → 8 unik. Brosur 2022–2023 (teks) memuat **jurusan → nama profesi** (mis. S1 T.Elektro
Arus Kuat → Pemeliharaan Transmisi & GI / Distribusi; S1 Akuntansi → Akuntansi; S2 Data Science →
Data Analitik) + persyaratan (usia: S2 max 30; Pro Hire pengalaman ≥5 th; IPK). Brosur 2025 = flyer
**gambar** (perlu OCR). **Tidak satupun memuat angka kuota/formasi per posisi.**
Sumber: R1b · Keyakinan: tinggi · Dampak: mapping jurusan→profesi sudah tercakup `profesi.csv`
(tambahan: usia S2≤30, Pro Hire≥5th). **Kuota per posisi wajib DIMODELKAN** (gap FTK + attrition) —
menguatkan F-017. OCR flyer 2025 di-skip (ROI rendah; data 2025 sudah ada di profesi.csv).

### F-028 · Juknis 0048-2025 BUKAN SOP rekrutmen [R2c]
Klaim: judul resminya **"Implementasi Kebijakan Strategis Human Experience Management System
Berbasis Moment That Matter"** — dokumen employee-experience sepanjang siklus hidup pegawai;
rekrutmen hanya satu sub-bagian (Tabel 3, hal 21–22). **Tidak memuat passing grade, vendor,
maupun durasi tahapan.** Kata "Prajabatan" tidak muncul; yang dipakai "OJT – First OJT".
Sumber: R2c (`sources/perdir/0048-PTs-DIR-2025/text.md`, transkrip 18 hal via OCR-vision) ·
Keyakinan: tinggi · Dampak: **passing grade TIDAK ADA di regulasi manapun yang kita punya** →
wajib dimodelkan (konsisten F-017/F-027).

### F-029 · Journey rekrutmen-seleksi resmi + kanal pengumuman [R2c]
Klaim (Tabel 3 Juknis 0048): **Rekrutmen**: Awareness → Interest & Consideration → Action (apply).
**Seleksi**: Seleksi Awal *Online Test* (contoh: **Tes Akademik, Bahasa Inggris**) → Seleksi Awal
*Offline Test* (contoh: **wawancara, tes kesehatan**) → Seleksi Akhir **OJT (First OJT)** →
Pemberitahuan Hasil Seleksi. Lalu Tabel 4 Pengangkatan Pegawai → Tabel 5 Onboarding.
**Kanal informasi rekrutmen**: Website, Job Fair, Iklan, Career Website eksternal, **Media Sosial**.
**Kanal notifikasi hasil**: email, SMS, website. Fitur disebut: *tracking status lamaran*, *real-time confirmation*.
Sumber: R2c · Keyakinan: tinggi · Dampak: **mengonfirmasi F-024 (online→offline) dari sumber regulasi**;
kanal di atas = isi tabel `pengumuman rekrutmen`; notifikasi = atribut tahapan.

### F-030 · Katalog historis PULIH dari Wayback: 111 program (80 baru) ⭐ [R1c]
Klaim: 153 snapshot arsip `rekrutmen.pln.co.id/vacancy/site/index` (2017–2026) memulihkan
**111 judul program unik**, di mana **80 tidak ada di web live**. Menegaskan F-011/F-021
(222 rekrutmen di sistem vs 31 tampil publik).
Jenis: Reguler S1/D3 **49** · **SMK 25** · Afirmasi Papua 17 · Pro Hire 6 · Diaspora 3 ·
Afirmasi Maluku/Nusra 3 · Campus/Career Fair 2 · Career Event 2 · Bidang Hukum 2 · S2 1 · Matematika 1.
Sumber: R1c (`sources/rekrutmen_pln/wayback/programs_historis.csv`) · Keyakinan: tinggi ·
Dampak: **daftar angkatan historis mock pakai judul asli**, bukan karangan.

### F-031 · Rekrutmen SMK/Pelaksana dulu masif & per-kota [R1c]
Klaim: 2017 ada **25 program tingkat SMK/Pelaksana**, dibuka **per kota**: Banda Aceh, Jayapura,
Mamuju, Banjarmasin, Ternate, Ambon, Medan, Palu, Gorontalo, Timika, Bandung, Kupang, Ende,
Tanjung Pinang, Pekanbaru, Pontianak, Yogyakarta, Padang, Jakarta, Balikpapan, Makassar, dst.
Setelah 2019 praktis hilang dari katalog.
Sumber: R1c · Keyakinan: tinggi · Dampak: **membuktikan pernyataan user** bahwa SMA/D1 dulu ada
dan kini mengecil (F-020: SMK tinggal 6%). Tren menurun ini harus tercermin di mock 2023–2026.

### F-032 · Jalur campus hiring & evolusi penamaan [R1c]
Klaim: ada jalur **campus/career fair**: "REKRUTMEN UMUM TINGKAT S1/D3 MELALUI AIRLANGGA CAREER FAIR"
(2017), "REKRUTMEN UMUM MELALUI TITIAN KARIR ITB OKTOBER 2017", "Indonesia Career Evening/Excellence"
(S2), plus dari halaman artikel: **D3 Kelas Kerjasama** (15 universitas) & **D4 Ikatan Dinas**
(5 universitas). Reguler 2019 juga dibuka **per kota** (Pontianak, Pekanbaru, Manado, Lampung,
Ambon, Aceh, Kupang, Medan, Bandung, Surabaya, Yogyakarta, Balikpapan, Palembang, Banjarmasin).
Penamaan berevolusi: "REKRUTMEN UMUM" (2017–2019) → "REKRUTMEN PLN GROUP" (2020+).
Sumber: R1c + halaman artikel · Keyakinan: tinggi · Dampak: jenis program mock bertambah
(campus hiring, ikatan dinas, kelas kerjasama) — cocok dgn ReqGathering#3 "campus hiring/BUMN".

### F-033 · FAQ situs: mekanisme akun & lamaran [R3]
Klaim: **lifetime member** (konfirmasi F-025); menu **Rekap Lamaran**; lamaran **bisa di-CANCEL**
selama periode masih buka, lalu perbaiki CV & lamar ulang; aktivasi email ± **3 jam** (menjelaskan
"45.080 akun belum aktivasi email" di F-019); dokumen fisik tidak diminta di awal, tapi wajib pada
tahap tes tertentu; **lokasi tes terkunci** pada yang dipilih saat daftar (konfirmasi F-024);
pengumuman via www.pln.co.id + aplikasi. Tidak dipungut biaya (banyak peringatan penipuan).
Sumber: R3 (halaman FAQ resmi) · Keyakinan: tinggi · Dampak: aturan siklus pendaftaran mock
(cancel/re-apply, akun belum aktivasi, lokasi terkunci).

### F-034 · SKEMA biodata/CV asli dari area member ⭐ [R1-login]
Klaim: struktur field halaman **Pratayang CV** (sumber utk tabel kandidat). Hanya nama field —
tanpa nilai. Sumber: R1-login (`sources/rekrutmen_pln/akun/skema_form.md`, GITIGNORED) · Keyakinan: tinggi.

**Identitas & domisili:** Nama Lengkap · Email · No KTP · Tempat Lahir · Tanggal Lahir · Jenis Kelamin ·
Agama · Status · No. Handphone · Alamat/Kota/Propinsi/Kode Pos **Domisili** · Alamat/Kota/Propinsi **Asal**
(dua alamat terpisah — domisili vs asal).

**Ukuran & fisik (BARU, tak ada di mock lama):** Ukuran Baju/Celana/Sepatu · `body_height` ·
`body_weight` · **BMI** · **Ketajaman Visus Mata Kiri & Kanan** (+ Tingkat Ketajaman + Silinder) ·
`abdominal_circumference` · **`tatto`**.
→ Menjelaskan kaitan ke tahap MCU/tes fisik (F-023: BMI, buta warna, THT) — kandidat sudah mengisi
data fisik sejak biodata.

**Kontak keluarga (tabel terpisah):** Hubungan Keluarga · Alamat · No Telp · Pekerjaan.

**Pendidikan (multi-baris):** Degree · Sekolah/Universitas · Program Studi · SKHU/IPK ·
Pendidikan Terakhir · Tahun Masuk · Tahun Lulus. Validasi sistem mewajibkan jenjang
**SD, SMP, SMA/SMK** diisi juga (bukan cuma pendidikan tinggi).

**Sertifikasi (multi-baris):** Kategori/Sertifikasi · Tahun · **Skor**.

**Berkas wajib unggah:** Akta Kelahiran · Surat Keterangan Belum Menikah · **Swafoto** ·
**Foto Full Body** (+ pasfoto profil).

**Rekap Lamaran (= tabel pendaftaran):** No · Nama Rekrutmen · **Posisi** · Tgl Lamar · Tgl Tutup · Opsi
(Opsi = tombol CANCEL selama periode buka, lih. F-033).

**Akun:** ID Member (numerik) · Alamat Email · No. Handphone.

Dampak: **mengganti tebakan skema `kandidat_biodata`/`pendidikan`/`sertifikat`/`pendaftaran`** di mock
lama. Field fisik & visus adalah temuan baru yang menyambungkan biodata → tahap MCU.

⚠️ **Catatan privasi:** dump mentah (html/png) memuat PII nyata pihak ketiga (NIK, HP, email, foto).
Folder `akun/` di-gitignore. Untuk kebutuhan proyek cukup `skema_form.md`; dump mentah sebaiknya dihapus.

### F-035 · Ukuran kohort rekrutmen ASLI per tahun ⭐⭐ [R6] — MENGOREKSI KALIBRASI
Klaim (Sustainability Report, PLN Induk): **peserta diklat prajabatan** = proksi ukuran kohort
rekrutmen → **2021: 337** (218P/119W) · **2022: 689** · **2023: 689** · **2024: 1.277** · **2025: 1.098**.
Sedangkan **"pegawai baru direkrut"** → **2023: 689** · **2024: 663** (494P/169W) · **2025: 76** (57P/19W).

⚠️ **Tafsir selisih belum pasti.** Untuk **2023 kedua angka SAMA (689)**, tapi 2024 & 2025 berbeda jauh.
Jadi hipotesis "prajabatan = lolos seleksi, direkrut = diangkat/SK tahun berjalan (jeda pipeline)"
**hanya cocok sebagian**. Kemungkinan lain: basis pelaporan berubah antar edisi, atau SR-2023 memakai
angka yang sama untuk dua metrik. Laporan tidak menjelaskan. **Jangan dipakai sebagai aturan keras**
tanpa konfirmasi tim HTD.
Sumber: R6 (SR-2024 hal. 239; SR-2025 hal. 203) + R6b (SR-2023 hal. 170) · Keyakinan: tinggi (angka), **rendah-sedang (tafsir selisih)** ·
Dampak: **asumsi lama "~2.000 diterima/tahun" ±2x terlalu tinggi.** Angka realistis PLN Induk
**±700–1.300/tahun**. Dengan 3–4 angkatan/tahun → **±200–400 per angkatan** (batas atas ~500 dari user tetap masuk akal).

### F-036 · Attrition ASLI: 2,7%/tahun & headcount MENURUN [R6]
Klaim (PLN Induk): turnover **2024: 1.031 orang (2,69%)** · **2025: 1.016 orang (2,71%)**.
Rincian 2024: pensiun normal 731P/146W, pensiun dini 5P/2W (sisanya meninggal, mengundurkan diri, PHK).
Headcount PLN Induk: 2022 **42.151** → 2023 **38.542** → 2024 **38.289** → 2025 **37.423**.
Sumber: R6 · Keyakinan: tinggi · Dampak: **model attrition pakai 2,7%/tahun, didominasi pensiun** —
memvalidasi perkiraan awal 2–3%. Penting: **rekrutmen < attrition → headcount menyusut**; mock harus
mencerminkan ini, bukan pertumbuhan. (Terjun 2022→2023 sebesar −3.609 adalah *carve-out* ke anak
perusahaan, bukan attrition: anak perusahaan naik 9.326 → 12.703.)

### F-037 · Validasi silang DAPEG vs laporan publik [R6]
Klaim: DAPEG internal (April 2026) = **37.072** pegawai; SR-2025 (PLN Induk, Des 2025) = **37.423**;
sheet FTK realisasi Des-2025 = **37.067**; FTK 2025 = 37.854. Semua konsisten di kisaran ~37rb dengan
selisih wajar akibat beda tanggal potong & definisi.
Sumber: R6 + Sample-03 · Keyakinan: tinggi · Dampak: **data internal kita tervalidasi sumber publik** —
master unit & headcount mockdb berpijak pada angka yang benar.

### F-038 · Demografi pegawai PLN Induk (untuk profil kandidat) [R6]
Klaim (SR-2024 hal. 42, PLN Induk 2024): **gender 78,89% pria / 21,11% wanita** (30.205/8.084).
**Pendidikan**: S3 20 · S2 1.806 · S1 17.232 · D3 8.645 · ≤D2 10.586.
**Usia** (ringkasan hal. 244): <30 th 27,31% · 30–50 th 63,65% · >50 th 9,05%. Usia minimum kerja 20 th.
Rekrutmen baru 2024 juga timpang gender: 74,5% pria. Prajabatan 2024 bahkan 86,45% pria.
Sumber: R6 · Keyakinan: tinggi (tabel rinci) · Dampak: distribusi gender & pendidikan kandidat mock —
**jangan 50:50**, tapi ~75:25 pria:wanita di kohort rekrutmen.

### F-039 · Rasio seleksi jauh lebih ketat dari perkiraan [R6]
Klaim: rekrutmen umum PLN Group 2025 = **245.217 pelamar**; kohort prajabatan PLN Induk 2025 = 1.098.
Rasio kasar ≈ **1:200** (perkiraan awal kita 1:60–80 terlalu longgar). Catatan: pembilang cakupan Group,
penyebut cakupan Induk — jadi rasio Group sesungguhnya agak lebih longgar, tapi tetap ≫ 1:80.
Sumber: R6 · Keyakinan: sedang (beda cakupan pembilang/penyebut) · Dampak: rasio funnel mock;
bandingkan juga dgn funnel HTD (F-019): 598.395 pelamar → 12.248 lulus wawancara → 2.453 lulus diklat.

### F-040 · Inkonsistensi di dokumen sumber PLN (dicatat, tidak diperbaiki) [R6]
Ada ≥6 ketidakcocokan angka **di dalam laporan resmi PLN sendiri**, mis.: ringkasan usia <30 th 2024
(10.455) ≠ penjumlahan tabel rinci (13.198); wanita 2024 tertulis 8.804 di satu tabel vs 8.084 di tabel
lain; total anak perusahaan 13.146 vs 13.061; peserta purnabakti 1.107 (narasi) vs 1.280 (tabel).
Sumber: R6 · Dampak: **jangan perlakukan angka laporan sebagai mutlak konsisten**; untuk mock pilih satu
sumber per metrik & catat pilihannya. Juga pengingat: dashboard nanti sebaiknya menampilkan sumber angka.

### F-041 · Jalur PPB/RBB menjelaskan tahun kosong 2021 & 2024 [R1c+R3]
Klaim: **2021 = PPB (Program Perekrutan Bersama)**, **2022–2024 = RBB (Rekrutmen Bersama BUMN)**
diselenggarakan **FHCI**, dan PLN ikut serta bersama Pertamina/Mandiri/BRI/KAI dll. Pengumuman RBB
ada di `rekrutmenbersama.fhcibumn.id`, **bukan** di situs rekrutmen PLN → karena itu 2021 & 2024
kosong di katalog PLN. Jejaknya tetap terlihat: arsip memuat *"REKRUTMEN PPB BUMN KHUSUS PUTRA
PUTRI PAPUA"*. RBB (semua BUMN) merekrut 5.900 pegawai reguler + 231 disabilitas **KUMULATIF
2022-2024** — BUKAN RBB 2024 sendirian (koreksi F-069, ditemukan angka ini tercampur skop saat
verifikasi ulang 2026-08-18; RBB 2024 sendiri: 688 lowongan/1.830 posisi, sumber Kompas 22 Mar 2024).
Sumber: R1c (bukti negatif dari 153 snapshot) + R3 (FHCI/berita) · Keyakinan: tinggi (adanya jalur RBB),
sedang (bahwa itu satu-satunya sebab kekosongan) · Dampak: menjelaskan kenapa kohort prajabatan tetap
terisi di tahun tanpa program PLN (mis. prajabatan 2025 = 1.098). **Catatan scope:** user sejak awal
memutuskan mock fokus ke program rekrutmen PLN sendiri, jadi RBB **di luar cakupan** — tapi wajib
diketahui agar timeline & angka kohort tidak salah tafsir.

### F-042 · Rekrutmen TIDAK langsung ke jabatan struktural ⭐ [aturan bisnis, tervalidasi DAPEG]
Klaim (dari user, diverifikasi ke DAPEG): pegawai baru **tidak mungkin** langsung menempati jabatan
struktural — Team Leader, Assistant Manager, Manager, Senior Manager, GM, VP, EVP. Jalurnya harus
lewat jenjang pelaksana dulu.
Verifikasi di `jabatan_klasifikasi.csv`:
- **Struktural (dikecualikan dari target rekrutmen):** 3.979 posisi / 14.907 pegawai —
  TEAM LEADER (G2), ASSISTANT MANAGER (G3), MANAGER (MD/G3), SENIOR MANAGER (MM), VP (MM), GM & EVP (MA).
- **Non-struktural G1/G2 (target sah):** 1.493 posisi / 16.973 pegawai.
- **Entry level fresh graduate = G1:** JUNIOR TECHNICIAN (4.968 pegawai) + JUNIOR OFFICER (1.198) — 383 posisi.
⚠️ **Penting:** jenjang saja tidak cukup untuk memfilter — **TEAM LEADER juga G2**, sama dengan
OFFICER/TECHNICIAN. Filter harus pakai `kelompok_jabatan`, bukan `jenjang`.

**Tangga jabatan non-struktural (terverifikasi DAPEG):**

| Grade | Kelompok jabatan | Pegawai |
|---|---|---:|
| G1 | Junior Technician 4.968 · Junior Officer 1.198 | 6.166 |
| G2 | Officer 7.976 · Technician 2.831 | 10.807 |
| G3 | Senior Officer 4.384 · Senior Technician 269 | 4.653 |
| SPC/SSP | Specialist 461 · Senior Specialist 59 | 520 |

Pola: **Junior X (G1) → X (G2) → Senior X (G3) → Specialist (SPC/SSP)**.

**Grade masuk menurut jenjang pendidikan** (dari pengetahuan domain user — **TIDAK dapat
diverifikasi dari DAPEG karena DAPEG tidak punya kolom pendidikan**):
- **SMK / D3** → **G1** (Junior Officer / Junior Technician)
- **S1 / D4** → **G2** (Officer / Technician) — *bukan* Junior
- **S2** → **G3** (Senior Officer) — Pro Hire mungkin ke SPC
Keyakinan: tinggi (tangga jabatan & aturan non-struktural), **sedang (pemetaan pendidikan→grade:
sumber pengetahuan domain, belum ada data pembanding)** · Dampak: aturan wajib di generator
penempatan OJT & SK. Jangan tempatkan semua pendaftar ke Junior — sesuaikan grade dengan jenjang
pendidikannya, dan **tidak pernah** ke jabatan struktural.

### F-043 · Lowongan PLN di RBB 2024 berhasil dipanen dari arsip ⭐ [R7]
Situs RBB sudah mati (SSL error), tapi Wayback mengarsipkan endpoint datanya
`rekrutmenbersama2024.fhcibumn.id/job/loadRecord/` (JSON 2,5 MB, 663 lowongan seluruh BUMN).
**20 lowongan milik PLN Group** (`sources/rbb_fhci/lowongan_pln_rbb.csv`).

**Entitas:** PLN ICON Plus 7 · PLN (Persero) 5 · PLN Batam 5 · Haleyora Power 3.
**Stream:** Digitalisasi & IT **7** · Engineering & Maintenance 6 · Keuangan 2 ·
Operasi/Produksi/Proyek 2 · Pengembangan Usaha/R&D 2 · Bisnis Niaga/Pemasaran 1.
**Syarat:** semua `vacancy_type` = **Fresh Graduate**; **umur maks D3 27 / S1 30**; **IPK min 3,00**;
`check_certificate` = 0. Tersedia juga daftar jurusan granular asli (`major_non_sma_custom`,
mis. "Instrumentasi Fisik, Teknik Biomedika, Teknik Elektro, …").

⚠️ **`total_job_available` BUKAN kuota.** Jumlahnya 1.777.000 untuk seluruh BUMN (RBB 2024 nyatanya
merekrut ~5.900) dan semua nilainya kelipatan 1.000 → kemungkinan bobot tampilan internal. Sudah
dikecualikan dari ekstraksi. **Kuota per posisi tetap tidak ditemukan di sumber manapun** (konsisten F-017/F-027).

**Dua kontras penting vs rekrutmen PLN sendiri:**
1. **Batas umur beda per jalur** — RBB: S1 ≤30; rekrutmen PLN sendiri: S1 ≤27 (F-022). Aturan
   administrasi mock harus per-jalur, bukan satu angka global.
2. **Bauran posisi beda** — RBB didominasi IT/Digital & subholding (Icon Plus/Batam/Haleyora),
   sedangkan rekrutmen PLN sendiri didominasi Distribusi/Transmisi (F-038, DAPEG).
Sumber: R7 · Keyakinan: tinggi · Dampak: kalau RBB dimasukkan ke mock, perlakukan sebagai **jalur
terpisah** dengan aturan & bauran posisi sendiri.
> Catatan cakupan: user sejak awal menetapkan mock fokus ke program rekrutmen PLN sendiri, jadi RBB
> tetap **opsional/di luar cakupan inti** — tapi datanya kini tersedia bila mau dipakai.
> **Belum terpanen:** PPB 2021 & edisi RBB selain 2024 — **status BELUM DIKETAHUI**, bukan "tidak ada".
> Percobaan CDX berikutnya gagal karena **archive.org membalas HTTP 503 Service Unavailable**.
> Didiagnosis dengan kontrol: domain yang terbukti punya arsip (`rekrutmenbersama2024`) *dan* domain
> omong kosong sama-sama dibalas 503 → **gangguan layanan sisi server, bukan rate limit ke kita
> dan bukan ketiadaan arsip**. (Koreksi: catatan sebelumnya menyebut "rate limit" — itu keliru.)
> 503 bersifat sementara (hitungan jam); CDX bekerja normal beberapa jam sebelumnya di sesi yang sama.
> **Aksi:** coba ulang `r7_rbb_fhci.py` + CDX untuk `ppb.fhcibumn.id*`, `rekrutmenbersama2022/2023/2025`
> lain waktu. Catatan: hasil "0 snapshot" untuk PDF SR-2022 **valid** (respons JSON normal, bukan 503).

### F-044 · Runtun waktu headcount 2020–2025 lengkap (2020 diturunkan) ⭐ [R6b]
**Cek silang antar edisi SR**: seluruh metrik yang beririsan (total pegawai induk & anak, prajabatan,
pendidikan, usia rinci, ringkasan 3-bucket, dana pensiun) **cocok persis angka-per-angka** antara
SR-2023 dan SR-2024 untuk tahun 2022 & 2023 → keyakinan tinggi pada data ini.

**Identitas terverifikasi:** `Statistik PLN (Group) = SR (Induk) + SR (Anak & Afiliasi)` —
selisih **0** untuk 2022 & 2023, **3** untuk 2024. Identitas ini dipakai menurunkan angka yang hilang.

| Tahun | Group (Statistik) | Induk (SR) | Anak & Afiliasi | Kohort prajabatan |
|---|---:|---:|---:|---:|
| 2020 | 53.385 | **~44.000** *(diturunkan)* | ~9.350 *(diturunkan)* | tidak tersedia |
| 2021 | 52.116 | 42.755 | 9.361 *(diturunkan)* | 337 |
| 2022 | 51.477 | 42.151 | 9.326 | 689 |
| 2023 | 51.245 | 38.542 | 12.703 | 689 |
| 2024 | 51.438 | 38.289 | 13.146 | 1.277 |
| 2025 | tidak tersedia | 37.423 | 12.535 | 1.098 |

Turunan 2020: Anak Perusahaan stabil ~9,3rb di 2021 (9.361 turunan) & 2022 (9.326 dilaporkan),
sehingga Induk 2020 ≈ 53.385 − ~9.350 ≈ **44.024–44.059**. Ini **estimasi berdasar identitas
terverifikasi**, bukan tebakan — tapi tetap tandai sebagai turunan di data dictionary.

**Gagal diperoleh:** SR-2022 (63,9 MB) — server PLN mengabaikan HTTP Range dan memutus koneksi
berulang (5 percobaan sah); tidak ada arsip Wayback untuk PDF ini. Dampaknya kecil karena 2020
sudah tertutup lewat identitas di atas.
Sumber: R6b · Keyakinan: tinggi (2021–2025), sedang (2020 turunan) · Dampak: **horison 2020–2026
kini berjangkar data nyata**, sesuai keputusan horison hibrida.

### F-045 · Lonjakan/penurunan headcount bukan attrition murni [R6b]
Klaim: penurunan besar 2022→2023 (42.151 → 38.542, −3.609) **bukan** attrition — di periode sama
Anak Perusahaan naik 9.326 → 12.703 (+3.377). Ini ***carve-out*** pemindahan pegawai ke subholding.
Sebaliknya 2021→2022 hanya −604 (attrition wajar). Kohort 2021 juga kecil (337) — konsisten dengan
2021 sebagai tahun jalur PPB (F-041), bukan rekrutmen mandiri PLN.
Sumber: R6b · Keyakinan: tinggi · Dampak: model mock **jangan** menafsirkan semua penurunan headcount
sebagai keluar/pensiun; sediakan mekanisme *carve-out/tugas karya* terpisah (sejalan F-015).

### F-046 · Teknis jalur RBB: PLN masuk di Tahap 3/TKB [R3]
**Pembagian kerja FHCI vs BUMN:**

| Tahap | Isi | Pelaksana |
|---|---|---|
| 1 | Seleksi Administrasi | **FHCI** (portal RBB terpusat) |
| 2 | Tes Online 1: TKD, AKHLAK, TWK, cek perangkat | **FHCI** |
| 3 | Tes Online 2: Bahasa Inggris, Learning Agility | **FHCI** |
| 4 | **TKB** (Tes Kompetensi Bidang) + psikotes + wawancara user/HR + **MCU** | ⭐ **masing-masing BUMN (= PLN)** |
| 5 | Pengumuman final → onboarding perusahaan | BUMN |

Peran PLN di tahap 1–3 hanya **menetapkan syarat** (umur/IPK/jurusan/stream per lowongan — persis
yang terpanen di F-043); kandidat sudah tersaring saat sampai ke PLN.

**Pemetaan ke pipeline PLN sendiri (F-023):** TKD/AKHLAK ≈ tes adaptif PLN · Tes Online 2 ≈ bagian
Inggris dari akading · TKB+wawancara+MCU ≈ tahap 5–7 jalur mandiri. Artinya kandidat RBB
**melewati tahap awal di luar sistem PLN**.

Sumber: R3 (detik, kompas, medcom, situs bimbel — konsisten lintas sumber) ·
Keyakinan: **sedang** (pemberitaan, bukan dokumen resmi PLN; detail PLN belum dikonfirmasi) ·
Dampak: lihat rekomendasi pemodelan di bawah.

**❓ BELUM DIKETAHUI — pertanyaan untuk tim HTD (Willy):**
1. Apakah kandidat RBB tercatat juga di `rekrutmen.pln.co.id`, atau baru masuk sistem HR setelah diterima?
2. Apakah hasil tes FHCI (TKD/AKHLAK/Inggris) diserahkan ke PLN, atau PLN hanya terima daftar yang lolos?
3. Apakah pegawai hasil RBB ikut prajabatan/OJT yang sama dengan jalur mandiri? (diduga ya — kohort
   prajabatan 2024/2025 tampaknya mencakup mereka, tapi belum terkonfirmasi)

**Rekomendasi pemodelan mock:** perlakukan RBB sebagai **jalur terpisah** dengan pipeline PLN yang
lebih pendek — kandidat masuk di tahap TKB; tahap-tahap awal ditandai `dilaksanakan FHCI` /
data kosong. Alasannya kuat:
- Realistis & menjelaskan kenapa 2021 & 2024 berbeda bentuknya
- Memberi dashboard perbandingan antar-jalur (funnel & kelengkapan data berbeda) — persis tema
  *recruitment source effectiveness* di ReqGathering#3 ("source mana paling banyak yield")
- Memperkuat tema **"data apa yang ada vs belum"** (F-017): kandidat RBB memang punya lebih sedikit
  jejak di sistem PLN

### F-056 · Larangan struktural BOCOR di langkah 05 — dan kenapa 161 cek tidak melihatnya ⭐⭐
Klaim: `pagu_rekrutmen.csv` versi pertama memuat **143 orang di jabatan struktural**
(134 TEAM LEADER + 9 ASSISTANT MANAGER), melanggar `larangan_struktural` di `jabatan.yaml` —
aturan yang file-nya sendiri tandai *"paling keras di seluruh mockdb"*.

**Penyebabnya persis jebakan yang diperingatkan aturan itu.** Langkah 05 menyaring kandidat
posisi pakai `level`, bukan `kelompok_jabatan`. Data DAPEG membuktikan saringan grade memang
mustahil memisahkan keduanya:

| kelompok_jabatan | grade | struktural? |
|---|---|---|
| OFFICER | G2 | tidak |
| **TEAM LEADER** | **G2** | **ya** |
| SENIOR OFFICER | G3 | tidak |
| **ASSISTANT MANAGER** | **G3** | **ya** |

Cacat kedua di keluarga yang sama: **level 4 (SPC/SSP) ikut terbawa** (10 orang). Satu-satunya
jalur masuk ke SPC menurut `jabatan.yaml` adalah `PRO_HIRE`, dan user memutuskan pro hire di
luar cakupan ("fokus di rekrutmen pegawai non jabatan").

**Temuan yang lebih penting dari cacatnya sendiri: celah verifikasi.** `00_verifikasi_rules.py`
menjalankan ±161 cek dan semuanya lulus — karena skrip itu memverifikasi **isi `rules/`**, tak
pernah membuka satu pun CSV keluaran. *Aturan yang benar tidak menjamin generator menaatinya.*
→ dibuat `build/00b_verifikasi_keluaran.py` (22 cek atas `out/master/*.csv`), termasuk penjaga
PII yang memindai kolom & nilai berpola NIP/NIK/email. Cek-nya diuji-negatif dengan lima cacat
suntikan; kelimanya tertangkap.

Perbaikan: saringan dibaca **dari** `jabatan.yaml` (bukan ditulis ulang di generator), kekosongan
struktural **tetap** dihitung dan tetap masuk kaskade promosi — yang dilarang cuma menjadikannya
tujuan rekrutmen luar. Total pagu tetap 6.221; 143 orang teralokasi ulang ke posisi non-struktural.
Sisa rekrutmen luar level 4+ (112 orang lintas horison) dibuang eksplisit & dilaporkan.
Sumber: audit langkah 05 (2026-08-17) · Keyakinan: **tinggi** (terukur langsung) ·
Dampak: **kelas cacat "aturan benar, generator melanggar" kini punya penangkap otomatis** —
jalankan `00b` tiap kali menyentuh `build/`.

### F-055 · Skema administrasi & tes seleksi — panen dari Sample-01/02/05 + berkas mock lama ⭐
Klaim: sepuluh berkas rujukan di `data sintetis/` memuat skema yang belum pernah masuk knowledge.
Sample-03 (F-053) & Sample-04 (F-054) sudah terdokumentasi; **enam sisanya belum**.

**(a) `Rekrutment_{Administrasi,Tes_Adaptif,Akademik_English,MCU,Wawancara}.csv` — mock lama
(16 Juli 2026), BUKAN data HR.** Bukti: ID berurutan `REG-2026-00001`; `VERIFIKATOR` cuma 10 nama
stok berulang ~1.000× masing-masing; `ENGLISH SKILL` = 1 untuk seluruh 10.000 baris; kolom
`Kesimpulan` MCU harfiah berisi teks placeholder *"Berisi semua hasil pemeriksaan"*; satu orang
tercatat SD Pariaman → SMP Pematangsiantar → SMA Depok.

**Tapi kerangka kolomnya layak dipanen**, dan terkorroborasi: skema `Administrasi` beririsan kuat
dengan `skema_form.md` (hasil scrape situs asli) — Ukuran Baju/Celana/Sepatu, No KTP, Tempat &
Tanggal Lahir, Agama, Status, IPK, Program Studi, Nama Rekrutmen semuanya cocok. Tiga hal yang
**belum ada padanannya** di knowledge:

1. **Kolom sisi verifikator.** Administrasi bukan lulus/gagal gelondongan melainkan **checklist
   per-kriteria**: 9 kolom flag 0/1 (`UMUR`, `STATUS NIKAH`, `IPK`, `JURUSAN`, `KTP`, `AKTA`,
   `IJAZAH`, `TRANSKRIP`, `ENGLISH SKILL`) + kolom `VERIFIKATOR` sebagai peran. → menyambung
   langsung ke `alasan_gagal` di `funnel.yaml`, yang selama ini cuma bobot tanpa bentuk kolom.
2. **Kunci join berganti di tengah proses.** Administrasi berkunci `ID_PENDAFTARAN`; kelima
   berkas tes berkunci `NO TES`. Digabung Sample-05 (di mana `NO TES` masih jadi identitas sampai
   penempatan OJT), polanya: **pendaftaran → lulus administrasi → terbit NO TES → NO TES dipakai
   sampai SK.** Ini mekanika nyata untuk langkah 08/09.
3. **Kosakata kategorikal.** `KATEGORI` I/II/III (adaptif) · `REKOMENDASI` DISARANKAN /
   DISARANKAN DENGAN PERTIMBANGAN / TIDAK DISARANKAN (wawancara).

⚠️ **Angkanya JANGAN dipakai.** Akademik (8.981) > adaptif (8.967) — mustahil. MCU gagal 65% vs
18% di aturan kita. Ujung-ke-ujung ~17% vs jangkar keras **2,05%** (F-019) — meleset ~8×. Format
`NO TES`-nya (`TES-AKD-2026-00007`) juga keliru; yang asli `2511/ES/92/D3-ELE/135615` (F-009).

✅ Konfirmasi: kelima berkas memetakan **5 dari 6 tahap** `funnel_mandiri` dengan nama sama (hanya
`psikologi` tak berberkas), dan akademik + English berada dalam **satu** berkas dengan sub-skor
terpisah — membenarkan keputusan menjadikan `akademik_inggris` satu tahap, bukan dua.

**(b) Sample-02 — deskripsi di F-054 keliru.** Bukan sekadar "format FTK per unit pelaksana",
melainkan dokumen **bertingkat**: blok ringkasan (Kantor Induk 150 + unit pelaksana 78/88 = 316),
lalu blok rinci per unit yang memecah FTK jadi `NAMA JABATAN × SEBUTAN JABATAN × JENJANG JABATAN ×
FTK` — sampai baris `Officer | Logistik | G2 | 2`. Dua konsekuensi diterapkan ke langkah 05:
ketiga kolom itu kini dipancarkan, dan **baris ber-FTK 0 dipertahankan** ("posisi ada, formasinya
nol" ≠ "posisi tidak ada").

**(c) Sample-01 (DTPEG) sudah TERANONIMKAN** — 12 baris, `FULAN` / `1234567ZY` /
`fulanfulan@pln.co.id` / `JALAN MERDEKA`. Aman dibedah. 133 kolom dengan **dua baris judul**
(label Indonesia + nama teknis SAP). Ini kamus kolom DAPEG yang selama ini cuma kita akses lewat
Sample-03 yang ber-PII.
Sumber: `data sintetis/` (2026-08-17) · Keyakinan: **sedang** untuk skema mock lama (terkorroborasi
sebagian lewat `skema_form.md`), **tinggi** untuk Sample-01/02/05 · Dampak: bahan skema langkah
08–09; mengoreksi F-054 soal Sample-02.

### F-054 · SKEMA Penetapan Pagu Rekrutmen ditemukan ⭐⭐ [Sample-04, referensi tim HR]
Klaim: `data sintetis/Sample-04-Penetapan Pagu Rekrutmen_2026.xlsx` adalah **format asli
dokumen pagu rekrutmen dari tim HR** (dikonfirmasi user 2026-08-17). Ini persis kelas data
yang F-017/F-027/F-043 nyatakan "tidak ditemukan di sumber manapun".

**Skema (10 kolom):**
`NO · HOLDING/AP SH · HOLDING/SUBHOLDING · DIREKTORAT/BIDANG/UNIT PELAKSANA · JABATAN ·
JURUSAN PENDIDIKAN · JUMLAH · PENDIDIKAN · KETERANGAN · Ket PPT`

Contoh baris: `HOLDING | UNIT INDUK DISTRIBUSI A | UNIT LAYANAN PELANGGAN |
JUNIOR OFFICER PELAYANAN PELANGGAN | D3 Administrasi Bisnis/Akuntansi | 2 | D3 | 3T`

**Enam hal yang dikoreksi/dikonfirmasi:**

1. ⚠️ **KUOTA PER POSISI PUNYA BENTUK NYATA.** F-017 benar bahwa ini domain **HST**, bukan
   HTD — dan inilah dokumennya. **Nilainya tetap tidak kita punya** (sampel dianonimkan:
   "UNIT INDUK DISTRIBUSI A", "SH AP A"; hanya 20 baris). Jadi `kuota` **tetap DIMODELKAN**,
   tapi **BENTUKNYA sekarang nyata** dan keluaran langkah 05 wajib mengikutinya.
2. ⭐ **Pemetaan pendidikan→grade F-042 TERVALIDASI INDEPENDEN.** F-042 menandai pemetaan
   ini "keyakinan sedang, tidak dapat diverifikasi dari DAPEG karena DAPEG tidak punya
   kolom pendidikan". Sampel ini punya kolom pendidikan **dan** jabatan, dan 20/20 baris
   konsisten: **D3 → JUNIOR OFFICER/JUNIOR TECHNICIAN (G1)** (15 baris),
   **S1 → OFFICER (G2)** (5 baris). Nol pengecualian. → **naikkan F-042 ke keyakinan tinggi.**
3. **Granularitas turun sampai UNIT LAYANAN**, bukan berhenti di unit pelaksana:
   "ULP BOBONG", "UNIT LAYANAN PELANGGAN", "UNIT LAYANAN PUSAT LISTRIK". Ini bertabrakan
   dengan keputusan README "tidak sampai unit layanan" — master kita (dari `BusA`) berhenti
   di unit pelaksana. Konsekuensi dicatat, tidak dipaksakan.
4. **Jurusan ditetapkan PER BARIS PAGU**, multi-jurusan dipisah garis miring:
   "D3 Teknik Listrik/Teknik Elektro", "D3 Administrasi Bisnis/Akuntansi". Menyambung
   langsung ke `rumpun_subbidang` hasil langkah 03 — sekarang punya padanan nyata.
5. **Nama jabatan = konvensi DAPEG**, bukan Analyst/Engineer. Menguatkan `jabatan.yaml`.
6. **Subholding ikut di dokumen pagu yang SAMA** (`AP SH`, 8 dari 20 baris) — konsisten
   DECISION-01 bahwa cakupan resmi adalah PLN Group.

**Kuirk:** `KETERANGAN` cuma dua nilai — **`3T`** untuk seluruh 12 baris holding (penempatan
daerah Terdepan/Terluar/Tertinggal) dan **`Rekrut 2026`** untuk 8 baris subholding. Kuota per
baris kecil (1–3 orang, total 30) — jadi dokumen pagu sesungguhnya panjang & halus, bukan
angka gelondongan per unit.

Berkas rujukan HR lain yang relevan: **Sample-02** (format FTK per unit pelaksana),
**Sample-05** (Penempatan OJT PLN Group 2026 → bahan langkah 11), **Sample-01** (DTPEG
133 kolom, sudah teranonimkan di sampel).
> **⚠️ DIKOREKSI oleh F-055:** deskripsi Sample-02 di atas keliru. Isinya dokumen bertingkat
> yang memecah FTK sampai `NAMA JABATAN × SEBUTAN JABATAN × JENJANG JABATAN`, bukan rekap
> per unit pelaksana. Lihat F-055(b).
Sumber: `data sintetis/Sample-04...xlsx` · Keyakinan: **tinggi** (dokumen HR langsung) ·
Dampak: mengunci skema keluaran langkah 05; menaikkan keyakinan F-042.

### F-053 · Runtun realisasi BULANAN dipanen — dan tiga jebakannya ⭐ [langkah 01 revisi]
Klaim: sheet ` FTK Unit Holding` ternyata memuat **15 kolom realisasi bulanan** per unit
(Des-2024 → Apr-2026), bukan cuma dua titik potong seperti yang diekstrak semula.
Sekarang dipanen ke `out/master/realisasi_bulanan.csv` (665 baris).

⚠️ **KOREKSI temuan sebelumnya.** Kolom yang dipakai sebagai "jangkar perencanaan 2026"
di `kohort.yaml` — `realisasi_apr_2026` — **hanya terisi 2 dari 49 baris**; 47 sisanya
`#VALUE!` di file sumbernya. Jangkar yang benar adalah **`realisasi_mar_2026` (49/49
lengkap, total 37.153)**. Sudah diperbaiki di seluruh aturan & dokumen.

**Tiga jebakan yang membuat runtun ini TIDAK boleh dijumlah begitu saja:**

| Jebakan | Isi | Akibat kalau lalai |
|---|---|---|
| **Kantor Pusat kosong Jan–Agt 2025** | 8 sel `#REF!` di baris KP | total anjlok **−3.947** di Jan-2025 lalu melonjak **+3.607** di Nov-2025 — terbaca sebagai PHK massal lalu rekrutmen massal. Tidak ada satupun yang terjadi. |
| **April 2026 rusak** | `#VALUE!` di 47/49 baris | total tampak 3.920 (cuma KP), turun 89% |
| **September & Oktober 2025 tidak ada kolomnya** | header lompat Agt → November | runtun berlubang 2 bulan; jangan diinterpolasi diam-diam |

Setelah KP dikeluarkan, runtun 46 unit sisanya mulus dan masuk akal: 33.950 (Jan-2025)
→ 33.467 (Agt-2025), turun rata-rata **−60/bulan** — konsisten dengan attrition 2,7%/tahun.

**Aturan pakai:** selalu cek **jumlah unit pelapor per bulan** sebelum menjumlahkan.
Bulan dengan cakupan unit berbeda tidak sebanding. Ini varian keempat dari pola yang sama
dengan F-040/F-045/F-049: **angka PLN tidak bisa dideretkan begitu saja** — kali ini
bukan karena definisi berubah, melainkan karena cakupan pelapor berubah.

Nilai tambahnya nyata: 13 titik bulanan per unit jauh lebih kaya daripada 2 titik tahunan,
dan bisa dipakai memvalidasi laju attrition per unit di langkah 04/05.
Sumber: `data sintetis/Sample-03...xlsx` sheet ` FTK Unit Holding` kolom 6–20 ·
Keyakinan: **tinggi** · Dampak: `realisasi_bulanan.csv` baru; jangkar 2026 dikoreksi.

### F-052 · Carve-out 2023 terukur 3.138 & PLN tak pernah mengisi kekosongannya ⭐ [langkah 04]

**(a) Besaran carve-out diturunkan, lalu tervalidasi silang.**
Identitas headcount 2023 menyisakan selisih yang tidak bisa dijelaskan attrition maupun
rekrutmen: `42.151 + 689 − 1.160 = 41.680` vs nyata `38.542`. Selisih **3.138** itulah
carve-out murni. Bandingkan dengan kenaikan Anak Perusahaan **+3.377** di periode sama
(F-045) — **selisih hanya 239 orang**, besaran wajar untuk rekrutmen subholding sendiri.
Dua jalur perhitungan yang sepenuhnya terpisah mendarat berdekatan, jadi tafsir carve-out
naik jadi keyakinan **tinggi**.

Dengan carve-out diperhitungkan, identitas headcount 2023 tertutup **persis nol**, dan
residu rata-rata tahun lain turun ke **0,52%**.

**(b) Kekosongan tidak pernah terisi penuh — itulah mekanisme penyusutan.**
Kebutuhan rekrutmen dihitung dari kekosongan bernama (pensiun/APS/meninggal/PHK) lalu
dikaskadekan turun lewat promosi sampai jenjang masuk:

| Tahun | Butuh | Kohort nyata | Terisi |
|---|---:|---:|---:|
| 2021 | 1.427 | 337 | **24%** |
| 2022 | 1.290 | 689 | 53% |
| 2023 | 1.158 | 689 | 59% |
| 2024 | 1.030 | 1.277 | **124%** |
| 2025 | 1.015 | 1.098 | **108%** |

⭐ **Titik baliknya 2024.** Sampai 2023 PLN merekrut jauh di bawah kekosongan yang tercipta
— itu penjelasan aritmetis penyusutan headcount 46.062 (2017) → 38.542 (2023), bukan sekadar
"kebijakan efisiensi". Sejak 2024 kohort justru **melampaui** kebutuhan, tapi headcount
masih turun karena efeknya belum masuk: mereka baru ber-SK setelah OJT (F-051). Angka
"ber-SK 2025 cuma 76 orang (7%)" karena itu **bukan kegagalan merekrut** — itu jeda pipeline.

**(c) Kaskade tidak mengubah JUMLAH, hanya SEBARAN JENJANG.** Setiap kekosongan akhirnya
diisi seseorang dan setiap rantai promosi berujung pada satu orang dari luar, jadi total
kebutuhan = total keluar secara identik. Yang ditentukan kaskade adalah pecahannya:
**L1 36% · L2 41% · L3 20% · L4 3%** — dan pecahan inilah yang menentukan berapa lowongan
D3 vs S1/D4 vs S2 yang harus dibuka.
Sumber: langkah 04 (`mockdb/build/04_attrition_proyeksi.py`) · Keyakinan: **tinggi** untuk
(a) & (b) [aritmetika atas angka nyata], **sedang** untuk (c) [peluang promosi dimodelkan] ·
Dampak: dasar langkah 05 (usulan kebutuhan & pagu) dan narasi utama dashboard.

### F-051 · Identitas headcount MEMILAH "prajabatan" vs "direkrut" ⭐⭐ [langkah 04]
Klaim: F-035 menggantungkan tafsir selisih antara **"peserta diklat prajabatan"** dan
**"pegawai baru direkrut"** (keyakinan rendah-sedang). Identitas headcount menyelesaikannya.

Uji: `headcount[t] = headcount[t−1] + masuk[t] − keluar[t]`

| Tahun | Awal | Masuk | Keluar | Model | Nyata | Selisih | Metrik masuk |
|---|---:|---:|---:|---:|---:|---:|---|
| 2017 | 43.956 | +4.484 | −2.256 | 46.184 | 46.062 | **+122** | direkrut |
| 2021 | 44.310 | +325 | −1.427 | 43.208 | 42.755 | **+453** | direkrut |
| 2024 | 38.542 | +663 | −1.031 | 38.174 | 38.289 | **−115** | direkrut |
| 2024 | 38.542 | +1.277 | −1.031 | 38.788 | 38.289 | +499 | prajabatan |
| 2025 | 38.289 | +76 | −1.016 | 37.349 | 37.423 | **−74** | direkrut |
| 2025 | 38.289 | +1.098 | −1.016 | 38.371 | 37.423 | +948 | prajabatan |

**"Direkrut" menutup identitas (selisih 0,2–1,1%); "prajabatan" tidak (sampai 2,5%, dan
selalu berlebih ke arah yang sama.)** 2024 & 2025 yang memutuskan — di situ kedua angka
berbeda jauh (663 vs 1.277; 76 vs 1.098).

⭐ **Tafsirnya justru membenarkan model pipeline kita:** peserta prajabatan **belum
terhitung sebagai pegawai**. Mereka sudah ttd kontrak dan sedang OJT, tapi baru masuk
headcount setelah **SK penempatan**. Persis pembedaan "diterima ≠ sudah jadi pegawai"
yang sudah dipasang di `funnel.yaml` (status_per_15sep2026) — dan sekarang terkonfirmasi
dari arah yang sepenuhnya berbeda, yaitu neraca headcount.

**Aturan pakai:**
- **Ukuran kohort rekrutmen** (berapa orang menjalani seleksi) → pakai **prajabatan**
  (337 · 689 · 689 · 1.277 · 1.098). Ini yang dipakai `kohort.yaml`. **Tidak berubah.**
- **Efek ke headcount** (berapa ber-SK tahun itu) → pakai **direkrut** (689 · 663 · 76).
  Ini yang dipakai langkah 04 untuk menggulirkan headcount.

**Residu 0,2–1,1% yang tersisa** (+122, +453, −115, −74) = perpindahan yang tidak
dilaporkan terpisah — **tugas karya & mutasi ke anak perusahaan** (F-015 mencatat Tugas
Karya disebut 114× di Perdir 0050, terbanyak dari semua mekanisme). Dimodelkan sebagai
`mutasi_keluar_tak_terlapor`, bukan disembunyikan.
Sumber: turunan dari F-036/F-044/F-048/F-035 · Keyakinan: **tinggi** (identitas aritmetis
diuji di 4 tahun) · Dampak: menutup pertanyaan terbuka F-035; mengunci dua metrik terpisah.

### F-050 · Bauran jurusan yang diundang TIDAK cocok dengan bauran kursi ⭐ [langkah 03]
Klaim: setelah 42 prodi asli dipetakan ke 18 rumpun lalu ke 15 sub bidang jabatan,
**dua sub bidang terbesar justru paling kekurangan pasokan**:

| Sub bidang | Pasokan (bauran prodi diundang) | Kursi G1+G2 nyata | Selisih |
|---|---:|---:|---:|
| **Distribusi** | 13,0% | **27,8%** | **−14,8** |
| **Transmisi dan Gardu Induk** | 9,9% | **16,2%** | **−6,3** |
| Keuangan dan Akuntansi | 9,6% | 6,5% | +3,2 |
| Manajemen Konstruksi dan Pengadaan | 11,9% | 8,9% | +3,0 |
| Perencanaan dan Kinerja | 8,3% | 5,5% | +2,9 |
| Pembangkitan | 6,4% | 3,6% | +2,8 |

Dua sub bidang teknik terbesar kurang **21 poin** gabungan, sementara sub bidang
non-teknik berlebih merata.

**Penjelasannya konsisten dengan temuan lain, bukan kebetulan:** kursi Distribusi &
Transmisi didominasi **JUNIOR TECHNICIAN** (4.968 pegawai G1, F-042) — jabatan lapangan
yang secara historis diisi lewat **rekrutmen SMK/D3 per kota**. Rekrutmen itu **berhenti
setelah 2019** (F-031: 25 program SMK di 2017, lalu hilang dari katalog). Yang tersisa
adalah bauran program berat-S1 yang secara struktural tidak memasok jabatan lapangan.
Jadi F-031 + F-042 + F-050 menceritakan satu hal yang sama dari tiga arah.

⚠️ **Batas klaim:** "pasokan" di sini diproksi dari **jumlah profesi yang membuka tiap
prodi** — jadi ia mengukur bauran jurusan yang **DIUNDANG PLN**, bukan bauran jurusan yang
**DIMILIKI PELAMAR**. Kalau ternyata pelamar teknik jauh lebih banyak melamar daripada
porsi undangannya, selisihnya menyempit. Keyakinan: **sedang**.

**Konsekuensi wajib untuk generator (langkah 11):** JANGAN memaksa pengisian kursi
proporsional berdasarkan kelayakan jurusan — kandidat yang sah untuk Distribusi akan habis
di tengah jalan. Kursi harus diisi dengan pelonggaran eksplisit, dan **kekurangannya
dilaporkan sebagai keluaran**, bukan ditutupi. Selisih inilah salah satu jawaban paling
berguna untuk ReqGathering#1 ("kebutuhan rekrutmen sebagai fungsi kebutuhan nyata").

**Kuirk sumber:** dataset RBB memuat satu jurusan bernama **`TEST MAJOR PAGI`** — data uji
yang tertinggal di data produksi. Satu-satunya dari 546 prodi yang tidak dapat rumpun,
sengaja dibiarkan tidak terklasifikasi supaya jejaknya terlihat.
Sumber: langkah 03 (`mockdb/build/03_rumpun_jurusan.py`) atas profesi.csv + programs.csv +
lowongan_pln_rbb.csv + jabatan_klasifikasi.csv · Dampak: aturan penempatan & narasi dashboard.

### F-048 · SR-2021 membuka 2019–2020 & MENGONFIRMASI jeda pipeline ⭐⭐ [R6c]
Klaim: SR-PLN-2021 (336 hal, diunduh user 2026-08-17) memuat runtun **rekrutmen & turnover
2019–2021 PLN Induk** — periode yang sebelumnya gelap total.

**Karyawan masuk (rekrutmen), hal. 193:**

| | 2019 | 2020 | 2021 |
|---|---:|---:|---:|
| Karyawan masuk | **1.935** | **1.096** | **325** |
| Pensiun alami | 2.122 | 1.656 | 1.216 |
| Meninggal | 135 | 117 | 146 |
| Mengundurkan diri | 100 | 72 | 65 |
| Gender masuk (L:P) | 68:32 | 70:30 | 65:35 |

**Usia saat masuk** (hal. 193) — 20–25 th: 2019 **87%** · 2020 **89%** · 2021 **98%**;
26–30 th: 13% · 11% · 1%. Di atas 30 th praktis nol.

⭐ **Mengonfirmasi jeda pipeline (F-035/kohort.yaml, sebelumnya keyakinan sedang).**
Cocokkan ukuran GELOMBANG dengan rekrutmen TAHUN BERIKUTNYA:

| Program | Bentuk gelombang | → Masuk thn+1 | Cocok? |
|---|---|---:|---|
| 2019 | ~30 entri per kota + campus fair (masif) | 1.096 (2020) | ✓ besar |
| 2020 | **hanya PPB Papua**, buka 30 Des | **325** (2021) | ✓ terkecil |
| 2023 | 14 entri: reguler + OAP 8 kota + Maluku + Diaspora | 1.277 (2024) | ✓ terbesar |

Tiga titik ekstrem jatuh pas tanpa dipaksakan. Pemetaan tanpa-jeda tidak menghasilkan
kecocokan ini. → **Naikkan keyakinan jeda pipeline dari sedang ke tinggi.**

⚠️ **JEBAKAN — tabel "Diklat Prajabatan" SR-2021 hal. 240 BUKAN ukuran kohort.**
Tabel itu mencatat 2019 **6.734** · 2020 **2.298** · 2021 **1.359** peserta — 3–20× lebih
besar dari karyawan masuk di tahun yang sama. Itu tabel **kursi pelatihan seluruh pegawai**
(satu baris di antara Diklat Profesi 91.476, Penjenjangan 22.916, dst), dan captionnya
sendiri memperingatkan "1 orang bisa mengikuti lebih dari 1 diklat dalam 1 tahun".
Yang benar dipakai: **"Karyawan masuk"** / **"Pegawai Baru Peserta Pelatihan Pra-Jabatan"**.
Siapa pun yang membaca tabel diklat itu sepintas akan mengira 2019 merekrut 6.734 orang.

⚠️ **Selisih antar-edisi (pola F-040):** rekrutmen 2021 = **325** (212L/113P) menurut SR-2021,
tapi **337** (218L/119W) menurut SR-2025. Metrik sama, angka beda 12. Dipakai SR-2021
(laporan tahun berjalan, paling dekat ke peristiwanya); selisihnya dicatat, bukan didamaikan.

**Koreksi gender:** F-038 memberi 75:25 dari kohort 2024. Runtun penuh ternyata jauh lebih
berayun: **2019 68:32 · 2020 70:30 · 2021 65:35 · 2022 72:28 · 2023 73:27 · 2024 86:14.**
→ `demografi.yaml` harus pakai **gender per tahun**, bukan satu angka global 75:25.

Sumber: R6c (`sources/laporan_pln/pdf/SR-PLN-2021.pdf` hal. 192–193, 240) ·
Keyakinan: **tinggi** · Dampak: horison bisa mundur ke program-2019 dengan jangkar nyata;
jeda pipeline naik jadi keyakinan tinggi; gender per tahun; usia masuk tervalidasi.

**➕ Tambahan SR-2017, SR-2018 & SR-2020** (diunduh user 2026-08-17) — runtun mundur ke 2016:

| Tahun | Rekrutmen Induk | Sumber | Headcount Induk | Anak |
|---|---:|---|---:|---:|
| 2016 | — | | 43.956 | 7.202 |
| **2017** | **4.484** | SR-2017 hal. 8 & 211 | 46.062 | 8.758 |
| 2018 | *tidak dilaporkan* | | 45.497 | 8.627 |
| 2019 | **1.927** / 1.935 | SR-2020 hal. 280 / SR-2021 | — | — |
| 2020 | **1.093** / 1.096 | SR-2020 hal. 280 / SR-2021 | **44.310** | — |
| 2021 | 325 | SR-2021 | 42.755 | 9.361ᵈ |

⭐ **Headcount 2020 = 44.310 NYATA** — menggantikan turunan F-044 (~44.024–44.059).
Selisihnya hanya ~280, jadi metode turunan lewat identitas `Group = Induk + Anak`
terbukti sehat. Turunan itu boleh diganti angka nyata sekarang.

⭐ **Era ledakan lalu kontraksi.** 2017 merekrut **4.484** orang (proyek 35.000 MW) dengan
headcount puncak 46.062 — lalu runtuh: 1.927 (2019) → 1.093 (2020) → **325** (2021).
Headcount ikut turun 46.062 → 37.423 (2025). Ini busur cerita nyata untuk dashboard,
bukan rekaan. 2017 juga persis tahun 25 program SMK per kota (F-031) — skala 4.484
menjelaskan kenapa program sebanyak itu dibuka.

Sumber lengkap: R6c (SR-2017 hal. 8/211/219 · SR-2018 hal. 244 · SR-2020 hal. 280 ·
SR-2021 hal. 192–193/240) · Keyakinan: **tinggi**.
> **Masih belum diperoleh:** SR-2022 (gagal lagi — server PLN mengabaikan HTTP Range,
> kasus sama F-044) dan rekrutmen 2018 (tidak dilaporkan di SR-2018 mana pun).
> Headcount 2019 juga belum ketemu; kandidat berikutnya `Statistik2020.pdf`.

### F-049 · ⚠️ DEFINISI TURNOVER BERUBAH ANTAR EDISI — jebakan 10× [R6c]
Klaim: laporan PLN memakai **dua definisi "pegawai keluar" yang berbeda**, dan
menggabungkannya menghasilkan lonjakan palsu.

| Edisi | Definisi | Turnover dilaporkan |
|---|---|---|
| SR-2017, SR-2020 | **SEMPIT** — hanya mengundurkan diri + PHK. Pensiun dilaporkan **terpisah** dan tidak dihitung | 2017 **0,34%** · 2019 0,3% · 2020 **0,2%** |
| SR-2021 dan sesudahnya | **LUAS** — pensiun alami + meninggal + mengundurkan diri | 2021 ~3,3% · 2024 **2,69%** · 2025 2,71% |

Bukti: SR-2017 menulis *"158 pegawai keluar (135 mengundurkan diri, 23 PHK) = 0,34% dari
46.062"* lalu **secara terpisah** *"2.098 pegawai keluar karena pensiun"* — pensiun jelas
di luar hitungan turnover. SR-2020 menulis *"total pegawai keluar 2020 adalah 82 orang …
turn over 0,2%"*, sementara SR-2021 mencatat pengunduran diri 2020 = **72** (metrik sempit
yang sama) tapi total keluar 2020 = **1.845** termasuk pensiun 1.656.

⚠️ **Dampak kalau lalai:** dashboard yang menarik runtun turnover apa adanya dari
2017→2025 akan menampilkan lompatan **0,2% → 2,7%** di 2021 dan terbaca sebagai krisis
retensi. Padahal tidak terjadi apa-apa — yang berubah cuma definisinya.

**Aturan untuk mockdb:** simpan `pensiun` sebagai jenis peristiwa TERSENDIRI dan hitung
dua metrik terpisah — `turnover_sempit` (APS + PHK) dan `turnover_luas` (semua sebab).
Jangan pernah menampilkan satu garis turnover lintas 2017–2025 tanpa menandai patahan
definisi di 2021. Ini varian ketiga dari pola yang sama dengan F-040 dan F-045
(carve-out): **angka PLN tidak bisa dideret begitu saja lintas tahun.**
Sumber: R6c · Keyakinan: **tinggi** · Dampak: `attrition.yaml` butuh dua metrik + penanda patahan.

### F-047 · Rasio 1:200 DITOLAK — funnel F-019 internal konsisten di 1:49 ⭐ [kalibrasi]
Klaim: dua angka rasio seleksi yang kita punya **tidak bisa sama-sama benar**, dan yang dipakai
mockdb adalah F-019, bukan F-039.

**Ketegangan:**

| Sumber | Hitungan | Rasio |
|---|---|---:|
| F-019 (sistem HTD, kumulatif s/d Jul-2026) | 598.395 pelamar → 12.248 lulus wawancara | **1:49** |
| F-039 (turunan) | 245.217 pelamar Group 2025 ÷ 1.098 prajabatan Induk 2025 | 1:223 |

**Tiga alasan memilih F-019:**
1. **Internal konsisten** — pembilang & penyebut dari satu sistem, satu tarikan tanggal, satu cakupan.
   F-039 mencampur **pembilang cakupan Group** dengan **penyebut cakupan Induk** (kelemahan yang
   sudah dicatat sendiri di F-039, keyakinan **sedang**).
2. **F-039 melanggar plafon F-019.** Kalau 2025 sendirian 245.217 pelamar, maka horison 2020–2026
   saja sudah menembus 598.395 kumulatif-sejak-awal — mustahil, karena katalog memuat 222 rekrutmen
   sejak ±2013.
3. **Satuannya beda.** Trio angka F-019 (1.282.833 akun · 601.373 berkas lengkap · 598.395 pelamar)
   jelas **level orang**. 245.217 kemungkinan besar **level aplikasi** — dengan akun *lifetime*
   (F-025) satu orang melamar >1 profesi dan >1 tahun, jadi aplikasi ≈ 1,3–1,8× orang.
   Ini menjelaskan selisihnya tanpa menyalahkan sumber manapun.

**Konsekuensi kalibrasi (dipakai generator):** end-to-end pendaftaran→diterima = **2,05%**;
lulus administrasi **64%** (keras, F-019); target diterima Group 2020–2026 = **±8.600**, dijangkar
ke kohort prajabatan asli F-035/F-044 — bukan ke rasio.
Silang-periksa yang meyakinkan: horison kita menyerap **70% pendaftaran** kumulatif *dan*
**70% lulus wawancara** kumulatif — dua proporsi ini jatuh sama tanpa dipaksakan.

⚠️ Rasio RBB **beda jauh & sengaja dibiarkan beda**: RBB 2024 nasional ±1,1 juta pendaftar untuk
5.900 diterima ≈ **1:186** (portal tunggal, semua BUMN sekaligus). Kontras 1:49 vs 1:186 antar-jalur
justru bahan *recruitment source effectiveness* (ReqGathering#3).
Sumber: turunan dari F-019/F-039/F-035/F-044 · Keyakinan: **sedang-tinggi** (logika satuan kuat,
tapi belum dikonfirmasi HTD) · Dampak: mengunci seluruh skala volume mockdb.

**❓ Pertanyaan untuk tim HTD (Willy):** apakah angka 598.395 "pelamar" di dashboard admin
menghitung **orang** atau **aplikasi**? Satu kalimat jawaban mengunci atau merontokkan seluruh
kalibrasi volume di atas.

### F-057 · Arsip resmi siaran pers PLN saat ini TIDAK BISA dipakai [R8]
Klaim: domain lama `web.pln.co.id` (sumber semua URL siaran pers yang sejauh ini kita rujuk,
termasuk F-039/angka 245.217) **sudah mati DNS-nya** — didekomisioning, bukan gangguan sementara.
Domain baru `www.pln.co.id/news/press-release` sudah live tapi endpoint datanya
(`/assets/sample/press-release.json`) masih **data contoh dari developer**: gambar dari
`fakestoreapi.com`, judul "PLN Raih Penghargaan" berulang, isi "This is a test paragraph".
Sumber: R8 (probe `curl`+`WebFetch` 2026-08-17: `web.pln.co.id` → `ENOTFOUND`; `www.pln.co.id` →
JSON dummy + backend CMS `cmscorp.sadigit.cloud` balas 500 WordPress kosong) · Keyakinan: **tinggi**
· Dampak: **rencana R8 Tingkat-1 (arsip resmi terstruktur) gugur untuk sumber ini.** Angka historis
dari domain lama (mis. F-039 245.217, F-043 sitiran RBB) tetap sah — itu snapshot yang sudah
ditangkap sebelum domain mati, bukan diragukan. Tapi tidak ada lagi cara terprogram menambah
angka baru dari kanal ini; jalur produktif = pers daerah (F-058) + halaman artikel
`rekrutmen.pln.co.id/content/...` (belum dipanen, kandidat R8 lanjutan) + situs kampus/politeknik.

### F-058 · Funnel per-tahap TIDAK seragam antar gelombang — bukti dari berita lokal ⭐⭐ [R8]
Klaim: `funnel.yaml` mengunci `lulus_administrasi_pct: 0,64` dan `akademik_inggris.lulus_pct: 0,45`
sebagai angka tunggal berlaku semua gelombang. Berita lokal PLN UP3 Biak (afirmasi OAP, Okt 2025)
membantah ini secara langsung dengan funnel per-tahap yang terekam utuh:

| Tahap | Jumlah | Rasio thd tahap sebelumnya |
|---|---:|---:|
| Mendaftar (8–21 Sep 2025) | 301 | — |
| Lolos administrasi | 155 | **51,5%** (vs jangkar nasional 64%) |
| Hadir akademik+Inggris | 139 | 89,7% |
| Hadir psikologi | 138 | **99,3%** (1 orang absen tanpa keterangan; NOL yang gugur) |

Bandingkan dengan funnel nasional afirmasi Papua yang lebih besar: **1.658 peserta lolos
administrasi dari 6 provinsi**, tes akademik/Inggris/TAP digelar serentak **6–9 Okt 2025 di 8 kota**
(bukan bertahap dengan jeda pengumuman, beda dengan pola nasional/mandiri di funnel.yaml).

**Diagnosis:** ada minimal dua *mode* seleksi, bukan satu:
- **Mode nasional/mandiri** (dasar funnel.yaml saat ini): tahap terpisah, jeda antar-pengumuman,
  no-show tinggi di tahap awal (pelamar iseng rontok di TAP).
- **Mode afirmasi/remote** (Papua, mungkin 3T lain): tes diborong 2–4 hari di satu venue karena
  lokasi terpencil — logistik tidak memungkinkan gelombang berjenjang. Kehadiran ~99%, eliminasi
  administrasi lebih longgar (kuota afirmasi terisi jauh di bawah pelamar per profesi umum),
  hampir tidak ada yang gugur di tahap akademik/psikologi begitu hadir administrasi.

Ini **menjelaskan** kebuntuan langkah 05/06 mockdb: jumlah pendaftar per tahap per gelombang
dipaksa keluar dari SATU funnel nasional, sementara kebutuhan unit & gender per tahun juga
dikunci terpisah — sistemnya over-determined, tidak ada solusi konsisten.
Sumber: RRI ([pln-up3-biak-gelar-tes-rekrutmen-pegawai](https://rri.co.id/daerah/1888397/pln-up3-biak-gelar-tes-rekrutmen-pegawai)),
Cenderawasih Pos ([301-pendaftar-antusias](https://cenderawasihpos.jawapos.com/lintas-papua/biak/10/10/2025/rekrutmen-pln-up3-biak-prioritaskan-afirmasi-oap-301-pendaftar-antusias/)),
ParaparaTV ([1.658 peserta 8 kota](https://www.paraparatv.id/2025/10/ikuti-seleksi-pln-1-658-putra-putri-terbaik-papua-ikut-tes-rekrutmen-di-8-kota/))
· Keyakinan: **tinggi** untuk angka Biak (dua media independen sama persis); **sedang** untuk
generalisasi "mode afirmasi = borongan" (baru 1 gelombang terverifikasi lengkap)
· Dampak: **funnel.yaml harus pecah jadi arketipe per jenis gelombang** (nasional/mandiri vs
afirmasi/remote), bukan satu angka jangkar dipaksa ke semua baris `seleksi_tahap`. Jangkar F-019
(64%/2,05%) tetap berlaku sebagai **rata-rata tertimbang seluruh gelombang**, bukan aturan per-gelombang.

### F-059 · Titik data funnel tambahan (kalibrasi arketipe, keyakinan bervariasi) [R8]
Klaim ringkas, tiap baris dari satu artikel bersitasi:
- **UGM Career Days 2017** (jalur *campus hiring*, D3+S1/D4): **942 peserta hadir psikotest**
  di Jogja Expo Center, 3 Apr 2017 — psikotest = tahap ke-4 (setelah administrasi, akademik+Inggris,
  adaptif). Sumber: [rekrutmen.pln.co.id/content/.../peserta-rekrutmen-pln-antusias-ikuti-psikotest](https://rekrutmen.pln.co.id/content/view/Mjk2MTQ5MTc3NTcyOA--/peserta-rekrutmen-pln-antusias-ikuti-psikotest),
  kutipan Hardian Sakti Laksana (Deputi Manajer Komunikasi & Bina Lingkungan). **Di luar horison
  2020+**, dipakai hanya sebagai kalibrasi bentuk arketipe *campus hiring* (venue tunggal per
  kampus/kota, bukan per-provinsi).
- **Rekrutmen Group 2025 nasional**: **245.217 pendaftar**, tutup 5 Okt 2025, tahapan akademik+Inggris
  → adaptif → kesehatan → wawancara final, tes digelar di 10 kota (Medan, Ambon, Mataram,
  Banjarmasin, Yogyakarta, Makassar, Manado, Jayapura, Jakarta, Palembang). Menguatkan F-039,
  bukan temuan baru — dicatat di sini karena sumbernya kini IDN Times (mengutip Direktur Legal &
  Manajemen Human Capital PLN Yusuf Didi Setiarto), bukan siaran pers langsung (F-057: siaran
  pers asli sudah tak terlacak).
Sumber: lihat tiap baris · Keyakinan: **rendah–sedang** (satu titik data per klaim, tidak
lintas-verifikasi) · Dampak: bahan mentah untuk `mockdb/rules/funnel.yaml` arketipe *campus_hiring*;
tidak mengubah jangkar apa pun.

### F-060 · Panen putaran 2 (subholding + wilayah lain Papua) — konfirmasi pola, tanpa arketipe baru [R8]
Klaim: perluasan pencarian ke (a) situs karier 4 subholding besar (Indonesia Power, Nusantara Power,
Icon Plus — Nusa Daya/EPI/PLN ES tidak dicek terpisah) dan (b) media daerah lain di luar 2 yang
awalnya dibagikan user, menghasilkan:
- **Subholding: NIHIL angka.** Situs karier subholding (`plnipservices.co.id/careers`,
  `pln-npservices.com/karir`, `plniconplus.co.id/careers`) semuanya halaman generik tanpa siaran
  pers berangka. Pola F-057 (hanya liputan holding yang menghasilkan angka) **menguat**: rekrutmen
  subholding tidak diliput media dengan detail proses/statistik seperti holding.
- **Wilayah Papua lain, media lain, angka baru:**
  - **UIW Papua & Papua Barat** (cakupan provinsi, bukan per-UP3): **1.186 pendaftar** per 12 Sep
    2025 (tengah jendela pendaftaran 8-21 Sep) — GM Diksi Erfani Umar, sumber KabarPapua/BeritaSatu.
  - **Nabire** (kabupaten, bagian dari gelombang Papua yang sama): dari **106 terdaftar, 88 hadir
    tes offline (83%)** 7-8 Okt 2025 — beda bentuk metrik dari Biak (ini terdaftar→hadir-offline,
    bukan tahap seleksi berurutan; sisanya kemungkinan besar tes online, bukan gugur).
  - Satu angka ditemukan lalu **dibuang**: "7.209 peserta lulus administrasi" (Politeknik Ujung
    Pandang 2023) ternyata halusinasi ringkasan pencarian — halaman aslinya (`poliupg.ac.id`,
    diverifikasi via WebFetch) **tidak memuat angka itu**; daftar sebenarnya ada di lampiran PDF
    yang tidak terbaca. Dicatat sebagai pengingat: **selalu verifikasi ke sumber primer**, jangan
    percaya ringkasan mesin pencari untuk angka.
- **Media yang sudah dipakai lintas 5 titik data:** RRI (daerah), Cenderawasih Pos, ParaparaTV,
  KabarPapua/BeritaSatu, IDN Times, rekrutmen.pln.co.id (artikel lama, arsip 2017). Semuanya
  **Papua/afirmasi atau nasional** — belum ada satu pun titik dari gelombang reguler di Jawa/Sumatera/
  Sulawesi non-afirmasi, konsisten dengan diagnosis awal (media lokal hanya meliput yang punya
  sudut berita: afirmasi, rekor jumlah pendaftar).
Sumber: lihat F-058/F-059 untuk daftar lengkap + `sources/berita/berita_rekrutmen.csv`
· Keyakinan: pola "subholding nihil" **tinggi** (3 situs dicek, konsisten kosong); titik data baru
sedang · Dampak: **tidak mengubah kesimpulan F-058** (funnel butuh arketipe, bukan angka tunggal).
Menguatkan bahwa arketipe `afirmasi_remote` valid lintas beberapa UP3/kabupaten (Biak, Nabire), bukan
kasus Biak yang kebetulan. Menutup R8 Tingkat-1 & sebagian besar Tingkat-2 untuk sesi ini — hasil
lebih lanjut kemungkinan besar diminishing returns tanpa strategi baru (mis. panen sistematis semua
artikel `rekrutmen.pln.co.id/content/all/2/artikel`, atau socmed humas unit/Instagram per UP3).

### F-061 · Funnel LENGKAP 6-tahap dari blog pengalaman kandidat asli (Medan, 2015) ⭐⭐⭐ [R8]
Klaim: blog pribadi (penulis mengidentifikasi diri sendiri — Rahmat Sanjaya, alumnus Politeknik
angkatan-4 Teknik Mesin, dibagikan publik sebagai panduan job-seeker, bukan kebocoran PII pihak
ketiga) mendokumentasikan **seluruh perjalanan seleksinya**, tes demi tes, dengan tanggal DAN
jumlah peserta tersisa di tiap tahap:

| # | Tahap | Tanggal | Lokasi | Tersisa | Rasio thd tahap sblm |
|---|---|---|---|---:|---:|
| 1 | Lulus administrasi | (~1 minggu setelah lamar) | — | **1.700** | (baseline blog, bukan total pendaftar) |
| 2 | GAT (General Aptitude Test / TPA) | Sab, 25 Apr 2015 | Gedung POLMED, Medan | **~900** | 52,9% |
| 3 | Tes akademik + Bahasa Inggris | Min, 26 Apr 2015 | Gedung POLMED, Medan | **~700** | 77,8% |
| 4 | Psikotes | Sen, 27 Apr 2015 | Gedung H. Anief, Medan (dipindah dari POLMED — bentrok anak perusahaan Garuda Indonesia) | **495** | 70,7% |
| 5 | Tes fisik | Sel, 12 Mei 2015 | Klinik Prodia, Medan | **295** | 59,6% |
| 6 | Tes lab & kesehatan penunjang | Sen, 25 Mei 2015 | Klinik Prodia, Medan | **138** | 46,8% |
| 7 | Wawancara | Rab, 10 Jun 2015 | Kantor PLN Jl. KL Yos Sudarso, Medan | *(hasil tak tercatat di artikel — bersambung)* | — |

**Temuan struktural yang MEREVISI F-058 (bukan membatalkan):** tiga tes kognitif pertama (GAT →
akademik+Inggris → psikotes) digelar **3 hari BERTURUT-TURUT** di kota yang sama (25-26-27 April),
bukan bertahap dengan jeda pengumuman mingguan seperti diasumsikan `funnel.yaml` saat ini untuk
jalur mandiri. Baru tahap fisik/lab/wawancara yang punya jeda panjang (2-4 minggu) — masuk akal,
karena itu perlu waktu proses lab & penjadwalan panel wawancara, bukan soal jalur afirmasi-vs-mandiri.
**Implikasi:** pola "borongan multi-hari di satu venue regional" tampaknya BUKAN ciri khusus jalur
afirmasi (seperti disimpulkan F-058) — itu mungkin **pola umum test center regional** untuk
tahap-tahap awal berbasis kognitif, di jalur mandiri maupun afirmasi. Yang benar-benar membedakan
afirmasi (Biak) dari mandiri (Medan 2015) kemungkinan besar bukan JADWAL, tapi **LAJU ELIMINASI**:
Medan 2015 tetap menggugurkan besar-besaran di tiap tahap (52,9% → 77,8% → 70,7% → 59,6% → 46,8%,
majemuk ~7,4% dari 1.700 lolos ke tahap wawancara), sedangkan Biak nyaris tidak menggugurkan
setelah administrasi (99,3% bertahan). Arketipe funnel sebaiknya dipisah oleh **laju eliminasi**,
bukan pola penjadwalan.
Sumber: [everydayisgood.home.blog/2020/08/17/pengalaman-rekrutmen-pln](https://everydayisgood.home.blog/2020/08/17/pengalaman-rekrutmen-pln/)
· Keyakinan: **tinggi** untuk kronologi & angka (narasi internal konsisten, tanggal berurutan logis,
detail sangat spesifik/tak mungkin dikarang) — **rendah** untuk representativitas (1 kota, 1 tahun,
2015, di luar horison 2019+, dan "1.700" adalah populasi test-center Medan bukan total pendaftar
nasional) · Dampak: **kalibrasi terbaik yang kita punya untuk struktur internal jalur mandiri**
tapi TIDAK menggantikan jangkar F-019 (itu tetap skala nasional 2020+); dipakai untuk BENTUK funnel
(berapa tahap, tahap mana yang borongan, tahap mana yang berjeda), bukan angka absolut.

### F-062 · Surat panggilan tes: sistem batch & venue regional [R8]
Klaim: dua surat panggilan tes asli (dari `rekrutmen.pln.co.id/recruitment/site/printinvitationtest/`,
diverifikasi via WebFetch dengan larangan eksplisit mengutip PII — hanya struktur diambil) menunjukkan:
- **Bandung, 27 Mar 2018**: "Tes Akademik dan Bahasa Inggris", tiba **90 menit** sebelum jadwal,
  venue publik disewa (Graha Batununggal Indah), *dress code* formal wajib (kemeja+bawahan kain,
  dilarang jeans/kaos/sandal), bawa alat tulis sendiri (pensil 2B, HB, penghapus, ballpoint, papan alas).
- **Online, 14 Okt 2023**: tahap sama ("Tes Akademik") sudah pindah ke **format online** via
  `seleksi.pln.co.id`, sistem **batch waktu** (mis. Batch 13, mulai 13:00 WIB), syarat teknis eksplisit
  (PC/laptop wajib, Chrome≥16, Windows≥XP, ≥512kbps), tidak hadir di jam batch = gugur otomatis.
Konfirmasi evolusi **offline→online** untuk tes akademik+Inggris antara 2018 dan 2023 (melengkapi
F-024 "drop point" yang sudah lebih dulu mencatat transisi ini secara umum).
Sumber: dua surat panggilan asli (kunci URL dari pencarian manual user, 2026-08-18) · Keyakinan:
tinggi untuk struktur/jadwal, tidak berlaku data pribadi (sengaja tidak diambil) · Dampak:
`tahapan.yaml` sudah punya arah offline→online (F-024); ini menambah bukti titik potong ≤2018
masih offline venue fisik, ≥2023 sudah online+batch.

### F-063 · Cek sistematis tiap gelombang 2019–2025 thd `angkatan.yaml` — konfirmasi + 1 sitasi meragukan [R8]
Klaim: user meminta pengecekan ulang tiap gelombang yang sudah dikunci di `angkatan.yaml` (seri
`utama`, angkatan 70-92) — apakah ada berita yang menguatkan, atau memang bolong secara berita saja
(bukan berarti tidak ada rekrutmennya). Hasil per angkatan:

**Dikuatkan / cocok kuat dengan berita:**
- **Angkatan 72** (yaml: 2019-09, "~7 kota"): siaran pers PLN eksplisit berjudul
  *["Cari Talenta Unggul, PLN Buka Rekrutmen di 7 Kota"](https://web.pln.co.id/cms/media/siaran-pers/2019/09/cari-talenta-unggul-pln-buka-rekrutmen-di-7-kota/)*
  — **"7 kota" cocok PERSIS**. Pendaftaran 7-20 Sep 2019, bertepatan UGM Career Days ke-26
  (7-8 Sep 2019). Kota yang teridentifikasi: Jakarta, Palembang, Medan, Banjarmasin, Yogyakarta,
  Makassar (+1). **Naikkan keyakinan gelombang ini dari `inferensi` mendekati `nyata`.**
- **Angkatan 73** (yaml: 2019-11, S2 Indonesia Career Evening): dikonfirmasi acara di London
  **28 Okt 2019** — dekat dengan "November" yang tertulis (selisih wajar, bisa jadi buka
  pendaftaran online menyusul setelah acara tatap muka). Sumber: [web.pln.co.id/.../jemput-bola-pln-rekrut-pelajar-s2-indonesia-terbaik-di-london](https://web.pln.co.id/cms/media/siaran-pers/2019/11/jemput-bola-pln-rekrut-pelajar-s2-indonesia-terbaik-di-london/).
- **Angkatan 71** (yaml: 2019-08, Airlangga Career Fair): acara & pendaftaran memang terkonfirmasi
  nyata, TAPI tanggalnya **Maret 2019** (pendaftaran 13-22 Mar, Airlangga Career Fair ke-31
  13-14 Mar), **bukan Agustus** seperti tertulis di yaml — lihat poin sitasi meragukan di bawah.

**⚠️ Sitasi meragukan — perlu dicek ulang sumber Wayback aslinya untuk gelombang 70 & 71:**
- yaml gelombang 70 (2019-07) mencantumkan entri "**Bursa Karir ITS ke-33**" sebagai bagian
  gelombang ini. Ditelusuri: **Bursa Karir ITS ke-33 terjadi April 2017** (terkait target rekrutmen
  6.056 pegawai 2017, F-031), bukan 2019. Edisi ITS di tahun 2019 yang benar adalah **ke-37 (20-21
  Mar 2019)** dan **ke-38 (25-26 Sep 2019)** — dan tidak satupun hasil pencarian mengonfirmasi
  kehadiran PLN spesifik di ke-37/ke-38.
- Ditambah temuan Airlangga Career Fair di atas (Maret, bukan Agustus untuk gelombang 71) — pola
  yang muncul: **peristiwa kampus yang dipakai sebagai penanda bulan gelombang 70/71 kemungkinan
  tertukar dengan tahun/gelombang lain saat R1c (panen Wayback) dulu**, ATAU deskripsi "entri" di
  `angkatan.yaml` memang cuma perkiraan longgar (sudah ditandai `sumber_nomor: inferensi`, jadi
  ini bukan pelanggaran janji, tapi bukti konkret bahwa dugaan bulannya kemungkinan meleset).
  **Tidak diperbaiki di sini** — findings hanya mencatat, `angkatan.yaml` adalah wilayah sesi build.
  Rekomendasi: sebelum sesi build memakai bulan 70/71 untuk apa pun yang presisi (mis. urutan
  dalam tahun), tarik ulang `sources/rekrutmen_pln/wayback/programs_historis.csv` baris 70/71 dan
  cocokkan tanggal `buka` aslinya dengan Maret vs Juli/Agustus.

**Diperkaya (bukan sekadar dikonfirmasi) — detail baru yang tidak ada di yaml:**
- **Angkatan 75** (yaml: "PPB/RBB nasional 2021", entri "0 -- tidak ada di katalog PLN"): ternyata
  **BUKAN generik nasional** — ini program **khusus Papua & Papua Barat**, pendaftaran
  **23 Des 2021 – 14 Jan 2022** (melintasi pergantian tahun). Sumber: [Kompas](https://www.kompas.com/tren/read/2021/12/24/200500265/dibuka-program-perekrutan-bersama-bumn-papua-dan-papua-barat-2021-ini),
  [Tribun Bogor](https://bogor.tribunnews.com/2021/12/24/lowongan-kerja-terbaru-desember-2021-rekrutmen-bersama-bumn-papua-dan-papua-barat).
  Ini kandidat kuat untuk memperbaiki `nama` gelombang 75 di `angkatan.yaml` jadi lebih spesifik,
  dan `tahun` mungkin perlu dipertanyakan (dibuka Des 2021, tapi hasil seleksi & penempatan
  realistisnya jatuh 2022 — konsisten dengan pola jeda pipeline F-048).
  > **❌ DITARIK 2026-08-18 — lihat F-067.** Versi pertama butir ini menulis "target eksplisit
  > **200 orang (kuota dibuka 250 posisi)**". **Kedua angka itu TIDAK ADA di artikel Kompas yang
  > disitasi**, dan PLN bahkan tidak disebut sama sekali di sana (diverifikasi WebFetch 2026-08-18).
  > Yang sah dari artikel itu hanya **tanggal pendaftaran** dan batas umur per jenjang
  > (SMA 22 / Diploma 25 / S1 28 / S2 33). Angka 200/250 dicabut.

**Genuinely bolong (dicari, nihil — SESUAI dugaan `angkatan.yaml` sendiri):**
- **Angkatan 79, 80** (Nov-Des 2022, D3/S1 reguler): tiga percobaan pencarian dengan kata kunci
  berbeda, nol hasil rekrutmen PLN spesifik Nov/Des 2022. Ini **memperkuat**, bukan melemahkan,
  keputusan `angkatan.yaml` sendiri untuk menandai gelombang ini "tidak terekam di katalog PLN" —
  bolongnya konsisten antara katalog resmi dan berita, jadi kemungkinan besar memang tidak
  terpublikasi luas (bukan berarti tidak terjadi).

**Tidak konklusif:**
- **Angkatan 87/88** (RBB 2024, diasumsikan 2 batch Mar & Agu): pendaftaran RBB 2024 yang
  terkonfirmasi cuma **SATU jendela nasional, 23 Mar – 1 Apr 2024**, dengan proses seleksi
  (bukan pendaftaran ulang) berlangsung sampai **~Agustus 2024**. Pencarian eksplisit untuk
  "batch 2 Agustus 2024" hanya menemukan pola umum RBB (BUMN besar seperti Pertamina/BRI/Telkom
  kadang buka batch 2), **tidak ada konfirmasi PLN ikut batch 2**. Asumsi "87=batch I, 88=batch II"
  di `angkatan.yaml` **belum terbukti maupun terbantah** — cukup masuk akal kalau 87/88 sebenarnya
  sama-sama bagian dari SATU proses Maret 2024, bukan dua pendaftaran terpisah.

Sumber: lihat tiap poin · Keyakinan: bervariasi per poin (dicatat di atas) · Dampak: **tidak ada
angka mockdb yang berubah dari temuan ini** — ini murni validasi-silang katalog vs berita. Nilai
utamanya untuk sesi build: (1) angkatan 72 boleh dipakai lebih percaya diri, (2) angkatan 75 punya
deskripsi lebih akurat untuk dipakai di dashboard/nama gelombang, (3) sitasi ITS ke-33 di gelombang
70 sebaiknya diverifikasi ulang ke Wayback sebelum dipakai sebagai fakta presisi bulan.

### F-067 · Angka "200/250" DICABUT — dan RBB ternyata jalan TIAP TAHUN, bukan selang-seling ⭐⭐ [cek-ricek]
Klaim: dua hal, satu koreksi dan satu hipotesis baru.

**(a) Pencabutan.** F-063 menulis program PPB Papua 2021 punya "target eksplisit 200 orang
(kuota dibuka 250 posisi)". **Kedua angka itu tidak ada di sumbernya.** Artikel Kompas yang
disitasi diverifikasi langsung (WebFetch 2026-08-18): yang ada hanya **tanggal pendaftaran
23 Des 2021 – 14 Jan 2022** dan batas umur per jenjang (SMA 22 / Diploma 25 / S1 28 / S2 33).
Tidak ada angka target, tidak ada kuota, dan **PLN tidak disebut sama sekali** — program itu
lintas BUMN. Tribun (sitasi kedua) memblokir akses (HTTP 403), jadi tidak bisa jadi penopang.

⚠️ **Tandanya sudah ada sejak awal dan terlewat:** angka itu tidak pernah masuk
`sources/berita/berita_rekrutmen.csv`, padahal 15 titik data lain semuanya tercatat di sana
lengkap dengan `kutipan_verbatim`. Klaim yang hidup hanya di prosa temuan, tanpa kutipan, layak
dicurigai. Ini kekambuhan persis dari jebakan yang F-060 sendiri catat ("7.209 peserta" yang
ternyata halusinasi ringkasan pencarian) — **aturan "verifikasi ke sumber primer" ternyata
dilanggar di temuan yang sama yang menuliskannya.**

Akibatnya: besar celah 2021 **TIDAK DIKETAHUI**. Yang masih berdiri cuma bahwa katalog PLN 2021
kosong, satu-satunya program terdokumentasi berlingkup Papua, dan 689 orang menjalani prajabatan
di 2022.

**(a2) Dari mana angka itu berasal — dan kenapa salahnya fatal.** Panen lanjutan menemukan
sumber aslinya: [Detik, 25 Jun 2021](https://www.detik.com/edu/edutainment/d-5619419/kementerian-bumn-buka-lowongan-kerja-untuk-1-000-putra-putri-papua-barat)
memuat kalimat bahwa **masih dibutuhkan "250 orang lagi untuk mencapai 1.000 target"**. Itu
**sisa target NASIONAL lintas seluruh BUMN**, bukan kuota PLN. Angka nyata programnya:

| | Angka | Cakupan |
|---|---:|---|
| Target program PPB Papua 2019–2021 | **1.000** | seluruh BUMN |
| Realisasi 2019 | **522** | seluruh BUMN (39 perusahaan) |
| Realisasi 2020 | **254** | seluruh BUMN (47 BUMN) |
| Sisa untuk 2021 | **~250** | seluruh BUMN |
| Lolos administrasi PPB Papua 2021 | **2.759** | seluruh BUMN |

Angka 2.759 dari dokumen primer *"Lolos Seleksi Administrasi PPB Papua 2021.pdf"* (61 halaman,
dibuat 20 Jan 2022 — tepat setelah pendaftaran tutup 14 Jan 2022), ditemukan lewat tautan
`bit.ly/PPBPapua2021` di artikel Kompas. **Berkasnya daftar nama pihak ketiga: hanya jumlah
barisnya yang diambil, tidak disimpan ke repo, tidak satu nama pun dikutip.**

⚠️ **Konsekuensinya jauh lebih besar dari sekadar mencabut satu angka.** Kalau SELURUH BUMN
hanya menyerap 254 orang (2020) dan ~250 orang (2021) dari program ini, maka porsi PLN paling
banyak beberapa puluh orang. Padahal `kohort.yaml` menyandarkan **dua tahun penuh** padanya:

| tahun program | gelombang di `angkatan.yaml` | kohort PLN | plafon program (semua BUMN) |
|---|---|---:|---:|
| 2020 | 74 — PPB Papua, buka 30 Des 2020 | **325** | 254 |
| 2021 | 75 — PPB Papua & Papua Barat | **689** | ~250 |

PLN sendirian tidak mungkin merekrut 325 orang dari program yang total nasionalnya 254. **Premis
`kohort.yaml` bahwa 2020 & 2021 adalah "tahun jalur PPB/RBB" karena itulah satu-satunya gelombang
di katalog TIDAK BISA DIPERTAHANKAN.** Kohort 325 & 689 tetap NYATA (dari SR); yang salah adalah
atribusinya ke gelombang PPB Papua.

**(b) Hipotesis baru dari cek-ricek `referensi/historychatgemini02.txt`** — bukan bukti, tapi
konsisten dengan bukti negatif kita sendiri:
- **PLN Induk menutup rekrutmen umum sepanjang 2020–2021** karena efisiensi anggaran pandemi.
  Cocok dengan bukti negatif kuat kita: nol judul baru di 32 snapshot Wayback 2021.
- **RBB edisi PERDANA = April 2022**, bukan 2021. Kalau benar, "jalur rbb" untuk 2021 di
  `kohort.yaml` mustahil — RBB belum ada.
- **PLN ikut RBB di 2022, 2023, 2024, DAN 2025** — jadi RBB dan mandiri **berjalan paralel tiap
  tahun**, bukan selang-seling. `kohort.yaml` yang menetapkan SATU `jalur` per tahun
  (2020 rbb · 2021 rbb · 2022 mandiri · 2023 mandiri · 2024 rbb · 2025 mandiri) kemungkinan
  menyederhanakan berlebihan.
- **Jadwalnya berbeda sistematis:** RBB dibuka Mar–Mei, mandiri dibuka Q3/Q4. Kalau benar, jeda
  pipeline tidak seragam — RBB (buka Mar, seleksi selesai ~Agu, F-063) bisa mendarat di kelas
  prajabatan **tahun yang sama**, sementara mandiri (buka Q3/Q4) mendarat **tahun berikutnya**.
  Ini calon penjelasan paling rapi untuk 689 orang prajabatan 2022: mereka mungkin keluaran
  **RBB April 2022 (jeda 0)**, bukan gelombang 2021 (jeda +1).

⚠️ **Status (b): HIPOTESIS, jangan diterapkan sebelum diverifikasi ke sumber primer.** Sumbernya
ringkasan chatbot, kelas sumber yang baru saja menjatuhkan kita di butir (a). Bukti tandingannya
sudah ada: chat itu menyebut RBB 2024 memberi PLN Group "12 posisi", padahal panen primer kita
(`lowongan_pln_rbb.csv`, arsip portal FHCI) memuat **20 lowongan**. Data primer menang.
Sumber: WebFetch Kompas 2026-08-18 (butir a); `referensi/historychatgemini02.txt` (butir b) ·
Keyakinan: **tinggi** untuk pencabutan (diverifikasi langsung), **rendah** untuk hipotesis RBB ·
Dampak: `angkatan.yaml` gelombang 75 dibersihkan dari angka karangan; celah 2021 kembali jadi
besaran tak diketahui; **`kohort.yaml -> jalur` per tahun masuk daftar yang perlu diuji ulang.**

### F-066 · Penempatan TIDAK mengikuti kota tes ⭐⭐ [keterangan user]
Klaim: kota tes dan lokasi penempatan adalah dua hal terpisah. Yang menentukan penempatan
adalah **FTK yang kosong**, bukan kedekatan geografis dengan tempat kandidat ikut seleksi.

**Bukti dari dalam prosesnya sendiri:** di wawancara kandidat ditanya apakah *siap ditempatkan
di seluruh Indonesia*. Pertanyaan itu tidak ada gunanya kalau penempatan mengikuti kota tes.

Ada **kecenderungan** — bukan aturan — menempatkan dekat alamat KTP, dan lebih kuat untuk
kandidat **perempuan**. Dimodelkan sebagai bobot lunak yang bisa dikalahkan kebutuhan FTK.

⚠️ **Kenapa ini penting dicatat eksplisit:** `kota_rekrutmen` di `profesi.csv` terkunci saat
mendaftar (F-024/F-033) dan *terlihat* seperti penanda wilayah. Pemodel mana pun akan default
menempatkan lulusan tes Makassar ke unit Sulawesi. Itu salah, dan salahnya tidak akan terlihat
di verifikasi mana pun karena hasilnya tetap "masuk akal".

**Pengecualian historis (DI LUAR horison):** ≤2016/17 ada angkatan SMA/SMK yang seleksinya
REGIONAL — peserta seleksi Sumatera Bagian Utara hanya ditempatkan di unit Sumbagut
(pembangkitan/transmisi/distribusi Sumbagut). Tidak dimodelkan, konsisten dengan
`angkatan.yaml -> smk_pelaksana.dimodelkan: false`. Dicatat supaya kalau horison dimundurkan
ke ≤2017, aturan penempatan ikut berubah — bukan diteruskan begitu saja.
Sumber: keterangan user (2026-08-18) · Keyakinan: **tinggi** (pengetahuan orang dalam) ·
Dampak: mengunci aturan langkah 11; ditulis ke `jabatan.yaml -> penempatan.lokasi_tes_bukan_lokasi_penempatan`.

### F-065 · Mekanisme carve-out: TUGAS KARYA, dan itu PILIHAN pegawai ⭐ [keterangan user]
Klaim: F-045/F-052 mengukur *besaran* carve-out 2023 (3.138 orang) tapi tidak tahu
*mekanismenya*. Mekanismenya: sekitar 2021–2022 PLN membentuk struktur holding-subholding —
anak perusahaan pemegang pembangkitan (Indonesia Power & Nusantara Power) dijadikan subholding,
dan banyak pembangkit PLN dialihkan pengelolaannya ke sana. Pegawainya **diberi pilihan**:

1. tetap di **holding**, tapi lokasi tugasnya dipindah; atau
2. tetap di **lokasi** yang sama, tapi berpindah ke subholding sebagai **tugas karya**.

**Tiga konsekuensi pemodelan:**
1. Carve-out bukan pemindahan borongan melainkan hasil **pilihan individu**, jadi besarannya
   tidak bisa diturunkan dari daftar aset pembangkit yang dialihkan. Angka 3.138 hasil identitas
   headcount (F-052) tetap cara terbaik mengukurnya.
2. Yang memilih tugas karya **tidak pindah rumah**; yang bertahan di holding justru pindah lokasi.
   Jadi **jangan** memodelkan carve-out sebagai relokasi geografis.
3. Mereka keluar dari headcount **holding** tapi tetap di dalam PLN Group — bukan attrition, dan
   **tidak** memunculkan kekosongan yang perlu direkrut ulang di lokasi yang sama.

Menjelaskan juga kenapa porsi Pembangkitan di holding tinggal 761 pegawai G1+G2 (langkah 02).
Sumber: keterangan user (2026-08-18) · Keyakinan: **tinggi** · Dampak: `attrition.yaml ->
carve_out.mekanisme`; melarang tafsir carve-out sebagai relokasi atau sebagai kekosongan.

### F-064 · DUA SUMBU over-determined di langkah 05/06 — satu selesai (R8), satu sudah punya prinsip (F-050) ⭐⭐ [sintesis]
Klaim: kebuntuan yang dilaporkan sesi build ("konflik antara rule kebutuhan unit dengan rule gender
menghasilkan angka bertentangan, terlihat di kasus Papua 2023/2025") sebenarnya **dua sumbu masalah
berbeda**, tercampur karena muncul bersamaan di titik yang sama (langkah 05→06). Keduanya sudah
punya jalan keluar — tidak ada yang butuh riset lebih lanjut.

**Sumbu 1 — jumlah pendaftar per tahap per gelombang.**
*Gejala:* satu funnel nasional tunggal (`funnel.yaml` lama: lulus administrasi 64%, dst.) dipaksa
berlaku ke SEMUA gelombang, padahal kohort per tahun (`kohort.yaml`, nyata) dan kebutuhan unit
per tahun sudah dikunci terpisah — tidak ada solusi funnel tunggal yang konsisten dengan keduanya
sekaligus.
*Bukti akar masalah:* berita Biak 2025 (F-058) dan blog kandidat Medan 2015 (F-061) menunjukkan
funnel NYATA berbeda jauh antar-gelombang — bukan variasi acak, tapi dua **arketipe laju eliminasi**
yang berbeda struktur:
- `nasional_mandiri`: eliminasi berat tiap tahap (Medan 2015: majemuk ~7,4% dari lulus-administrasi
  ke pra-wawancara)
- `afirmasi_remote`: eliminasi nyaris nol setelah administrasi (Biak: 99,3% bertahan tiap tahap)
*Resolusi:* `funnel.yaml` dipecah per arketipe (dipilih per gelombang lewat `angkatan.yaml` ->
`jenis_program`: AFIRMASI vs REGULER/CAMPUS/dst.), BUKAN satu angka jangkar untuk semua. Jangkar
nasional F-019 (64%/2,05%) tetap berlaku sebagai **rata-rata tertimbang seluruh gelombang**, bukan
aturan per-gelombang. **STATUS: siap dikerjakan** — datanya sudah ada (F-058/F-059/F-061), tinggal
restrukturisasi `funnel.yaml` (pekerjaan sesi build, bukan riset lagi).

**Sumbu 2 — kebutuhan unit (pagu) vs bauran jurusan/gender historis gelombang.**
*Gejala:* `pagu_rekrutmen.csv`/`usulan_kebutuhan.csv` (langkah 05, bottom-up dari attrition +
kekosongan per unit — F-051/F-052) menyatakan BERAPA orang dibutuhkan di BIDANG/UNIT mana. Tapi
gelombang/program yang REAL terjadi di tahun itu (angkatan.yaml, nyata dari programs.csv) punya
bauran jurusan & gender sendiri yang sudah baku secara historis (mis. 2023 didominasi afirmasi 3T
Papua+Maluku -> gender 86:14, `demografi.yaml`). Kedua hal ini **independen dan tidak dijamin
cocok** — memaksa generator memuaskan keduanya secara PERSIS di tahun & bidang yang sama adalah
over-determined, gejalanya sama seperti Sumbu 1 tapi di layer berbeda (bidang/gender, bukan volume).
*Bukti bahwa ini BUKAN masalah baru:* sudah ditemukan & diputuskan di **langkah 03**, jauh sebelum
langkah 05/06 ditulis — lihat F-050: kursi Distribusi (−14,8 poin) & Transmisi (−6,3 poin) kurang
pasokan dari bauran jurusan yang diundang program. Keputusan yang SUDAH TERTULIS saat itu:
> "JANGAN memaksa pengisian kursi proporsional berdasarkan kelayakan jurusan... Kursi harus diisi
> dengan pelonggaran eksplisit, dan **kekurangannya dilaporkan sebagai keluaran, bukan ditutupi**."
`demografi.yaml` (§1 gender) menulis prinsip yang sama dari sisi gender: *"Generator harus
menghasilkan angka ini LEWAT bauran program, bukan dengan memaksa 0,86 di sisi kandidat."*
*Resolusi:* **prinsipnya sudah ada, tinggal ditegakkan di kode.** Urutan wajib:
1. `angkatan.yaml` (gelombang & program REAL tahun itu) → menentukan bauran bidang/gender yang
   TERJADI — ini kebenaran yang tidak bisa dinegosiasi ulang.
2. `pagu_rekrutmen.csv`/`usulan_kebutuhan.csv` (kebutuhan unit) → **bukan target keras** yang harus
   dipenuhi persis. Perannya jadi **pembanding/indikator gap**: unit mana yang under-supplied tahun
   itu, dilaporkan sebagai keluaran dashboard ("kebutuhan vs realisasi"), bukan dipaksa sama dengan
   memutar-mutar bauran gelombang yang sudah nyata.
3. Gender per tahun (`demografi.yaml`) HARUS muncul sebagai HASIL dari langkah 1 (bauran program
   nyata × gender per bidang), diverifikasi cocok dengan angka nyata F-048 — bukan dipaksakan
   langsung ke kandidat.
*Dugaan akar bug di sesi build:* kemungkinan besar langkah 06 (atau turunannya) mencoba memuaskan
`pagu_rekrutmen.csv` sebagai constraint keras BERSAMAAN dengan mencocokkan bauran gelombang nyata
— melanggar urutan di atas. **STATUS: prinsip sudah dikunci sejak langkah 03, cek implementasi
kode di 05→06, bukan riset lebih lanjut.**

**Ringkasan untuk sesi build:** kedua sumbu SELESAI dari sisi riset/keputusan. Sumbu 1 butuh
restrukturisasi `funnel.yaml` (data sudah ada). Sumbu 2 butuh audit kode supaya `pagu_rekrutmen.csv`
diperlakukan sebagai pelaporan-gap (sesuai F-050 yang sudah lama diputuskan), bukan target keras
yang dipaksa sama dengan bauran gelombang nyata dari `angkatan.yaml`.
Sumber: sintesis F-050, F-058, F-061, `demografi.yaml`, `mockdb/rules/README.md` (urutan kausal)
· Keyakinan: tinggi (logika, bukan angka baru) · Dampak: **membuka blokade langkah 05/06** tanpa
riset tambahan — dua perbaikan konkret untuk sesi build.

### F-068 · Limpasan gelombang ujung tahun ke laporan tahun berikutnya — mekanisme dikonfirmasi, besaran belum ⭐ [keterangan user]
Klaim: `jeda_pipeline` (F-048) memakai SATU angka lag (~13 bulan, tutup gelombang → SK) untuk
seluruh peserta satu gelombang. Padahal siswa yang **gagal ujian OJT dan mengulang** bisa dapat SK
berbulan-bulan lebih lambat dari kelompok utamanya — kalau gelombangnya sendiri sudah tutup dekat
akhir tahun, sebagian pesertanya bisa **ber-SK di tahun laporan SR berikutnya**, bukan tahun yang
diasumsikan `masuk_di`.

**Bukti (pengalaman langsung user, angkatan Okt 2016):**
> Pendaftaran Okt 2016 → wawancara s.d. akhir Des 2016 → pengumuman lolos awal Jan 2017 → ttd
> kontrak, samapta, pembidangan → OJT mulai April → ujian OJT Agustus (saat itu OJT cuma 3 bulan,
> "sepertinya sekarang diperpanjang") → **pengangkatan (SK) September** untuk yang lulus ujian
> pertama. Tapi ada teman yang **tidak lulus ujian pertama, SK-nya baru turun November** — mundur
> 2 bulan dari kelompok utama. Kalau ada yang tidak lulus ujian ULANGnya lagi, "bisa jadi dapat
> SK-nya Januari" — mundur ke TAHUN KALENDER BERIKUTNYA.

**Implikasi ke kohort.yaml:** gelombang yang tutup di kuartal 4 punya risiko limpasan lebih tinggi
karena marjin waktunya ke pergantian tahun lebih tipis. Dicek pola bulan tutup tiap tahun_program
yang sudah "kualitas tinggi" (sudah pas ke katalog visible tanpa residu):

| tahun_program | gelombang penutup terakhir | risiko limpasan |
|---|---|---|
| 2019 | campus fair ~Nov | sedang |
| 2020 | PPB buka 30 Des 2020 | tinggi |
| 2021 | PPB tutup pendaftaran 14 Jan 2022 (F-067) | tinggi |
| 2022 | S2 ICE 7 Okt | sedang |
| 2023 | Putra-Putri Maluku & Nusa Tenggara 16 Okt | sedang-tinggi |
| 2024 | RBB ~Mar/Apr | rendah |

**Kenapa BELUM dipakai untuk mengisi residu 2024 (~744, F-067) atau tahun lain:** tiga alasan
menahan diri dari memasukkan angka spekulatif ke `komposisi_jalur`:
1. F-048 sudah membuktikan kecocokan pipeline ~13 bulan SANGAT presisi di 3 titik ekstrem (program
   2019/2020/2023) tanpa dipaksakan — limpasan besar semestinya merusak kecocokan setajam itu.
2. Limpasan realistis paling banyak sebagian KECIL dari satu gelombang (kelompok yang mengulang
   ujian OJT, bukan seluruh angkatan) — residu 744 di 2024 terlalu besar untuk dijelaskan limpasan
   saja.
3. Tidak ada footnote metodologi di SR (sudah dicek halaman sekitar tabel pra-jabatan SR-2025 hal.
   202-204) yang menjelaskan cutoff/batas hitung per tahun.

**Status: mekanisme terbukti nyata (kesaksian langsung), besaran belum terukur.** Kandidat
penjelas TAMBAHAN kecil untuk residu `tidak_diketahui` di 2020/2021/2024 — bukan pengganti
`ikatan_dinas.yaml`, dan tidak diberi angka di `komposisi_jalur` sampai ada cara mengukurnya
(mis. data lulus-vs-mengulang ujian OJT per gelombang, yang tidak kita punya).
Sumber: keterangan langsung user (pengalaman pribadi angkatan Okt 2016); SR-PLN-2025-160726.pdf
hal. 200-204 (dicek, tidak ada footnote metodologi) · Keyakinan: **tinggi** untuk mekanisme
(kesaksian langsung + konsisten dgn `durasi_hari_setelah_tutup` di kohort.yaml), **tidak ada**
untuk besaran · Dampak: tidak mengubah `komposisi_jalur` yang sudah ditulis; jadi catatan
metodologi untuk sesi mendatang kalau ada data ujian-OJT per gelombang.

### F-069 · "5.900 diterima RBB" ternyata KUMULATIF 2022-2024, bukan RBB 2024 saja — dan 1.830 posisi akhirnya tersitasi ⭐⭐ [cek-ricek]
Klaim: dua hal ditemukan sambil menelusuri ulang dari mana angka "54" (porsi PLN di RBB 2024,
`kohort.yaml`) berasal.

**(a) 688 lowongan / 1.830 posisi / 110 BUMN — sekarang tersitasi.** Angka ini dipakai sejak sesi
sebelumnya untuk menghitung "54" tapi TIDAK PERNAH masuk `findings.md` dengan kutipan verbatim —
persis pola yang menjatuhkan F-067(a). Diverifikasi ulang 2026-08-18:

> *"Ia menjelaskan, pelamar dapat menemukan lebih dari 100 BUMN yang membuka 688 lowongan untuk
> 1.830 posisi"* — [Kompas.com, 22 Maret 2024](https://www.kompas.com/tren/read/2024/03/22/193000365/rekrutmen-bersama-bumn-2024-ada-1.830-posisi-lulusan-sma-dan-difabel-bisa)

Dikonfirmasi silang oleh iNews.id ("Rekrutmen Bersama BUMN 2024 Buka 688 Lowongan") dan beberapa
media lain, semua tanggal sekitar 22-24 Maret 2024 (persis saat pendaftaran RBB 2024 dibuka).
**1.830 posisi ini KUOTA/TARGET yang diumumkan di awal, bukan konfirmasi realisasi akhir** —
konsisten dengan pola target>realisasi yang berulang di proyek ini (ITPLN 150→147/135/109, dst).

**Dampak ke `kohort.yaml`:** angka "54" (= 20/688 x 1.830, dibulatkan) ternyata SUDAH memakai
basis yang benar (posisi spesifik RBB 2024, bukan angka lintas-tahun) — kekhawatiran sebelumnya
bahwa satuannya salah TIDAK TERBUKTI. Yang perlu diperbaiki cuma catatan sitasinya (sekarang
tertaut ke Kompas 22 Mar 2024), plus tambah peringatan bahwa 54 kemungkinan sedikit
OVER-estimate (karena 1.830 kuota, bukan realisasi akhir).

**(b) TEMUAN LEBIH BESAR: "5.900 pegawai reguler + 231 disabilitas" (F-041, dan `funnel.yaml`
`rasio_nasional_rujukan: 186`) ternyata KUMULATIF seluruh program RBB/PPB 2022-2024, BUKAN RBB
2024 sendirian** seperti tertulis di F-041 ("RBB 2024 secara total... merekrut 5.900..."). Sumber
sekunder (pencarian 2026-08-18) menyatakan tegas program ini "berjalan dari 2022 sampai 2024"
untuk mencapai total 5.900+231 itu — tiga angkatan RBB digabung, bukan satu.

⚠️ **Konsekuensi ke kalibrasi funnel RBB:** `funnel.yaml` memasangkan **5.900 (kumulatif 3 tahun)**
dengan **±1,1 juta pendaftar (yang tampaknya KHUSUS 2024** — pencarian independen menemukan
1.384.743 pendaftar RBB 2024 per 16 Maret 2024, masih sebelum pendaftaran tutup 17 Maret**)
untuk menghasilkan rasio 1:186. **Itu bandingkan pembilang lintas-tahun dengan penyebut satu-
tahun — jebakan yang sama persis dengan F-039 (1:223, dicampur cakupan Group vs Induk) yang
sudah lebih dulu ditolak di proyek ini (F-047).** Rasio 1:186 kemungkinan keliru, tapi BELUM
diganti — perlu angka realisasi RBB 2024 SENDIRI (bukan kumulatif) untuk kalibrasi ulang, dan
angka itu belum ditemukan di pencarian manapun sejauh ini.

**Status: (a) selesai, `kohort.yaml` tidak perlu diubah, cuma sitasi ditambah. (b) BELUM
diperbaiki** — `funnel.yaml` `funnel_rbb.fhci_agregat` (rasio 1:186, lolos_kumulatif_fhci 0,0196)
tetap dipertahankan APA ADANYA untuk saat ini karena tidak ada pengganti yang lebih baik, tapi
ditandai TIDAK ANDAL sampai angka RBB-2024-murni ditemukan.
Sumber: Kompas.com 22 Mar 2024 (butir a); pencarian web 2026-08-18, sumber sekunder tanpa
kutipan primer resmi FHCI (butir b) · Keyakinan: **tinggi** untuk (a), **sedang** untuk (b)
(pola "kumulatif 2022-2024" konsisten di 2 sumber independen, tapi belum ketemu rilis resmi
FHCI yang menyatakannya eksplisit) · Dampak: `kohort.yaml` komposisi_jalur 2024 (rbb:54) AMAN;
`funnel.yaml` funnel_rbb butuh audit lanjutan sebelum dipakai generator 08.

### F-070 · Infografik resmi FHCI: rincian per-tahun PPB/RBB 2021-2024 — konfirmasi F-069(b) & angka baru untuk 2021/2024 ⭐⭐⭐ [sumber primer, user]
Klaim: user membagikan tangkapan layar infografik resmi dari `fhcibumn.com/program/rekrutmen-
bersama-bumn-rbb-vPteSd` (halaman program RBB milik FHCI sendiri — sumber PRIMER, bukan berita
sekunder), berjudul *"Transformasi Program Rekrutmen: Rekrutmen Bersama BUMN (RBB)"*. Rincian per
tahun:

| tahun | kategori | peserta |
|---|---|---:|
| 2021 | PPB Papua & Papua Barat | **154** |
| 2022 | RBB Reguler batch 1 | 2.297 |
| 2022 | RBB Reguler batch 2 | 805 |
| 2022 | RBB Disabilitas | 137 |
| 2022 | RBB Papua & Papua Barat | 256 |
| 2023 | RBB Reguler | 1.420 |
| 2023 | RBB Disabilitas | 47 |
| 2024 | RBB Reguler | **1.378** |
| 2024 | RBB Disabilitas | 47 |
| **total (semua tahun)** | RBB Reguler | **5.900** |
| **total (semua tahun)** | PPB/RBB Disabilitas | 231 |
| **total (semua tahun)** | PPB/RBB Papua & Papua Barat | 410 |

**Konfirmasi F-069(b):** 2.297+805+1.420+1.378 = **5.900 persis** — membuktikan tuntas bahwa
"5.900" memang kumulatif 4 batch 2022-2024, bukan angka satu tahun. F-069(b) yang tadinya
berstatus "keyakinan sedang, sumber sekunder" sekarang **naik ke tinggi, sumber primer FHCI**.

**Dua angka baru yang mengubah `kohort.yaml`:**
1. **RBB Reguler 2024 = 1.378** (realisasi RIIL nasional, bukan kuota 1.830 dari F-069(a)).
   Porsi PLN dihitung ulang: 20 lowongan PLN / 688 lowongan nasional x 1.378 = **40,1 ≈ 40**
   (turun dari 54). Ini basis lebih baik karena REALISASI, bukan target — konsisten dengan pola
   target>realisasi yang berulang di proyek ini.
2. **PPB Papua & Papua Barat 2021 = 154 peserta NASIONAL (realisasi, bukan target).** Ini
   MENGISI celah yang sebelumnya "TIDAK DIKETAHUI" (F-067: sebelumnya cuma ada "sisa target
   ~250", bukan realisasi). 154 sekarang jadi **batas atas keras** untuk komponen `ppb_papua`
   tahun_program 2021 di `kohort.yaml` (yang saat ini bernilai 49 — masih di bawah 154, jadi
   TIDAK bertentangan, tapi porsi PLN dari 154 tetap belum punya metode penurunan yang solid
   seperti RBB 2024, karena tidak ada data "lowongan PLN" granular untuk PPB 2021 seperti F-043
   punya untuk RBB 2024). Nilai 49 DIPERTAHANKAN apa adanya, tapi keyakinannya dinaikkan sedikit
   karena sekarang punya batas atas yang solid, bukan lagi disandarkan ke angka target.

**Yang TIDAK terjawab infografik ini:** tahun 2020 (PPB Papua realisasi 254, F-067) tidak muncul
di linimasa FHCI ini sama sekali — grafik dimulai dari 2021. Konsisten dengan dugaan bahwa FHCI
menghitung "RBB" sebagai brand yang baru dimulai 2021/2022, sementara PPB 2019/2020 mungkin
di-track terpisah (di luar cakupan infografik "transformasi" ini). Tidak mengubah apa pun untuk
tahun_program 2020.

**Dampak:** `kohort.yaml` tahun_program 2024: rbb 54->40, residu tidak_diketahui 744->758.
`angkatan.yaml` X-02: diterima 744->758, jenjang_sebaran disesuaikan. `funnel.yaml`
`volume_target` dihitung ulang. Tahun_program 2021: tidak ada perubahan angka, cuma keyakinan
ppb_papua naik & catatan diperbarui.
Sumber: [fhcibumn.com/program/rekrutmen-bersama-bumn-rbb-vPteSd](https://fhcibumn.com/program/rekrutmen-bersama-bumn-rbb-vPteSd)
(tangkapan layar dibagikan user 2026-08-18) · Keyakinan: **tinggi** (sumber primer resmi FHCI,
bukan berita sekunder) · Dampak: lihat di atas.

### F-071 · PLN TERNYATA JUGA ikut RBB 2022 & 2023 — data primer dipanen ulang dari arsip Wayback ⭐⭐⭐ [audit induk-vs-subholding + panen primer]
Klaim: audit sistematis seluruh horison (2026-08-18, dipicu temuan 2022 di F-070) menemukan
DUA tahun tambahan (2022, 2023) yang selama ini dilabeli `jalur: mandiri` murni ternyata JUGA
punya partisipasi RBB nyata dari PLN — bukan cuma 2020/2021/2024 seperti diasumsikan sejak F-041.

**(a) RBB 2022 — data granular dipanen langsung, setara F-043.** Endpoint `loadRecord` (sama
seperti yang dipanen F-043 untuk 2024) ternyata terarsip Wayback untuk KEDUA batch RBB 2022:

| batch | snapshot | lowongan nasional | **lowongan PLN** | peserta diterima nasional (F-070) |
|---|---|---:|---:|---:|
| Batch 1 | 13 Apr 2022 | 839 | **9** | 2.297 |
| Batch 2 | 1 Des 2022 | 308 | **0** | 805 |

Disimpan permanen: `knowledge/sources/rbb_fhci/raw_loadRecord_2022b1.json`,
`raw_loadRecord_2022b2.json`. **Batch 1 cocok PERSIS dengan berita** ([Detik, 14-25 Apr
2022](https://finance.detik.com/bumn/d-6047227/rekrutmen-bersama-bumn-2022-ditutup-2-hari-lagi-cek-lowongan-kerja-di-pln)):
9 lowongan PLN ditemukan satu-satu cocok dengan judul yang disebut berita (Assistant Analyst
Pemasaran & Pelayanan Pelanggan, 7x Assistant Engineer bidang Distribusi/Proteksi/Meter/Gardu
Induk). **Batch 2 menunjukkan NOL lowongan PLN dari 87 tenant** — bertentangan dengan
[Kompas, 2 Des 2022](https://www.kompas.com/tren/read/2022/12/02/180000365/rekrutmen-bersama-bumn-2022-dibuka-ini-lowongan-dari-pln-dan-kai)
yang menulis *"Dua BUMN di antaranya yang membuka rekrutmen, yakni KAI dan PLN"* — KAI memang
ada (8 lowongan) di data primer, PLN tidak. Data primer menang (pola sama F-067). Caveat:
snapshot diambil hari pembukaan (1 Des), ada kemungkinan kecil PLN masuk belakangan tapi tidak
ada snapshot lain untuk mengecek.

**(b) RBB 2023 — partisipasi dikonfirmasi PLN sendiri, data granular TIDAK ditemukan.**

> *"PT PLN (Persero) menyediakan lowongan kerja untuk 32 posisi"* — [siaran pers PLN, Mei
> 2023](https://web.pln.co.id/cms/media/siaran-pers/2023/05/pln-buka-32-lowongan-pekerjaan-di-rekrutmen-bersama-bumn-2023/),
> dikonfirmasi silang [Kompas](https://money.kompas.com/read/2023/05/17/212053726/rekrutmen-bersama-bumn-2023-cek-lowongan-kerja-pln-buat-d3-dan-s1),
> [Liputan6](https://www.liputan6.com/bisnis/read/5286487/pln-buka-32-posisi-lowongan-kerja-di-rekrutmen-bersama-bumn-2023-ayo-daftar),
> dan 3 media lain. Pendaftaran 11-20 Mei 2023.

Percobaan memanen data granular (endpoint `loadRecord`) untuk 2023 GAGAL: domain
`rekrutmenbersama2023.fhcibumn.id` nol snapshot; endpoint `loadRecord` di domain utama cuma
terarsip 2× dan keduanya 2022. Ditemukan alternatif: 120 halaman `/job/detail/<id>` terarsip
untuk 2023 — disampel 40, **nol mengandung "PLN"**. **Ini BUKAN bukti negatif**: kalau porsi
PLN 32/>2.000 lowongan nasional (~1,6%), ekspektasi statistik di sampel 40 cuma ~0,6 — nol
sepenuhnya wajar. Berhenti di titik ini; siaran pers PLN sendiri jadi sumber terkuat yang ada.

**(c) Angka final yang dipakai (keputusan user 2026-08-18, BUKAN hasil rasio presisi).**
User eksplisit: *"saat ini kita masih menebak-nebak yg beneran PLN dapat dari RBB ini berapa,
jadi pake angka yg kuberi aja dulu sampai nnti bisa kita konfirm ke tim rekrutmen."*

| tahun | dasar (lowongan = batas bawah) | keputusan user |
|---|---|---:|
| 2022 RBB Reguler | 9 lowongan batch 1 x ~2-3 peserta/lowongan | **30** |
| 2022 RBB Papua & Papua Barat | 256 nasional (F-070) | **51** |
| 2023 RBB | 32 lowongan x ~1-3 peserta/lowongan | **60** |
| 2024 RBB | 20 lowongan (F-043) x realisasi 1.378 (F-070) | **40 (tidak diubah)** |

**Dampak ke `kohort.yaml`:**
- 2022: `komposisi_jalur` jadi rbb(30) + ppb_papua(51) + tidak_diketahui(608, turun dari 639)
- 2023: `komposisi_jalur` BARU — rbb(60) + mandiri(1217). Bedanya dari `tidak_diketahui`:
  sumber 1.217 ini DIKETAHUI (OAP+Diaspora+Maluku, gelombang nyata katalog PLN), cuma
  pemecahan presisinya (berapa dari tiap gelombang vs RBB) belum diverifikasi granular.
- `tahapan.yaml`: `tahap_agregat_fhci.berlaku_tahun` diperluas dari `[2020,2021,2024]` ke
  `[2020,2021,2022,2023,2024]`.
- `00_verifikasi_rules.py`: cek "tahun RBB konsisten" diperbaiki -- sebelumnya menurunkan
  daftar tahun RBB dari field `jalur` mentah (yang cuma bisa "mandiri" ATAU "rbb" per
  tahun), sekarang dari `komposisi_jalur` (yang mengizinkan campuran). Field `jalur` per
  tahun TERBUKTI tidak representatif lagi -- tetap dipertahankan sebagai penanda pola
  funnel/timeline DOMINAN gelombang katalog (dipakai generator 06), bukan klaim sumber
  headcount tunggal.

**Yang masih terbuka:** field `jalur` per tahun (mandiri|rbb, satu nilai) sekarang jelas
konsep yang terlalu sederhana -- RBB & mandiri jalan PARALEL tiap tahun 2020-2024. Belum
diputuskan apakah field ini dipensiunkan sepenuhnya (diganti murni oleh `komposisi_jalur`)
atau dipertahankan sebagai penanda dominan. Juga belum dicoba: apakah 2019/2025 (belum
diaudit ada-tidaknya komponen RBB tersembunyi) perlu direvisi juga.
Sumber: `knowledge/sources/rbb_fhci/raw_loadRecord_2022b1.json`,
`raw_loadRecord_2022b2.json` (panen primer 2026-08-18); Detik 14-25 Apr 2022; Kompas 2 Des
2022; PLN siaran pers Mei 2023 + Kompas/Liputan6 Mei 2023 (butir b); keputusan angka final:
user 2026-08-18 · Keyakinan: **tinggi** untuk keberadaan partisipasi RBB 2022/2023 (multi-
sumber independen), **rendah** untuk besaran porsi PLN persisnya (diakui eksplisit sebagai
taksiran sementara) · Dampak: lihat di atas.

### F-072 · Audit 2019 & 2025 (item terbuka F-071) — 2019 bersih, 2025 belum bisa dinilai ⭐ [cek-ricek]
Klaim: melengkapi audit horison penuh yang diminta F-071, dua tahun tersisa dicek:

**2019 — TIDAK ada komponen RBB/PPB tersembunyi.** PPB Papua (satu-satunya program bersama BUMN
yang eksis periode ini) baru **diinagurasi 22 Februari 2020**; kebijakannya memang diumumkan
Presiden 10 Sep 2019, tapi eksekusi (pendaftaran, tes) baru berjalan sepanjang **2020**, dan
dasar hukumnya (Surat MBU S-165/MBU/03/2020) baru terbit **Maret 2020**. RBB generik sendiri
baru mulai 2021 (sebagai PPB) lalu berganti nama RBB 2022. Kohort `tahun: 2019` (tes 2019 →
masuk 2020, `induk_diterima: 1093`) mendahului semua program ini secara kronologis — tidak ada
yang perlu dikoreksi.

**2025 — RBB 2025 nyata & PLN ikut, tapi kohort 2025 belum bisa dipecah.** RBB 2025 dibuka
resmi (pendaftaran Mar-Jul 2025, ≥2.000 lowongan lintas 100+ BUMN), dan PLN Indonesia Power
konfirmasi berpartisipasi (halaman `career_detail` sendiri di portal `rekrutmenbersama2025.
fhcibumn.id`). **Tapi** `induk_diterima: 1050` untuk kohort 2025 di `kohort.yaml` berstatus
**TURUNAN** ("SR-2026 belum terbit") — bukan headcount nyata. Memecahnya jadi `komposisi_jalur`
sekarang berarti menaksir di atas taksiran (dua lapis dugaan bertumpuk) — ditolak, konsisten
dengan disiplin sitasi sesi ini. **Tindak lanjut:** begitu SR-2026 terbit dan `induk_diterima`
2025 dikoreksi jadi NYATA, cek ulang partisipasi RBB 2025 PLN (kemungkinan bisa panen granular
`loadRecord` dari domain `rekrutmenbersama2025.fhcibumn.id` selagi masih hidup — belum coba,
lihat metodologi F-043/F-071).
Sumber: WebSearch 2026-08-18 (fhcibumn.com/gallery/news RBB-2025 launch; puskib.ummetro.ac.id
sejarah PPB→RBB; antaranews "776 putra putri Papua" re: inagurasi PPB Papua Feb 2020; jadibumn.id
career_detail PLN Indonesia Power RBB 2025) · Keyakinan: **tinggi** (2019 bersih), **tinggi**
(2025 RBB+PLN terjadi) tapi **n/a** untuk besaran (data belum nyata) · Dampak: horison
2019-2025 kini teraudit penuh untuk komponen RBB tersembunyi; item terbuka F-071 selesai.
`kohort.yaml` diberi catatan penanda di kedua entri (2019: audit bersih; 2025: RBB pending
SR-2026) agar tidak diaudit ulang dari nol.

### F-073 · Field `jalur` per-tahun DIPENSIUNKAN — digantikan sepenuhnya oleh penanda per-gelombang ⭐ [keputusan user]
Klaim: menutup item terbuka F-071. Field `jalur` (mandiri|rbb, satu nilai per tahun) di
`kohort.yaml` **dihapus**. Alasannya sudah terbukti sejak F-067/F-071: RBB & mandiri jalan
PARALEL tiap tahun (2020-2024), jadi satu nilai per tahun secara struktural tidak bisa benar
-- ia cuma kebetulan cocok untuk tahun-tahun di mana satu-satunya gelombang KATALOG yang
tampak memang RBB-timed (2020/2021/2024) atau memang mandiri-timed (2019/2022/2023/2025).

**Perbaikan:** konsep "pola funnel/timeline gelombang katalog" (dipakai generator 06 untuk
`jenis_program`, `sumber_rekrutmen`, `umur_maks`) dipindah ke granularitas yang sebenarnya
benar -- **per-gelombang**, bukan per-tahun. Semua 21 gelombang di `angkatan.yaml` (seri utama
+ khusus) sekarang punya `jalur:` eksplisit sendiri (`mandiri` atau `rbb`); sebelumnya cuma
74/75/87/88 yang eksplisit (karena memang gelombang RBB-timed), sisanya diam-diam mewarisi
field kohort yang kini dihapus. `06_gelombang_program_profesi.py:122` diubah dari
`g.get("jalur", info["jalur"])` (fallback ke kohort) jadi `g["jalur"]` (wajib per-gelombang).

**Yang TIDAK berubah:** semua nilai efektifnya. Setiap gelombang mewarisi persis nilai yang
dulu datang dari kohort tahunnya -- audit ini murni pemindahan tempat definisi, bukan koreksi
angka. Diverifikasi: `06_gelombang_program_profesi.py` jalan bersih pasca-perubahan, total
diterima tetap 8.851 = kohort Group, `00_verifikasi_rules.py` semua cek tetap lulus.
Sumber: keputusan user 2026-08-18 (menutup item terbuka F-071) · Keyakinan: tinggi ·
Dampak: `kohort.yaml` kohort_per_tahun_program tidak lagi punya field `jalur`; jangan
dipakai lagi di generator manapun -- pola funnel/timeline sekarang murni properti gelombang
(`angkatan.yaml`), sumber headcount murni properti `komposisi_jalur`.

### F-074 · RBB 2025 dikonfirmasi & dikuantifikasi — 24 lowongan, dimasukkan ke komposisi_jalur meski basis masih TURUNAN ⭐⭐ [keputusan user]
Klaim: menindaklanjuti F-072 (yang menemukan RBB 2025 terjadi tapi tidak menguantifikasi karena
`induk_diterima` 2025 masih TURUNAN). User memutuskan tetap masukkan komponen RBB ke
`komposisi_jalur` 2025 walau basisnya belum NYATA — dua lapis taksiran diakui eksplisit.

**Panen lowongan PLN Group di RBB 2025 (metode berbeda dari F-043/F-071 -- lihat catatan):**

| entitas | lowongan | sumber |
|---|---:|---|
| PT PLN Indonesia Power | **22** | [Arah Pena](https://www.arahpena.com/ragam/77914721985/pt-pln-indonesia-power-di-rbb-bumn-2025-cek-22-posisi-lowongan-kualifikasi-persyaratan-dan-cara-daftar) -- dikonfirmasi 2 kutipan WebSearch independen |
| PT PLN Nusantara Power | **2** | [bersamabumn.com/rbb/pt-pln-nusantara-power](https://www.bersamabumn.com/rbb/pt-pln-nusantara-power/), diverifikasi lewat **snapshot Wayback beku 18 Apr 2025** (di dalam jendela pendaftaran RBB 2025, Mar-Jul) -- bukan data 2026 yang ketumpahan. Isi: Jr Technician Mesin (D3 Teknik Mesin) + Jr Technician Pengendalian Konstruksi (D3 Teknik Sipil), IPK min 3.00, umur maks 27. |
| PT PLN (Persero) sendiri | **0** | bersamabumn.com: "belum ada posisi dibuka" utk RBB -- yang ada cuma Rekrutmen Nasional PLN Group mandiri (1-5 Okt 2025) |
| Nusa Daya/EPI/ES/Icon Plus/Batam/Haleyora | tidak ditemukan | tidak terdaftar di direktori RBB bersamabumn.com -- bukan bukti negatif kuat (situs pihak ketiga, cakupannya tidak lengkap terbukti dari absennya slug Indonesia Power juga padahal Indonesia Power terkonfirmasi ikut lewat sumber lain) |

**Total: 24 lowongan PLN Group.**

⚠️ **Data granular per-lowongan GAGAL dipanen**, beda dari F-043 (2024)/F-071 (2022): situs RBB
2025 (`rekrutmenbersama2025.fhcibumn.id`) ternyata **SPA** (Single Page Application) -- CDX
Wayback punya ratusan snapshot tapi isinya app-shell React kosong (`<title>Wayback Machine</title>`,
tanpa data), karena listing lowongan di-fetch lewat API runtime yang tidak ikut terarsip sebagai
halaman terpisah. Endpoint `loadRecord` (yang berhasil untuk 2022/2024) TIDAK ADA lagi di 2025 --
arsitektur situsnya sudah berubah. Dua kutipan berita/aggregator di atas jadi sumber terkuat yang ada.

**Angka final (keputusan user 2026-08-18):** pola sama F-071 -- lowongan sebagai batas bawah,
~2 peserta/lowongan (median taksiran 2022-2023) → **24 × 2 = 48**. Ditambahkan ke `kohort.yaml`
2025 sebagai `komposisi_jalur`: rbb(48) + mandiri(1002, sisa dari gelombang katalog nyata 91+92).

**Konsekuensi eksplisit dari basis TURUNAN:** beda dari 2020-2024 (yang induk_diterima-nya NYATA
dari SR), 2025 punya DUA lapis dugaan bertumpuk -- total 1.050 itu sendiri proyeksi, porsi RBB
48 di dalamnya proyeksi kedua di atas proyeksi pertama. User eksplisit terima risiko ini demi
mencerminkan bahwa RBB 2025 memang terjadi, bukan diam-diam. Begitu SR-2026 terbit dan
`induk_diterima` dikoreksi ke NYATA, seluruh komposisi ini (bukan cuma porsi RBB) perlu dievaluasi
ulang -- dicatat sebagai TODO di `kohort.yaml`.

**Dampak lain:** `tahapan.yaml` `tahap_agregat_fhci.berlaku_tahun` diperluas dari
`[2020,2021,2022,2023,2024]` ke `[...,2025]` supaya cek konsistensi `00_verifikasi_rules.py`
(tahun RBB kohort vs tahapan) tetap lulus.
Sumber: WebSearch 2026-08-18 (Arah Pena; bersamabumn.com); Wayback CDX + fetch langsung
(`rekrutmenbersama2025.fhcibumn.id` domain dump, `bersamabumn.com/rbb/pt-pln-nusantara-power`
snapshot 20250418002316); keputusan angka final: user 2026-08-18 · Keyakinan: **tinggi**
(keberadaan & entitas partisipasi RBB 2025), **rendah** (besaran 48 -- taksiran eksplisit,
DAN bertumpuk di atas basis 2025 yang sendirinya belum nyata) · Dampak: lihat di atas.

### F-075 · Funnel dipecah jadi dua arketipe (F-064 Sumbu 1 dieksekusi) ⭐⭐ [sesi build]
Klaim: menutup item terbuka F-064 Sumbu 1. `funnel.yaml` `funnel_mandiri` yang semula satu
daftar tahap tunggal dipecah jadi dua arketipe bersarang, dipilih per gelombang lewat
`jenis_program` (dihitung generator 06 dari judul+jalur):

- **`nasional_mandiri`** — bentuk & angka IDENTIK dengan funnel_mandiri lama (jangkar keras
  F-019: 64%/2,05%). Menyerap REGULER, S2, PRO_HIRE, DIASPORA, BIDANG, CAMPUS + `default_residu`
  untuk siluman (`angkatan.yaml` seri.siluman, tidak punya `jenis_program` sendiri).
- **`afirmasi_remote`** (BARU) — dikalibrasi dari Biak 2025 (F-058, satu gelombang terobservasi
  penuh): administrasi lulus 51,5% (tinggi, 2 media independen), akademik_inggris & psikologi
  nyaris tanpa gugur (897/993 hadir, 0 gugur -- tinggi). Tiga tahap tanpa data Biak (adaptif,
  fisik_mcu, wawancara) diberi laju tinggi TURUNAN konsisten-tesis, KECUALI wawancara yang
  disengaja diberi laju lebih ketat (0,55) sebagai titik penyempitan kuota sesungguhnya --
  dialasankan dari bukti tak langsung: Papua 2025 nasional 1.658 lulus administrasi (F-059)
  vs target diterima gelombang 91 = 979 (rasio keseluruhan ~59%, jauh lebih ketat dari tahap
  yang benar-benar terekam). End-to-end hasil rantai: **18,88%** (1:5,3) -- jauh lebih longgar
  dari nasional_mandiri (1:49), TAPI TIDAK dijangkarkan ke angka nasional independen apa pun
  (beda dari nasional_mandiri yang ditutup persis ke F-019) -- ditandai keyakinan campuran,
  bukan angka final presisi.

**Pemilihan arketipe otomatis:** `pemilihan_arketipe.peta` di `funnel.yaml` memetakan tiap
`jenis_program` ke arketipe. AFIRMASI (OAP/Papua/Maluku & Nusa Tenggara) -> afirmasi_remote;
enam kode lain -> nasional_mandiri (DIASPORA dan BIDANG/CAMPUS default konservatif karena
tidak ada data khusus jalur itu).

**Verifikasi:** `00_verifikasi_rules.py` [2] direstruktur -- `rantai_arketipe()` menguji rantai
perkalian KEDUA arketipe (nasional_mandiri wajib mendarat di jangkar F-019; afirmasi_remote
cuma wajib konsisten-diri + terbukti jauh lebih longgar), plus cek kosakata tahap sama &
peta hanya menunjuk arketipe yang ada. `00b_verifikasi_keluaran.py` dapat cek baru: tiap
`jenis_program` yang MUNCUL NYATA di `profesi.csv` (selain RBB) harus punya entri di peta --
kalau generator 06 memunculkan kode baru tanpa dipetakan, cek ini gagal (diuji: ketujuh kode
non-RBB yang benar-benar muncul semua terpetakan). Generator 06 dijalankan ulang, `00` dan
`00b` dua-duanya SEMUA CEK LULUS, angka kohort tidak berubah (8.851 tetap).
Sumber: F-058, F-059, F-061 (data funnel); F-064 (resolusi/keputusan sebelumnya) · Keyakinan:
tinggi (nasional_mandiri, tidak berubah dari sebelumnya), campuran (afirmasi_remote -- 3 dari
6 tahap terverifikasi, 3 turunan) · Dampak: `funnel.yaml` siap dipakai generator 08 (kandidat
& pendaftaran per tahap) tanpa lagi over-determined oleh satu funnel nasional tunggal.

### F-076 · 10 gelombang tanpa tgl_tutup diisi -- 3 dari sumber nyata, 7 taksiran median jendela ⭐ [sesi build]
Klaim: menutup item terbuka poin [1] audit generator 06 ("10 dari 19 gelombang tidak punya
tgl_tutup"). Dua kelompok:

**Nyata (3 gelombang) -- tanggal SUDAH ada di catatan lain, cuma belum diwiring ke kolom
terstruktur:**
- G2019-072 (Reguler gel. III): siaran pers PLN "Cari Talenta Unggul, PLN Buka Rekrutmen di
  7 Kota", pendaftaran 7-20 Sep 2019 (sudah tercatat di `konfirmasi_berita`, F-063)
- G2021-075 (Papua & Papua Barat 2021): Kompas 24 Des 2021, pendaftaran 23 Des 2021 - 14 Jan
  2022 (sudah tercatat di field `pendaftaran`, F-063)
- G2024-087 (RBB 2024 batch I): 23 Mar - 1 Apr 2024 (sudah tercatat di field `pendaftaran`, F-046)

**Taksiran (7 gelombang) -- cuma bulan yang diketahui atau gelombangnya sendiri shell/diragukan:**
G2019-007/070/071/073 (Pro Hire + Reguler gel I/II + S2 Career Evening -- cuma bulan dari
snapshot Wayback), G2022-079/080 (shell 100% sintetis, F-071), G2024-088 (RBB batch II, F-063:
eksistensinya sendiri belum terbukti). Diberi tanggal **median jendela pendaftaran nyata**
lintas 13 gelombang bertanggal lengkap di horison (4-22 hari, median **10 hari**) -- hari-dalam-
bulan dipilih tanggal 15 (titik tengah, bukan klaim presisi), tutup = buka+10.

**Implementasi:** `angkatan.yaml` tiap gelombang kini punya `tgl_status: nyata|estimasi` +
(untuk yang bulan-saja) field `tgl_buka`/`tgl_tutup` terpisah dari `buka` -- `buka` TETAP
bulan-saja untuk 2019 karena generator 06 memakainya untuk mencocokkan judul arsip Wayback
per-bulan (`per_bulan` dict, regex `\d{4}-\d{2}` ketat); mengubah presisinya akan MEMATAHKAN
pencocokan itu (ditangkap sebelum commit -- lihat "Errors and fixes"). `06_gelombang_
program_profesi.py` dapat fungsi `tgl_rencana()` yang membaca tanggal presisi-penuh dari
`buka`/`tutup` kalau ada, else fallback ke `tgl_buka`/`tgl_tutup`. Kolom baru `tgl_status`
ditambahkan ke gelombang.csv/program.csv/profesi.csv (nyata/estimasi), roll-up gelombang
memakai status TERBURUK di antara profesinya. `00b_verifikasi_keluaran.py` dapat 2 cek baru:
nol gelombang tanpa tanggal, dan pelaporan (bukan gagal) berapa yang estimasi -- hasil saat
ini **7/19 gelombang pakai tanggal ESTIMASI**, sisanya nyata dari sumber primer.
Sumber: F-063 (siaran pers Sep 2019, Kompas Des 2021), F-046 (RBB 2024), median dihitung dari
13 jendela nyata di `angkatan.yaml`/`gelombang.csv` · Keyakinan: tinggi (3 nyata, sumber sudah
tersitasi sebelumnya), rendah-disengaja (7 taksiran, ditandai eksplisit `tgl_status`) · Dampak:
gelombang.csv sekarang 0/19 tanpa tanggal (dari 10/19 sebelumnya); dashboard WAJIB tampilkan
badge "estimasi" memakai kolom `tgl_status` baru, jangan tampilkan tanggal taksiran seolah pasti.

### F-077 · Generator 07 (kota/UPDL/vendor/tahap_ref) -- 1 vendor real, 9 DIMODELKAN dgn nama perusahaan real [sesi build]
Klaim: langkah 07 HANDOFF ("vendor & lokasi seleksi") murni memateriali­sasi master yang
sudah ada aturannya -- **kota** (43, sudah di `tahapan.yaml` sejak fondasi) dan **UPDL**
(11, sudah nyata di `unit_pelaksana.csv` via `jenis_unit=UPDL`) tidak butuh keputusan baru,
tinggal difilter/ditulis ulang jadi `kota.csv`/`updl.csv`. Yang butuh keputusan baru:
**vendor** psikologi & fisik/MCU (pemilik_proses=VENDOR di `tahapan.yaml`).

Satu-satunya vendor bernama yang muncul di sumber tersitasi: **"Klinik Prodia, Medan"**
(F-061, blog rekrutmen 2015, tes fisik & lab). Sistem asli PLN tidak menyimpan daftar
vendor per kota untuk tahap ini (domain operasional vendor, bukan HTD -- pola sama F-017).
9 vendor lain di `rules/vendor.yaml` **DIMODELKAN**: dipilih nama perusahaan yang **memang
real** dan bergerak di jasa lab-kesehatan (Prodia cabang lain, Kimia Farma Diagnostika) atau
assessment psikologi (LPT UI, Daya Dimensi Indonesia, UPAC PLN Corporate University, Bina
Talenta) di Indonesia -- bukan nama karangan -- ditempatkan di `kota_offline_utama` (F-024:
Jakarta, Medan, Surabaya, Makassar, Palembang, Balikpapan). Setiap baris DIMODELKAN ditandai
`status_sumber` + catatan penjelas kenapa nama itu masuk akal untuk peran tsb.

Penugasan vendor→kota→kandidat per tahap BUKAN bagian langkah 07 (murni tabel master) --
itu langkah 09 (tahapan seleksi). `catatan_penunjukan` di `vendor.yaml` sudah menuliskan
aturan sementara: kota_terkunci = kota_basis vendor dapat vendor itu; kota lain pakai
vendor `kota_basis: nasional` (VEND08/VEND09 psikologi) atau vendor fisik_mcu terdekat
(fisik_mcu belum punya cadangan nasional eksplisit -- keputusan lokasi per-kota didorong
ke langkah 09, ditandai DIMODELKAN di sana).

Verifikasi: `00_verifikasi_rules.py` cek [12] baru (kode tak kembar, tipe_layanan valid,
tahap VENDOR di `tahapan.yaml` cocok dgn tipe vendor yang ada, vendor nyata wajib
rujukan). `00b_verifikasi_keluaran.py` cek baru (kota=43, updl=11 & persis subset
`unit_pelaksana.csv`, vendor tak kembar & DIMODELKAN wajib catatan, tahap_ref=16 & kode
seleksinya cocok `funnel.yaml`) + penjaga PII diperluas (`updl.csv:nama_lengkap` adalah
nama UNIT, bukan orang -- pengecualian sama seperti `unit_pelaksana.csv`).
Sumber: F-061 (Prodia) · Keyakinan: tinggi (Prodia, kota, UPDL -- semua dari data
tersitasi/nyata), rendah-disengaja (9 vendor lain, `status_sumber: DIMODELKAN` eksplisit)
· Dampak: `out/master/` bertambah `kota.csv`(43), `updl.csv`(11), `vendor.csv`(10),
`tahap_ref.csv`(16); `00` dan `00b` dua-duanya SEMUA CEK LULUS; siap jadi basis
penugasan tahap offline di langkah 09.

### F-078 · Generator 08 (kandidat & pendaftaran) -- administrasi dijalankan sungguhan, bukan diundi; ikatan dinas dikeluarkan dari pendaftaran [sesi build]
Klaim: `08_kandidat_pendaftaran.py` membangkitkan 368.912 akun kandidat & 218.928 baris
pendaftaran, dengan dua penyesuaian penting yang TIDAK ADA di `profesi.csv` (langkah 06)
apa adanya:

**(1) Ikatan dinas dikeluarkan dari basis penghitungan pendaftar.** `profesi.csv.
diterima_target` berjumlah 8.851 (= seluruh kohort Group), tapi itu KELIRU dipakai
langsung sebagai basis "berapa yang mendaftar" -- `funnel_ikatan_dinas.pendaftaran:
tidak_ada` (peserta ikatan dinas diseleksi lewat jalur kampus, tak pernah menyentuh
portal rekrutmen PLN). Ternyata `diterima_target` per profesi MENCAMPUR ikatan dinas
ke profesi katalog nyata tanpa penanda (warisan langkah 06: `target = induk_diterima +
sub_diterima` per tahun, dan `induk_diterima` kohort.yaml sendiri sudah termasuk
komposisi ikatan dinas). Langkah 08 mengurangi porsi ikatan dinas per tahun (2020:200,
2021:640, 2024:300 = total 1.140, dari `kohort.yaml.komposisi_jalur`) secara
proporsional dari `diterima_target` sebelum dibalik jadi jumlah pendaftar --
hasilnya **7.711**, PERSIS sama dengan `funnel.yaml.status_per_15sep2026.lulus_
wawancara`. Diuji otomatis di `00b_verifikasi_keluaran.py`.
⚠️ **Catatan residual yang TIDAK diperbaiki** (di luar cakupan langkah 08): pembagian
`sumber_rekrutmen` (mandiri/rbb) di level profesi.csv (6.259/2.592) TIDAK cocok dengan
pembagian jalur sesungguhnya di `kohort.yaml.komposisi_jalur` (mandiri 6.951/rbb 760) --
tahun bergelombang tunggal (2020, 2021) berlabel `rbb` di katalog membawa SELURUH
kursi tahun itu (termasuk `tidak_diketahui`/siluman yang seharusnya arketipe
`nasional_mandiri`) sebagai `rbb`. Ini warisan sumbu-2 F-064 yang butuh perbaikan di
langkah 06 kalau mau ditutup persis; langkah 08 memakai tag `sumber_rekrutmen` apa
adanya per profesi (jadi total pendaftar RBB sedikit membengkak, mandiri sedikit
menyusut, dibanding rincian funnel.yaml) -- volume total & angka DITERIMA tidak
terpengaruh, cuma komposisi jalur di level pendaftar granular.

**(2) Administrasi (jalur mandiri) dijalankan SUNGGUHAN, bukan diundi dari target 64%.**
Biodata (umur, IPK, prodi, status kawin, kelengkapan berkas) dibangkitkan dulu dari
`demografi.yaml` (dikalibrasi supaya laju lulus ALAMI mendekati jangkar F-019), lalu
kriteria `administrasi.yaml` (umur_maks per jalur+jenjang dari `profesi.csv`, IPK
minimal per prodi dari `profesi_prodi.csv`, kesesuaian jurusan, status BELUM MENIKAH,
kelengkapan berkas per tahun) diperiksa PER KANDIDAT PER PENDAFTARAN sungguhan --
`alasan_gagal` (boleh >1) adalah hasil pemeriksaan nyata, bukan label tempelan. Hasil
aktual: laju gagal administrasi 32,7% (target 36%, selisih 3 poin -- sepola dengan
toleransi yang sudah diterima di F-075 funnel afirmasi). Persis `diterima_pendaftaran`
dipilih dari kolam lulus-administrasi sebagai DITERIMA (jangkar keras); sisa lulus-
administrasi disebar ke tahap berikutnya (adaptif..wawancara) memakai proporsi
`multiplier_lulus` funnel arketipe (nasional_mandiri/afirmasi_remote, F-075). Jalur RBB
tidak dites administrasi PLN sama sekali (titik masuk akademik_inggris, F-046) --
langsung disebar 4 tahap PLN via proporsi `funnel_rbb`.
🐛 **Bug tertangkap & diperbaiki sebelum commit:** percobaan pertama memakai gender
KANDIDAT dari target `diterima_per_tahun_program` (65:35..86:14) alih-alih baseline
`gender.pelamar` (62:38) + `variasi_per_bidang` -- persis pelanggaran yang diperingatkan
demografi.yaml ("jangan paksa target di sisi pelamar"). Hasilnya 76:24 P:W di seluruh
kandidat, jauh dari wajar. Diperbaiki: gender kini EMERGENT dari bidang prodi yang
disampel per slot (TEKNIK 82% P, NON-TEKNIK 45% P, campuran 62% P baseline) --
hasil akhir 63,4% P, dalam rentang wajar. Bug kedua: fallback "profesi tanpa entri
`profesi_prodi.csv`" (96 dari 219 profesi) awalnya menandai SEMUA pelamarnya
`jurusan_tidak_sesuai` (polaritas terbalik -- seharusnya "tak ada acuan buat dinilai
salah" bukan "otomatis salah"), yang menaikkan laju gagal administrasi ke 74% sebelum
diperbaiki.
Sumber: F-019/F-047 (jangkar funnel), F-064/F-075 (arketipe), F-046 (RBB), demografi.yaml/
administrasi.yaml/kelengkapan.yaml (kalibrasi biodata) · Keyakinan: sedang (mekanisme &
jangkar keras diuji otomatis; distribusi alasan_gagal individual menyimpang dari bobot
target administrasi.yaml -- lihat catatan di kode, diterima sebagai variasi wajar N kecil
per profesi, tidak dikejar presisi per-alasan) · Dampak: `out/master/` bertambah
`kandidat.csv`(368.912), `pendaftaran.csv`(218.928), `kandidat_pendidikan.csv`(~1,07jt),
`kandidat_sertifikasi.csv`(~146rb), `kandidat_keluarga.csv`(~366rb),
`kandidat_berkas.csv`(~1,35jt); `00b_verifikasi_keluaran.py` dapat blok cek baru + penjaga
PII diperluas (kandidat.csv/kandidat_keluarga.csv SENGAJA berbentuk PII sintetis 100% --
dikecualikan dari guard kolom/nilai, diganti cek bahwa generatornya sendiri tidak pernah
membaca sumber PII asli).

### F-079 · Generator 09 (tahapan seleksi) -- baris per-tahap dijabarkan dari hasil final langkah 08, bukan mengundi ulang siapa lulus [sesi build]
Klaim: `09_seleksi_tahap.py` membangkitkan 464.688 baris `seleksi_tahap.csv` (per
pendaftaran x tahap yang benar-benar dicapai) + 9 baris `seleksi_tahap_agregat.csv`
(FHCI, tanpa nama, HANDOFF butir 3b), TANPA mengubah lagi siapa DITERIMA/GAGAL --
itu jangkar keras yang sudah final dari `pendaftaran.csv` (langkah 08,
`tahap_gugur`/`hasil_akhir`). Langkah ini murni menjabarkan angka itu jadi
perjalanan per-tahap:

**(1) Tahap yang dicapai = urutan tahapan.yaml sampai persis di `tahap_gugur`
(atau seluruhnya kalau DITERIMA).** Jalur mandiri mulai dari `administrasi` (6
tahap); jalur RBB mulai dari `akademik_inggris` (4 tahap PLN, F-046) -- tahap FHCI
di depannya tidak per-kandidat, direkap di `seleksi_tahap_agregat.csv` dgn metode
mundur dari jumlah serah-terima AKTUAL (bukan taksiran pra-generate
`pelamar_fhci_porsi_pln` di funnel.yaml yg TEBAKAN): `jumlah_lulus` tiap tahap FHCI
dihitung dari `lulus_pct` (0,40/0,28/0,175) mundur dari titik akhir (jumlah
pendaftaran RBB nyata per tahun_program), sehingga akurat terhadap data yang benar-
benar dibangkitkan, bukan estimasi lama. Hasil: 3 tahun berjalur RBB di data
aktual (2020/2021/2024, sesuai `sumber_rekrutmen` per profesi -- lihat catatan
residual F-078 soal tag ini tidak 100% cocok komposisi_jalur asli).
**(2) Tahap yang SUDAH dilalui (sebelum titik gugur) selalu HADIR+LULUS** --
konsisten dengan fakta pendaftaran.csv (kalau tidak lulus tahap itu, tidak akan
sampai ke tahap berikutnya). **Di titik gugur sendiri**, HADIR vs TIDAK_HADIR
diundi dari rasio no-show relatif (`(1-hadir_pct)/(1-hadir_pct*lulus_pct)`,
funnel.yaml per tahap/arketipe) -- supaya "gagal karena tidak datang" tidak
disamakan begitu saja dengan "hadir tapi gagal tes".
**(3) Skor 100% DIMODELKAN** (F-028: tidak ada passing grade di regulasi manapun),
dikalibrasi supaya konsisten dgn ambang `tahapan.yaml.passing_grade` DAN dengan
hasil LULUS/GAGAL yang sudah final dari langkah 08 (skor lulus selalu >= ambang,
skor gagal selalu < ambang). Tahap kategorikal (psikologi/fisik_mcu/wawancara)
diberi label (DISARANKAN/FIT/dst), bukan skor mentah -- cocok dgn F-017 (sistem
asli memang cuma simpan lulus/gagal).
**(4) Kota tes & vendor dikunci SEKALI per pendaftaran** (F-024, lokasi tes
terkunci saat daftar) dan dipakai ulang di semua tahap offline pendaftaran itu.
Profesi berkota spesifik (afirmasi 3T) memakai kota itu; profesi "Seluruh
Indonesia" disebar 80% ke 6 kota offline utama (Jakarta/Medan/Surabaya/Makassar/
Palembang/Balikpapan -- persis cakupan kota_basis vendor.csv) + 20% ke 43-kota
penuh. Vendor dipilih cocok kota kalau ada (fisik_mcu 6 vendor, 1/kota); psikologi
2 vendor "nasional" jadi fallback kalau kota tak match.
Diuji: `wawancara.hasil==LULUS` dijumlah persis = `DITERIMA` di pendaftaran.csv
(7.711=7.711); tiap pendaftaran GAGAL berhenti tepat 1x di tahap terakhirnya (tak
ada gugur ganda/di tengah); titik masuk sesuai jalur. Semua diuji otomatis di
`00b_verifikasi_keluaran.py`.
⚠️ **Simplifikasi yang disengaja, tidak dikejar presisi lebih jauh:** (a) skor
disimpan sebagai satu `skor_total`/`kategori_hasil` per tahap, bukan per-komponen
(tahapan.yaml mencatat `komponen`, mis. wartegg/pauli_kraepelin/papi_kostick utk
psikologi) -- dashboard cukup dilayani level tahap; (b) `buta_warna_wajib_lulus_
untuk: [TEKNIK]` (tahapan.yaml) TIDAK ditegakkan silang ke field `buta_warna`
kandidat.csv, karena `bidang` pekerjaan (Distribusi/Transmisi/dst) belum ada
sebagai kolom di profesi.csv (beda taksonomi dari `bidang` prodi TEKNIK/NON-TEKNIK
yang sudah dipakai administrasi) -- kalau field itu ditambahkan di langkah
berikutnya, konsistensi ini bisa ditutup.
Sumber: tahapan.yaml (kosakata tahap, passing_grade, kehadiran), funnel.yaml
(hadir_pct/lulus_pct per arketipe & RBB), kohort.yaml (durasi_hari_setelah_tutup) ·
Keyakinan: tinggi (mekanika & jangkar keras diuji otomatis; skor & kota/vendor
DIMODELKAN sesuai peringatan tahapan.yaml sendiri) · Dampak: `out/master/`
bertambah `seleksi_tahap.csv`(464.688), `seleksi_tahap_agregat.csv`(9);
`00b_verifikasi_keluaran.py` dapat blok cek baru.

### F-080 · Generator 10 (pasca-seleksi) -- kontrak/SAMAPTA/pembidangan/OJT/SK dipotong tepat di `tanggal_sekarang`, bukan diasumsikan semuanya sudah selesai [sesi build]
Klaim: `10_pasca_seleksi.py` membangkitkan 49.977 baris `pasca_tahap.csv`, satu baris
per (pendaftaran DITERIMA x tahap `tahapan.yaml.tahap_pasca` yang SUDAH terjadi
pada tanggal potong 2026-09-15). Jangkar keras: hanya 7.711 pendaftaran `hasil_akhir
== DITERIMA` (persis sama dengan jangkar F-079) yang diproses; kedua jalur
(mandiri/rbb) memakai kosakata pasca yang SAMA tanpa percabangan (HANDOFF butir 4b
poin 2 -- "setelah serah-terima, RBB memakai pipeline PLN yang identik").
**(1) Tanggal tiap tahap = `tgl_tutup` profesi + offset dari
`kohort.yaml.durasi_hari_setelah_tutup`.** Untuk tahap bertitik-tunggal
(pengumuman_akhir, ttd_kontrak, samapta, pembidangan, ujian_ojt, sk_penempatan)
offset diundi uniform dalam rentang `[mulai,selesai]` (persis pola langkah 09) --
kalau rentangnya satu titik (mulai==selesai) hasilnya otomatis deterministik.
**(2) OJT beda perlakuan.** `durasi.ojt = {mulai:195, selesai:375}` (rentang 180
hari) BUKAN jendela sampling sekali-titik seperti tahap lain -- ia adalah tanggal
MULAI & SELESAI program itu sendiri (prajabatan berjalan sbg KELAS/kohort, 30-60
orang/UPDL, bukan per-individu -- HANDOFF §6 keputusan "batas ±500/angkatan
dilepas"). Diverifikasi persis: gelombang 2025 (tutup 2025-10-05) menghasilkan
`ojt_mulai=2026-04-18`, `ojt_selesai=2026-10-15` -- SAMA PERSIS dengan angka yang
sudah didokumentasikan manual di `kohort.yaml §2b.status_pada_tanggal_potong`
sebelum generator ini ditulis (bukan dicocokkan mundur).
**(3) Pemotongan di tanggal_sekarang (F-018, "diterima != sudah jadi pegawai").**
Iterasi tahap_pasca berurutan; begitu satu tahap jatuh SETELAH 2026-09-15, loop
berhenti -- tahap itu dan seluruhnya sesudahnya TIDAK ditulis (bukan ditulis dengan
status "BELUM" kosong, supaya tabel tidak perlu kolom NULL masif). Untuk OJT
spesifik: kalau tanggal potong jatuh DI DALAM jendela mulai-selesai, statusnya
`BERJALAN` dengan `progres = (tanggal_sekarang - mulai)/(selesai - mulai)`, dan
loop berhenti di situ (ujian_ojt/sk_penempatan belum ditulis). Hasil generate:
5.711 pendaftaran sudah ber-SK (pegawai penuh), 2.000 sedang OJT progres
0,83-0,91 (tergantung tgl_tutup persis profesinya) -- angka 2.000 ini SEJALAN
dengan narasi manual "±2.000 orang sudah kontrak tapi belum SK" di
`kohort.yaml §2b`, dan seluruh sisa gelombang 2025 (angkatan 91/92) adalah SATU-
SATUNYA tahun yang OJT-nya masih berjalan (diverifikasi: `tahun_program` &
`angkatan` OJT BERJALAN semuanya {2025}/{91,92}) -- persis klaim dokumen.
`urutan` kolom melanjutkan dari `seleksi_tahap.csv` (1-6) jadi 7-13, supaya
perjalanan lintas dua tabel punya satu deret urutan tunggal.
Diuji (`00b_verifikasi_keluaran.py`): tiap pendaftaran menempuh tahap_pasca sbg
PREFIKS berurutan tanpa lompat; sk_penempatan hanya muncul kalau ketujuh tahap
sebelumnya lengkap; OJT BERJALAN selalu jadi baris TERAKHIR pendaftaran itu;
progres selalu [0,1] dan selalu 1,0 utk tahap non-OJT. Determinisme diuji manual
(hash MD5 identik lintas 2x jalan, seed tunggal 20260915).
Sumber: tahapan.yaml (tahap_pasca), kohort.yaml (durasi_hari_setelah_tutup,
tanggal_sekarang, §2b status_pada_tanggal_potong sbg angka pembanding) ·
Keyakinan: tinggi (mekanika & jangkar keras diuji otomatis; tanggal & progres
COCOK PERSIS dgn contoh manual yang sudah didokumentasikan sebelum kode ditulis) ·
Dampak: `out/master/` bertambah `pasca_tahap.csv`(49.977); `00b_verifikasi_
keluaran.py` dapat blok cek baru.

### Catatan penamaan "Analyst/Engineer" vs DAPEG
Gemini + LinkedIn menunjukkan istilah "Analyst"/"Engineer" dipakai kolokial (mis. "Assistant Analyst
Logistik at PLN UIP JBB"), tapi **posisi FORMAL di DAPEG (April 2026, 37rb pegawai) = Officer/
Technician/Specialist** (0 "Analyst"). Untuk mock: posisi formal holding pakai nama DAPEG; yg dipilih
pelamar = "minat profesi" (bidang, dari `profesi.csv`). Subholding (di luar DAPEG) mungkin pakai
konvensi Analyst/Engineer — tapi kita model ringkas.

### Catatan R5 (seleksi.pln.co.id)
3 gambar di `referensi/seleksi pln co id/` = **duplikat WA0026/0028/0029** (view admin
rekrutmen.pln.co.id), bukan seleksi.pln.co.id. Per Willy (F-018) seleksi.pln.co.id hanya modul tes
akademik & Inggris. → R5 tak menambah material baru; tercakup R4. Tidak ada screenshot seleksi asli.

---

## Keputusan yang menunggu (DECISION)

### DECISION-01 · Cakupan = PLN Group ✅ DIPUTUSKAN (2026-08-16)
Dikunci ke **PLN Group** dengan pola **"holding kaya, subholding ringkas"**:
- **Holding**: detail penuh — unit induk → unit pelaksana → posisi (dari DAPEG, sudah ada).
- **Subholding/Anak Perusahaan** (Indonesia Power, Nusantara Power, Nusa Daya, EPI, PLN ES, Icon Plus):
  cukup di level **nama perusahaan + bidang + jumlah**, tanpa struktur unit internal.
Alasan: sesuai definisi resmi (F-012), data asli (F-002/F-003), dan bentuk `profesi.csv`.
Konsekuensi ke mockdb: `mockdb/README.md` (yg tertulis "holding saja") harus diupdate saat mockdb dilanjut.
