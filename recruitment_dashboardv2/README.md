# Dashboard Rekrutmen PLN v2

Dashboard di atas `mockdb/out/rekrutmen.duckdb` (34 tabel, 4,22 juta baris).
Terpisah total dari `recruitment_dashboard/` (v1).

## Jalankan

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Database dibaca langsung dari `../mockdb/out/rekrutmen.duckdb` secara **read-only** —
tidak perlu menyalin data ke folder ini.

## Struktur

```
streamlit_app.py      titik masuk — navigasi & elemen lintas halaman
core/
  db.py               koneksi DuckDB read-only + cache query
  metrics.py          SATU implementasi tiap KPI (dipakai halaman & chatbot)
  theme.py            token warna
  format.py           format angka gaya Indonesia
components/ui.py      hero, kartu insight, badge, sakelar mode analis
app_pages/            satu berkas per halaman
docs/                 PRD, kamus metrik, wireframe, design system, backlog
```

## Dua aturan arsitektur

1. **Halaman tidak menulis SQL agregat sendiri.** Semua angka lewat `core/metrics.py`,
   supaya halaman dan chatbot tidak pernah memberi angka berbeda.
2. **Database tidak dimuat ke memori.** 4,22 juta baris — yang di-cache hasil query,
   bukan tabelnya.

## Status

| Halaman | Status |
|---|---|
| 1 Ringkasan | ✅ jadi |
| 2 Perencanaan | ⏳ placeholder |
| 3 Corong seleksi | ⏳ placeholder |
| 4 Kandidat | ⏳ placeholder |
| 5 Pasca-seleksi & OJT | ⏳ placeholder |
| 6 Penempatan | ⏳ placeholder |
| 7 Kualitas data | ⏳ placeholder |
| 8 Chatbot | ⏳ placeholder — port dari v1 |

## Dokumen

Baca `docs/PRD.md` dulu, lalu `docs/metrik.md` (kamus metrik + SQL terverifikasi).
`docs/backlog.md` memuat ide yang belum masuk cakupan.
