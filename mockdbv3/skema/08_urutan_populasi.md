# Urutan populasi mockdbv3

Dihitung dari relasi FK di keenam file skema, bukan dari urutan section. 70 tabel, 8 lapis,
**tidak ada siklus** — artinya seluruh basis data bisa diisi sekali jalan tanpa perlu
menonaktifkan FK atau mengisi kolom belakangan.

Aturannya sederhana: sebuah tabel baru boleh diisi setelah semua tabel yang ditunjuk FK-nya
terisi. `unit` tidak dihitung bergantung pada dirinya sendiri walau punya `unit_atasan_id` —
cukup mengisi baris level 1 sebelum level 2.

---

## Lapis 0 — 21 tabel, tanpa dependensi apa pun

Bisa dikerjakan sekarang, dan bisa paralel. Dikelompokkan menurut apa yang dibutuhkan untuk
mengisinya, bukan menurut section asalnya.

### A. Fakta dunia nyata — harus akurat, bukan karangan

| tabel | perkiraan baris | sumber |
|---|---|---|
| `provinsi` | 38 | data resmi |
| `jurusan` | 150-300 | daftar prodi + jurusan SMK |
| `jenjang_pendidikan` | 6 | SMA, SMK, D3, D4, S1, S2 |
| `grade` | 10-12 | istilah PLN: G1, G2, G3, MAK, MM, MA, MD, JE, SSP, SPC |
| `kelompok_jabatan` | 6-10 | Officer, Junior Officer, Team Leader, Assistant Manager, Manager, VP |
| `jenis_unit` | 4 | Divisi, Bidang, Unit Induk, Unit Pelaksana |
| `lini_bisnis` | 8-12 | Kantor Pusat, Distribusi, Transmisi, Pembangkitan, Penyaluran, Diklat, Sertifikasi, … |
| `peraturan_3t` | 2-3 | mis. Perpres 63/2020 |

`jurusan` yang paling berat dan paling menentukan. Ia memberi makan
`pemetaan_jurusan_sub_bidang` di lapis 2 — lapisan penilaian yang wajib kamu review dan tidak
boleh ditebak generator.

### B. Kosakata internal PLN — kamu yang menentukan isinya

| tabel | perkiraan baris | catatan |
|---|---|---|
| `bidang` | 2-4 | TEKNIK / NON-TEKNIK |
| `fungsi` | 5-10 | Enjiniring, Pemeliharaan, Operasi, Perencanaan, … |
| `jalur_rekrutmen` | 3 | MANDIRI, RBB, IKATAN_DINAS |
| `tahap_referensi` | 13 | daftarnya sudah dikonfirmasi lewat alur tiap jalur |
| `jenis_program` | 4 | Reguler, Pro Hire, PLN Group, Ikatan Dinas |
| `metode_kelulusan` | 3 | Ambang Nilai, Peringkat, Kualitatif |
| `jenis_kekosongan` | 4-5 | pensiun, mengundurkan diri, meninggal dunia, PHK |
| `angkatan` | 20-40 | Sample-05 menyebut Angkatan 91 & 92 untuk 2026 — penomorannya berlanjut, jadi angkatan 2016 ada di kisaran 70-an |

### C. Lookup sepele — bisa langsung, tidak perlu diskusi

`agama` (6) · `status_perkawinan` (4) · `alasan_gugur` (7) · `alasan_berhenti` (5)

### D. Sumbu waktu

`tahun_program` — satu baris per tahun sepanjang rentang mock. Perlu diputuskan: mulai tahun
berapa sampai berapa.

---

## Lapis 1 — 8 tabel

`kota_kabupaten` (butuh `provinsi`) · `sub_bidang` (butuh `bidang`) · `jabatan` ·
`komponen_nilai` · `tahap_jalur` · `syarat_pelamar` · `aturan_grade_masuk` ·
`program_rekrutmen`

## Lapis 2 — 9 tabel

`perusahaan` · `institusi_pendidikan` · `vendor` · `venue` · `daerah_3t` ·
`klasifikasi_jabatan` · `pemetaan_jurusan_sub_bidang` · `profesi_rekrutmen` · `kandidat`

## Lapis 3 — 10 tabel

`unit` · `institusi_jurusan` · `posisi`* · `tahap_program` · `bukaan_profesi` ·
`pagu_rekrutmen_perusahaan` · `pegawai` · `kandidat_alamat` · `kandidat_data_fisik` ·
`kandidat_pengalaman_kerja` · `kandidat_sertifikasi`

## Lapis 4 — 7 tabel

`posisi` · `kandidat_pendidikan` · `kelas_ikatan_dinas` · `lokasi_tes` ·
`tahap_program_komponen` · `bukaan_profesi_jurusan` · `bukaan_profesi_pagu_perusahaan`

## Lapis 5 — 6 tabel

`formasi_tenaga_kerja` · `jumlah_pegawai_bulanan` · `usulan_kebutuhan` ·
`proyeksi_kekosongan` · `kandidat_ikatan_dinas` · `pendaftaran`

## Lapis 6 — 2 tabel

`pagu_rekrutmen` · `pendaftaran_tahap`

## Lapis 7 — 7 tabel

`bukaan_profesi_pagu` · `kelas_ikatan_dinas_pagu` · `pendaftaran_nilai` ·
`pemeriksaan_kesehatan` · `pembidangan` · `penempatan_ojt` · `sk_penempatan`

---

## Tabel yang paling banyak dirujuk

Kalau salah di sini, salahnya menyebar ke seluruh basis data:

```
kota_kabupaten      9 tabel merujuk
kandidat            8
jenjang_pendidikan  6
posisi              6
jalur_rekrutmen     6
tahun_program       6
sub_bidang          5
```

Empat dari tujuh ada di lapis 0 atau 1. Itu alasan tambahan untuk tidak buru-buru di lapis
awal walau tabelnya kecil-kecil.

---

## Yang perlu diputuskan sebelum mulai

1. **Rentang tahun mock.** Menentukan isi `tahun_program`, penomoran `angkatan`, dan volume
   seluruh data. Kalau 10 tahun, 2016-2026?
2. **Bentuk berkas.** Satu CSV per tabel di `mockdbv3/data/`, lalu satu skrip yang memuatnya
   ke DuckDB? Atau langsung SQL INSERT? CSV lebih mudah kamu periksa dan koreksi manual.
3. **Urutan pengerjaan di dalam lapis 0.** Usul saya mulai dari kelompok C dan D (cepat,
   tanpa diskusi), lalu B (kosakata, butuh keputusanmu), lalu A — dengan `jurusan` paling
   akhir karena paling besar dan paling berpengaruh.
