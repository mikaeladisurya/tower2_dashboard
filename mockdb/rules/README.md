# rules/ — aturan generator

Hasil penyulingan **49 temuan** di `knowledge/findings.md` jadi aturan yang bisa
dieksekusi. File-file ini adalah **input** generator Python di `build/`, dan sengaja
dibuat supaya bisa diedit tangan tanpa menyentuh kode.

## Peta file

| File | Isi | Temuan utama |
|---|---|---|
| `kohort.yaml` | **Mengunci skala seluruh database.** Ukuran kohort per tahun, jalur, jeda pipeline, durasi tahapan | F-048, F-035, F-044, F-041 |
| `funnel.yaml` | Konversi & kehadiran tiap tahap, volume pendaftar, funnel RBB | F-019, F-020, F-047, F-046 |
| `administrasi.yaml` | Umur & IPK per jalur, berkas wajib, alasan gagal, siklus pendaftaran | F-022, F-043, F-034, F-033 |
| `tahapan.yaml` | Kosakata tahapan, mode, pemilik proses, sistem sumber, passing grade, 43 kota | F-023, F-024, F-018, F-028 |
| `angkatan.yaml` | Peta nomor per gelombang + **lubang yang dibiarkan kosong**, struktur program→profesi, kode profesi, nomor tes | F-008, F-009, F-003, F-021 |
| `demografi.yaml` | **Gender per tahun (65:35→86:14)**, jenjang, usia, IPK, prodi, alamat, blok fisik & visus | F-048, F-038, F-020, F-034 |
| `jabatan.yaml` | Larangan struktural, grade per pendidikan, pembidangan, aturan penempatan | F-042, F-005 |
| `attrition.yaml` | Laju 2,7%, sebab keluar, carve-out, **patahan definisi turnover**, runtun headcount 2016–2025 | F-036, F-045, **F-049**, F-048 |
| `kelengkapan.yaml` | Kelengkapan field bertahap per tahun, field yang tak pernah ada | keputusan user, F-017, F-034 |
| `bidang_jabatan.csv` | 109 kata kunci klasifikasi jabatan (*first-match-wins*) — sudah dipakai langkah 02 | — |

## Konvensi

**`status_sumber`** — muncul di banyak tempat, artinya:

| Nilai | Arti |
|---|---|
| *(tidak ada)* | angka NYATA dari sumber tersitasi |
| `TURUNAN` | dihitung dari angka nyata lewat penalaran yang ditulis di tempat |
| `DIMODELKAN` | **tidak ada di sistem asli sama sekali** — direka penuh, wajib ditandai di dashboard |
| `ASUMSI` | tidak ada sumber, dan tidak diturunkan dari apa pun — tebakan wajar |

**`rujukan`** — kode temuan di `knowledge/findings.md`. Kalau sebuah angka tidak punya
`rujukan` maupun `status_sumber`, itu bug — laporkan.

**`peringatan`** — jebakan yang sudah pernah hampir terinjak. Baca sebelum mengubah
angka di sekitarnya.

## Urutan kausal

Generator tidak boleh mengarang jumlah pelamar lalu berharap jumlah diterima keluar
benar. Arahnya terbalik:

```
kohort.yaml (berapa DITERIMA — angka nyata dari laporan PLN)
    ↓ dibagi laju
funnel.yaml (berapa yang harus MENDAFTAR)
    ↓
demografi.yaml (siapa mereka)
    ↓ diuji dengan
administrasi.yaml (siapa yang gugur, dan KENAPA)
    ↓
tahapan.yaml (perjalanan tiap orang)
    ↓ dibatasi
jabatan.yaml (ke mana mereka ditempatkan)
```

`attrition.yaml` masuk dari sisi lain — ia menghasilkan **kebutuhan** yang jadi alasan
kohort itu ada. `kelengkapan.yaml` bekerja terakhir, **mengosongkan** field yang belum
ada di tahun bersangkutan.

## Tiga hal yang tidak boleh dilupakan

1. **Jangan mengisi mundur.** Field yang belum ada di 2019 harus NULL di 2019.
   (`kelengkapan.yaml`)
2. **Jangan menyaring jabatan pakai `jenjang`.** Team Leader juga G2. Pakai
   `kelompok_jabatan`. (`jabatan.yaml`)
3. **Jangan menderetkan angka PLN lintas tahun begitu saja.** Tiga jebakan berbeda:
   penurunan headcount 2023 = carve-out bukan attrition (F-045); definisi turnover
   berubah di 2021 (F-049); angka tidak konsisten antar tabel dalam satu laporan (F-040).
   (`attrition.yaml`)
4. **Jangan mengisi lubang nomor angkatan.** Lubang itu bukti katalog publik tidak
   lengkap. (`angkatan.yaml`)

## Verifikasi

```
python mockdb/build/00_verifikasi_rules.py
```

±160 cek silang antar file. Angka di file-file ini saling bergantung, dan kesalahannya
**tidak memunculkan error** — cuma menghasilkan database yang diam-diam salah. Contoh
yang sudah tertangkap skrip ini saat aturan pertama ditulis: bobot alasan gagal
administrasi berjumlah 0,98 (bukan 1,00) dan `end_to_end_pct` RBB tertulis 0,4418
padahal hasil perkalian laju tahapnya 0,2749 — cukup untuk meleset ~60% di volume RBB.

Jalankan setiap kali menyentuh folder ini.

## Kalau angka kalibrasi berubah

Beberapa angka bergantung pada tafsir yang belum dikonfirmasi tim HTD. Titik ubahnya
sengaja dibuat tunggal:

| Kalau ternyata… | Ubah | Efek |
|---|---|---|
| "598.395 pelamar" ternyata aplikasi, bukan orang | `funnel.yaml → end_to_end_pct` | volume pendaftar naik ~2,5×; jumlah diterima tidak berubah |
| rekrutmen dicatat di tahun seleksi, bukan tahun berikutnya | `kohort.yaml → jeda_pipeline.jeda_bulan: 0` | tabel kohort digeser satu tahun |
| rekrutmen SMK tingkat unit ternyata tetap berjalan | `angkatan.yaml → smk_pelaksana.dimodelkan: true` + porsi SMK di `demografi.yaml` | seri SMK hidup lagi |
| tiap program Diaspora 2023 punya angkatan sendiri | `angkatan.yaml → 82 jadi 82/83/84` | lubang tinggal 85 |
| urutan tes berbeda per gelombang | `tahapan.yaml → urutan` | tidak perlu ubah kode |
| skor FHCI ternyata diserahkan ke PLN | `kelengkapan.yaml → per_jalur.rbb` | kolom skor RBB tidak lagi kosong permanen |
