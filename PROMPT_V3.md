# Membangun Dashboard Rekrutmen PLN v3

Berkas ini adalah briefing lengkap. Baca seluruhnya sebelum menulis kode.

Ada dua dashboard terdahulu di repositori ini: `recruitment_dashboard/` (v1) dan
`recruitment_dashboardv2/` (v2). Keduanya berfungsi. v3 dibangun bukan karena keduanya
rusak, tapi karena **tampilan dan susunan isinya salah sasaran** — dan alasannya
didokumentasikan di bawah supaya tidak terulang.

Bangun di folder baru: `recruitment_dashboardv3/`. Jangan ubah v1 dan v2.

---

## 1. Untuk siapa dashboard ini

**Tim pelaksana rekrutmen PLN.** Pekerjaan mereka membentang dari perencanaan formasi,
pelaksanaan seleksi, pertanggungjawaban, sampai SK pegawai — dan tidak terbatas pada
daftar itu.

**Ukuran keberhasilan: layak dibuka setiap hari.** Ini bukan laporan yang dicetak sekali
lalu diarsipkan. Kalau isinya sama persis tiap kali dibuka, dashboard ini gagal. Isinya
harus memberi kabar terkini: apa yang berubah, apa yang perlu perhatian hari ini.

Konsekuensi langsung: setiap angka "terbaru"/"baru"/"aktif" harus dihitung **relatif
tanggal potong** (lihat P3), bukan relatif baris data terakhir yang kebetulan ada.

---

## 2. Preferensi pemilik dashboard — aturan mengikat

Aturan berikut lahir dari koreksi berulang di sesi-sesi sebelumnya. Masing-masing
disertai contoh nyata kesalahannya. **Jangan tafsirkan ulang; ikuti apa adanya.**

### P1 · Judul chart adalah nama benda, bukan kalimat temuan

```
SALAH:  "Pendaftaran bergelombang, bukan mengalir rata"
SALAH:  "S1/D-IV mendominasi pelamar"
SALAH:  "Pelamar pria dua kali lipat wanita di tiap umur"

BENAR:  "Tren Pendaftaran Bulanan"
BENAR:  "Jenjang Pendidikan Pelamar"
BENAR:  "Sebaran Umur & Jenis Kelamin"
```

Judul dibaca orang yang sama setiap hari. Kalimat temuan hanya berguna sekali; sesudah
itu jadi kebisingan, dan lebih buruk lagi — temuan itu bisa **basi** ketika datanya
berubah, sementara judulnya tetap.

> **PENTING:** v2 punya doktrin bernama **D1** di `recruitment_dashboardv2/docs/design_system.md`
> §11 yang berbunyi *"Judul chart = temuan, bukan kategori"*. **Doktrin itu DIBATALKAN.**
> Kalau Anda membaca dokumen v2 dan menemukannya, abaikan. Contoh "SALAH" di atas bukan
> kelalaian — semuanya hasil taat pada D1.

### P2 · Nol penjelasan developer di UI

Tidak di judul, tidak di tooltip `help=`, tidak di `st.caption`, tidak di mana pun yang
dilihat pengguna.

```
SALAH (tooltip KPI):
  "Akun terdaftar dalam 30 hari terakhir sampai 15 September 2026.
   Nol karena tidak ada gelombang dibuka — gelombang terakhir tutup 345 hari lalu."
```

Itu penjelasan developer ke developer. Tim rekrutmen tidak peduli kenapa query-nya
begitu. Semua alasan "kenapa angkanya begini", jebakan data, dan asumsi pemodelan
**pindah ke `docs/CATATAN_DATA.md`** (lihat §7).

Tooltip boleh ada, tapi isinya **definisi bisnis** yang membantu pengguna, bukan
pembelaan teknis. Contoh boleh: *"Pelamar yang lolos seluruh tahap seleksi."*

### P3 · Terkini berarti relatif hari ini, bukan relatif data

Tanggal potong ada di `core/db.py` v2 sebagai `TANGGAL_POTONG` (15 September 2026).
Semua hitungan "baru / terkini / sedang berjalan / N hari terakhir" bertumpu ke sana.

Jangan pernah memakai `max(tanggal_x)` dari tabel sebagai pengganti "hari ini" hanya
supaya angkanya terlihat berisi. Itu menampilkan aktivitas setahun lalu seolah kejadian
kemarin, dan justru menyembunyikan hal yang paling perlu terlihat.

