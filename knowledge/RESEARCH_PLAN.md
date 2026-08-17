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

## 8. Sumber tambahan yang ditemukan di tengah riset

| Kode | Sumber | Kenapa berharga | Status |
|---|---|---|---|
| **R1c** | **Wayback Machine** (web.archive.org) | Situs PLN menghapus pengumuman angkatan lama. Arsip 2017–2026 memulihkan judul program yang hilang | ✅ 111 program (80 baru) |
| **R1-login** | Area member rekrutmen.pln.co.id | Satu-satunya sumber **skema biodata/CV asli** | ✅ selesai; PII dibersihkan |
| **R3-situs** | Halaman FAQ + Info Rekrutmen/artikel | Mekanisme akun, cancel lamaran, jalur campus hiring | ✅ |
| **R6** | Laporan **Statistik PLN** 2014–2025, Annual Report 2014–2025, Sustainability Report 2022–2025 | Runtun waktu jumlah pegawai → kalibrasi attrition & kebutuhan rekrutmen | ✅ SR-2024/2025 + Statistik 2020–2024 |
| **R6b** | Sustainability Report **2022 & 2023** | Tiap SR memuat tabel komparatif 3 tahun → menjangkarkan **2020–2021** | 🔄 berjalan |
| **R7** | **RBB/FHCI** (arsip Wayback endpoint `/job/loadRecord/`) | Mengisi celah 2021 & 2024; syarat umur/IPK per jalur | ✅ 20 lowongan PLN dari RBB 2024 |
| — | Socmed PLN (IG) | Sudah terjawab Wayback (F-030) | ⬜ tidak perlu |
| — | Situs karier subholding | Subholding dimodelkan ringkas (DECISION-01) | ⬜ prioritas rendah |
| — | PPB 2021 & edisi RBB lain | Percobaan kena *rate limit* archive.org, bukan bukti tak ada | ⬜ bisa dicoba ulang |
| **R8** | **Berita/pers lokal + blog kandidat + surat panggilan tes** (media daerah, situs kampus, subholding, blog pribadi) via matriks kueri pencarian + panen manual user | Mengisi funnel **per-tahap per-gelombang** — tidak ada di sumber manapun sebelumnya. Ditemukan dari kasus nyata: berita Biak 2025 membantah jangkar funnel tunggal → funnel harus dipecah jadi arketipe, TAPI pembeda sebenarnya adalah **laju eliminasi**, bukan pola jadwal (F-061 merevisi F-058) | ✅ Tingkat 1 (arsip resmi) **mati/nihil**. Tingkat 2 (berita): **17 titik data** dari 7+ sumber independen, termasuk **funnel 6-tahap LENGKAP** dari blog kandidat 2015 (F-061 ⭐⭐⭐) + skema surat panggilan tes 2018 & 2023 (F-062) → `sources/berita/berita_rekrutmen.csv`. Tingkat 3 (socmed) belum dikerjakan. |

## 8b. Peta media untuk panen R8 (dipakai sebagai matriks kueri, bukan crawl buta)

Ditulis setelah 2 putaran panen (F-057–F-060) — daftar ini bukan tebakan, kolom "sudah kena"
tercatat dari apa yang benar-benar menghasilkan titik data.

**Jaringan nasional dgn kanal daerah (paling produktif — media lokal di bawah payung besar):**

| Jaringan | Pola domain daerah | Sudah kena? |
|---|---|---|
| **Antara** | `<kota/provinsi>.antaranews.com` (mis. `mataram.`, `papuatengah.`) | belum dicoba langsung — kandidat kuat |
| **RRI** | `rri.co.id/daerah/...` | ✅ Biak, Nabire |
| **Tribun (Kompas Gramedia)** | `<kota>.tribunnews.com` — 22 unit: Aceh(Serambinews), Batam, Medan, Pekanbaru, Jambi, Palembang, Lampung, Babel, Jakarta, Jogja, Bandung, Semarang, Surabaya, Kupang, Manado, Makassar(Tribun-Timur), Balikpapan, Banjarmasin, Pontianak, Bali | ✅ tersirat (aceh.tribunnews.com dipakai R3 lama) |
| **Jawa Pos Group / Radar** | banyak berawalan "Radar" + media daerah bermerek sendiri: Cenderawasih Pos (Papua), Riau Pos, Manado Post, Kaltim Post, Sumatera Ekspres, Harian Fajar (Makassar), Pontianak Post | ✅ Cenderawasih Pos (Biak) |
| **Kompas Gramedia lain** | kompas.com, money.kompas.com | ✅ (angka nasional 2025) |
| **Detik** | detik.com + kanal daerah (detikSulsel, detikJabar, dst), finance.detik.com untuk BUMN | dipakai sesekali, belum sistematis |
| **IDN Times** | idntimes.com + kanal kota | ✅ (angka nasional 245.217) |

