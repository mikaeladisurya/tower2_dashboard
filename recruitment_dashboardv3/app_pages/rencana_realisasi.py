"""Halaman 6 -- Rencana & Realisasi.

Pertanyaan harian: seberapa tepat perencanaan kami ternyata? Seperti Corong
Seleksi (halaman 4), ini analisis lintas-tahun atas riwayat yang sudah tuntas
(2019-2025) -- bukan pemantauan satu kohort yang sedang berjalan -- jadi
halaman ini tidak terikat `hari_ini()` (penyimpangan yang sama, disetujui
ATURAN_TAMPILAN.md §4.5).
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components.tampilan import keadaan_kosong
from core import metrics
from core.format import desimal

_LABEL_ANGKA_RENCANA = {
    "pagu": "Pagu",
    "target_gelombang": "Target Gelombang",
    "ditempatkan": "Realisasi",
}

_LABEL_JALUR = {True: "Jalur RBB", False: "Jalur Mandiri"}
_WARNA_RBB = "#8764B8"

st.title("Rencana & Realisasi")

# ── Blok 1: pagu, target gelombang, realisasi per tahun ─────────────────────
st.subheader("Pagu vs Target vs Realisasi")
tiga_angka = metrics.pagu_target_realisasi_tahunan()

if tiga_angka.empty:
    keadaan_kosong("Belum ada data rencana dan realisasi")
else:
    _panjang = tiga_angka.melt(
        id_vars="tahun",
        value_vars=list(_LABEL_ANGKA_RENCANA),
        var_name="jenis",
        value_name="jumlah",
    )
    _panjang["jenis"] = _panjang["jenis"].map(_LABEL_ANGKA_RENCANA)
    _chart_tiga_angka = (
        alt.Chart(_panjang)
        .mark_bar()
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            xOffset=alt.XOffset("jenis:N", title="Jenis"),
            y=alt.Y("jumlah:Q", title="Jumlah"),
            color=alt.Color("jenis:N", title="Jenis"),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("jenis:N", title="Jenis"),
                alt.Tooltip("jumlah:Q", title="Jumlah", format=","),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(_chart_tiga_angka, width="stretch")
    st.dataframe(
        tiga_angka,
        column_config={
            "tahun": st.column_config.NumberColumn("Tahun", format="%d"),
            "pagu": st.column_config.NumberColumn("Pagu", format="localized"),
            "target_gelombang": st.column_config.NumberColumn(
                "Target Gelombang", format="localized"
            ),
            "ditempatkan": st.column_config.NumberColumn("Realisasi", format="localized"),
            "selisih_pagu_target": st.column_config.NumberColumn(
                "Selisih Pagu-Target", format="localized"
            ),
        },
        hide_index=True,
        width="stretch",
    )

# ── Blok 2: rencana vs realisasi per unit induk (2019-2024) ─────────────────
st.subheader("Rencana vs Realisasi Unit Induk 2019-2024")
per_unit = metrics.rencana_realisasi_per_unit()

if per_unit.empty:
    keadaan_kosong("Belum ada unit dengan rencana tercatat")
else:
    _chart_unit = (
        alt.Chart(per_unit)
        .mark_bar()
        .encode(
            x=alt.X("selisih:Q", title="Selisih Rencana-Realisasi"),
            y=alt.Y("nama_pendek:N", sort="-x", title="Unit Induk"),
            tooltip=[
                alt.Tooltip("nama_pendek:N", title="Unit Induk"),
                alt.Tooltip("rencana:Q", title="Rencana"),
                alt.Tooltip("realisasi:Q", title="Realisasi"),
                alt.Tooltip("selisih:Q", title="Selisih"),
            ],
        )
        .properties(height=max(320, 18 * len(per_unit)))
    )
    st.altair_chart(_chart_unit, width="stretch")

# ── Blok 3: pemenuhan per tahun, tahun RBB ditandai visual ──────────────────
st.subheader("Pemenuhan Target per Tahun")
pemenuhan = metrics.pemenuhan_per_tahun()

if pemenuhan.empty:
    keadaan_kosong("Belum ada data pemenuhan target")
else:
    pemenuhan_mandiri = pemenuhan[~pemenuhan["tahun_rbb"]]
    with st.container(border=True, horizontal=True):
        st.metric(
            "Rata-rata Pemenuhan Jalur Mandiri",
            desimal(pemenuhan_mandiri["pct_pemenuhan"].mean()) + "%",
            help="Rata-rata persentase realisasi terhadap Target Gelombang, tahun jalur mandiri PLN.",
            icon=":material/target:",
        )
        st.metric(
            "Rata-rata Seluruh Tahun",
            desimal(pemenuhan["pct_pemenuhan"].mean()) + "%",
            help="Rata-rata persentase realisasi terhadap Target Gelombang, seluruh tahun program.",
            icon=":material/summarize:",
        )

    _pemenuhan_tampil = pemenuhan.assign(
        label_jalur=pemenuhan["tahun_rbb"].map(_LABEL_JALUR)
    )
    _warna_primer = st.context.theme.get("primaryColor") or "#0078D4"
    _chart_pemenuhan = (
        alt.Chart(_pemenuhan_tampil)
        .mark_bar()
        .encode(
            x=alt.X("tahun:O", title="Tahun"),
            y=alt.Y("pct_pemenuhan:Q", title="Pemenuhan (%)"),
            color=alt.Color(
                "label_jalur:N",
                title="Jalur",
                scale=alt.Scale(
                    domain=["Jalur Mandiri", "Jalur RBB"],
                    range=[_warna_primer, _WARNA_RBB],
                ),
            ),
            tooltip=[
                alt.Tooltip("tahun:O", title="Tahun"),
                alt.Tooltip("label_jalur:N", title="Jalur"),
                alt.Tooltip("target_gelombang:Q", title="Target Gelombang"),
                alt.Tooltip("ditempatkan:Q", title="Realisasi"),
                alt.Tooltip("pct_pemenuhan:Q", title="Pemenuhan (%)"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(_chart_pemenuhan, width="stretch")

    st.dataframe(
        pemenuhan,
        column_config={
            "tahun": st.column_config.NumberColumn("Tahun", format="%d"),
            "target_gelombang": st.column_config.NumberColumn(
                "Target Gelombang", format="localized"
            ),
            "ditempatkan": st.column_config.NumberColumn("Realisasi", format="localized"),
            "pct_pemenuhan": st.column_config.NumberColumn("Pemenuhan (%)", format="%.1f%%"),
            "tahun_rbb": st.column_config.CheckboxColumn("Jalur RBB", disabled=True),
        },
        hide_index=True,
        width="stretch",
    )