**Angka 0 yang jujur lebih baik daripada angka lama yang tampak terkini.** Kalau memang
sedang tidak ada gelombang berjalan, itu fakta operasional yang layak tampil.

### P4 · Pakai bentuk chart yang sudah dikenal orang

Sankey seperti Sankey pada umumnya. Piramida penduduk seperti piramida penduduk pada
umumnya. Jangan mengarang tata letak baru untuk bentuk yang sudah punya konvensi mapan —
pengguna kehilangan kemampuan membacanya sekilas.

### P5 · Jangan over-agregasi

Tampilkan granularitas penuh selama data mendukung dan chart-nya masih terbaca. Umur
20–34 ditampilkan per tahun, bukan dikelompokkan per 5 tahun, karena 15 batang masih
nyaman dibaca dan bentuknya lebih informatif.

### P6 · Label pendek

```
SALAH:  "Gugur Administrasi (tidak lolos)"    BENAR:  "Gugur Administrasi"
SALAH:  "NoShow Administrasi (tidak hadir)"   BENAR:  "NoShow Administrasi"
```

### P7 · Hemat ruang vertikal

Widget besar yang bertumpuk ditolak. `st.pills` dengan 6 pilihan memakan hampir seluruh
tinggi sidebar — pakai `st.selectbox` yang ringkas. Satu tombol popover lebih baik
daripada dua tombol ikon berjejer.

### P8 · Kotak isi sampai mentok bawah

Tinggi kontainer yang harus mengisi layar memakai CSS `max-height: calc(100vh - Npx)`
lewat selektor `.st-key-<key>`, **bukan** `height=420` piksel tetap. Tinggi tetap
menyisakan ruang kosong besar di layar lebar.

### P9 · Tiru implementasi yang sudah terbukti

Sebelum mengarang alternatif yang terasa "lebih baik", lihat dulu bagaimana v1/v2
melakukannya. Dua kali di sesi sebelumnya alternatif buatan sendiri ditolak dan harus
dikembalikan ke pola v1. Kalau menyimpang, sebutkan alasannya lebih dulu.

### P10 · Tanpa emoji

Pakai ikon Material: `:material/dashboard:`, `:material/download:`. Berlaku untuk seluruh
halaman, tombol, dan label.

### P11 · Ukur, jangan berasumsi

Saat bicara "lambat" atau "berat", ukur dulu dengan angka. Di sesi sebelumnya, dugaan
soal penyebab kelambatan chatbot meleset; yang ketemu lewat pengukuran justru
penyebab lain sama sekali (popover yang memicu ping jaringan di setiap render halaman).

---

## 3. Yang diwarisi dari v2

### Chatbot — port apa adanya, jangan dirancang ulang

Ini permintaan eksplisit pemilik. Salin dari v2 dan sesuaikan seperlunya:

| Berkas v2 | Isi |
|---|---|
| `recruitment_dashboardv2/chat/chatbot.py` | Mesin text-to-SQL agentic, guard `_is_safe_select`, cache prompt skema |
| `recruitment_dashboardv2/chat/chat_ui.py` | `render_turn`, `submit_question`, pemilih model + status |
| `recruitment_dashboardv2/chat/chat_store.py` | Penyimpanan percakapan |
| `recruitment_dashboardv2/app_pages/chatbot.py` | Halaman chatbot penuh ("RecruitMan") |
| `recruitment_dashboardv2/streamlit_app.py` (blok popover) | Popover mengambang di semua halaman |

**Dua-duanya harus ada:** halaman chatbot penuh **dan** popover chatbot di setiap halaman.
Riwayat percakapan dibagi lewat `session_state["active_conversation_id"]` yang sama.

Perhatikan `auto_check=False` pada pemanggilan `render_model_status_selector` dari popover
— tanpa itu, setiap render halaman memicu ping jaringan nyata (pernah menambah ~5 detik
ke setiap navigasi, dan membuat suite tes membengkak dari 15 detik jadi 30 menit).

### Arsitektur data

- **DuckDB read-only langsung ke berkas**, jangan pernah memuat tabel ke memori sebagai
  DataFrame — isinya 4,22 juta baris. Pola ada di `recruitment_dashboardv2/core/db.py`.
