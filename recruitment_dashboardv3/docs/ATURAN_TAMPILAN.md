# Aturan tampilan v3

Pengganti doktrin D1–D6 milik v2, yang **dibatalkan seluruhnya**.

Berkas ini **mengikat**. `v3-pembangun` membacanya sebelum menulis baris pertama;
`v3-auditor` memeriksa kode terhadapnya. Kalau kode dan berkas ini bertentangan, berkas ini
yang benar.

Tiap aturan diberi tanda:

- **[mekanis]** — bisa diuji regex di `tests/uji_disiplin.py` (G9). Pelanggaran = tes merah.
- **[manual]** — harus dilihat mata. Masuk daftar periksa tinjauan visual G18.

---

## 1. Keputusan arsitektur: v3 (nyaris) tidak punya primitif tata letak

**`recruitment_dashboardv2/components/ui.py` dibuang seluruhnya.** Kesepuluh fungsinya tidak
diport: `judul_halaman`, `baris_kpi`, `temuan_halaman`, `blok_chart`, `spanduk_dimodelkan`,
`tentang_halaman`, `mode_analis`, `sakelar_mode_analis`, `lapis_analis`, `halaman_segera`.

Alasannya per primitif — bukan pukul rata:

| Primitif v2 | Kenapa dibuang |
|---|---|
| `judul_halaman(j)` | Isinya persis `st.title(j)`. Pembungkus bernilai nol. |
| `temuan_halaman(kalimat)` | **Inilah yang melembagakan D1.** Argumennya *wajib* kalimat temuan. Dilarang keras punya padanannya. |
| `blok_chart(judul)` | Saudara kandung `temuan_halaman` dengan bentuk sama. Di v2, seluruh pelanggaran P1 bersarang di dalam kedua fungsi ini. |
| `tentang_halaman(teks)` | Vektor pelanggaran P2 by design. Di v2 fungsi ini membocorkan nama kolom (`kota_domisili`) dan jalur internal (`mockdb/ISSUES_SEBARAN.md`) ke layar. |
| `spanduk_dimodelkan(t)` | Injeksi HTML/CSS besar, bertentangan dengan panduan resmi Streamlit. Juga memanggil `core/theme.py` yang dibuang. |
| `baris_kpi(items)` | API berbasis list-of-dict menyembunyikan teks yang tampil di balik struktur data — auditor jadi sulit membacanya. |
| `mode_analis` + `sakelar_mode_analis` + `lapis_analis` | Sakelar global menggandakan permukaan tinjauan visual. Lihat §1.2. |
| `halaman_segera(judul, isi)` | Teks aslinya melanggar P2 — menyebut jalur internal `docs/wireframe.md` dan berbunyi seperti catatan developer. Penggantinya di §1.4. |

### 1.1 Yang dipakai sebagai gantinya: perintah Streamlit langsung

```python
# BENAR — apa yang tampil terbaca langsung di kode
st.title("Pasca-Seleksi")
with st.container(border=True):
    st.subheader("Sebaran peserta per UPDL")
    st.altair_chart(grafik, width="stretch")

# SALAH — teks tampil tersembunyi di balik pembungkus
ui.judul_halaman("Pasca-Seleksi")
with ui.blok_chart("Sebaran peserta per UPDL"):
    ...
```

Alasan pokoknya bukan soal jumlah baris, melainkan **keterbacaan bagi auditor**.
`st.subheader("...")` adalah teks yang benar-benar muncul di layar. Pembungkus membuat
pelanggaran P1 dan P2 bersembunyi di dalam argumen fungsi.

### 1.2 Sakelar "mode analis" tidak diport

v2 punya toggle global yang memunculkan tabel rinci dan tombol unduh di tiap halaman.
Tidak diport, karena tiap halaman jadi punya dua keadaan, dan G18 sudah menuntut tinjauan
manual **terang dan gelap** — dengan sakelar ini menjadi empat keadaan per halaman.

Unduh CSV tetap boleh, sebagai `st.download_button` biasa di tempat yang memang perlu.
Bukan di balik mode tersembunyi.

> Ini keputusan produk, bukan aturan teknis. Kalau pemilik menginginkan mode analis kembali,
> ini tempat membantahnya.

