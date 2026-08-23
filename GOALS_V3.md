# GOALS — Dashboard Rekrutmen PLN v3

Antrean kerja untuk membangun `recruitment_dashboardv3/`. Berkas ini adalah **sumber
kebenaran**: `PROMPT_V3.md` menjelaskan *kenapa*, berkas ini menentukan *apa yang
dikerjakan berikutnya dan kapan dianggap selesai*.

Dipanggil lewat `/goal <n>` (mis. `/goal 0`) atau `/goal status`.

---

## Aturan mengikat P1–P11 — ringkasan padat

Sumber lengkap: `PROMPT_V3.md` §2. Ringkasan ini ditempel di sini supaya tetap terbaca
walau `PROMPT_V3.md` tidak ikut masuk konteks. **Jangan ditafsirkan ulang.**

| # | Aturan | Salah | Benar |
|---|---|---|---|
| **P1** | Judul chart = **nama benda**, bukan kalimat temuan. Doktrin D1 milik v2 **DIBATALKAN**. | "Pendaftaran bergelombang, bukan mengalir rata" | "Tren Pendaftaran Bulanan" |
| **P2** | **Nol** penjelasan developer di UI — tidak di judul, `help=`, `st.caption`, di mana pun. `help=` boleh berisi **definisi bisnis**. | "Nol karena tidak ada gelombang dibuka — gelombang terakhir tutup 345 hari lalu" | "Pelamar yang lolos seluruh tahap seleksi." |
| **P3** | "Terkini" = relatif **`TANGGAL_POTONG`**, bukan relatif baris data terakhir. Angka 0 yang jujur > angka lama yang tampak terkini. | `WHERE tanggal > (SELECT max(tanggal) - 30 …)` | `WHERE tanggal > TANGGAL_POTONG - 30` |
| **P4** | Pakai bentuk chart yang sudah punya konvensi. Sankey seperti Sankey, piramida penduduk seperti piramida penduduk. | tata letak karangan sendiri | konvensi baku |
| **P5** | Jangan over-agregasi. Tampilkan granularitas penuh selama terbaca. | umur dikelompokkan per 5 tahun | umur 20–34 per tahun (15 batang) |
| **P6** | Label pendek. | "Gugur Administrasi (tidak lolos)" | "Gugur Administrasi" |
| **P7** | Hemat ruang vertikal. | `st.pills` 6 pilihan di sidebar | `st.selectbox` |
| **P8** | Kotak isi sampai mentok bawah: CSS `max-height: calc(100vh - Npx)` lewat `.st-key-<key>`. | `height=420` | `.st-key-<key> { max-height: calc(100vh - 220px) }` |
| **P9** | Tiru implementasi v1/v2 yang sudah terbukti. Kalau menyimpang, **sebutkan alasannya lebih dulu**. | mengarang alternatif "lebih baik" | port pola yang ada |
| **P10** | Tanpa emoji. Ikon Material saja. | 📊 | `:material/dashboard:` |
| **P11** | Ukur, jangan berasumsi. "Lambat"/"berat" harus disertai angka hasil pengukuran. | "sepertinya query-nya berat" | "navigasi 5,2 dtk → 0,3 dtk setelah `auto_check=False`" |

## Batas & tata kelola (PROMPT_V3 §8)

- Venv bersama `tower2_dashboard/.venv` — **jangan bikin venv baru**. Jalankan dari dalam
  folder v3 dengan `../.venv/Scripts/python.exe`.
- Database `mockdb/out/rekrutmen.duckdb`, dibuka **read-only**, **tidak pernah** dimuat
  penuh ke DataFrame (4,22 juta baris).
- Halaman **tidak menulis SQL**. Semua angka lewat `core/metrics.py`.
- **Jangan sentuh** `recruitment_dashboard/` (v1) dan `recruitment_dashboardv2/` — dibaca saja.
- v1 port 8501, v2 port 8502, **v3 port 8503**.
- Rahasia di `.streamlit/secrets.toml` (sudah gitignored). Jangan commit kunci asli.
- **Commit hanya saat diminta. Jangan push tanpa diminta.**
- Jangan pernah menunjuk `mockdb/out/rekrutmen.duckdb.tmp/` (sisa direktori sementara).