- **Halaman tidak menulis SQL.** Semua angka lewat satu modul metrik (`core/metrics.py`),
  supaya angka di halaman dan jawaban chatbot tidak pernah berbeda.
- **Venv bersama** di `tower2_dashboard/.venv`. Jangan bikin venv baru. Jalankan dengan
  `../.venv/Scripts/python.exe` dari dalam folder v3.

### Yang DIBUANG dari v2

- Doktrin **D1** (judul chart = kalimat temuan) — lihat P1.
- `components/ui.py` v2 beserta primitifnya (`temuan_halaman`, `blok_chart`, dst).
- `core/theme.py` v2 — diganti tema bawaan Streamlit (§5).
- Susunan 8 halaman v2 — dirancang ulang dari alur kerja, bukan dari bentuk tabel (§6).

---

## 4. Dokumen yang dibaca — dan cara membacanya

### Wajib
`referensi/PLN_Recruitment_Master_Context_2019_2026.docx` — konteks rekrutmen PLN
2019–2026. Sumber utama untuk memahami pekerjaan tim rekrutmen.

### Berguna, tapi baca sebagai wawasan — BUKAN batasan
- `recruitment_dashboardv2/docs/metrik.md` — 44 metrik yang SQL-nya sudah dijalankan dan
  diverifikasi terhadap database, lengkap dengan jebakan datanya. Sangat berharga untuk
  tahu kolom mana yang tidak bisa dipercaya.
- `mockdb/ISSUES_SEBARAN.md` — lima kolom yang dibagikan acak seragam oleh generator
  (`kota_domisili`, `kota_asal`, `sekolah_universitas`, dll). Jangan bangun analisis di
  atas kolom-kolom ini tanpa sadar.
- `recruitment_dashboardv2/docs/backlog.md`, `PRD.md`, `wireframe.md`.

> **Cara membacanya sangat penting.** Dokumen-dokumen itu memberi tahu **apa yang ada di
> database**, bukan **apa yang seharusnya ada di dashboard**. v2 tersesat justru karena
> membiarkan bentuk tabel database menentukan susunan halamannya.
>
> v3 **tidak boleh terkekang oleh bagaimana database dibuat.** Rancang dari kebutuhan tim
> rekrutmen. Kalau database belum mengakomodir sebuah fitur yang jelas berguna, **fitur
> itu tetap dibuat** — di halaman Eksplorasi (§6) — karena justru itulah yang akan jadi
> catatan untuk pengembangan database berikutnya.

---

## 5. Fondasi visual

Paket Streamlit yang terpasang membawa aset desain resmi. **Panggil skill
`developing-with-streamlit` lebih dulu** (router yang memuat referensi versi-cocok), lalu
gunakan:

```
.venv/Lib/site-packages/streamlit/.agents/skills/developing-with-streamlit/
├── references/
│   ├── design.md          ikon vs emoji, badge status, buang divider, sentence casing
│   ├── dashboards.md      KPI rows, cards, sparkline, parallel fragments + skeleton
│   ├── theme.md           warna, tipografi, Google Fonts, warna chart, radius
│   ├── layouts.md         kolom maks 4, alignment, kontainer, dialog
│   └── best-practices.md  aturan umum
└── assets/templates/
    ├── themes/configs/    12 tema siap pakai (shadcn, financial-dashboard, fluent, nord, …)
    └── apps/dashboard-metrics/   pola KPI+skeleton, popover filter, rentang waktu
```

**Keputusan pemilik:** pakai salah satu tema bawaan sebagai `.streamlit/config.toml`, dan
jadikan `dashboard-metrics` **acuan pola** — bukan disalin mentah. Pola yang layak ditiru
dari sana: kartu KPI dengan skeleton loading, filter di dalam popover, pemilih rentang
waktu (1M/6M/1Y/QTD/YTD/All), toggle chart/tabel.

Tunjukkan pilihan tema ke pemilik sebelum melanjutkan — identitas PLN condong ke navy/biru.

### Catatan soal "taste-skill"