**Media independen fokus wilayah (terutama Papua/3T — kandidat terbaik untuk arketipe afirmasi):**
ParaparaTV, KabarPapua.co/BeritaSatu Network, Fajar Papua, Jubi.id (independen, kritis, layak dicoba),
Klikpapua.com. ✅ 4 dari 5 sudah menghasilkan titik data (F-058, F-060).

**Kandidat belum dicoba (prioritas lanjutan kalau diminta):**
- `rekrutmen.pln.co.id/content/all/2/artikel` — halaman artikel resmi situs rekrutmen sendiri,
  bukan siaran pers holding. Beda dari F-057 (yang mati itu `web.pln.co.id`, bukan ini).
- Antara jaringan daerah (belum dicoba eksplisit meski jaringan terbukti reliable via RRI-style URL)
- Situs Pemda/Pemprov (kadang memuat siaran pers rekrutmen BUMN sebagai berita daerah)
- Instagram humas per-UP3 (Tingkat 3, mahal — manual, tidak terindeks pencarian)

**Yang TERBUKTI tidak produktif (jangan diulang tanpa strategi baru):** situs karier subholding
(F-060), domain `web.pln.co.id` (mati, F-057), rentang tahun 2020–2022 non-afirmasi (nol hit
lintas 3 putaran pencarian — media tidak meliput rekrutmen rutin tanpa sudut berita).

## 9. Status log

| Tgl | Kejadian |
|---|---|
| 2026-08-16 | Plan dibuat. Probe R1 sukses (situs server-rendered). Tooling: Playwright+Chromium ADA, pymupdf dipasang. |
| 2026-08-16 | **R1** 31 program + 128 profesi + 30 PDF. **R2** triage 9 perdir, ekstrak 0056 & 0050. **R4** chat HTD (peta ketersediaan data, funnel asli). **DECISION-01** dikunci: PLN Group. |
| 2026-08-16 | **R2c** Juknis 0048 (via subagent Sonnet) — ternyata dok *employee experience*, bukan SOP rekrutmen. **R1c** Wayback: 111 program historis. **R1b** brosur: kuota TIDAK ada di sumber manapun → wajib dimodelkan. |
| 2026-08-16 | **R1-login**: skema biodata/CV asli didapat (termasuk field fisik: BMI, visus, tatto). Akun ternyata milik pihak ketiga → dump HTML/PNG & profil browser **dihapus**, nama disensor; hanya `skema_form.md` disimpan. |
| 2026-08-17 | **R8 dibuka**: sesi build (terpisah) mentok di langkah 05/06 — jumlah pendaftar per tahap per gelombang over-determined (funnel tunggal vs kebutuhan unit vs gender per tahun saling bertentangan). User menemukan berita Biak yang memuat funnel per-tahap asli → hipotesis: berita/pers daerah bisa mengisi celah ini. Probe `web.pln.co.id` **mati DNS** (F-057); domain baru `www.pln.co.id` masih data developer dummy. Panen via pencarian: funnel Biak lengkap (301→155→139→138), agregat Papua 1.658/8 kota, kalibrasi campus_hiring (UGM 2017, 942). **Kesimpulan F-058**: funnel bukan satu angka — minimal 2 arketipe (nasional/mandiri berjenjang vs afirmasi/remote diborong). `funnel.yaml` perlu direstrukturisasi jadi per-arketipe sebelum langkah 05/06 dilanjut. |
| 2026-08-18 | **R8 lanjut, putaran 2-4**: (a) subholding nihil angka, Nabire+regional Papua konfirmasi arketipe afirmasi (F-060); (b) user bagi 5 sumber manual → blog kandidat Medan 2015 kasih **funnel 6-tahap lengkap** — MEREVISI F-058: pembeda arketipe adalah **laju eliminasi**, bukan pola jadwal (F-061 ⭐⭐⭐); surat panggilan tes konfirmasi transisi offline(2018)→online(2023) (F-062); (c) cek sistematis tiap gelombang 2019-2025 vs `angkatan.yaml`: angkatan 72 dikuatkan kuat (7 kota cocok persis), angkatan 75 diperkaya (target 200-250 org, Papua-spesifik bukan nasional generik), angkatan 79/80 bolongnya genuinely konsisten (bukan cuma di katalog PLN, di berita juga nihil) — TAPI ditemukan **sitasi meragukan**: "Bursa Karir ITS ke-33" di gelombang 70 ternyata acara 2017, bukan 2019 (edisi 2019 asli = ke-37/ke-38); perlu diverifikasi ulang ke Wayback sebelum dipakai presisi (F-063). Total panen: **17 titik data** di `sources/berita/berita_rekrutmen.csv`. |