### 1.3 Dua helper yang boleh ada — keduanya bukan tata letak

Hanya dua, di `components/tampilan.py`:

**`tinggi_kontainer(key, offset_px)`** — menyuntik CSS `max-height: calc(100vh - Npx)` lewat
selektor `.st-key-<key>`. Wajib ada supaya P8 diterapkan seragam, dan hanya `.st-key-*` yang
didukung resmi Streamlit. Dibangun di G7.

**`keadaan_kosong(keadaan, ikon=None, terakhir=None)`** — keadaan kosong yang bermartabat
(§4.3). Wajib seragam karena ketujuh halaman akan mengalaminya.

⚠️ **`keadaan_kosong` berpotensi jadi `temuan_halaman` yang baru** — tempat prosa menumpuk.
Karena itu dibatasi keras: `keadaan` harus **frasa benda atau pernyataan keadaan pendek**,
bukan penjelasan sebab. Diperiksa auditor seperti judul chart.

**Selain dua ini, jangan menambah helper tampilan tanpa membicarakannya lebih dulu.**

### 1.4 Halaman yang belum dibangun

G7 memasang navigasi tujuh halaman, sedangkan halamannya baru dibangun satu per satu di
G10–G16. Ada jeda saat entri navigasi sudah ada tapi isinya belum.

**Jangan port `halaman_segera()` milik v2** — teksnya berbunyi *"Kerangka aplikasi sudah
jalan, halaman ini menyusul. Rencana isinya ada di `docs/wireframe.md`"*: penjelasan developer
dan jalur internal, dua-duanya melanggar P2.

Pakai yang sudah ada, tanpa fungsi baru:

```python
st.title("Perencanaan Formasi")
keadaan_kosong("Halaman ini belum tersedia")
```

---

## 2. P1–P11

### P1 · Judul chart adalah nama benda, bukan kalimat temuan

**[mekanis] + [manual]** — aturan tersulit, paling sering dilanggar.

Doktrin **D1** milik v2 berbunyi sebaliknya dan **DIBATALKAN**. Kalau membaca
`recruitment_dashboardv2/docs/design_system.md` §11, abaikan — semua contoh "SALAH" di bawah
adalah hasil taat pada D1.

| Melanggar | Patuh |
|---|---|
| "Pendaftaran bergelombang, bukan mengalir rata" | "Tren Pendaftaran Bulanan" |
| "S1/D-IV mendominasi pelamar" | "Jenjang Pendidikan Pelamar" |
| "Tes online kehilangan separuh pesertanya" | "No-show per Tahap" |
| "Jalur RBB nyaris tak berjejak di sistem PLN" | "Jejak RBB di Sistem PLN" |

**Uji cepat:** *apakah judul itu bisa jadi basi kalau datanya berubah bulan depan?* Kalau ya,
itu kalimat temuan. Frasa benda tidak pernah basi.

Berlaku untuk: `st.title` · `st.header` · `st.subheader` · `st.markdown("**…**")` sebagai
judul · `title=` pada Altair/Plotly · `.properties(title=…)` · label `st.metric` · judul
kontainer.

**Pengecualian: argumen `keadaan_kosong`.** Pernyataan keadaan secara sah memakai bentuk
negatif — *"Tidak ada gelombang yang sedang dibuka"* itu benar, bukan pelanggaran. Argumen
`keadaan_kosong` diuji **hanya** untuk panjang dan tanda baca kalimat, **tanpa** daftar kata
penanda klaim di bawah. Yang tetap dilarang: menerangkan *sebab* kosongnya (itu P2).

**Proksi mekanis (G9)** — semua ini menandakan kalimat, bukan frasa benda:
- mengandung `.`, `!`, atau `?` di akhir
- mengandung koma — kalimat temuan hampir selalu punya (`"…, bukan mengalir rata"`)
- lebih dari **6 kata**
- mengandung kata penanda klaim: `adalah` `bukan` `lebih` `paling` `hanya` `tidak` `belum`
  `naik` `turun` `kehilangan` `mendominasi` `ternyata` `justru` `masih`

Proksi ini **tidak menangkap semuanya**. Penilaian akhir tetap [manual].

### P2 · Nol penjelasan developer di UI

