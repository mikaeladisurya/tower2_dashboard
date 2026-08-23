"""Lapis 2 -- perilaku halaman.

`streamlit.testing.v1.AppTest` selalu dimuat lewat `streamlit_app.py`, lalu
`at.switch_page(...)` -- memuat berkas halaman langsung gagal karena butuh
konteks navigasi `st.navigation` (dibuktikan di G7/G8). `tests/conftest.py`
sudah menaruh root v3 di sys.path.

Perhatian performa (kriteria selesai G9: suite < ~60 detik): `AppTest.from_file`
tidak dipanggil ulang untuk tiap skenario kalau bisa dihindari -- beberapa tes
membangun satu instance lalu menjalankan beberapa langkah di atasnya.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

HALAMAN = [
    "app_pages/beranda.py",
    "app_pages/perencanaan.py",
    "app_pages/seleksi.py",
    "app_pages/corong.py",
    "app_pages/pasca.py",
    "app_pages/rencana_realisasi.py",
    "app_pages/profil.py",
    "app_pages/eksplorasi.py",
    "app_pages/chatbot.py",
]


def _muat(halaman: str | None = None) -> AppTest:
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.run(timeout=30)
    if halaman is not None:
        at.switch_page(halaman)
        at.run(timeout=30)
    return at


def test_beranda_adalah_halaman_default():
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.title[0].value == "Beranda"


def test_tiap_halaman_dimuat_tanpa_exception():
    for halaman in HALAMAN:
        at = _muat(halaman)
        assert not at.exception, f"{halaman}: {[str(e) for e in at.exception]}"


def test_pindah_halaman_beruntun_tanpa_exception():
    """Simulasi navigasi sidebar berurutan ke seluruh 9 halaman dalam satu
    sesi AppTest -- beberapa bug (cache lintas halaman, session_state bocor)
    hanya muncul di transisi antar-halaman, bukan di pemuatan tunggal."""
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    at.run(timeout=30)
    assert not at.exception
    for halaman in HALAMAN:
        at.switch_page(halaman)
        at.run(timeout=30)
        assert not at.exception, f"{halaman}: {[str(e) for e in at.exception]}"


def test_pemilih_tanggal_ubah_session_state_tanpa_exception():
    at = _muat("app_pages/beranda.py")
    at.session_state["tanggal_acuan"] = date(2019, 9, 10)
    at.run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]


def test_pemilih_tanggal_widget_date_input_tanpa_exception():
    at = _muat("app_pages/beranda.py")
    assert len(at.date_input) >= 1
    at.date_input[0].set_value(date(2027, 1, 6)).run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]


def test_pasca_dengan_tanggal_jauh_melewati_horison_tanpa_exception():
    """Pasca-Seleksi terikat `hari_ini()` (beda dari Corong Seleksi) -- harus
    tetap hidup pada tanggal yang jauh melewati horison data (J9: SK kohort
    2025 tidak akan pernah terbit berapa pun acuan dimajukan)."""
    at = _muat("app_pages/pasca.py")
    at.session_state["tanggal_acuan"] = date(2027, 1, 6)
    at.run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]


def test_pasca_ganti_kohort_tanpa_exception():
    at = _muat("app_pages/pasca.py")
    assert len(at.selectbox) >= 1
    pemilih_kohort = at.selectbox[0]
    opsi_lain = [o for o in pemilih_kohort.options if o != pemilih_kohort.value]
    assert opsi_lain
    pemilih_kohort.set_value(opsi_lain[0]).run(timeout=30)
    assert not at.exception, [str(e) for e in at.exception]


def _popover_mengambang(at: AppTest):
    """Popover RecruitMan mengambang berkunci `floating_chatbot` -- dibedakan
    dari popover lain milik halaman itu sendiri (mis. menu percakapan di
    halaman RecruitMan penuh, yang juga memakai st.popover). AppTest tidak
    mengekspos `key=` widget lewat atribut `.key` untuk Block -- kuncinya
    tetap terbaca lewat akhiran `proto.id` (mis. "...-floating_chatbot")."""
    return [p for p in at.get("popover") if p.proto.id.endswith("-floating_chatbot")]


def test_popover_mengambang_muncul_di_beranda_bukan_di_chatbot():
    at_beranda = _muat("app_pages/beranda.py")
    assert len(_popover_mengambang(at_beranda)) == 1

    at_chatbot = _muat("app_pages/chatbot.py")
    assert len(_popover_mengambang(at_chatbot)) == 0
