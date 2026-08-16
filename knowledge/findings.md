# Findings — Riset Rekrutmen PLN

Store fakta tersuling lintas sumber. Format tiap entri: klaim · sumber · keyakinan · tanggal · dampak.
Sumber: **R1** situs rekrutmen, **R2** perdir, **R3** web, **R4** chat HTD, **R5** seleksi.

---

### F-001 · Katalog program rekrutmen bisa diambil utuh & asli
Klaim: `rekrutmen.pln.co.id/vacancy/site/index` memuat **31 program** (2020–2025), server-rendered,
4 halaman. Tiap program: judul, jenjang, lokasi tes, minat profesi, program studi, tgl buka/tutup,
status, + PDF brosur. Semua field terisi 31/31.
Sumber: R1 (scrape 2026-08-16, `sources/rekrutmen_pln/programs.csv`) · Keyakinan: **tinggi** · Dampak: **nama & struktur program/angkatan pakai data asli, bukan karangan.**

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
Tahun yang muncul di situs: 2020, 2022, 2023, 2025 (2021 & 2024 tidak muncul — kemungkinan tak
dipublish/tak ada gelombang).
Sumber: R1 · Keyakinan: sedang (ketiadaan 2021/2024 belum tentu berarti tak ada rekrutmen) · Dampak: kalibrasi tanggal & jumlah angkatan per tahun.

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

### F-011 · [IDE RISET] Kemungkinan ada angkatan yang dihapus dari web
Klaim: katalog situs (31 program) mungkin **tidak lengkap** — pengumuman angkatan bisa dihapus
setelah selesai. Tahun 2021 & 2024 kosong di situs; bisa jadi memang tak ada gelombang, atau sudah
dihapus. Rencana verifikasi (nanti): telusuri socmed PLN yang dulu dipakai announce pembukaan
(IG @pln, @pln_corpu, @pln_persero, dll) untuk menemukan gelombang yang pernah dibuka tapi hilang dari web.
Sumber: usul user · Keyakinan: hipotesis · Status: **belum dieksekusi** · Dampak: kelengkapan daftar angkatan historis.

### F-009 · Struktur kode profesi
Klaim: profesi 2025 berkode `{SUBHOLDING}.{TIPE}.{JENJANG}[.varian]`:
SUBHOLDING = IP (Indonesia Power), NP (Nusantara Power), ND (Nusa Daya), ES (Electricity Services),
ICON (Icon Plus), PLN (PLN Persero); TIPE = UM (Umum), OAP (Orang Asli Papua), HK (Hukum),
S2EX (S2 Experienced). Contoh: IP.UM.D3, ND.UM.S1, PLN.OAP.S1, S2EX.HK. Program lama (2022–23)
pakai kode numerik `{n}.{m}` (4.8, 3.1, ICON.14).
Sumber: R1 · Keyakinan: tinggi · Dampak: skema `kode_profesi` mockdb + konfirmasi daftar subholding penempatan.

### F-010 · Granularitas: 1 program → banyak profesi
Klaim: 31 program → **128 profesi**. Tiap profesi = (jenjang × rumpun jurusan × penempatan) dengan
tanggal, kota, angkatan, kode, program studi, dan **minimal IPK per jurusan** sendiri (mis. Teknik
min 3, non-teknik/OAP min 2.5). Data di `profesi.csv`.
Sumber: R1 · Keyakinan: tinggi · Dampak: unit granular pendaftaran = profesi, bukan program. Min IPK per jurusan → rules administrasi mockdb.

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