## Kebijakan model

| Model | Untuk apa |
|---|---|
| **opus** | Pertimbangan desain & kebenaran yang mahal kalau salah: rancangan halaman, SQL metrik, ranjau performa. Semua penyajian di titik `[GATE]`. |
| **sonnet** | Membangun mengikuti rancangan yang sudah disepakati — porsi terbesar pekerjaan. |
| **haiku** | Fan-out baca-saja & verifikasi mekanis: inventarisasi berkas, ekstraksi teks, jalankan pytest, jalankan SQL, pindai regex. |

Subagent: `v3-pembangun` (menulis kode) · `v3-auditor` (menilai P1–P11, baca-saja) ·
`v3-pemeriksa` (jalankan & laporkan mentah, baca-saja). Model per goal ditulis di barisnya
masing-masing dan boleh diubah tanpa menyentuh definisi agent.

## Titik henti

Goal bertanda **`[GATE]`** berhenti dan menunggu keputusan pemilik. Goal lain jalan sampai
tuntas lalu lapor. **Tidak ada penerusan otomatis** ke goal berikutnya.

---

## Status

| Goal | Judul | Model | Status |
|---|---|---|---|
| G0 | Kerangka folder v3 | sonnet | SELESAI |
| G1 | Konteks kerja tim rekrutmen | haiku → opus | SELESAI |
| G2 | Susunan halaman `[GATE]` | opus | SELESAI |
| G3 | Tema `[GATE]` | sonnet → opus | SELESAI |
| G4 | Aturan tampilan v3 | opus | SELESAI |
| G5 | `core/db.py` + `core/format.py` | sonnet | SELESAI |
| G6 | `core/metrics.py` | opus | SELESAI |
| G7 | Kerangka aplikasi + navigasi | sonnet | SELESAI |
| G8 | Port chatbot apa adanya | opus | SELESAI |
| G9 | Harness tes 3 lapis | sonnet | SELESAI |
| G10 | Halaman 1 — Beranda `[GATE]` | sonnet | SELESAI |
| G11 | Halaman 2 — Perencanaan Formasi `[GATE]` | sonnet | SELESAI |
| G12 | Halaman 3 — Seleksi Berjalan `[GATE]` | sonnet | BELUM |
| G13 | Halaman 4 — Corong Seleksi `[GATE]` | sonnet | BELUM |
| G14 | Halaman 5 — Pasca-Seleksi `[GATE]` | sonnet | BELUM |
| G15 | Halaman 6 — Rencana & Realisasi `[GATE]` | sonnet | BELUM |
| G16 | Halaman 7 — Profil Pelamar `[GATE]` | sonnet | BELUM |
| G17 | Halaman Eksplorasi `[GATE]` | sonnet | BELUM |
| G18 | Konsolidasi & serah terima | opus | BELUM |

Legenda: `BELUM` · `JALAN` · `MENUNGGU KEPUTUSAN` · `SELESAI`

---

# FASE 1 — Fondasi & kesepakatan bentuk

## G0 · Kerangka folder v3

- **Prasyarat:** —
- **Subagent:** `v3-pembangun` · **sonnet**
- **Menyentuh:** `recruitment_dashboardv3/` (baru)

Buat struktur folder: `core/ app_pages/ chat/ components/ docs/ tests/ data/ .streamlit/`.

- `requirements.txt` — salin dari `recruitment_dashboardv2/requirements.txt`.
- `pytest.ini` — salin pola v2 (`python_files = uji_*.py`, `python_classes = Uji*`).
- `tests/conftest.py` — **tulis dengan benar**, jangan tiru `sys.path.insert(0, parents[1])`
  yang dipakai v2 di kepala tiap berkas tes. Ini satu-satunya penyimpangan dari P9 yang
  sudah disepakati di muka, alasannya: pola v2 itu duplikatif dan rapuh.