**[mekanis] + [manual]**

Tidak di judul, `help=`, `st.caption`, `st.info`, atau di mana pun yang dilihat pengguna.

- `help=` boleh berisi **definisi bisnis**: *"Pelamar yang lolos seluruh tahap seleksi."*
- `help=` **dilarang** membela query, menyebut nama tabel/kolom, atau menerangkan kekosongan
  data: *"Nol karena tidak ada gelombang dibuka — gelombang terakhir tutup 345 hari lalu"*

Semua alasan "kenapa angkanya begini" → [CATATAN_DATA.md](CATATAN_DATA.md). Tanpa kecuali.

**Proksi mekanis (G9)** — dilarang muncul di `app_pages/*.py` di dalam string yang tampil:
- nama tabel: `pendaftaran` `seleksi_tahap` `pasca_tahap` `penempatan` `kandidat`
  `gelombang` `unit_induk` `usulan_kebutuhan` `pagu_rekrutmen` `proyeksi_kekosongan`
- nama kolom ber-`snake_case` (regex `[a-z]+_[a-z_]+` di dalam string tampil).
  ⚠️ **Kecualikan token `:material/...:` lebih dulu** — nama ikon Material juga ber-snake_case
  (`:material/pending_actions:`), dan tanpa pengecualian ini uji nomor 3 akan merah palsu di
  hampir tiap halaman.
- jalur berkas: `mockdb/` `.duckdb` `docs/` `.md`
- kata: `generator` `dimodelkan` `query` `tabel` `kolom` `database`
- `st.caption(` — **dilarang seluruhnya** di `app_pages/`

### P3 · Terkini relatif `hari_ini()`, bukan relatif data

**[mekanis]** — **direvisi di G2, ini versi yang berlaku.**

Rumusan asli P3 berbunyi *"relatif `TANGGAL_POTONG`"*. Keputusan pemilik di G2 mengubah
jangkarnya: **tanggal berjalan sungguhan**, karena tanggal potong hanya simbolik dan orang
akan membuka dashboard ini pada 6 Januari 2027.

Yang **tidak** berubah: **jangan pernah memakai `max(tanggal)` sebagai pengganti hari ini**
supaya angkanya terlihat berisi. Itu menampilkan aktivitas setahun lalu seolah kejadian
kemarin.

**Angka 0 yang jujur lebih baik daripada angka lama yang tampak terkini.**

```python
# BENAR
jendela_awal = hari_ini() - timedelta(days=30)

# SALAH — memalsukan kekinian
WHERE tanggal > (SELECT max(tanggal) FROM pendaftaran) - 30

# SALAH — jangkar beku, dashboard mati di 2027
WHERE tanggal > DATE '2026-09-15' - 30
```

**Proksi mekanis (G9):**
- `max(` atas kolom bertanggal yang dipakai sebagai batas jendela waktu
- literal `2026-09-15` atau `TANGGAL_POTONG` di `app_pages/` maupun `core/metrics.py`
- `date.today()` / `datetime.now()` dipanggil di luar `core/db.py` — semua halaman **wajib**
  lewat `hari_ini()`, supaya pemilih tanggal berlaku seragam
- angka hari yang di-hardcode dalam string tampil (mis. `"345 hari"`)

### P4 · Bentuk chart yang sudah punya konvensi

**[manual]**

Sankey digambar seperti Sankey. Piramida penduduk seperti piramida penduduk — dua sisi
berhadapan, sumbu umur vertikal. Corong seperti corong. Peta seperti peta.

Jangan mengarang tata letak baru untuk bentuk yang sudah punya konvensi mapan. Pembaca
menghabiskan perhatiannya untuk memahami bentuknya, bukan datanya.

Prefer chart berbasis Vega (`st.altair_chart`, `st.bar_chart`, dsb.) daripada Plotly —
sejalan panduan resmi Streamlit dan otomatis memakai palet tema dari `config.toml`.

### P5 · Jangan over-agregasi

**[manual]**

Granularitas penuh selama data mendukung dan chart masih terbaca.

- Umur 20–34 → **15 batang per tahun**, bukan 3 kelompok lima tahunan
- 48 unit induk → tampilkan 48, bukan "10 teratas + lainnya", kecuali ruang benar-benar tidak
  cukup
