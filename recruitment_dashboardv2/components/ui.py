"""Primitif tata letak — dipakai SEMUA halaman, supaya redesign nanti murah.

Ditulis ulang 2026-08-19 mengikuti doktrin keterbacaan D1-D6 (docs/design_system.md
§11), setelah review halaman 1: "terlalu AI — info di mana-mana, banyak caption
kecil". Yang dibuang dari versi sebelumnya: hero() gradien, insight() per-chart,
badge NYATA di tiap KPI, judul_seksi() berdeskripsi permanen.

Prinsip: native dulu (`st.metric` sudah mendukung border + sparkline + help sejak
1.57), kustom hanya untuk yang benar-benar tidak ada padanannya.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pandas as pd
import streamlit as st

from core import theme

# Badge sumber data — dipakai HANYA saat membedakan (D4), bukan di tiap KPI.
BADGE = {
    "nyata": ":blue-badge[NYATA]",
    "dimodelkan": ":orange-badge[DIMODELKAN]",
    "agregat": ":gray-badge[AGREGAT]",
}


def judul_halaman(judul: str) -> None:
    """Judul halaman polos (D6) — tanpa spanduk gradien, tanpa subjudul permanen."""
    st.title(judul)


def baris_kpi(items: list[dict[str, Any]]) -> None:
    """Baris KPI native (D4): tanpa badge tertulis, konteks di tooltip `help=`.

    Tiap item: {"label": str, "value": str, "help": str (opsional),
    "chart_data": list (opsional, sparkline), "chart_type": "bar"|"line" (opsional)}.
    """
    with st.container(horizontal=True):
        for item in items:
            st.metric(
                item["label"],
                item["value"],
                help=item.get("help"),
                border=True,
                chart_data=item.get("chart_data"),
                chart_type=item.get("chart_type", "bar"),
                delta_color="off",
            )


@contextmanager
def temuan_halaman(kalimat: str) -> Iterator[None]:
    """Blok chart JANGKAR PERHATIAN halaman — panggil TEPAT SEKALI per halaman (D3).

    Judulnya ADALAH satu-satunya kalimat temuan di halaman ini (D1). Chart eksotis
    (Sankey/treemap/peta) atau chart utama lainnya dirender di dalam `with` ini.
    """
    with st.container(border=True):
        st.markdown(f"##### {kalimat}")
        yield


@contextmanager
def blok_chart(judul: str) -> Iterator[None]:
    """Blok chart pendukung — maksimal 2 per halaman (D5).

    Judul boleh singkat/deskriptif kalau chart-nya sudah menjelaskan diri sendiri
    lewat warna/anotasi (mis. legenda jalur). Bukan tempat kartu insight terpisah.
    """
    with st.container(border=True):
        st.markdown(f"**{judul}**")
        yield


def spanduk_dimodelkan(teks: str) -> None:
    """Peringatan permanen — HANYA untuk halaman yang seluruh isinya dimodelkan (D4).

    Bukan badge berulang di tiap KPI. Dipakai satu kali per halaman, kalau perlu.
    """
    t = theme.token()
    st.html(
        f"""
        <div style="
            background: {t['surface_card']};
            border: 1px solid {theme.STATUS['peringatan']};
            border-left: 5px solid {theme.STATUS['peringatan']};
            border-radius: 10px;
            padding: 13px 16px;
            margin-bottom: 14px;
            color: {t['text_primary']};
            font-size: 14px;
            line-height: 1.55;">
          <strong>Seluruh halaman ini dimodelkan.</strong><br>{teks}
        </div>
        """
    )


def tentang_halaman(teks: str) -> None:
    """Penjelasan on-demand (D2): tertutup secara default, tidak menyita ruang
    bagi pembaca yang sudah hafal. Isinya definisi metrik & jebakan data halaman ini."""
    with st.expander("Tentang halaman ini"):
        st.markdown(teks)


def mode_analis() -> bool:
    """Status sakelar lapis analis. Berlaku lintas halaman."""
    st.session_state.setdefault("mode_analis", False)
    return st.session_state["mode_analis"]


def sakelar_mode_analis() -> None:
    st.session_state.setdefault("mode_analis", False)
    st.toggle(
        "Mode analis",
        key="mode_analis",
        help="Menampilkan filter, tabel rinci, dan tombol unduh di tiap halaman.",
    )


def lapis_analis(df: pd.DataFrame, nama_berkas: str, label_tabel: str = "Data rinci") -> None:
    """Tabel + unduh CSV, dipanggil di dalam `if ui.mode_analis():` pada tiap halaman."""
    st.markdown(f"**{label_tabel}**")
    st.dataframe(df, hide_index=True, width="stretch")
    st.download_button(
        "Unduh CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=nama_berkas,
        mime="text/csv",
        icon=":material/download:",
    )


def halaman_segera(judul: str, isi: list[str]) -> None:
    """Placeholder halaman yang belum dibangun — menampilkan rencana isinya."""
    judul_halaman(judul)
    st.info(
        "Kerangka aplikasi sudah jalan, halaman ini menyusul. "
        "Rencana isinya ada di `docs/wireframe.md`.",
        icon=":material/construction:",
    )
    st.markdown("**Rencana isi halaman:**")
    for baris in isi:
        st.markdown(f"- {baris}")