- `.streamlit/secrets.toml.example` — salin dari v2.
- `.streamlit/secrets.toml` — salin isi nyata dari v2 (lokal, gitignored). **Jangan** cetak
  isinya ke layar atau ke laporan.
- `streamlit_app.py` — hello-world sementara; navigasi sungguhan menyusul di G7.
- `.streamlit/config.toml` **belum dibuat** di sini — tema baru diputuskan di G3.

**Selesai bila:**
1. `../.venv/Scripts/streamlit.exe run streamlit_app.py --server.port 8503` hidup tanpa galat.
2. v2 di port 8502 masih bisa jalan berdampingan (uji berdampingan, bukan diklaim).
3. `git status` menunjukkan hanya berkas di `recruitment_dashboardv3/` yang baru.

---

## G1 · Konteks kerja tim rekrutmen

- **Prasyarat:** G0
- **Subagent:** `Explore` ×3 paralel · **haiku** untuk membaca · **sintesis akhir opus**
- **Menghasilkan:** `docs/KONTEKS_KERJA.md`, `docs/CATATAN_DATA.md`

**Wajib dibaca:** `referensi/PLN_Recruitment_Master_Context_2019_2026.docx` (41,5 KB).
Ekstrak lewat `zipfile` + parse `word/document.xml` — **jangan pasang dependensi baru**.

**Berguna sebagai wawasan, BUKAN batasan:** `knowledge/HANDOFF.md`, `mockdb/docs/ERD.md`,
`mockdb/docs/kamus_data.md`, `mockdb/ISSUES_SEBARAN.md`, `mockdb/ISSUES_MASTER_DATA.md`,
`recruitment_dashboardv2/docs/metrik.md`, `recruitment_dashboardv2/docs/backlog.md`.

> **Cara membacanya menentukan.** Dokumen-dokumen itu memberi tahu **apa yang ada di
> database**, bukan **apa yang seharusnya ada di dashboard**. v2 tersesat justru karena
> membiarkan bentuk tabel menentukan susunan halamannya.

**`docs/KONTEKS_KERJA.md`** — alur kerja tim rekrutmen dari perencanaan formasi sampai SK.
Untuk tiap tahap: siapa pelakunya · sistem apa yang dipakai · keputusan apa yang diambil ·
**pertanyaan apa yang muncul berulang tiap hari**. Bagian terakhir itu yang jadi bahan G2.

**`docs/CATATAN_DATA.md`** — dibuka dengan jebakan data yang **sudah terverifikasi**, jangan
ditemukan ulang dari nol:

1. Lima kolom dibagikan acak seragam oleh generator — `kandidat.kota_domisili`,
   `kandidat.kota_asal`, `kandidat.tempat_lahir`, `kandidat.ukuran_baju`,
   `kandidat_pendidikan.sekolah_universitas`. Jangan bangun analisis di atasnya.
2. `kota_asal` **duplikat persis** `kota_domisili` (bug generator).
3. Kota & propinsi diundi terpisah → 1.334 pasangan kota–propinsi yang mustahil
   (mis. Jakarta/Jawa Barat). Jangan pernah tampilkan keduanya berdampingan.
4. `unit_induk` punya baris duplikat "UID Jawa Tengah & DIY" dengan `jumlah_pegawai=4`.
   Mitigasi v2: `WHERE jumlah_pegawai > 50`.
5. Kode gender adalah **P = Pria / W = Wanita**, bukan L/P.
6. Durasi pasca-seleksi konstan 400 hari → analisis SLA/bottleneck tidak bermakna.
7. Jangan JOIN `seleksi_tahap_agregat` langsung ke `pendaftaran` (3 baris/tahun → hasil 3× lipat).
8. Gap FTK wajib pakai `realisasi_mar_2026`, bukan `apr_2026` (hanya terisi 1 dari 48 unit).

Kolom yang **aman** dibangun di atasnya (sudah tervalidasi berpola): `propinsi_domisili`,
`agama`, `status_perkawinan`, `degree`, `program_studi`, `seleksi_tahap.lokasi_kota`,
`vendor_id`, `bidang_pembidangan`, `penempatan.unit_induk`.

