# Skema mockdbv3 — Section 2: PERENCANAAN

Section ini menjawab: **berapa orang yang boleh direkrut, untuk jabatan apa, di unit mana,
tahun berapa, dan dari jenjang/jurusan apa.** Keluaran akhirnya adalah pagu rekrutmen, yang
nanti dipakai section PROGRAM sebagai batas kuota.

Prinsip desain sama dengan section MASTER:
1. Semua tabel entitas punya primary key sendiri.
2. Tidak menyimpan nilai turunan yang bisa dihitung ulang lewat join/agregat.
3. Tidak ada kolom untuk kepentingan generator/analis — bentuknya database produksi.
4. Data yang berubah menurut waktu wajib punya kolom periode, bukan kolom "current".
5. Kosakata yang dipakai lintas tabel jadi tabel lookup, bukan teks bebas.

Tambahan prinsip khusus section ini:

6. **Usulan dan persetujuan adalah dua kejadian berbeda, jadi dua tabel berbeda.** Besar
   pemotongan tidak disimpan sebagai kolom — dihitung dari selisih dua tabel itu.
7. **Orang itu bilangan bulat.** Tidak ada kolom jumlah pegawai bertipe pecahan di section ini.

---

## Alur data section ini

```
formasi_tenaga_kerja  (target: berapa kursi seharusnya ada)
        ─┐
jumlah_pegawai_bulanan      (realisasi: berapa kursi terisi — dari MASTER)
        ─┤
proyeksi_kekosongan   (berapa kursi akan kosong tahun depan, per sebab)
        ─┘
             ↓  unit mengusulkan
        usulan_kebutuhan     (apa yang diminta unit)
             ↓  kantor pusat memutuskan
        pagu_rekrutmen       (apa yang disetujui)
             ↓
        (section PROGRAM)

  di jalur terpisah, ditetapkan HTD masing-masing perusahaan:
        pagu_rekrutmen_perusahaan  (jatah SubHolding / Anak Perusahaan)
```

---

## A. Siklus perencanaan

### `tahun_program`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun` | INTEGER UNIQUE | 2019 … 2026 |
| `status_tahun` | VARCHAR | Perencanaan, Berjalan, Selesai |

Induk untuk semua tabel di section ini. Alasannya cuma satu: integritas referensial —
`INTEGER tahun` polos tidak bisa dijaga, salah ketik `2204` lolos tanpa protes di 6 tabel,
FK ke lookup menolaknya.

Kolom tanggal siklus sengaja **tidak** ada di sini. Kapan unit mengajukan sudah direkam
`usulan_kebutuhan.tanggal_usulan`, kapan pagu turun sudah direkam
`pagu_rekrutmen.tanggal_ditetapkan`. Kalau disalin ke sini juga, dua sumber bisa berbeda
dan tidak ada yang tahu mana yang benar.

---

## B. Target dan proyeksi

### `formasi_tenaga_kerja`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun_program_id` | INTEGER FK → `tahun_program.id` | |
| `posisi_id` | INTEGER FK → `posisi.id` | unit `level = 2` × jabatan |
| `jumlah_formasi` | INTEGER | jumlah kursi yang disetujui ada |

UNIQUE (`tahun_program_id`, `posisi_id`)

FTK: berapa kursi yang **seharusnya** ada. Pasangannya adalah `jumlah_pegawai_bulanan` di MASTER
yang berisi berapa kursi yang **benar-benar** terisi. Gap FTK = formasi − realisasi, dihitung
lewat join, tidak disimpan (v1 menyimpannya sebagai kolom `gap_ftk` — itu nilai turunan).

### `jenis_kekosongan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Pensiun, Mengundurkan Diri, Meninggal Dunia, PHK, Mutasi Keluar |

### `proyeksi_kekosongan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun_program_id` | INTEGER FK → `tahun_program.id` | siklus: kapan proyeksi ini dibuat |
| `tahun_proyeksi_id` | INTEGER FK → `tahun_program.id` | untuk tahun berapa |
| `posisi_id` | INTEGER FK → `posisi.id` | unit `level = 2` × jabatan |
| `jenis_kekosongan_id` | INTEGER FK → `jenis_kekosongan.id` | |
| `jumlah_kekosongan` | INTEGER | |

UNIQUE (`tahun_program_id`, `tahun_proyeksi_id`, `posisi_id`, `jenis_kekosongan_id`)

