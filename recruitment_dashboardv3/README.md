# Dashboard Rekrutmen PLN v3

Dashboard internal untuk memantau rekrutmen PLN — dari perencanaan formasi sampai SK
penempatan — dibaca langsung dari `mockdb/out/rekrutmen.duckdb` (35 tabel, 4.224.932 baris).

Dibangun setelah v1 dan v2. Perbedaan utama dari v2: susunan halaman dirancang dari alur
kerja tim rekrutmen (lihat `docs/KONTEKS_KERJA.md`), bukan dari bentuk tabel database;
jangkar waktu adalah tanggal berjalan sungguhan, bukan tanggal beku; dan tinjauan visual
manual (terang & gelap) jadi bagian wajib serah terima, bukan cuma tes headless.

## Menjalankan

Venv dibagi dengan seluruh `tower2_dashboard/` — jangan bikin venv baru.

```bash
cd recruitment_dashboardv3
../.venv/Scripts/streamlit.exe run streamlit_app.py --server.port 8503
```

v1 tetap di port 8501, v2 di port 8502 — ketiganya bisa jalan berdampingan.

`.streamlit/secrets.toml` (kunci API chatbot) tidak ikut commit — salin dari
`.streamlit/secrets.toml.example` dan isi sendiri.

## Struktur

| Folder | Isi |
|---|---|
| `app_pages/` | 8 halaman Streamlit (7 berdata nyata + Eksplorasi). Tidak menulis SQL — semua angka lewat `core/metrics.py`. |
| `core/` | `db.py` (koneksi read-only + cache), `format.py` (format angka Indonesia), `metrics.py` (satu fungsi per metrik), `eksplorasi_sintetis.py` (generator data sintetis, khusus halaman Eksplorasi). |
| `chat/` | Chatbot "RecruitMan" — diport apa adanya dari v2, halaman penuh + popover mengambang. |
| `components/` | `tampilan.py` — primitif tata letak minimal (bukan pengganti `temuan_halaman()` v2). |
| `docs/` | Dokumentasi kerja — lihat bagian berikut. |
| `tests/` | Tiga lapis: `uji_metrik.py` (angka jangkar ke DB nyata), `uji_halaman.py` (`AppTest`), `uji_disiplin.py` (aturan P1–P11 mekanis). |

## Halaman

Beranda · Perencanaan Formasi · Seleksi Berjalan · Corong Seleksi · Pasca-Seleksi ·
Rencana & Realisasi · Profil Pelamar · Eksplorasi (data sintetis, ditandai jelas terpisah).

## Dokumen kerja

- `docs/ATURAN_TAMPILAN.md` — aturan tampilan P1–P11 yang mengikat, dengan penanda
  `[mekanis]`/`[manual]`.
- `docs/CATATAN_DATA.md` — **satu-satunya** tempat penjelasan "kenapa angkanya begini",
  jebakan data, dan keputusan query. Tidak pernah tampil di UI.
- `docs/USULAN_DATABASE.md` — kebutuhan data yang belum terpenuhi, bersumber dari halaman
  Eksplorasi, bahan pertimbangan v4.
- `docs/metrik.md` — tiap fungsi di `core/metrics.py`, SQL-nya, dan hasil eksekusi nyata.
- `docs/KONTEKS_KERJA.md`, `docs/RANCANGAN_HALAMAN.md` — dasar rancangan halaman.

## Tes

```bash
../.venv/Scripts/python.exe -m pytest
```

233 tes, sekitar 8 detik. Kalau melar jauh dari itu, curigai ping jaringan nyata di jalur
render popover chatbot (`auto_check` harus `False`) — pernah membuat suite v2 membengkak
dari 15 detik ke 30 menit.

## Batasan yang diketahui

Horison data berakhir **2026-10-15** — sesudahnya halaman yang bergantung status "sedang
berjalan" akan tampil kosong, ini keadaan yang benar, bukan galat. Rincian lengkap di
`docs/CATATAN_DATA.md`.