**Selesai bila:** laporan mengutip **3 kalimat asli** dari .docx tersebut — bukti berkas
benar-benar terbaca, bukan diringkas dari ingatan.

---

## G2 · Susunan halaman `[GATE]`

- **Prasyarat:** G1
- **Model:** **opus**, dikerjakan langsung — tidak didelegasikan
- **Menghasilkan:** `docs/RANCANGAN_HALAMAN.md` + mengisi judul G10–G14 di berkas ini

**Jangan meniru 8 halaman v2** (Ringkasan · Perencanaan · Corong · Kandidat · Pasca ·
Penempatan · Kualitas · Chatbot). Susunan itu lahir dari bentuk tabel database.

Rancang dari `docs/KONTEKS_KERJA.md`. Hipotesis awal PROMPT_V3 §6 boleh — bahkan sebaiknya —
dibantah kalau dokumen konteks menunjukkan lain: beranda operasional · perencanaan formasi
& pagu · pelaksanaan seleksi berjalan · kandidat · pasca-seleksi/penempatan/SK ·
pertanggungjawaban.

Untuk tiap halaman usulan, sebutkan: **pertanyaan harian yang dijawabnya** · blok isinya ·
metrik yang dibutuhkan · apakah datanya sudah ada di database atau belum.

Ukuran keberhasilan yang harus dipenuhi rancangan ini: **layak dibuka setiap hari**. Kalau
isi sebuah halaman sama persis tiap kali dibuka, halaman itu gagal dan harus dirancang ulang.

**Berhenti:** sajikan usulan ke pemilik. **Tidak ada satu baris kode halaman** sebelum
susunan disetujui.

---

## G3 · Tema `[GATE]`

- **Prasyarat:** G0
- **Subagent:** `v3-pembangun` · **sonnet** menyiapkan contoh; penyajian pilihan **opus**
- **Menghasilkan:** `recruitment_dashboardv3/.streamlit/config.toml`

**Panggil skill `developing-with-streamlit` lebih dulu** (router pemuat referensi
versi-cocok; Streamlit terpasang 1.62.0). Lalu baca `references/theme.md` dan
`references/design.md`.

Dari 12 tema di `.venv/Lib/site-packages/streamlit/.agents/skills/developing-with-streamlit/assets/templates/themes/configs/`
(`dracula`, `financial-dashboard`, `fluent`, `jupyter`, `material-ui`, `minimal`, `nord`,
`one-dark-pro`, `shadcn`, `solarized-light`, `ubuntu`, `vscode`) — saring 2–3 yang condong
navy/biru sesuai identitas PLN.

**Jalankan tiap kandidat di port 8503 dan tunjukkan tangkapan layarnya.** Daftar kode hex
saja tidak cukup untuk menilai.

Jadikan templat `assets/templates/apps/dashboard-metrics/` sebagai **acuan pola** — bukan
disalin mentah. Yang layak ditiru: kartu KPI dengan skeleton loading · filter di dalam
popover · pemilih rentang waktu · toggle chart/tabel.

**Catatan:** `github.com/Leonxlnx/taste-skill` **tidak dipasang** — dibangun untuk
React/Vue/Svelte, tuas utamanya tidak ada di Streamlit, dan penerapan harfiahnya mendorong
injeksi CSS besar yang bertentangan dengan panduan resmi Streamlit. Yang diserap prinsipnya:
hindari pola generik, jaga hierarki tipografi, disiplin spasi, kendalikan kepadatan informasi.

**Selesai bila:** pemilik memilih satu tema, dan `config.toml` ditulis.

---

## G4 · Aturan tampilan v3 (pengganti D1–D6)

- **Prasyarat:** G2, G3
- **Model:** **opus** — berkas ini mengikat semua goal sesudahnya
- **Menghasilkan:** `docs/ATURAN_TAMPILAN.md`

Tulis ulang P1–P11 sebagai aturan yang bisa ditegakkan. Tiap aturan diberi tanda:

- **[mekanis]** — bisa diuji regex di `tests/uji_disiplin.py` (G9)
- **[manual]** — harus dilihat mata; masuk daftar periksa tinjauan visual G18

Termasuk satu keputusan arsitektur: **apakah v3 punya primitif tata letak sama sekali**, dan
kalau ya apa saja. `components/ui.py` milik v2 dibuang seluruhnya
(`temuan_halaman`, `blok_chart`, `spanduk_dimodelkan`, `judul_halaman`, `baris_kpi`,
`tentang_halaman`, `mode_analis`, `lapis_analis`). **Dilarang** ada padanan
`temuan_halaman()` dalam bentuk apa pun — primitif itulah yang melembagakan D1.

Berkas ini yang dibaca `v3-pembangun` dan `v3-auditor` sebelum bekerja.

---

# FASE 2 — Fondasi kode

## G5 · `core/db.py` + `core/format.py`

- **Prasyarat:** G0
- **Subagent:** `v3-pembangun` · **sonnet**; verifikasi angka `v3-pemeriksa` · **haiku**

Port pola `recruitment_dashboardv2/core/db.py` (58 baris) apa adanya (P9):

- `@st.cache_resource koneksi()` → `duckdb.connect(str(DB_PATH), read_only=True)`
- `.cursor()` **per panggilan** — koneksi dibagi lintas sesi, ini yang membuatnya aman thread
- `@st.cache_data(ttl=3600, show_spinner=False)` di `query()` dan `skalar()`
- Cache di tingkat **hasil query**, tidak pernah DataFrame yang dimuat penuh
- `DB_PATH = Path(__file__).resolve().parents[2] / "mockdb" / "out" / "rekrutmen.duckdb"`

Penyesuaian v3:

- **`hari_ini()` adalah jangkar waktu** (revisi P3 di G4, keputusan pemilik di G2).
  Default tanggal berjalan sungguhan; bisa di-override pemilih tanggal lewat `session_state`.
  **Satu-satunya sumber waktu** — halaman tidak pernah memanggil `date.today()` sendiri.
- `TANGGAL_POTONG` **dibaca dari tabel `_meta_generator`** (`kunci = 'tanggal_sekarang'` →
  `2026-09-15`), tidak diketik dari ingatan. Perannya turun jadi penanda **horison data**,
  bukan patokan tampilan.
- Tambah helper P3 `jendela(hari) -> tuple[date, date]`, terikat **`hari_ini()`** — bukan
  `TANGGAL_POTONG`, dan tidak pernah ke `max(tanggal)`.
- Buang `daftar_tabel()` — tidak dipakai siapa pun di v2 (chatbot punya `TABEL_INTI` sendiri).

`core/format.py` diport dari v2 (44 baris, pemformat angka Indonesia).

**Selesai bila:** skrip verifikasi mencetak **35 tabel** dan **4.224.925 baris**, dan
`TANGGAL_POTONG` yang terbaca sama dengan `_meta_generator`.

⚠️ Kedua angka itu berbeda basis, dan itu memang benar: 35 tabel **termasuk**
`_meta_generator`, sedangkan 4.224.925 baris **tidak** menghitung 7 baris tabel itu (total
sesungguhnya 4.224.932). Tes harus menyebut basisnya eksplisit — lihat `CATATAN_DATA.md` §1.

---

## G6 · `core/metrics.py`

- **Prasyarat:** G2, G5
- **Subagent:** `v3-pembangun` · **opus** — SQL salah = angka salah di seluruh dashboard;
  eksekusi angka `v3-pemeriksa` · **haiku**
- **Menghasilkan:** `core/metrics.py`, `docs/metrik.md`

Fungsi-per-metrik seperti v2: modul datar, tanpa registry dict, tanpa dekorator, **tanpa
cache sendiri** (mengandalkan `core.db.query`/`skalar` yang sudah `@st.cache_data`).
Kembalian `pd.DataFrame` atau `dict`.

