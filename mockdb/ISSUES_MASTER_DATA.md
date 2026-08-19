# Catatan anomali master data — untuk rebuild generator berikutnya

**Status: dicatat, belum dikerjakan.** Sama seperti `ISSUES_SEBARAN.md` — dashboard v2
dibangun di atas snapshot yang sudah diverifikasi, jadi perbaikan ditunda ke rebuild
generator berikutnya. Berkas ini fokus ke anomali *baris master data* (baris ganda/salah
match), beda kategori dari cacat sebaran acak seragam.

## Temuan

### `unit_induk` — baris ganda untuk "UID Jawa Tengah & DIY"

```sql
select * from unit_induk where nama_pendek ilike '%jateng%'
```

Menghasilkan **dua baris** untuk unit yang sama:

| nama_pendek | jumlah_pegawai | ftk_2025 | realisasi_mar_2026 |
|---|---:|---:|---:|
| UID Jawa Tengah & DIY | 1.643 | 1.516 | 1.654 | ← baris benar |
| UID Jawa Tengah & DIY | 4 | 144 | 4 | ← baris anomali |

Baris kedua kemungkinan gagal-match saat ekstraksi DAPEG (`01_extract_master.py`) — angka
`jumlah_pegawai=4` terlalu kecil untuk unit induk mana pun, tapi `ftk_2025=144` masuk akal
sebagai pecahan formasi yang salah dialokasikan.

**Mitigasi yang sudah dipakai di `docs/metrik.md` (M14):** filter `WHERE jumlah_pegawai > 50`
saat menghitung gap FTK per unit — baris anomali otomatis tersingkir tanpa perlu tahu
penyebabnya lebih dulu. Dashboard v2 memakai mitigasi ini di halaman Perencanaan, dan
melaporkan anomalinya di halaman Kualitas Data.

**Belum diperiksa** (untuk rebuild nanti): apakah unit lain punya baris ganda serupa yang
kebetulan tidak tertangkap filter `> 50` karena kedua baris sama-sama besar, dan apakah akar
penyebabnya di `01_extract_master.py` (dua baris sumber match ke `nama_pendek` yang sama)
atau di sheet sumber sendiri.

## Prinsip kerja untuk temuan sejenis

Sesuai arahan user 2026-08-19: **temuan data dicatat, tidak menghentikan pembangunan
dashboard.** Tampilan dirancang supaya tetap memberi insight berguna dengan mitigasi
(filter/pengecualian) yang dicatat eksplisit di `metrik.md` dan ditampilkan sebagai transparansi
di halaman Kualitas Data — bukan disembunyikan, dan bukan alasan menunda pembangunan.
Perbaikan akar masalah menunggu rebuild generator.
