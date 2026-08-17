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

### F-041 · Jalur PPB/RBB menjelaskan tahun kosong 2021 & 2024 [R1c+R3]
Klaim: **2021 = PPB (Program Perekrutan Bersama)**, **2022–2024 = RBB (Rekrutmen Bersama BUMN)**
diselenggarakan **FHCI**, dan PLN ikut serta bersama Pertamina/Mandiri/BRI/KAI dll. Pengumuman RBB
ada di `rekrutmenbersama.fhcibumn.id`, **bukan** di situs rekrutmen PLN → karena itu 2021 & 2024
kosong di katalog PLN. Jejaknya tetap terlihat: arsip memuat *"REKRUTMEN PPB BUMN KHUSUS PUTRA
PUTRI PAPUA"*. RBB 2024 secara total (semua BUMN) merekrut 5.900 pegawai reguler + 231 disabilitas.
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
Keyakinan: tinggi · Dampak: aturan wajib di generator penempatan OJT & SK — hanya JUNIOR OFFICER/
JUNIOR TECHNICIAN (dan OFFICER/TECHNICIAN untuk Pro Hire/experienced), **tidak pernah** struktural.

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
> **Belum terpanen:** PPB 2021 & edisi RBB lain — percobaan CDX berikutnya kena *rate limit*
> archive.org (respons kosong), **bukan** bukti arsipnya tak ada. Bisa dicoba ulang lain waktu.

### Catatan penamaan "Analyst/Engineer" vs DAPEG
Gemini + LinkedIn menunjukkan istilah "Analyst"/"Engineer" dipakai kolokial (mis. "Assistant Analyst
Logistik at PLN UIP JBB"), tapi **posisi FORMAL di DAPEG (April 2026, 37rb pegawai) = Officer/
Technician/Specialist** (0 "Analyst"). Untuk mock: posisi formal holding pakai nama DAPEG; yg dipilih
pelamar = "minat profesi" (bidang, dari `profesi.csv`). Subholding (di luar DAPEG) mungkin pakai
konvensi Analyst/Engineer — tapi kita model ringkas.

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
Klaim (Sustainability Report, PLN Induk): **peserta diklat prajabatan** = ukuran kohort rekrutmen
sebenarnya → **2022: 689 · 2023: 689 · 2024: 1.277 · 2025: 1.098**.
Sedangkan **"pegawai baru direkrut"** (= resmi diangkat/SK tahun berjalan) → **2024: 663** (494P/169W);
**2025: 76** (57P/19W). Laporan tidak menjelaskan selisihnya, tapi cocok dengan **jeda pipeline** kita:
seleksi thn N → prajabatan → OJT → SK thn N+1 (mis. gelombang Okt-2025 baru diangkat 2026).
Sumber: R6 (SR-2024 hal. 239; SR-2025 hal. 203) · Keyakinan: tinggi (angka), sedang (tafsir selisih) ·
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