- 11 UPDL → tampilkan sebelas

Kalau harus dipotong, sebutkan pemotongannya di label sumbu — bukan di caption.

### P6 · Label pendek

**[manual]** — sempat ditandai [mekanis]; itu keliru. Lihat catatan proksi di bawah.

"Gugur Administrasi", bukan "Gugur Administrasi (tidak lolos)".

Kurung penjelas **boleh** kalau membawa informasi baru: "Tes Adaptif (online)" sah, karena
mode tes adalah dimensi yang berbeda. Yang dilarang kurung yang mengulang arti labelnya
sendiri.

**Kenapa tidak mekanis.** Membedakan kurung yang mengulang arti dari kurung yang menambah
informasi butuh pemahaman makna, bukan pencocokan teks. Contoh acuan aturan ini sendiri —
"Gugur Administrasi (tidak lolos)" — **tidak punya satu pun kata yang tumpang tindih** dengan
teks di luar kurung, jadi regex overlap-kata justru melewatkannya.

**Yang boleh dimekaniskan (G9, uji 16):** *tandai* setiap label yang mengandung kurung untuk
ditinjau mata — jangan memutuskan otomatis. Tes ini **melaporkan**, tidak menggagalkan.

### P7 · Hemat ruang vertikal

**[mekanis] + [manual]**

- `st.selectbox`, bukan `st.pills` berisi 6 pilihan
- Satu tombol popover, bukan dua tombol ikon berjejer
- `st.container(horizontal=True)` untuk baris KPI, bukan `st.columns` kecuali butuh rasio
  lebar presisi
- Filter di dalam popover, bukan menumpuk di badan halaman

**Proksi mekanis (G9):** `st.pills(` dengan lebih dari 4 opsi.

### P8 · Kotak isi sampai mentok bawah

**[mekanis]**

```python
# BENAR
tinggi_kontainer("corong", offset_px=220)   # -> .st-key-corong { max-height: calc(100vh - 220px) }

# SALAH
st.container(height=420)
```

Hanya selektor `.st-key-*` yang didukung resmi Streamlit. Jangan memakai selektor internal
lain — mereka berubah tanpa pemberitahuan antar versi.

**Proksi mekanis (G9):** `height=<angka>` pada `st.container`. `height=` pada `st.dataframe`
**boleh** — itu tinggi tabel, bukan kontainer layar-penuh.

### P9 · Tiru implementasi v1/v2 yang sudah terbukti

**[manual]**

Sebelum mengarang alternatif yang terasa "lebih baik", lihat dulu bagaimana v1/v2
melakukannya. Dua kali di sesi sebelumnya alternatif buatan sendiri ditolak dan harus
dikembalikan ke pola v1.

**Kalau menyimpang, sebutkan alasannya lebih dulu di laporan** — sebelum kodenya ditulis,
bukan sesudah ditanya.

Penyimpangan yang **sudah disetujui di muka**, tidak perlu diminta ulang:

1. `tests/conftest.py` menggantikan `sys.path.insert` berulang di tiap berkas tes (G0)
2. `components/ui.py` dibuang seluruhnya (§1)
3. Doktrin D1 dibatalkan, diganti P1
4. Jangkar waktu `hari_ini()` menggantikan `TANGGAL_POTONG` (P3)

### P10 · Tanpa emoji

**[mekanis]**

Ikon Material saja: `:material/dashboard:`, `:material/download:`, `:material/today:`.

**Proksi mekanis (G9):** regex rentang emoji Unicode atas seluruh `*.py` di v3. Token
`:material/...:` dikecualikan.

### P11 · Ukur, jangan berasumsi

**[mekanis] + [manual]**

"Lambat", "berat", "cepat" harus disertai angka hasil pengukuran nyata.

- Salah: *"sepertinya query-nya berat"*
- Benar: *"navigasi 5,2 dtk → 0,3 dtk setelah `auto_check=False`"*

Berlaku juga untuk laporan subagent, bukan hanya komentar kode.

**Proksi mekanis (G9):** kata `lambat`/`berat`/`cepat`/`optimal` di komentar tanpa angka
di baris yang sama.

---

