# Catatan cacat sebaran — untuk rebuild generator berikutnya

**Status: dicatat, belum dikerjakan.** Ditemukan 2026-08-19 saat memverifikasi data untuk
`recruitment_dashboardv2`. Perbaikannya sengaja ditunda sampai generator dibangun ulang —
lihat alasan di §"Kenapa ditunda" — jadi berkas ini adalah pengingat, bukan tugas terbuka.

Akar masalahnya sudah diperingatkan `README.md` sendiri: *"aturan yang benar tidak menjamin
generator menaatinya."* Lima bidang di bawah adalah contoh baru dari peringatan itu:
`00b_verifikasi_keluaran.py` tidak punya cek sebaran, jadi lolos tanpa terdeteksi.

## Cara verifikasi ulang

```python
import duckdb
con = duckdb.connect("mockdb/out/rekrutmen.duckdb", read_only=True)

def sebaran(tabel, kolom, filt=""):
    df = con.execute(f"select {kolom} v, count(*) n from {tabel} {filt} group by 1 order by 2 desc").df()
    df = df[df["v"].notna()]
    top, bot = df["n"].iloc[0], df["n"].iloc[-1]
    print(f"{tabel}.{kolom}: {len(df)} nilai, top/bawah={top/bot:.2f}")
```

Rasio top/bawah mendekati **1,0** = kemungkinan besar `rng.choice()` seragam tanpa bobot.
Rasio berpola benar biasanya di atas 2× (lihat kolom pembanding di tabel bawah).

## Temuan

| Bidang | Rasio top/bawah | Nilai unik | Pembanding yang benar |
|---|---:|---:|---|
| `kandidat.kota_domisili` | **1,05** | 43 | `seleksi_tahap.lokasi_kota` = 37,7× |
| `kandidat.kota_asal` | **1,07** | 43 | — |
| `kandidat.tempat_lahir` | **1,04** | 43 | — |
| `kandidat.ukuran_baju` | **1,02** | 4 | — |
| `kandidat_pendidikan.sekolah_universitas` | **1,02** | 15 (dari 68) | `program_studi` = 10,1× |

Pembanding yang sudah berpola benar (tidak perlu disentuh): `propinsi_domisili` 16,4× ·
`agama` 867× · `status_perkawinan` 184× · `degree` (jenjang) 21,1× · `program_studi` 10,1× ·
`lokasi_kota` (kota tes) 37,7× · `vendor_id` 4,0× · `bidang_pembidangan` 11,4× ·
`unit_induk` (penempatan) 74,5×.

### Detail 1 — `kota_domisili` diundi seragam

43 kota, top/bawah 1,05. `demografi.yaml` **sudah** mendefinisikan `sebaran_provinsi_asal`
(diturunkan dari sebaran pegawai per unit induk — Jawa dominan, Papua kecil kecuali gelombang
afirmasi) tapi generator mengabaikannya:

```python
# mockdb/build/08_kandidat_pendaftaran.py:557
kota_domisili = rng.choice(kota_master, size=n_kandidat)   # tanpa bobot p=
```

**Akibat ke dashboard:** grafik "sebaran kandidat per provinsi" akan tampak berpola, tapi itu
artefak — provinsi dengan lebih banyak kota di `kota_master` otomatis dapat lebih banyak
kandidat, bukan karena minat pelamar nyata.

### Detail 2 — kota × provinsi tidak koheren

Kota dan provinsi diundi **independen** (baris 555 & 557 dipanggil terpisah), sehingga
pasangannya tidak masuk akal:

```
kota_domisili='Jakarta', propinsi_domisili='Jawa Barat'   -> 1.208 kandidat
kota_domisili='Jakarta', propinsi_domisili='DKI Jakarta'  ->   705 kandidat
```

1.334 pasangan kota-provinsi unik di data, padahal seharusnya 43 (satu per kota).
**Akibat:** tabel apa pun yang menampilkan kota & provinsi bersisian akan memalukan.

### Detail 3 — `kota_asal` adalah salinan `kota_domisili`

```python
# mockdb/build/08_kandidat_pendaftaran.py:640
alamat_domisili[i] if punya_asal[i] else "", kota_domisili[i] if punya_asal[i] else "",
#                                             ^^^^^^^^^^^^^^^ harus kota_asal[i], variabel ini tidak pernah dibuat
```

Identik di seluruh 199.310 baris yang punya kedua alamat. `demografi.yaml` sudah menulis
`pct_domisili_beda_provinsi_dari_asal: 0.34` — aturan itu tidak pernah dieksekusi. Fitur
"dua blok alamat" (F-034, salah satu perubahan besar di ERD v2 dari ERD lama) jadi kosmetik.

### Detail 4 — almamater tanpa sinyal

15 dari 68 nilai unik `sekolah_universitas` muncul (filter `pendidikan_terakhir`), top/bawah
1,02. Konversi pelamar→diterima antar kampus 3,10%–3,76% — rentang yang terlalu sempit untuk
jadi insight apa pun.

```sql
-- provokasi: hampir semua kampus sama persis konversinya
with t as (
  select kp.sekolah_universitas kampus, count(*) pelamar,
         sum(case when p.hasil_akhir='DITERIMA' then 1 else 0 end) diterima
  from pendaftaran p join kandidat_pendidikan kp on kp.kandidat_id=p.kandidat_id
  where kp.pendidikan_terakhir group by 1)
select kampus, pelamar, diterima, round(100.0*diterima/pelamar,2) pct from t order by pct desc
```