Isi awal goal ini: helper bersama + **metrik halaman pertama saja**. Tiap goal halaman
sesudahnya menambah metriknya sendiri ke modul yang sama.

`recruitment_dashboardv2/docs/metrik.md` berisi 44 metrik (M01–M43) yang SQL-nya sudah
dijalankan dan diverifikasi terhadap database ini. **Pakai ulang yang cocok** (P9) — tapi
hanya yang dibutuhkan rancangan G2, bukan seluruhnya.

Angka jangkar v2 yang sudah terverifikasi: `pendaftaran = 218.928` · `diterima = 7.711` ·
`sudah_sk = 5.711` · `gap_ftk = 701`.

**Selesai bila:** setiap fungsi sudah **dijalankan** terhadap DB nyata dan hasilnya tercatat
di `docs/metrik.md`. Tidak boleh ada satu pun angka yang belum pernah dieksekusi.

---

## G7 · Kerangka aplikasi + navigasi

- **Prasyarat:** G3, G4
- **Subagent:** `v3-pembangun` · **sonnet**

`streamlit_app.py`: `st.set_page_config` → daftar `st.Page` → `st.navigation(position="sidebar")`
→ `halaman.run()` **di baris terakhir**.

- Ikon Material di tiap halaman (P10) — tanpa emoji.
- Sidebar ringkas: `st.selectbox`, **bukan** `st.pills` (P7).
- Helper CSS tinggi kontainer (P8): `max-height: calc(100vh - Npx)` lewat selektor
  `.st-key-<key>`, **bukan** `height=` piksel tetap. Hanya `.st-key-*` yang didukung resmi
  Streamlit — jangan pakai selektor internal lain.

---

## G8 · Port chatbot apa adanya

- **Prasyarat:** G3, G7
- **Subagent:** `v3-pembangun` · **opus** — ada tiga ranjau performa yang mudah
  "diperbaiki" jadi rusak; pengukuran `v3-pemeriksa` · **haiku**

**Ini permintaan eksplisit pemilik: salin dari v2, jangan dirancang ulang.**

| Sumber v2 | Tujuan v3 |
|---|---|
| `chat/chatbot.py` (717 baris) | `chat/chatbot.py` |
| `chat/chat_ui.py` (270) | `chat/chat_ui.py` |
| `chat/chat_store.py` (276) | `chat/chat_store.py` |
| `app_pages/chatbot.py` (162) | `app_pages/chatbot.py` — halaman penuh "RecruitMan" |
| blok popover `streamlit_app.py` baris 45–113 | blok popover `streamlit_app.py` |

Sesuaikan **hanya jalur impor**. `chat/chatbot.py` dan `chat/chat_store.py` tidak mengimpor
`components/` sama sekali, jadi porting-nya bersih.

**Wajib ikut utuh — jangan "diperbaiki":**

- `_is_safe_select()` + `_FORBIDDEN_SQL` (allow-list `SELECT`/`WITH`, tolak `;` bertumpuk,
  blokir DML/DDL/`PRAGMA`/`INFORMATION_SCHEMA`/`READ_CSV`/`HTTPFS`/dst).
- `@functools.lru_cache(maxsize=1)` di `_build_schema_prompt()` — tanpa itu **~1,3 detik
  per giliran percakapan** terbuang membangun ulang prompt skema.
- Budget: `LLM_REQUEST_TIMEOUT=30`, `LLM_PING_TIMEOUT=10`, `MAX_TOOL_ITERATIONS=10`,
  `AGENT_TIME_BUDGET_SECONDS=90`.
- `docs/metrik.md` **tetap tidak** dimasukkan ke prompt (~5.700 token per giliran).

**Dua-duanya harus ada:** halaman chatbot penuh **dan** popover mengambang di setiap
halaman, berbagi `session_state["active_conversation_id"]` yang sama.

⚠️ **`auto_check=False`** wajib pada pemanggilan `render_model_status_selector` dari
popover. Badan `with st.popover(...)` dieksekusi server-side di **setiap** render halaman,
bukan hanya saat dibuka — tanpa flag itu, tiap navigasi memicu ping jaringan nyata (terukur
**~5 detik per navigasi**, dan pernah membuat suite tes membengkak dari 15 detik jadi 30 menit).