Pemilik menanyakan `github.com/Leonxlnx/taste-skill`. **Jangan dipasang.** Skill itu
dibangun untuk React/Vue/Svelte tempat DOM dikuasai penuh; tuas utamanya (motion GSAP,
layout bebas, eksperimen tipografi) tidak tersedia di Streamlit. Penerapan harfiahnya
mendorong injeksi CSS besar lewat `st.html`, yang bertentangan dengan panduan resmi
Streamlit sendiri — *"Prefer native Streamlit elements over recreating UI with custom
HTML"* (`best-practices.md`) — dan rapuh, karena hanya `.st-key-*` yang didukung resmi.

**Yang diserap adalah prinsipnya:** hindari pola generik, jaga hierarki tipografi,
disiplin spasi, kendalikan kepadatan informasi.

---

## 6. Susunan halaman — rancang sendiri

**Jangan meniru 8 halaman v2.** Susunan itu lahir dari bentuk tabel database.

Setelah membaca dokumen konteks PLN, rancang susunan halaman dari **alur kerja tim
rekrutmen**. Hipotesis awal berikut boleh — bahkan sebaiknya — dibantah kalau dokumen
menunjukkan yang lain:

- Beranda operasional: *apa yang perlu perhatian hari ini*
- Perencanaan formasi & pagu
- Pelaksanaan seleksi yang sedang berjalan
- Kandidat
- Pasca-seleksi, penempatan & SK
- Pertanggungjawaban / pelaporan

Diskusikan susunan yang Anda usulkan dengan pemilik **sebelum** membangun halamannya.

### Halaman Eksplorasi (keputusan pemilik)

Satu halaman terpisah, jelas terpisah dari halaman berdata nyata, menampung **fitur yang
datanya belum ada di database**. Bangun penuh memakai data sintetis supaya terlihat hidup
dan bisa dinilai. Pemilik akan menelusuri usulan-usulan Anda di halaman ini.

Setiap fitur di halaman ini otomatis jadi satu baris di `docs/USULAN_DATABASE.md`.

---

## 7. Berkas catatan — tempat semua penjelasan bermuara

Dua berkas untuk developer, **tidak pernah tampil di UI**:

| Berkas | Isi |
|---|---|
| `docs/CATATAN_DATA.md` | Alasan "kenapa angkanya begini", jebakan data, asumsi pemodelan, keputusan query |
| `docs/USULAN_DATABASE.md` | Kebutuhan data yang belum terpenuhi — bersumber dari halaman Eksplorasi |

Setiap kali tergoda menulis penjelasan di `help=`, judul, atau caption: tulis di sini.

---

## 8. Batas & tata kelola

- Venv bersama `tower2_dashboard/.venv` — jangan bikin baru.
- Database: `mockdb/out/rekrutmen.duckdb`, dibuka **read-only**.
- Rahasia: `.streamlit/secrets.toml` (sudah di-gitignore lewat pola `**/.streamlit/secrets.toml`).
  Salin dari `recruitment_dashboardv2/.streamlit/secrets.toml.example`. Jangan pernah
  commit kunci asli.
- Jangan sentuh `recruitment_dashboard/` (v1) dan `recruitment_dashboardv2/`.
- **Commit hanya saat diminta.** Jangan push tanpa diminta.
- v1 jalan di port 8501, v2 di 8502 — pakai port lain untuk v3 (mis. 8503) supaya bisa
  dibandingkan berdampingan.

---

## 9. Cara kerja yang diharapkan

Ritme yang cocok dengan pemilik, terbukti di sesi sebelumnya:

1. **Diskusikan dulu** rancangan/pendekatan sebelum membangun — terutama susunan halaman
   dan pilihan tema.
2. **Bangun satu bagian, tunjukkan, minta tanggapan**, baru lanjut. Jangan membangun
   delapan halaman sekaligus lalu menyerahkannya utuh.
3. **Verifikasi dengan menjalankan**, bukan dengan meyakinkan. Setiap angka yang tampil
   harus sudah dijalankan terhadap database sungguhan.
4. **Laporkan apa adanya.** Kalau tes gagal, sampaikan beserta keluarannya. Kalau sebuah
   langkah dilewati, katakan.

Pertimbangkan menyiapkan tes otomatis sejak awal seperti v2 (`tests/` tiga lapis: angka
metrik, perilaku halaman lewat `streamlit.testing.v1.AppTest`, dan disiplin desain). Lapis
ketiga terbukti berguna — tapi **perbarui aturannya** mengikuti P1–P11 di berkas ini, jangan
menyalin aturan v2 yang menegakkan D1.