**Dua kolom tahun, bukan satu.** Siklus perencanaan tidak hanya memproyeksikan satu tahun
ke depan: ada rencana tahunan dan ada rencana lima tahunan (RJPP, RUPTL), dan pensiun —
terutama yang tepat waktu — memang bisa dihitung jauh di muka. Jadi siklus 2022 bisa
menghasilkan proyeksi untuk 2023 sampai 2027.

Kalau hanya ada satu kolom tahun, proyeksi 2026 yang dibuat di siklus 2022 akan tertimpa
proyeksi 2026 yang dibuat di siklus 2025, dan pertanyaan "seberapa meleset proyeksi jangka
panjang HST?" jadi tidak bisa dijawab. Dengan dua kolom, keduanya hidup berdampingan.

Ini juga syarat supaya jalur Ikatan Dinas bisa ditelusuri asal-usulnya: kelas yang dibuka
2022 mengisi kursi 2026, jadi harus ada proyeksi 2026 yang sudah dibuat di siklus 2022.

Bentuk panjang (satu baris per sebab), bukan lebar seperti v1 yang punya kolom `pensiun`,
`mengundurkan_diri`, `meninggal_dunia`, `phk` bersebelahan. Alasannya: menambah sebab baru
tidak mengubah struktur tabel, dan agregat per sebab jadi `GROUP BY` biasa.

Nilai `jumlah` bilangan bulat. v1 mengisi kolom ini dengan pecahan (`pensiun = 0.0143`)
karena angka harapan model probabilistik ditulis apa adanya — di database produksi yang
dicatat adalah jumlah orang, bukan ekspektasi statistik.

---

## C. Usulan dari unit

### `usulan_kebutuhan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun_program_id` | INTEGER FK → `tahun_program.id` | |
| `posisi_id` | INTEGER FK → `posisi.id` | unit `level = 2` × jabatan; usulan lahir di sini |
| `jumlah_usulan` | INTEGER | |
| `tanggal_usulan` | DATE | |

UNIQUE (`tahun_program_id`, `posisi_id`)

Apa yang diminta unit, apa adanya, sebelum keputusan kantor pusat. Baris ini tidak pernah
diubah setelah pagu turun — kalau ditimpa, angka pemotongan hilang dan tidak bisa dianalisis.

**Tidak ada `jenjang_pendidikan_id` di sini.** Unit mengusulkan berdasarkan jabatan/posisi
yang kosong, titik. Jenjang pendidikan ditetapkan tim HST saat menyusun pagu. Sebagian
besar sudah terikat jabatannya lewat `aturan_grade_masuk` (Junior Technician = G1), tapi
tidak seluruhnya: **G1 bisa diisi SMK atau D3**, dan pemilihannya keputusan HST.

Karena itu jenjang pertama kali muncul di `pagu_rekrutmen`, dan pergeserannya jadi sesuatu
yang bisa dianalisis — "unit mengusulkan 5 Junior Technician, HST menetapkannya sebagai
kursi D3, bukan SMK".

Kolom `sub_bidang`, `kelompok_jabatan`, `kode_grade`, `level` yang ada di v1 tidak diulang
di sini: semuanya melekat pada jabatan lewat `posisi` → `klasifikasi_jabatan` di MASTER.

---

## D. Pagu (keputusan kantor pusat)

### `pagu_rekrutmen`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun_program_id` | INTEGER FK → `tahun_program.id` | siklus: kapan pagu diputuskan |
| `tahun_terisi_id` | INTEGER FK → `tahun_program.id` | untuk mengisi kursi tahun berapa |
| `usulan_kebutuhan_id` | INTEGER FK → `usulan_kebutuhan.id`, NULL | NULL = pagu tanpa usulan (inisiatif pusat) |
| `posisi_id` | INTEGER FK → `posisi.id` | unit `level = 2` × jabatan |
| `jenjang_pendidikan_id` | INTEGER FK → `jenjang_pendidikan.id` | |
| `jalur_rekrutmen_id` | INTEGER FK → `jalur_rekrutmen.id` | Mandiri atau RBB |
| `jumlah_pagu` | INTEGER | jumlah yang disetujui |
| `tanggal_ditetapkan` | DATE | |

UNIQUE (`tahun_program_id`, `tahun_terisi_id`, `posisi_id`, `jenjang_pendidikan_id`, `jalur_rekrutmen_id`)

