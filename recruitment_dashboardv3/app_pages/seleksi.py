"""Halaman 3 -- Seleksi Berjalan.

Pertanyaan harian: gelombang yang sedang jalan sudah sampai mana? Halaman ini
kosong pada banyak tanggal karena memang tidak selalu ada gelombang terbuka --
lihat docs/RANCANGAN_HALAMAN.md §5. Kosongnya halaman ini adalah fakta
keadaan proses rekrutmen pada tanggal acuan, bukan galat.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

from components.tampilan import keadaan_kosong
from core import db, metrics
from core.format import angka

st.title("Seleksi Berjalan")

acuan = db.hari_ini()
gelombang_terbuka = metrics.gelombang_terbuka(acuan=acuan)

if gelombang_terbuka.empty:
    keadaan_kosong("Tidak ada Gelombang yang sedang dibuka")

    terakhir = metrics.gelombang_terakhir_selesai(acuan=acuan)
    if terakhir is not None:
        st.subheader("Hasil Gelombang Terakhir")
        with st.container(border=True):
            st.markdown(f"**{terakhir['nama_gelombang']}**")
            st.markdown(f":gray[Ditutup {terakhir['tgl_tutup']:%d %B %Y}]")
            with st.container(border=True, horizontal=True):
                st.metric(
                    "Pendaftar",
                    angka(terakhir["pendaftar"]),
                    help="Jumlah pelamar yang mendaftar pada Gelombang ini.",
                    icon=":material/how_to_reg:",
                )
                st.metric(
                    "Diterima",
                    angka(terakhir["diterima"]),
                    help="Pelamar yang lolos seluruh tahap seleksi pada Gelombang ini.",
                    icon=":material/verified:",
                )
                st.metric(
                    "Gugur",
                    angka(terakhir["gagal"]),
                    help="Pelamar yang tidak lolos salah satu tahap seleksi.",
                    icon=":material/cancel:",
                )

        gugur = metrics.gugur_per_tahap_gelombang(terakhir["gelombang_id"])
        if not gugur.empty:
            st.subheader("Sebaran Gugur per Tahap")
            _chart_gugur = (
                alt.Chart(gugur)
                .mark_bar()
                .encode(
                    x=alt.X("jumlah:Q", title="Jumlah Gugur"),
                    y=alt.Y("nama:N", sort=alt.SortField("urutan"), title="Tahap"),
                    tooltip=[
                        alt.Tooltip("nama:N", title="Tahap"),
                        alt.Tooltip("jumlah:Q", title="Jumlah Gugur"),
                    ],
                )
                .properties(height=max(220, 32 * len(gugur)))
            )
            st.altair_chart(_chart_gugur, width="stretch")
else:
    daftar_gelombang = gelombang_terbuka["gelombang_id"]
    if len(daftar_gelombang) > 1:
        gelombang_id = st.selectbox("Gelombang", options=daftar_gelombang)
    else:
        gelombang_id = daftar_gelombang.iloc[0]
    baris_gelombang = gelombang_terbuka.set_index("gelombang_id").loc[gelombang_id]

    # ── Blok 1: gelombang terbuka ────────────────────────────────────────────
    st.subheader("Gelombang Terbuka")
    with st.container(border=True):
        st.markdown(f"**{baris_gelombang['nama_gelombang']}**")
        with st.container(border=True, horizontal=True):
            st.metric(
                "Hari Tersisa",
                angka(baris_gelombang["hari_tersisa"]),
                help="Hari sampai penutupan Gelombang ini.",
                icon=":material/hourglass_top:",
            )
            st.metric(
                "Profesi Dibuka",
                angka(baris_gelombang["n_profesi"]),
                help="Jumlah profesi yang dibuka pada Gelombang ini.",
                icon=":material/work:",
            )
            st.metric(
                "Target Diterima",
                angka(baris_gelombang["diterima_target"]),
                help="Target jumlah pelamar yang akan diterima pada Gelombang ini.",
                icon=":material/flag:",
            )

    profesi = metrics.profesi_gelombang(gelombang_id)
    st.markdown("**Profesi Dibuka**")
    st.dataframe(
        profesi,
        column_config={
            "nama_profesi": st.column_config.TextColumn("Profesi"),
            "jenjang": st.column_config.TextColumn("Jenjang"),
            "kota_rekrutmen": st.column_config.TextColumn("Kota"),
            "kuota": st.column_config.NumberColumn("Kuota", format="localized"),
        },
        hide_index=True,
        width="stretch",
    )

    # ── Blok 2: posisi peserta per tahap ─────────────────────────────────────
    st.subheader("Posisi Peserta per Tahap")
    posisi = metrics.posisi_tahap_seleksi(gelombang_id, acuan=acuan)
    _chart_posisi = (
        alt.Chart(posisi)
        .transform_fold(["menunggu", "sudah_lewat"], as_=["status", "jumlah"])
        .mark_bar()
        .encode(
            x=alt.X("jumlah:Q", title="Jumlah Peserta"),
            y=alt.Y("nama:N", sort=alt.SortField("urutan"), title="Tahap"),
            color=alt.Color(
                "status:N",
                title="Status",
                scale=alt.Scale(
                    domain=["sudah_lewat", "menunggu"],
                    range=[
                        st.context.theme.get("primaryColor") or "#0078D4",
                        st.context.theme.get("secondaryBackgroundColor") or "#D3D3D3",
                    ],
                ),
                legend=alt.Legend(labelExpr="datum.value == 'sudah_lewat' ? 'Sudah Lewat' : 'Menunggu'"),
            ),
            tooltip=[
                alt.Tooltip("nama:N", title="Tahap"),
                alt.Tooltip("status:N", title="Status"),
                alt.Tooltip("jumlah:Q", title="Jumlah"),
            ],
        )
        .properties(height=max(220, 32 * len(posisi)))
    )
    st.altair_chart(_chart_posisi, width="stretch")

    # ── Blok 3: jadwal tahap berikutnya ──────────────────────────────────────
    st.subheader("Jadwal Tahap Berikutnya")
    jadwal = metrics.jadwal_tahap_berikutnya(gelombang_id, acuan=acuan)
    if jadwal.empty:
        keadaan_kosong("Tidak ada tahap terjadwal berikutnya")
    else:
        baris_jadwal = jadwal.iloc[0]
        with st.container(border=True, horizontal=True):
            st.metric(
                baris_jadwal["nama_tahap"],
                f"{baris_jadwal['tanggal_tahap']:%d %b %Y}",
                help="Tahap seleksi terdekat berikutnya pada Gelombang ini.",
                icon=":material/event_upcoming:",
            )
        st.dataframe(
            jadwal,
            column_order=["lokasi_kota", "vendor", "jumlah"],
            column_config={
                "lokasi_kota": st.column_config.TextColumn("Kota"),
                "vendor": st.column_config.TextColumn("Vendor"),
                "jumlah": st.column_config.NumberColumn("Jumlah", format="localized"),
            },
            hide_index=True,
            width="stretch",
        )

    # ── Blok 4: kehadiran tahap terakhir ─────────────────────────────────────
    st.subheader("Kehadiran Tahap Terakhir")
    kehadiran = metrics.kehadiran_tahap_terakhir(gelombang_id, acuan=acuan)
    if kehadiran is None:
        keadaan_kosong("Belum ada tahap berkehadiran yang lewat")
    else:
        pct_hadir = 100.0 * kehadiran["hadir"] / kehadiran["total"] if kehadiran["total"] else 0.0
        with st.container(border=True, horizontal=True):
            st.metric(
                kehadiran["nama"],
                f"{pct_hadir:.1f}%",
                help="Persentase peserta yang hadir pada tahap terakhir yang sudah berlangsung.",
                icon=":material/how_to_reg:",
            )
            st.metric(
                "Hadir",
                angka(kehadiran["hadir"]),
                icon=":material/check_circle:",
            )
            st.metric(
                "Tidak Hadir",
                angka(kehadiran["tidak_hadir"]),
                icon=":material/highlight_off:",
            )
        st.markdown(f":gray[{kehadiran['tanggal_tahap']:%d %B %Y}]")