## 3. Aturan arsitektur

Bukan bagian P1–P11, tapi ditegakkan sama kerasnya.

| Aturan | Tanda | Proksi mekanis |
|---|---|---|
| Halaman tidak menulis SQL — semua angka lewat `core/metrics.py` | [mekanis] | `SELECT` / `FROM` **huruf besar** di `app_pages/*.py` — lihat catatan di bawah |
| Kolom PII tidak pernah tampil | [mekanis] | `nama_lengkap` `no_ktp` `email` `no_handphone` `alamat_domisili` `alamat_asal` di `app_pages/` |
| Tabel penuh tidak pernah dimuat ke DataFrame | [manual] | `SELECT *` tanpa `LIMIT`/agregat |
| Database dibuka read-only | [mekanis] | `duckdb.connect(` tanpa `read_only=True` |
| Isi `secrets.toml` tidak pernah dicetak | [manual] | — |
| `use_container_width` tidak dipakai (usang) | [mekanis] | `use_container_width` di mana pun |

⚠️ **Uji SQL wajib case-sensitive dan berbatas kata.** Tiap berkas `app_pages/*.py` memuat
`from core import metrics` — pencocokan `FROM` yang case-insensitive akan menggagalkan
**setiap halaman** karena impor Python biasa, bukan karena SQL. Cocokkan hanya kata kunci
huruf besar (`SELECT`, `FROM`), sesuai konvensi penulisan SQL di proyek ini.

---

## 4. Aturan realtime

Dari keputusan pemilik di G2. **Mengikat semua halaman.**

### 4.1 Status dihitung dari tanggal, tidak pernah dibaca dari kolom `status`

**[mekanis]**

Kolom `pasca_tahap.status` adalah snapshot beku saat data digenerate. Dibaca apa adanya,
dashboard menyatakan "2.000 sedang OJT" selamanya — termasuk di 2027.

```sql
-- BENAR
WHERE tanggal_mulai <= :hari_ini AND tanggal_selesai > :hari_ini

-- SALAH
WHERE status = 'BERJALAN'
```

**Proksi mekanis (G9):** `status = 'BERJALAN'` atau `status='SELESAI'` di `core/metrics.py`.

Berlaku juga untuk `gelombang` (buka/tutup) dan `seleksi_tahap`.

### 4.2 `hari_ini()` adalah satu-satunya sumber waktu

**[mekanis]**

Disediakan `core/db.py`, bisa di-override pemilih tanggal lewat `session_state`. Tidak ada
halaman yang memanggil `date.today()` sendiri — kalau ada, pemilih tanggal tidak berlaku
seragam dan halaman jadi tidak konsisten satu sama lain.

### 4.3 Keadaan kosong yang bermartabat

**[manual]**

Karena waktu berjalan, tiap halaman **pasti** akan mengalami saat datanya nihil. Horison data
berakhir 2026-10-15 (lihat J10).

- Salah: *"Tidak ada data — gelombang terakhir tutup 345 hari lalu"* — penjelasan developer,
  melanggar P2, dan angka harinya di-hardcode
- Salah: `st.error(...)` atau `st.warning(...)` — keadaan kosong bukan kesalahan
- Benar: *"Tidak ada gelombang yang sedang dibuka"* + tautan ke gelombang terakhir yang selesai

Keadaan kosong adalah **fakta keadaan**, bukan pesan galat dan bukan permintaan maaf.

### 4.4 Tidak ada angka hari yang di-hardcode

**[mekanis]** — semuanya dihitung terhadap `hari_ini()`.

Yang dilarang: **jumlah hari** yang di-hardcode dalam teks yang tampil (`"345 hari lalu"`),
karena besok angkanya sudah salah. Yang boleh: **tanggal kalender** yang memang tetap, seperti
horison data 2026-10-15 di `CATATAN_DATA.md` — itu fakta yang tidak bergerak.

---

## 5. Daftar periksa tinjauan visual manual — G18

Dijalankan sungguhan lalu **dilihat mata**. Ini yang **tidak pernah dilakukan di v2** dan jadi
salah satu sebab v3 ada. AppTest headless tidak bisa menilai "chart terbaca sekali lihat".