Besar pemotongan = `jumlah_usulan` − `jumlah_pagu` lewat join ke `usulan_kebutuhan`.
Tidak disimpan sebagai kolom (v1: `usulan_sebelum_potong` bersebelahan dengan `jumlah`,
sehingga satu baris mengaku sebagai dua kejadian sekaligus).

Kolom `keterangan` v1 yang berisi "3T" atau "Rekrut 2019" tidak ada di sini: "Rekrut 2019"
sudah jadi `tahun_program_id`, dan status 3T adalah sifat lokasi — lihat catatan perubahan
MASTER di bawah.

`jalur_rekrutmen_id` ada di tingkat pagu karena pembagian kursi Mandiri vs RBB memang
diputuskan saat penetapan pagu, bukan belakangan saat program_rekrutmen dibuka.

**`tahun_terisi_id` terpisah dari `tahun_program_id`** karena keputusan dan pemenuhannya
tidak selalu di tahun yang sama. Jalur Ikatan Dinas paling ekstrem: pagu diputuskan 2022,
kelas kuliah 2022-2025, kursinya baru terisi 2026. Tapi ini bukan kolom khusus ikatan
dinas — jalur Mandiri pun sering berjarak: program_rekrutmen 2024, OJT sepanjang 2024-2025, SK
penempatan 2025.

Dengan satu kolom saja, dua-duanya salah: ditulis 2022 berarti kursinya seolah terisi 2022;
ditulis 2026 berarti keputusannya seolah dibuat 2026, padahal anggarannya sudah lama keluar.

### `pagu_rekrutmen_perusahaan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun_program_id` | INTEGER FK → `tahun_program.id` | |
| `perusahaan_id` | INTEGER FK → `perusahaan.id` | SubHolding atau Anak Perusahaan |
| `jenjang_pendidikan_id` | INTEGER FK → `jenjang_pendidikan.id` | |
| `jalur_rekrutmen_id` | INTEGER FK → `jalur_rekrutmen.id` | |
| `jumlah_pagu` | INTEGER | |
| `tanggal_ditetapkan` | DATE | |

UNIQUE (`tahun_program_id`, `perusahaan_id`, `jenjang_pendidikan_id`, `jalur_rekrutmen_id`)

Pagu SubHolding / Anak Perusahaan dipisah dari `pagu_rekrutmen`, bukan digabung dengan
kolom NULL-able, karena dua alasan:

1. **Penetapnya pihak berbeda.** Pagu holding ditetapkan HTD holding; pagu SH/AP ditetapkan
   HTD masing-masing perusahaan. Dua proses berbeda, sama seperti usulan dan pagu dipisah.
2. **Bentuk datanya berbeda.** SH/AP tidak punya baris `unit` (dangkal per keputusan
   cakupan) dan tidak memakai katalog `jabatan` PLN. Kalau dipaksa satu tabel, `posisi_id`
   harus NULL-able dan `perusahaan_id` ditambahkan, dan tiap query wajib menghafal aturan kapan kolom itu
   berlaku — persis pola yang bikin v1 sulit dibaca.

Ongkosnya: "total pagu satu tahun" perlu UNION dua tabel, dan gampang lupa satu sisi.
Ditutup dengan satu view gabungan saat implementasi.

Pagu SH/AP tidak punya `usulan_kebutuhan_id`: usulan internal SH/AP tidak dimodelkan.
Perannya di sini sebagai **acuan kebutuhan penempatan**, bukan sebagai hasil proses
perencanaan holding.

### ~~`pagu_program_studi`~~ — dipindah ke section PROGRAM

Daftar jurusan yang diterima **tidak** menempel ke baris pagu. Yang diumumkan ke pelamar
adalah **profesi_rekrutmen**, hasil gabungan pagu banyak unit, dan daftar jurusannya seragam
se-Indonesia untuk satu profesi_rekrutmen. Menempelkannya ke tiap baris pagu berarti menyimpan
daftar yang sama berulang kali di ratusan baris — dan membuka peluang dua unit punya
daftar berbeda untuk profesi_rekrutmen yang sama, sesuatu yang tidak terjadi di lapangan.

Jalur dari pagu ke jurusan tetap ada, lewat sub bidang:

```
pagu_rekrutmen.posisi_id
   → posisi.jabatan_id                        (MASTER)
   → klasifikasi_jabatan.sub_bidang_id        (MASTER)
   → pemetaan_jurusan_sub_bidang                (MASTER)
   → jurusan
```