Satu penyesuaian tak terhindarkan: gradien tombol popover v2 memanggil `theme.token()` dari
`core/theme.py` yang **dibuang** di v3 — ganti sumber warnanya ke `config.toml` hasil G3.

`data/chat_history.db` milik v3 sendiri; jangan berbagi berkas dengan v2.

**Selesai bila:** waktu navigasi antar halaman **diukur** sebelum dan sesudah popover
dipasang, dan selisihnya dilaporkan sebagai angka (P11).

---

## G9 · Harness tes 3 lapis

- **Prasyarat:** G6, G7
- **Subagent:** `v3-pembangun` · **sonnet**; eksekusi suite `v3-pemeriksa` · **haiku**

**Lapis 1 — `tests/uji_metrik.py`:** angka jangkar dari G6 diuji terhadap DB nyata. Termasuk
tes *bentuk* yang menjaga dari cacat data mock (mis. filter anomali `unit_induk`, dan uji
sebaran berpola untuk memastikan kolom yang dipakai bukan salah satu dari lima kolom acak
seragam).

**Lapis 2 — `tests/uji_halaman.py`:** `streamlit.testing.v1.AppTest`. Muat selalu lewat
`streamlit_app.py` lalu `at.switch_page(...)` — memuat berkas halaman langsung gagal karena
butuh konteks navigasi.

**Lapis 3 — `tests/uji_disiplin.py`: DITULIS ULANG untuk P1–P11.** Jangan salin dari v2 —
berkas v2 menegakkan D1 yang sudah dibatalkan, dan meng-grep `ui.temuan_halaman(` yang tidak
akan ada di v3. Aturan mekanis minimal:

- tanpa emoji (P10) — ikon Material dikecualikan
- tanpa `st.caption` penjelas (P2)
- tanpa `SELECT` di `app_pages/*.py` (arsitektur)
- tanpa kolom PII (`nama_lengkap`, `no_ktp`, `email`, `no_handphone`, `alamat_*`)
- tanpa `height=` piksel tetap pada kontainer layar-penuh (P8)
- **judul chart berupa frasa benda** (P1) — proksi mekanis: ringkas, tanpa tanda baca kalimat
- tanpa `max(tanggal…)` dipakai sebagai pengganti hari ini (P3)

Yang tidak bisa diuji mesin masuk daftar periksa **[manual]** di `docs/ATURAN_TAMPILAN.md`.

**Selesai bila:** seluruh suite lolos **dan** rampung di bawah ~60 detik. Kalau melar,
curigai ping jaringan di jalur render — itu penyebabnya di v2.

---

# FASE 3 — Halaman, satu per satu

## G10–G16 · Halaman 1…7 `[GATE tiap goal]`

Judul hasil G2 (**tujuh halaman**, bukan lima): **G10 Beranda** · **G11 Perencanaan Formasi** ·
**G12 Seleksi Berjalan** · **G13 Corong Seleksi** · **G14 Pasca-Seleksi** ·
**G15 Rencana & Realisasi** · **G16 Profil Pelamar**. Rincian tiap halaman di
`recruitment_dashboardv3/docs/RANCANGAN_HALAMAN.md`.

**Mengikat semua halaman — dashboard ini realtime.** Keputusan pemilik: jangkar waktu adalah
**`date()` sungguhan**, ditambah pemilih "lihat per tanggal" yang defaultnya hari ini.
`TANGGAL_POTONG` bukan patokan tampilan, hanya penanda horison data.

Status apa pun (berjalan/selesai/belum mulai) **dihitung dari perbandingan tanggal terhadap
`hari_ini()`**, tidak pernah dibaca dari kolom `status` yang beku saat generate — kolom itu
akan menyatakan "2.000 sedang OJT" selamanya, bahkan di 2027. Tidak boleh ada angka hari yang
di-hardcode. Tiap halaman wajib punya keadaan kosong yang bermartabat: fakta keadaan, bukan
pesan galat atau penjelasan developer.