Tema hasil G3 punya mode terang **dan** gelap, jadi tiap halaman diperiksa **dua kali**.

Per halaman, di kedua mode:

- [ ] Semua judul chart frasa benda, tidak ada yang berbunyi seperti kalimat temuan (P1)
- [ ] Tidak ada teks yang menjelaskan kenapa angkanya begitu (P2)
- [ ] Angka "terkini" masuk akal terhadap tanggal yang sedang dipilih (P3)
- [ ] Bentuk chart sesuai konvensinya (P4)
- [ ] Granularitas tidak dipotong tanpa alasan (P5)
- [ ] Label pendek, tidak ada kurung yang mengulang (P6)
- [ ] Tidak perlu menggulir untuk melihat isi pokok halaman (P7)
- [ ] Kontainer mengisi sampai bawah layar, tidak terpotong di tengah (P8)
- [ ] Tidak ada emoji (P10)
- [ ] **Kontras terbaca di kedua mode** — teks di atas latar, warna chart di atas latar
- [ ] Keadaan kosong diuji dengan memundurkan/memajukan pemilih tanggal (§4.3)
- [ ] Chart terbaca sekali lihat, tanpa perlu dipelajari

---

## 6. Ringkasan aturan mekanis — bahan G9

`tests/uji_disiplin.py` **ditulis ulang**, tidak disalin dari v2 — berkas v2 menegakkan D1
yang sudah dibatalkan dan meng-grep `ui.temuan_halaman(` yang tidak akan ada di v3.

> **Tabel ini harus berdiri sendiri.** G9 menulis tes langsung dari sini, jadi tiap
> pengecualian ditulis ulang di barisnya — jangan mengandalkan pembaca menoleh balik ke §2.

| # | Uji | Cakupan | Pengecualian wajib |
|---|---|---|---|
| 1 | Tanpa emoji | seluruh `*.py` | token `:material/...:` |
| 2 | Tanpa `st.caption(` | `app_pages/` | — |
| 3 | Tanpa nama tabel/kolom/jalur berkas di string tampil | `app_pages/` | **buang token `:material/...:` lebih dulu** — nama ikon juga ber-snake_case (`:material/pending_actions:`); tanpa ini merah palsu di hampir tiap halaman |
| 4 | Tanpa `SELECT`/`FROM` | `app_pages/` | **case-sensitive + batas kata** (`SELECT`, `FROM`) — kalau tidak, `from core import metrics` menggagalkan setiap halaman |
| 5 | Tanpa kolom PII | `app_pages/` | — |
| 6 | Tanpa `height=<angka>` pada `st.container` | `app_pages/` | `height=` pada `st.dataframe` boleh |
| 7 | Judul chart lolos proksi frasa benda | `app_pages/` | — |
| 7a | Argumen `keadaan_kosong(...)`: cek panjang & tanda baca **saja** | `app_pages/` | **jangan terapkan daftar kata penanda klaim** — pernyataan keadaan sah memakai bentuk negatif (*"Tidak ada gelombang yang sedang dibuka"*) |
| 8 | Tanpa `max(tanggal…)` sebagai pengganti hari ini | `core/metrics.py` | — |
| 9 | Tanpa literal `2026-09-15` / `TANGGAL_POTONG` | `app_pages/`, `core/metrics.py` | — |
| 10 | Tanpa `date.today()` / `datetime.now()` | seluruh v3 **kecuali** `core/db.py` | `core/db.py` justru wajib memilikinya |
| 11 | Tanpa `status = 'BERJALAN'` / `status='SELESAI'` | `core/metrics.py` | — |
| 12 | Tanpa `use_container_width` | seluruh v3 | — |
| 13 | `duckdb.connect` selalu `read_only=True` | `core/` | — |
| 14 | Tanpa `st.pills(` berisi >4 opsi | `app_pages/` | — |
| 15 | Tanpa padanan `temuan_halaman` di `components/` | `components/` | — |
| 16 | **Laporkan** label berkurung untuk ditinjau mata (P6) | `app_pages/` | tes ini **melaporkan, tidak menggagalkan** |

Uji 15 menjaga keputusan §1: kalau suatu hari muncul fungsi yang argumennya kalimat temuan,
tes ini yang menangkapnya.