## Kenapa ditunda

Diputuskan 2026-08-19: dashboard v2 sedang dibangun di atas snapshot data yang sudah
diverifikasi (30 metrik, semua SQL dijalankan & angkanya tercatat di
`recruitment_dashboardv2/docs/metrik.md`). Mengubah generator sekarang berarti menggeser
aliran RNG dan membatalkan verifikasi itu. Perbaikan ditunda ke rebuild generator berikutnya,
bukan disisipkan di tengah pekerjaan dashboard.

**Dampak sementara ke dashboard v2:** halaman "Kandidat & Pasar" tidak menampilkan sebaran
asal per provinsi maupun analisis almamater — datanya diketahui cacat. Sebagai gantinya,
jangkar perhatian halaman itu adalah peta volume tes per kota (`lokasi_kota`, sudah berpola
benar). Lihat `recruitment_dashboardv2/docs/backlog.md` (B7) dan `docs/wireframe.md` halaman 4.

## Usulan perbaikan untuk rebuild berikutnya

1. **Geografi koheren.** Pasangan kota→provinsi tetap dari master (bukan dua `rng.choice`
   independen); bobot kota mengikuti `sebaran_provinsi_asal` yang sudah ada di
   `rules/demografi.yaml`.
2. **Kota tes berkorelasi domisili.** Mayoritas kandidat memilih kota tes = kota domisili;
   sisanya kota besar terdekat. Ini prasyarat supaya analisis "no-show vs jarak tempuh" jadi
   mungkin di masa depan (sekarang mustahil — kecocokan kota domisili/kota tes cuma
   kebetulan 1/43 ≈ 2,3%, persis rasio yang teramati di data).
3. **`kota_asal` sungguh berbeda dari domisili**, sesuai porsi 34% yang sudah tertulis di
   aturan (perbaiki bug baris 640 — variabel yang disalin salah).
4. **Almamater berjenjang + akreditasi.** Tidak ada data publik jumlah lulusan per kampus
   yang diterima PLN, jadi bobotnya disusun dari struktur nyata yang sudah ada di repo:
   - Kampus mitra ikatan dinas/kelas kerjasama — ITPLN, PENS, 18 PTN yang sudah
     terdokumentasi di `rules/ikatan_dinas.yaml`
   - Akreditasi BAN-PT (Unggul / Baik Sekali / Baik) sebagai kolom baru di master kampus
   - Kedekatan geografis dengan unit PLN
5. **Perilaku akreditasi (ide user, dicatat supaya tidak hilang):** akreditasi lebih tinggi →
   peluang lulus tiap tahap seleksi naik, TAPI peluang no-show juga naik — kandidat kampus
   unggulan melamar ke banyak perusahaan sekaligus dan PLN kerap jadi pilihan kedua/ketiga,
   bukan pilihan pertama. Dua efek berlawanan dalam satu dimensi; ini sendiri sudah jadi
   temuan yang layak ditonjolkan begitu datanya benar — tidak perlu caption tambahan untuk
   menjelaskannya kalau chart-nya dirancang menunjukkan dua kurva berlawanan arah itu.
6. **`ukuran_baju`** ikut sebaran realistis (M & L dominan, bukan seragam 4 kategori).
7. **Tambahkan cek sebaran ke `build/00b_verifikasi_keluaran.py`**: untuk tiap kolom
   kategori yang secara bisnis seharusnya berpola (bukan benar-benar acak), uji rasio
   top/bawah dan gagalkan build kalau di bawah ambang (mis. < 1,3). Ini yang akan menangkap
   cacat sejenis di masa depan tanpa perlu disapu manual lagi.
8. **Jaga kompatibilitas dengan verifikasi yang sudah ada.** Mengubah urutan panggilan RNG
   di `08_kandidat_pendaftaran.py` menggeser seluruh aliran acak hilir dan berpotensi
   mengubah angka-angka yang sudah diverifikasi di `recruitment_dashboardv2/docs/metrik.md`
   (funnel, penempatan, pagu — semuanya downstream dari kandidat). Bidang-bidang yang
   diperbaiki sebaiknya memakai generator acak ber-seed terpisah
   (`np.random.default_rng(seed_khusus)`) supaya aliran utama tidak tersentuh. Setelah
   rebuild, jalankan `recruitment_dashboardv2/tests/uji_metrik.py` — yang boleh berubah
   hanya metrik bergeografi & almamater; semua metrik funnel/penempatan/pagu harus tetap
   sama persis.

## Berkas yang akan tersentuh saat dikerjakan

- `mockdb/build/08_kandidat_pendaftaran.py` (baris 544 `tempat_lahir`, 557 `kota_domisili`,
  597 `ukuran_baju`, 640 bug `kota_asal`)
- `mockdb/build/09_seleksi_tahap.py` (korelasi kota tes ↔ domisili)
- `mockdb/rules/demografi.yaml` (sudah punya `sebaran_provinsi_asal`, tinggal dipakai)
- `mockdb/rules/kampus.yaml` (baru — daftar kampus + akreditasi + status mitra)
- `mockdb/build/00b_verifikasi_keluaran.py` (cek sebaran baru)
