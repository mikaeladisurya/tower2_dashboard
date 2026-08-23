"""Lapis 3 -- aturan mekanis P1-P11, ditulis LANGSUNG dari
`docs/ATURAN_TAMPILAN.md` §6 (tabel 16 uji). Tabel itu berdiri sendiri --
tiap pengecualian di sini adalah salinan dari kolom "Pengecualian wajib" di
barisnya masing-masing, bukan hasil menoleh balik ke §2.

BUKAN salinan dari recruitment_dashboardv2/tests/uji_disiplin.py -- berkas v2
menegakkan doktrin D1 ("judul chart = temuan") yang DIBATALKAN di v3, dan
meng-grep `ui.temuan_halaman(` yang tidak ada di v3.

Cakupan tiap uji mengikuti kolom "Cakupan" di tabel §6 apa adanya -- tidak
diperluas ke chat/ atau streamlit_app.py kecuali baris itu eksplisit berkata
"seluruh v3" (uji 1, 10, 12).
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_PAGES = ROOT / "app_pages"
COMPONENTS = ROOT / "components"
CORE = ROOT / "core"

HALAMAN = sorted(APP_PAGES.glob("*.py"))

# Seluruh *.py v3 -- dipakai uji 1, 10, 12. Dibatasi ke folder kode milik v3
# (bukan .venv/site-packages), dan mengecualikan cache bytecode.
#
# `tests/` dikecualikan dari cakupan uji 10 & 12 secara khusus (bukan uji 1):
# berkas tes INI SENDIRI wajib memuat token literal "date.today()" dan
# "use_container_width" sebagai isi assert/pesan galat untuk bisa mengujinya --
# itu bukan pelanggaran P3/arsitektur, melainkan keniscayaan menguji string
# terlarang lewat kode yang harus menyebut string itu apa adanya. Uji 1 (emoji)
# tidak masuk masalah yang sama, jadi tests/ tetap ikut diaudit di sana.
SELURUH_V3 = sorted(
    p
    for p in ROOT.rglob("*.py")
    if "__pycache__" not in p.parts
    and ".venv" not in p.parts
    and "data" not in p.parts
)
SELURUH_V3_KECUALI_TESTS = [p for p in SELURUH_V3 if "tests" not in p.parts]


def _baca(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _bersihkan(path: Path) -> str:
    """Teks berkas TANPA komentar `#...` dan TANPA docstring modul/fungsi/kelas.

    Proksi mekanis di sini menyasar *kode yang benar-benar jalan* -- string
    yang tampil ke pengguna atau dirangkai jadi SQL -- bukan komentar/docstring
    developer yang sah mengutip nama tabel, jalur `docs/*.md`, atau menyebut
    `date.today()`/`use_container_width` sebagai contoh larangan (persis yang
    dilakukan berkas tes ini sendiri, dan komentar di `app_pages/chatbot.py`
    yang menjelaskan kenapa `st.caption(` dihindari). Tanpa pembersihan ini,
    berkas tes ini akan gagal mengaudit dirinya sendiri.
    """
    teks = _baca(path)

    # 1) Kosongkan token komentar (bukan menghapus baris, supaya nomor baris
    #    dan panjang teks lain di baris yang sama tidak bergeser).
    baris = teks.splitlines(keepends=True)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(teks).readline):
            if tok.type == tokenize.COMMENT:
                srow, scol = tok.start
                _, ecol = tok.end
                line = baris[srow - 1]
                baris[srow - 1] = line[:scol] + line[ecol:]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    teks = "".join(baris)

    # 2) Kosongkan docstring modul/fungsi/kelas (baris penuh -- docstring
    #    selalu berdiri sebagai pernyataan ekspresi sendiri).
    try:
        pohon = ast.parse(teks)
    except SyntaxError:
        return teks
    baris = teks.splitlines(keepends=True)
    target = [pohon] + [
        n for n in ast.walk(pohon)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for node in target:
        body = getattr(node, "body", None)
        if not body:
            continue
        pertama = body[0]
        if (
            isinstance(pertama, ast.Expr)
            and isinstance(pertama.value, ast.Constant)
            and isinstance(pertama.value.value, str)
        ):
            for i in range(pertama.value.lineno - 1, pertama.value.end_lineno):
                baris[i] = "\n"
    return "".join(baris)


def _buang_token_material(teks: str) -> str:
    """Buang token `:material/...:` -- ikon Material juga ber-snake_case
    (`:material/pending_actions:`), dipakai uji 1 & 3."""
    return re.sub(r":material/[a-z_]+:", "", teks)


# ──────────────────────────────────────────────────────────────────────────────
# Uji 1 -- Tanpa emoji -- seluruh *.py -- kecualikan token :material/...:
# ──────────────────────────────────────────────────────────────────────────────

POLA_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "]"
)


@pytest.mark.parametrize("berkas", SELURUH_V3, ids=lambda p: str(p.relative_to(ROOT)))
def test_01_tanpa_emoji(berkas: Path):
    isi = _buang_token_material(_bersihkan(berkas))
    ditemukan = POLA_EMOJI.findall(isi)
    assert not ditemukan, f"{berkas}: emoji ditemukan {ditemukan}"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 2 -- Tanpa st.caption( -- app_pages/ -- tanpa pengecualian
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_02_tanpa_st_caption(halaman: Path):
    isi = _bersihkan(halaman)
    assert "st.caption(" not in isi, f"{halaman.name}: st.caption( ditemukan"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 3 -- Tanpa nama tabel/kolom/jalur berkas di string tampil -- app_pages/
# Pengecualian: buang token :material/...: lebih dulu
# ──────────────────────────────────────────────────────────────────────────────

NAMA_TABEL = [
    "pendaftaran",
    "seleksi_tahap",
    "pasca_tahap",
    "penempatan",
    "kandidat",
    "gelombang",
    "unit_induk",
    "usulan_kebutuhan",
    "pagu_rekrutmen",
    "proyeksi_kekosongan",
]
KATA_TERLARANG = ["generator", "dimodelkan", "query", "tabel", "kolom", "database"]
JALUR_TERLARANG = ["mockdb/", ".duckdb", "docs/", ".md"]


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_03_tanpa_nama_tabel_kolom_jalur(halaman: Path):
    isi = _buang_token_material(_bersihkan(halaman))

    ditemukan_tabel = [t for t in NAMA_TABEL if re.search(rf"\b{t}\b", isi)]
    assert not ditemukan_tabel, f"{halaman.name}: nama tabel di string: {ditemukan_tabel}"

    ditemukan_jalur = [j for j in JALUR_TERLARANG if j in isi]
    assert not ditemukan_jalur, f"{halaman.name}: jalur berkas di string: {ditemukan_jalur}"

    ditemukan_kata = [k for k in KATA_TERLARANG if re.search(rf"\b{k}\b", isi, re.IGNORECASE)]
    assert not ditemukan_kata, f"{halaman.name}: kata developer di string: {ditemukan_kata}"

    # Nama kolom snake_case di dalam string TAMPIL saja -- dibatasi ke argumen
    # pertama panggilan pemunculan teks (st.title/header/subheader/markdown/
    # write/text/metric/button/expander/popover/keadaan_kosong) dan kwarg
    # help=/label=, supaya key= session_state atau nama variabel kode tidak
    # ikut ketangkap sebagai false positive.
    pola_string_tampil = re.compile(
        r"(?:st\.(?:title|header|subheader|markdown|write|text|metric|button|"
        r"expander|popover|info|success)\(|keadaan_kosong\(|"
        r"\bhelp\s*=|\blabel\s*=)\s*[\"']([^\"']+)[\"']"
    )
    string_tampil = pola_string_tampil.findall(isi)
    pola_snake = re.compile(r"\b[a-z]+_[a-z_]+\b")
    ditemukan_snake = [s for s in string_tampil if pola_snake.search(s)]
    assert not ditemukan_snake, (
        f"{halaman.name}: kemungkinan nama kolom snake_case di string tampil: {ditemukan_snake}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Uji 4 -- Tanpa SELECT/FROM -- app_pages/ -- case-sensitive + batas kata
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_04_tanpa_select_from(halaman: Path):
    isi = _baca(halaman)
    assert not re.search(r"\bSELECT\b", isi), f"{halaman.name}: SELECT ditemukan"
    assert not re.search(r"\bFROM\b", isi), f"{halaman.name}: FROM ditemukan"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 5 -- Tanpa kolom PII -- app_pages/
# ──────────────────────────────────────────────────────────────────────────────

KOLOM_PII = [
    "nama_lengkap",
    "no_ktp",
    "email",
    "no_handphone",
    "alamat_domisili",
    "alamat_asal",
]


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_05_tanpa_kolom_pii(halaman: Path):
    isi = _baca(halaman)
    ditemukan = [k for k in KOLOM_PII if re.search(rf"\b{k}\b", isi)]
    assert not ditemukan, f"{halaman.name}: kemungkinan kolom PII: {ditemukan}"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 6 -- Tanpa height=<angka> pada st.container -- app_pages/
# height= pada st.dataframe boleh
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_06_tanpa_height_piksel_pada_container(halaman: Path):
    isi = _baca(halaman)
    ditemukan = re.findall(r"st\.container\([^)]*height\s*=\s*\d+", isi)
    assert not ditemukan, f"{halaman.name}: st.container(height=<angka>) ditemukan: {ditemukan}"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 7 -- Judul chart lolos proksi frasa benda -- app_pages/
# Uji 7a -- argumen keadaan_kosong(...): cek panjang & tanda baca SAJA
# ──────────────────────────────────────────────────────────────────────────────

KATA_PENANDA_KLAIM = [
    "adalah",
    "bukan",
    "lebih",
    "paling",
    "hanya",
    "tidak",
    "belum",
    "naik",
    "turun",
    "kehilangan",
    "mendominasi",
    "ternyata",
    "justru",
    "masih",
]

# st.title(...) / st.header(...) / st.subheader(...) / title=... dengan argumen
# string literal sederhana (menangkap kasus umum kutip tunggal/ganda).
POLA_JUDUL = re.compile(
    r"(?:st\.title|st\.header|st\.subheader)\(\s*[\"']([^\"']+)[\"']"
)
POLA_TITLE_KWARG = re.compile(r"\btitle\s*=\s*[\"']([^\"']+)[\"']")
POLA_KEADAAN_KOSONG = re.compile(r"keadaan_kosong\(\s*[\"']([^\"']+)[\"']")


def _lolos_proksi_frasa_benda(teks: str) -> list[str]:
    alasan = []
    if teks.rstrip().endswith((".", "!", "?")):
        alasan.append("berakhir tanda baca kalimat")
    if "," in teks:
        alasan.append("mengandung koma")
    if len(teks.split()) > 6:
        alasan.append("lebih dari 6 kata")
    kata_ditemukan = [
        k for k in KATA_PENANDA_KLAIM if re.search(rf"\b{k}\b", teks, re.IGNORECASE)
    ]
    if kata_ditemukan:
        alasan.append(f"kata penanda klaim: {kata_ditemukan}")
    return alasan


def _lolos_proksi_keadaan(teks: str) -> list[str]:
    """Uji 7a -- hanya panjang & tanda baca, TANPA kata penanda klaim (§6 baris 7a)."""
    alasan = []
    if teks.rstrip().endswith((".", "!", "?")):
        alasan.append("berakhir tanda baca kalimat")
    if "," in teks:
        alasan.append("mengandung koma")
    if len(teks.split()) > 6:
        alasan.append("lebih dari 6 kata")
    return alasan


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_07_judul_chart_frasa_benda(halaman: Path):
    isi = _baca(halaman)
    kandidat = POLA_JUDUL.findall(isi) + POLA_TITLE_KWARG.findall(isi)
    pelanggaran = {}
    for teks in kandidat:
        alasan = _lolos_proksi_frasa_benda(teks)
        if alasan:
            pelanggaran[teks] = alasan
    assert not pelanggaran, f"{halaman.name}: judul melanggar proksi frasa benda: {pelanggaran}"


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_07a_keadaan_kosong_hanya_panjang_dan_tanda_baca(halaman: Path):
    isi = _baca(halaman)
    kandidat = POLA_KEADAAN_KOSONG.findall(isi)
    pelanggaran = {}
    for teks in kandidat:
        alasan = _lolos_proksi_keadaan(teks)
        if alasan:
            pelanggaran[teks] = alasan
    assert not pelanggaran, f"{halaman.name}: keadaan_kosong(...) melanggar: {pelanggaran}"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 8 -- Tanpa max(tanggal...) sebagai pengganti hari ini -- core/metrics.py
# ──────────────────────────────────────────────────────────────────────────────

METRICS_PY = CORE / "metrics.py"


def test_08_metrics_tanpa_max_tanggal_sebagai_hari_ini():
    isi = _baca(METRICS_PY)
    ditemukan = re.findall(r"max\s*\(\s*tanggal\w*\s*\)", isi, re.IGNORECASE)
    assert not ditemukan, f"core/metrics.py: max(tanggal...) ditemukan: {ditemukan}"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 9 -- Tanpa literal 2026-09-15 / TANGGAL_POTONG -- app_pages/, core/metrics.py
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "berkas",
    HALAMAN + [METRICS_PY],
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_09_tanpa_literal_tanggal_potong(berkas: Path):
    isi = _bersihkan(berkas)
    assert "2026-09-15" not in isi, f"{berkas}: literal 2026-09-15 ditemukan"
    assert "TANGGAL_POTONG" not in isi, f"{berkas}: TANGGAL_POTONG ditemukan"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 10 -- Tanpa date.today()/datetime.now() -- seluruh v3 kecuali core/db.py
# ──────────────────────────────────────────────────────────────────────────────

DB_PY = CORE / "db.py"


@pytest.mark.parametrize(
    "berkas",
    [p for p in SELURUH_V3_KECUALI_TESTS if p != DB_PY],
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_10_tanpa_date_today_datetime_now(berkas: Path):
    isi = _bersihkan(berkas)
    assert "date.today()" not in isi, f"{berkas}: date.today() ditemukan"
    assert "datetime.now()" not in isi, f"{berkas}: datetime.now() ditemukan"


def test_10_db_py_justru_wajib_memiliki_date_today():
    isi = _bersihkan(DB_PY)
    assert "date.today()" in isi, "core/db.py: date.today() seharusnya ada -- satu-satunya sumber waktu"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 11 -- Tanpa status = 'BERJALAN' / status='SELESAI' -- core/metrics.py
# ──────────────────────────────────────────────────────────────────────────────


def test_11_metrics_tanpa_status_berjalan_selesai_beku():
    isi = _bersihkan(METRICS_PY)
    assert not re.search(r"status\s*=\s*'BERJALAN'", isi)
    assert not re.search(r"status\s*=\s*'SELESAI'", isi)


# ──────────────────────────────────────────────────────────────────────────────
# Uji 12 -- Tanpa use_container_width -- seluruh v3
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("berkas", SELURUH_V3_KECUALI_TESTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_12_tanpa_use_container_width(berkas: Path):
    isi = _bersihkan(berkas)
    assert "use_container_width" not in isi, f"{berkas}: use_container_width ditemukan"


# ──────────────────────────────────────────────────────────────────────────────
# Uji 13 -- duckdb.connect( selalu punya read_only=True di baris yang sama -- core/
# ──────────────────────────────────────────────────────────────────────────────

CORE_PY_FILES = sorted(CORE.glob("*.py"))


@pytest.mark.parametrize("berkas", CORE_PY_FILES, ids=lambda p: p.name)
def test_13_duckdb_connect_read_only(berkas: Path):
    isi = _baca(berkas)
    for baris in isi.splitlines():
        if "duckdb.connect(" in baris:
            assert "read_only=True" in baris, (
                f"{berkas.name}: duckdb.connect( tanpa read_only=True di baris yang sama: {baris!r}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Uji 14 -- Tanpa st.pills( berisi >4 opsi -- app_pages/
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("halaman", HALAMAN, ids=lambda p: p.name)
def test_14_tanpa_st_pills_lebih_dari_4_opsi(halaman: Path):
    isi = _baca(halaman)
    for match in re.finditer(r"st\.pills\(([^)]*)\)", isi, re.DOTALL):
        argumen = match.group(1)
        daftar = re.search(r"\[([^\]]*)\]", argumen)
        if daftar:
            jumlah_opsi = len([o for o in daftar.group(1).split(",") if o.strip()])
            assert jumlah_opsi <= 4, (
                f"{halaman.name}: st.pills( dengan {jumlah_opsi} opsi (>4): {match.group(0)[:120]}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Uji 15 -- Tanpa padanan temuan_halaman di components/ -- hanya dua fungsi boleh
# ──────────────────────────────────────────────────────────────────────────────

TAMPILAN_PY = COMPONENTS / "tampilan.py"


def test_15_components_hanya_dua_fungsi_tinggi_kontainer_dan_keadaan_kosong():
    for berkas in sorted(COMPONENTS.glob("*.py")):
        if berkas.name == "__init__.py":
            continue
        isi = _baca(berkas)
        nama_fungsi = re.findall(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", isi, re.MULTILINE)
        assert berkas == TAMPILAN_PY or not nama_fungsi, (
            f"{berkas.name}: fungsi tak terduga di components/: {nama_fungsi}"
        )

    isi_tampilan = _baca(TAMPILAN_PY)
    nama_fungsi = re.findall(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", isi_tampilan, re.MULTILINE)
    assert set(nama_fungsi) == {"tinggi_kontainer", "keadaan_kosong"}, (
        f"components/tampilan.py: fungsi ditemukan {nama_fungsi}, seharusnya persis "
        "{'tinggi_kontainer', 'keadaan_kosong'}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Uji 16 -- LAPORKAN (jangan gagalkan) label berkurung -- app_pages/
# ──────────────────────────────────────────────────────────────────────────────


def _string_constants_tanpa_docstring(path: Path) -> list[str]:
    """Semua literal string (ast.Constant) dalam kode, KECUALI docstring
    modul/fungsi/kelas -- dipakai supaya tiap kandidat diperiksa sebagai satu
    literal utuh, bukan hasil regex yang meloncat lintas batas string (bug
    yang ditemukan versi awal uji ini: `\\([^)]*\\)` naif atas teks mentah
    mencocokkan potongan lintas beberapa literal & docstring sekaligus)."""
    isi = _baca(path)
    try:
        pohon = ast.parse(isi)
    except SyntaxError:
        return []
    docstring_ids = set()
    target = [pohon] + [
        n for n in ast.walk(pohon)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for node in target:
        body = getattr(node, "body", None)
        if not body:
            continue
        pertama = body[0]
        if (
            isinstance(pertama, ast.Expr)
            and isinstance(pertama.value, ast.Constant)
            and isinstance(pertama.value.value, str)
        ):
            docstring_ids.add(id(pertama.value))
    return [
        n.value
        for n in ast.walk(pohon)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and id(n) not in docstring_ids
    ]


def test_16_laporkan_label_berkurung_untuk_tinjau_mata():
    """Tidak menggagalkan apa pun -- hanya mencetak temuan untuk ditinjau mata
    (P6, tidak bisa dimekaniskan sepenuhnya -- lihat ATURAN_TAMPILAN.md §6 no 16)."""
    for halaman in HALAMAN:
        kandidat = _string_constants_tanpa_docstring(halaman)
        ditemukan = [s for s in kandidat if re.search(r"\([^)]+\)", s)]
        if ditemukan:
            print(f"\n[uji_disiplin][16][tinjau-mata] {halaman.name}: label berkurung: {ditemukan}")
    assert True