Horison data berakhir **2026-10-15**; sesudahnya halaman live memang kosong. Perbaikan
generator untuk v4 dicatat di `recruitment_dashboardv3/docs/USULAN_DATABASE.md` bagian A —
**bukan lingkup v3**.

- **Prasyarat:** G4, G6, G7, G9 — dan halaman sebelumnya sudah disetujui
- **Subagent:** `v3-pembangun` · **sonnet** → audit `v3-auditor` · **sonnet** →
  jalankan `v3-pemeriksa` · **haiku**

Judul dan jumlah pastinya diisi oleh G2. Kalau G2 menghasilkan lebih atau kurang dari lima
halaman, nomor sesudahnya digeser saat itu juga.

**Pola tiap goal:**
1. Tambahkan metrik yang dibutuhkan halaman ini ke `core/metrics.py` — **jalankan tiap SQL**.
2. Bangun halaman.
3. `v3-auditor` memeriksa P1–P11.
4. Jalankan di port 8503 + `uji_disiplin.py`.
5. **Tunjukkan ke pemilik, berhenti, minta tanggapan.** Jangan lanjut ke halaman berikutnya.

Kalau audit menemukan pelanggaran **P1 dua kali berturut-turut** pada halaman yang sama,
naikkan halaman itu ke **opus** — itu tanda rancangannya, bukan penulisannya, yang bermasalah.

---

## G17 · Halaman Eksplorasi `[GATE]`

- **Prasyarat:** semua halaman berdata nyata selesai
- **Subagent:** `v3-pembangun` · **sonnet**
- **Menghasilkan:** halaman Eksplorasi + `docs/USULAN_DATABASE.md`

Satu halaman terpisah, **jelas ditandai terpisah** dari halaman berdata nyata, menampung
fitur yang **datanya belum ada di database**.

v3 tidak boleh terkekang oleh bagaimana database dibuat. Kalau sebuah fitur jelas berguna
bagi tim rekrutmen tapi datanya belum ada, **fitur itu tetap dibuat di sini** — dibangun
penuh dengan data sintetis supaya terlihat hidup dan bisa dinilai. Justru inilah yang jadi
catatan untuk pengembangan database berikutnya.

Setiap fitur di halaman ini **otomatis** jadi satu baris di `docs/USULAN_DATABASE.md`:
fitur apa · data apa yang kurang · tabel/kolom yang perlu ditambah.

---

# FASE 4 — Penutup

## G18 · Konsolidasi & serah terima

- **Prasyarat:** G17
- **Model:** **opus**; suite penuh oleh `v3-pemeriksa` · **haiku**

1. Rapikan `docs/CATATAN_DATA.md` — semua "kenapa angkanya begini", jebakan data, asumsi
   pemodelan, dan keputusan query bermuara di sini. Verifikasi ulang: **nol** penjelasan
   developer tersisa di UI (P2).
2. Jalankan suite penuh, laporkan keluarannya apa adanya.
3. **Tinjauan visual manual, terang dan gelap** — dijalankan sungguhan lalu dilihat. Ini
   yang **tidak pernah dilakukan di v2** dan jadi salah satu sebab v3 ada. AppTest headless
   tidak bisa menilai "chart terbaca sekali lihat".
4. `README.md` v3.
5. Laporkan apa adanya: yang gagal disebut gagal, yang dilewati disebut dilewati.

---

## Dua berkas catatan — tempat semua penjelasan bermuara

| Berkas | Isi | Tampil di UI? |
|---|---|---|
| `docs/CATATAN_DATA.md` | Alasan "kenapa angkanya begini", jebakan data, asumsi pemodelan, keputusan query | **Tidak pernah** |
| `docs/USULAN_DATABASE.md` | Kebutuhan data yang belum terpenuhi — bersumber dari halaman Eksplorasi | **Tidak pernah** |

Setiap kali tergoda menulis penjelasan di `help=`, judul, atau caption: **tulis di sini.**