`pemetaan_jurusan_sub_bidang` adalah **referensi** (jurusan apa yang relevan dengan sub
bidang ini — tidak berubah tiap program_rekrutmen). Daftar jurusan yang benar-benar dibuka adalah
**keputusan**, berubah tiap program_rekrutmen, dan tempatnya menempel ke profesi_rekrutmen di section PROGRAM.
Dipisah karena alasan yang sama seperti usulan dipisah dari pagu: kalau digabung, tidak
bisa lagi dijawab "tahun ini jurusan relevan apa saja yang justru tidak dibuka".


**Catatan nama:** akhiran `_perusahaan` di sini adalah pengganti singkatan **SH/AP**, yaitu
**SubHolding dan Anak Perusahaan**. Nama lamanya `..._shap`, diganti karena "shap" singkatan
internal yang tidak bisa ditebak siapa pun di luar tim — termasuk chatbot yang membaca skema
ini. Pilihan kata "perusahaan" cocok karena baris-baris ini memang menunjuk
`perusahaan.id` yang berkategori SubHolding atau Anak Perusahaan, bukan Holding.

---

## E. Aturan dan syarat

### `aturan_grade_masuk`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `jalur_rekrutmen_id` | INTEGER FK → `jalur_rekrutmen.id` | |
| `jenjang_pendidikan_id` | INTEGER FK → `jenjang_pendidikan.id` | |
| `pengalaman_minimal_bulan` | INTEGER, NULL | NULL untuk jalur fresh graduate |
| `grade_id` | INTEGER FK → `grade.id` | grade saat diangkat |
| `berlaku_mulai` | DATE | |
| `berlaku_sampai` | DATE, NULL | NULL = masih berlaku |

UNIQUE (`jalur_rekrutmen_id`, `jenjang_pendidikan_id`, `pengalaman_minimal_bulan`,
`berlaku_mulai`)

Ini rumah untuk aturan yang tertunda dari section MASTER: SMK/D3 → G1, S1/D4 → G2, S2 → G3.
Ditaruh sebagai data bertanggal, bukan di dalam kode generator, karena aturan grade masuk
memang bisa berubah antar tahun dan perubahan itu harus bisa ditelusuri.

`jalur_rekrutmen_id` ada karena aturan pendidikan → grade **tidak berlaku untuk Pro Hire**.
Pro Hire merekrut orang berpengalaman untuk grade tinggi, disiapkan menjabat dalam sekitar
satu tahun, jadi grade masuknya di kisaran S2 ke atas apa pun ijazahnya. Tanpa kolom jalur,
satu baris "S1 → G2" akan diterapkan ke pelamar Pro Hire berpengalaman 10 tahun dan
menghasilkan grade yang salah.

`pengalaman_minimal_bulan` membuat satu jalur bisa punya beberapa tingkat: Pro Hire dengan
5 tahun pengalaman dan Pro Hire dengan 12 tahun tidak masuk di grade yang sama. Untuk jalur
Mandiri/RBB kolom ini NULL dan aturannya murni pendidikan.

Contoh isi:

```
 id  jalur      jenjang  pengalaman_min  grade  berlaku_mulai
  1  MANDIRI    SMK      NULL            G1     2016-01-01
  2  MANDIRI    D3       NULL            G1     2016-01-01
  3  MANDIRI    S1       NULL            G2     2016-01-01
  4  MANDIRI    S2       NULL            G3     2016-01-01
  5  RBB        S1       NULL            G2     2020-01-01
  6  PRO_HIRE   S1        60             G3     2022-01-01
  7  PRO_HIRE   S1       144             MM     2022-01-01
  8  PRO_HIRE   S2        60             MM     2022-01-01
```

Angka pengalaman dan grade di atas ilustrasi, bukan aturan PLN yang sudah dikonfirmasi —
perlu dipastikan saat putaran populasi.

### `syarat_pelamar`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `jalur_rekrutmen_id` | INTEGER FK → `jalur_rekrutmen.id` | |
| `jenjang_pendidikan_id` | INTEGER FK → `jenjang_pendidikan.id` | |
| `usia_maksimal` | INTEGER | |
| `pengalaman_minimal_bulan` | INTEGER, NULL | NULL untuk jalur fresh graduate; diisi untuk Pro Hire |
| `ipk_minimal` | DECIMAL(3,2), NULL | NULL untuk jenjang SMA/SMK (pakai nilai rapor/SKHU) |
| `nilai_minimal` | DECIMAL(4,2), NULL | untuk SMA/SMK |
| `berlaku_mulai` | DATE | |
| `berlaku_sampai` | DATE, NULL | |

Syarat berbeda per jalur (PLN Mandiri S1 ≤ 27 tahun, RBB S1 ≤ 30) dan berubah antar tahun,
jadi berupa data bertanggal, bukan konstanta di kode.

---

## Perubahan yang sudah diterapkan ke section MASTER

- **Status 3T** dipindah ke MASTER sebagai `peraturan_3t` + `daerah_3t` (bertanggal), bukan
  kolom boolean, karena daftar daerah tertinggal ditetapkan pemerintah per periode dan
  diperbarui. Kolom `keterangan` v1 di `pagu_rekrutmen` jadi tidak diperlukan.

---

## Daftar tabel section PERENCANAAN (9 tabel)

| # | tabel | isi |
|---|---|---|
| 1 | `tahun_program` | siklus perencanaan per tahun |
| 2 | `formasi_tenaga_kerja` | target jumlah kursi (FTK) per unit × jabatan × tahun |
| 3 | `jenis_kekosongan` | lookup sebab kekosongan |
| 4 | `proyeksi_kekosongan` | proyeksi kursi kosong per sebab |
| 5 | `usulan_kebutuhan` | permintaan unit, sebelum dipotong |
| 6 | `pagu_rekrutmen` | keputusan kantor pusat, per jalur |
| 7 | `pagu_rekrutmen_perusahaan` | pagu SubHolding/Anak Perusahaan, ditetapkan HTD masing-masing |
| 8 | `aturan_grade_masuk` | jenjang pendidikan → grade saat diangkat |
| 9 | `syarat_pelamar` | batas usia & nilai per jalur × jenjang |

---

## Yang perlu kamu putuskan

1. **Nama tabel dan kolom** — semua di atas usulan saya.
2. ~~Grain unit~~ — sudah diputuskan: **semua tabel di section ini wajib menunjuk unit
   ber-`level = 2`**, tidak ada NULL. Dikonfirmasi lewat `Sample-02-Contoh Format
   Pagu FTK 2026.xlsx`, yang memecah FTK per unit dengan "KANTOR INDUK" sebagai salah satu
   baris unit, sejajar dengan unit pelaksana lain. Konsekuensi ke MASTER: `unit` harus punya
   baris ber-`jenis_unit='Kantor Induk'` untuk tiap unit induk.

   Menyusul keputusan tabel `unit` tunggal berjenjang di MASTER, pasangan kolom
   `unit_induk_id` + `unit_pelaksana_id` di seluruh section ini menciut jadi satu `unit_id`,
   lalu menciut sekali lagi jadi `posisi_id` setelah `posisi` (unit × jabatan) jadi tabel
   tersendiri di MASTER — sekaligus menutup peluang muncul kombinasi unit-jabatan yang
   tidak masuk akal.
   Rekap ke tingkat induk lewat `unit.unit_atasan_id`, bukan lewat kolom kedua yang harus
   dijaga konsistensinya.

   Setelah Kantor Pusat ikut digranulasi, `level = 2` mencakup **Bidang di Kantor Pusat**,
   **Bidang di kantor unit induk**, dan **Unit Pelaksana** — semuanya diperlakukan sama,
   tanpa cabang khusus untuk Kantor Pusat. Konsekuensinya jumlah baris FTK/usulan/pagu naik
   cukup banyak dibanding rancangan yang mengagregasi Kantor Pusat.
3. ~~Penanda 3T~~ — sudah diputuskan: tabel bertanggal di MASTER (lihat di atas).
4. ~~Revisi pagu~~ — sudah diputuskan: **pagu tahunan saja**, tidak ada versi/riwayat revisi.

## Catatan yang muncul dari contoh angka

Satu baris `usulan_kebutuhan` bisa menghasilkan **beberapa** baris `pagu_rekrutmen` karena
pagu dipecah per jalur (Mandiri/RBB). Jadi besar pemotongan dihitung sebagai
`jumlah_usulan − SUM(jumlah_pagu) GROUP BY usulan_kebutuhan_id`, bukan pengurangan
baris-ke-baris. Kalau ternyata di lapangan usulan pun sudah dipecah per jalur sejak awal,
`usulan_kebutuhan` perlu `jalur_rekrutmen_id` juga dan hubungannya jadi satu-ke-satu.
