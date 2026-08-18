"""Verifikasi KELUARAN generator di mockdb/out/master/.

Pendamping `00_verifikasi_rules.py`. Bedanya penting:

    00_verifikasi_rules  -> membaca rules/*.yaml   (apakah ATURANnya konsisten)
    00b_verifikasi_keluaran -> membaca out/master/*.csv (apakah HASILnya menaati aturan)

Kekosongan itulah yang membiarkan langkah 05 memasukkan 143 orang ke jabatan struktural:
seluruh 161 cek lama lulus, karena tak satu pun di antaranya pernah membuka CSV hasil.
Aturan yang benar tidak menjamin generator menaatinya.

Jalankan:  python mockdb/build/00b_verifikasi_keluaran.py
Keluar 0 kalau semua cek lulus, 1 kalau ada yang gagal.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"
SRC = ROOT / "knowledge" / "sources"

TOL = 1e-3

# Nama jenjang di CSV keluaran vs kunci di jabatan.yaml. Dipisah supaya pemetaan
# pendidikan->grade tetap dibaca dari aturan, bukan ditulis ulang di sini.
ALIAS_PENDIDIKAN = {"SMK": "SMK", "D3": "D-III", "S1": "S1/D-IV", "S2": "S2"}

# Penjaga PII. DAPEG asli (Sample-03) memuat 37 ribu nama + NIP; keluaran generator
# tidak boleh pernah memuat kolom orang. Lihat HANDOFF §8.
KOLOM_PII = re.compile(
    r"\b(nip|nik|ktp|npwp|no_?rek|rekening|telepon|ponsel|hp|email|nama_lengkap|"
    r"nama_pegawai|alamat|tgl_lahir|tanggal_lahir|birth)\b",
    re.I,
)
POLA_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

gagal: list[str] = []


def cek(nama: str, kondisi: bool, detail: str = "") -> None:
    if kondisi:
        print(f"  OK    {nama}" + (f" -- {detail}" if detail else ""))
    else:
        gagal.append(f"{nama}: {detail}")
        print(f"  GAGAL {nama} -- {detail}")


def baca(nama_berkas: str) -> list[dict]:
    path = MASTER / nama_berkas
    if not path.exists():
        print(f"\n  BERKAS HILANG: {path.relative_to(ROOT)}")
        print("  Jalankan generator yang menghasilkannya dulu (langkah 01/04/05).")
        gagal.append(f"berkas hilang: {nama_berkas}")
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# 1. Larangan struktural -- aturan paling keras di mockdb
# ---------------------------------------------------------------------------
def cek_struktural(R: dict, pagu: list[dict], usulan: list[dict]) -> None:
    print("\n[ larangan struktural ]")
    terlarang = {s.strip().upper() for s in R["jabatan"]["larangan_struktural"]["kelompok_jabatan_terlarang"]}

    bad = Counter(
        x["nama_jabatan"].strip().upper() for x in pagu
        if x["nama_jabatan"].strip().upper() in terlarang
    )
    orang = sum(int(x["jumlah"]) for x in pagu if x["nama_jabatan"].strip().upper() in terlarang)
    cek("pagu: tidak ada jabatan struktural", not bad,
        f"{sum(bad.values())} baris / {orang} orang: {dict(bad)}" if bad else
        f"{len(pagu):,} baris bersih")

    # Disaring lewat kelompok, bukan grade. TEAM LEADER bergrade G2 (sama dengan OFFICER)
    # dan ASSISTANT MANAGER bergrade G3 (sama dengan SENIOR OFFICER), jadi saringan
    # berbasis grade memang tidak bisa memisahkan keduanya -- persis peringatan jabatan.yaml.
    badu = Counter(
        x["kelompok_jabatan"].strip().upper() for x in usulan
        if x["kelompok_jabatan"].strip().upper() in terlarang
    )
    cek("usulan: tidak ada jabatan struktural", not badu,
        f"{sum(badu.values())} baris: {dict(badu)}" if badu else f"{len(usulan):,} baris bersih")


# ---------------------------------------------------------------------------
# 2. Grade masuk sesuai jenjang pendidikan
# ---------------------------------------------------------------------------
def cek_grade_masuk(R: dict, pagu: list[dict]) -> None:
    print("\n[ grade masuk per jenjang pendidikan ]")
    peta = R["jabatan"]["grade_masuk"]["pemetaan"]

    salah_grade, salah_kelompok, tak_dikenal = [], [], set()
    for x in pagu:
        pend = x["pendidikan"].strip()
        kunci = ALIAS_PENDIDIKAN.get(pend)
        if kunci is None or kunci not in peta:
            tak_dikenal.add(pend)
            continue
        aturan = peta[kunci]
        if x["kode_grade"].strip() != aturan["grade"]:
            salah_grade.append(f"{pend}->{x['kode_grade']} (harusnya {aturan['grade']})")
        if x["nama_jabatan"].strip().upper() not in {k.upper() for k in aturan["kelompok"]}:
            salah_kelompok.append(f"{pend}->{x['nama_jabatan']}")

    cek("jenjang pendidikan dikenal", not tak_dikenal, f"asing: {tak_dikenal}")
    cek("kode_grade sesuai pendidikan", not salah_grade,
        f"{len(salah_grade)} baris, mis. {salah_grade[:3]}" if salah_grade else
        "D3->G1, S1->G2, S2->G3")
    cek("kelompok jabatan sesuai pendidikan", not salah_kelompok,
        f"{len(salah_kelompok)} baris, mis. {salah_kelompok[:3]}" if salah_kelompok else
        "sesuai F-042/F-054")

    # Level 4 (SPC/SSP) hanya bisa dimasuki lewat PRO_HIRE, dan pro hire di luar cakupan.
    lv = {x["level"] for x in pagu}
    cek("tidak ada level pro hire (4+) di pagu", not {l for l in lv if int(l) >= 4},
        f"level ada: {sorted(lv)}")


# ---------------------------------------------------------------------------
# 3. Total pagu mendarat di ukuran kohort nyata
# ---------------------------------------------------------------------------
def cek_total_pagu(R: dict, pagu: list[dict]) -> None:
    print("\n[ total pagu vs kohort ]")
    kohort = {
        r["tahun"]: r for r in R["kohort"]["kohort_per_tahun_program"]
        if r.get("ada_gelombang", True)
    }
    per_tahun: dict[int, int] = defaultdict(int)
    for x in pagu:
        per_tahun[int(x["tahun_program"])] += int(x["jumlah"])

    total, target = sum(per_tahun.values()), sum(i["induk_diterima"] for i in kohort.values())
    cek("total pagu = total kohort induk", total == target, f"{total:,} vs {target:,}")

    meleset = [
        f"{t}: {per_tahun.get(t, 0)} vs {i['induk_diterima']}"
        for t, i in sorted(kohort.items()) if per_tahun.get(t, 0) != i["induk_diterima"]
    ]
    cek("pagu per tahun = kohort per tahun", not meleset, "; ".join(meleset) or f"{len(kohort)} tahun cocok")

    cek("tidak ada tahun di luar kohort", not (set(per_tahun) - set(kohort)),
        f"asing: {sorted(set(per_tahun) - set(kohort))}")
    cek("semua baris pagu berjumlah >= 1", all(int(x["jumlah"]) >= 1 for x in pagu),
        f"{sum(1 for x in pagu if int(x['jumlah']) < 1)} baris bernilai < 1")


# ---------------------------------------------------------------------------
# 4. Keutuhan rujukan antar berkas
# ---------------------------------------------------------------------------
def cek_rujukan(pagu: list[dict], usulan: list[dict], unit: list[dict]) -> None:
    print("\n[ keutuhan rujukan antar berkas ]")
    penuh = {u["unit_induk"] for u in unit}
    pendek = {u["nama_pendek"] for u in unit}

    asing_p = {x["holding_subholding"] for x in pagu} - pendek
    cek("pagu: unit dikenal di unit_induk.csv", not asing_p, f"asing: {sorted(asing_p)[:4]}")

    asing_u = {x["unit_induk"] for x in usulan} - penuh
    cek("usulan: unit dikenal di unit_induk.csv", not asing_u, f"asing: {sorted(asing_u)[:4]}")

    # nama_jabatan + sebutan_jabatan harus bisa merangkai balik jadi jabatan utuh.
    pecah = [
        x["jabatan"] for x in pagu
        if f"{x['nama_jabatan']} {x['sebutan_jabatan']}".strip() != x["jabatan"].strip()
    ]
    cek("pemecahan nama/sebutan jabatan pulih utuh", not pecah,
        f"{len(pecah)} baris, mis. {pecah[:2]}" if pecah else "gaya Sample-02")

    beda = [x for x in pagu if not x["jurusan_pendidikan"].startswith(x["pendidikan"])]
    cek("jurusan_pendidikan berawalan jenjangnya", not beda, f"{len(beda)} baris menyimpang")


# ---------------------------------------------------------------------------
# 5. Kewarasan angka
# ---------------------------------------------------------------------------
def cek_angka(usulan: list[dict], proyeksi: list[dict], ringkas: list[dict]) -> None:
    print("\n[ kewarasan angka ]")
    negatif = [x for x in usulan if float(x["usulan"]) < 0 or float(x["kekosongan"]) < 0]
    cek("usulan & kekosongan tidak negatif", not negatif, f"{len(negatif)} baris negatif")

    pecah = [
        x for x in usulan
        if abs(float(x["kekosongan"]) + float(x["gap_ftk"]) - float(x["usulan"])) > 0.01
    ]
    cek("usulan = kekosongan + gap_ftk", not pecah, f"{len(pecah)} baris tidak menutup")

    if proyeksi and ringkas:
        a = sum(float(x["kekosongan"]) for x in proyeksi)
        b = sum(float(x["kekosongan"]) for x in ringkas)
        cek("proyeksi rinci = ringkasannya", abs(a - b) < max(1.0, a * TOL),
            f"{a:,.1f} vs {b:,.1f}")

    neg = [x for x in proyeksi if float(x["kekosongan"]) < 0]
    cek("kekosongan proyeksi tidak negatif", not neg, f"{len(neg)} baris negatif")

    # Baris berformasi nol sengaja DIPERTAHANKAN (gaya Sample-02): posisi ada di unit,
    # tapi formasinya nol tahun itu. Kalau tidak ada satu pun, ambang pembuangan
    # kemungkinan hidup lagi dan membuat "formasi nol" tak bisa dibedakan dari
    # "posisi tidak ada".
    tipis = sum(1 for x in usulan if float(x["usulan"]) < 0.5)
    cek("baris berformasi nol dipertahankan", tipis > 0,
        f"{tipis:,} dari {len(usulan):,} baris ({tipis / len(usulan):.0%})")


# ---------------------------------------------------------------------------
# 6. Penjaga PII -- keluaran tidak boleh memuat data orang
# ---------------------------------------------------------------------------
def cek_pii() -> None:
    print("\n[ penjaga PII ]")
    tersangka_kolom: list[str] = []
    tersangka_nilai: list[str] = []
    for path in sorted(MASTER.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as f:
            r = csv.reader(f)
            kolom = next(r, [])
            for k in kolom:
                if KOLOM_PII.search(k):
                    tersangka_kolom.append(f"{path.name}:{k}")
            for i, baris in enumerate(r):
                if i >= 400:
                    break
                for sel in baris:
                    if POLA_EMAIL.search(sel) or re.fullmatch(r"\d{16}", sel.strip()):
                        tersangka_nilai.append(f"{path.name}: {sel[:24]}")
                        break

    # `nama_lengkap` di unit_pelaksana.csv adalah nama UNIT, bukan orang -- itu satu-satunya
    # pengecualian yang sudah ditelusuri. Selain itu, temuan apa pun harus diperiksa manual.
    tersangka_kolom = [t for t in tersangka_kolom if t != "unit_pelaksana.csv:nama_lengkap"]
    cek("tidak ada kolom berbau PII di out/master", not tersangka_kolom,
        f"{tersangka_kolom[:5]}" if tersangka_kolom else "sudah dikurangi pengecualian unit_pelaksana")
    cek("tidak ada nilai berpola email/NIK", not tersangka_nilai, f"{tersangka_nilai[:3]}")


# ---------------------------------------------------------------------------
# 7. Katalog gelombang/program/profesi (langkah 06)
# ---------------------------------------------------------------------------
def cek_katalog(R: dict, gel: list[dict], prog: list[dict], prof: list[dict],
                prodi: list[dict]) -> None:
    print("\n[ katalog gelombang/program/profesi ]")
    ang = R["angkatan"]

    # --- aturan paling keras langkah 06: tidak ada judul yang dikarang ---
    asli: set[str] = set()

    def norm(j: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", (j or "").upper())

    for path, kolom in (
        (SRC / "rekrutmen_pln" / "programs.csv", "title"),
        (SRC / "rekrutmen_pln" / "wayback" / "programs_historis.csv", "judul"),
        (SRC / "rbb_fhci" / "lowongan_pln_rbb.csv", "vacancy_name"),
    ):
        if path.exists():
            with path.open(encoding="utf-8-sig", newline="") as f:
                asli |= {norm(r[kolom]) for r in csv.DictReader(f)}

    karangan = [
        p["judul"] for p in prog
        if p["sumber_judul"] != "tidak_terekam" and norm(p["judul"]) not in asli
    ]
    cek("tidak ada judul program yang dikarang", not karangan,
        f"{len(karangan)} judul asing, mis. {karangan[:2]}" if karangan else
        f"{len(prog)} judul, semua terlacak ke sumber")

    penanda = [p for p in prog if p["sumber_judul"] == "tidak_terekam"]
    cek("gelombang tanpa judul diberi penanda", all("tidak terekam" in p["judul"] for p in penanda),
        f"{len(penanda)} program berpenanda eksplisit")

    # SMK tidak dimodelkan di horison ini (angkatan.yaml -> smk_pelaksana).
    smk = [p["judul"] for p in prog if re.search(r"\bSMK\b|TINGKAT SMA", p["judul"].upper())]
    cek("tidak ada program SMK di horison", not smk, f"{len(smk)} program: {smk[:2]}")

    # --- nomor angkatan: yang dialokasikan hadir, yang dilubangi tetap kosong ---
    dipakai = {int(g["angkatan"]) for g in gel}
    for seri in ("utama", "khusus"):
        alokasi = {a for tahun in ang["seri"][seri]["alokasi_horison"].values() for a in tahun}
        hadir = {a for a in dipakai if any(
            int(g["angkatan"]) == a and g["seri"] == seri for g in gel)}
        cek(f"angkatan seri {seri} sesuai alokasi", hadir == alokasi,
            f"hasil {sorted(hadir)} vs aturan {sorted(alokasi)}")
    lubang = set(ang["seri"]["utama"]["lubang"])
    cek("lubang angkatan tetap kosong", not (dipakai & lubang),
        f"terisi: {sorted(dipakai & lubang)}" if dipakai & lubang else f"{sorted(lubang)} kosong")

    # --- jeda pipeline ---
    salah = [g for g in gel if int(g["tahun_masuk"]) != int(g["tahun_program"]) + 1]
    cek("tahun_masuk = tahun_program + 1", not salah, f"{len(salah)} gelombang menyimpang")

    # --- total diterima dijangkar ke kohort ---
    koh = {r["tahun"]: r for r in R["kohort"]["kohort_per_tahun_program"]
           if r.get("ada_gelombang", True)}
    per_tahun: dict[int, int] = defaultdict(int)
    for p in prof:
        per_tahun[int(p["tahun_program"])] += int(p["diterima_target"])
    total = sum(per_tahun.values())
    target = sum(i["induk_diterima"] + i["sub_diterima"] for i in koh.values())
    cek("total diterima = kohort Group", total == target, f"{total:,} vs {target:,}")

    meleset = [f"{t}: {per_tahun.get(t, 0)} vs {i['induk_diterima'] + i['sub_diterima']}"
               for t, i in sorted(koh.items())
               if per_tahun.get(t, 0) != i["induk_diterima"] + i["sub_diterima"]]
    cek("diterima per tahun = kohort per tahun", not meleset, "; ".join(meleset) or f"{len(koh)} tahun cocok")

    # --- keutuhan rujukan ---
    gid = {g["gelombang_id"] for g in gel}
    pid = {p["program_id"] for p in prog}
    fid = {p["profesi_id"] for p in prof}
    cek("program merujuk gelombang yang ada", not ({p["gelombang_id"] for p in prog} - gid), "")
    cek("profesi merujuk program & gelombang yang ada",
        not ({p["program_id"] for p in prof} - pid) and not ({p["gelombang_id"] for p in prof} - gid), "")
    cek("profesi_prodi merujuk profesi yang ada", not ({p["profesi_id"] for p in prodi} - fid),
        f"{len(prodi):,} baris syarat IPK per prodi")

    # --- syarat administrasi masuk akal & sesuai jalur ---
    tabel = R["administrasi"]["umur_maks_saat_daftar"]
    salah_umur = [
        f"{p['profesi_id']} {p['sumber_rekrutmen']}/{p['jenjang']}={p['umur_maks']}"
        for p in prof if p["jenis_program"] != "PRO_HIRE"
        and p["status_sumber"] != "NYATA_RBB"
        and int(p["umur_maks"]) != tabel.get("rbb" if p["sumber_rekrutmen"] == "rbb" else "mandiri",
                                             {}).get(p["jenjang"], int(p["umur_maks"]))
    ]
    cek("batas umur sesuai jalur", not salah_umur,
        f"{len(salah_umur)} menyimpang, mis. {salah_umur[:2]}" if salah_umur else
        "mandiri vs rbb dibedakan (F-022/F-043)")

    ipk_aneh = [p["profesi_id"] for p in prof if not 2.0 <= float(p["min_ipk"]) <= 4.0]
    cek("IPK minimal dalam rentang wajar", not ipk_aneh, f"{len(ipk_aneh)} di luar 2,0-4,0")

    # --- setiap jenis_program non-RBB harus punya arketipe funnel (F-064) ---
    peta_arketipe = R["funnel"]["pemilihan_arketipe"]["peta"]
    muncul = {p["jenis_program"] for p in prof} - {"RBB"}
    tak_terpetakan = muncul - set(peta_arketipe)
    cek("tiap jenis_program non-RBB punya arketipe funnel", not tak_terpetakan,
        f"{tak_terpetakan} tidak ada di funnel.yaml pemilihan_arketipe.peta" if tak_terpetakan else
        f"{sorted(muncul)} semua terpetakan")

    kosong = [g["gelombang_id"] for g in gel if int(g["n_profesi"]) == 0]
    cek("setiap gelombang punya profesi", not kosong, f"kosong: {kosong}")

    tanpa_tanggal = [g["gelombang_id"] for g in gel if not g["tgl_buka"] or not g["tgl_tutup"]]
    cek("semua gelombang punya tgl_buka & tgl_tutup", not tanpa_tanggal,
        f"{tanpa_tanggal} tidak ada tanggal" if tanpa_tanggal else "0 kosong (F-076)")
    n_estimasi = sum(1 for g in gel if g["tgl_status"] == "estimasi")
    cek("tgl_status terisi utk tiap gelombang", all(g["tgl_status"] in ("nyata", "estimasi") for g in gel),
        f"{n_estimasi}/{len(gel)} gelombang pakai tanggal ESTIMASI (F-076) -- wajib ditandai di dashboard")

    # Kursi subholding hanya boleh jatuh ke entri berpenempatan subholding. `sub_diterima`
    # di kohort.yaml diturunkan dari jumlah entri itu (F-003), jadi kalau alokasi memakai
    # pemisahan lain, sebuah gelombang bisa menerima lebih sedikit orang daripada angka
    # yang diturunkan dari entri penempatannya sendiri.
    meleset_sh = []
    for t, i in sorted(koh.items()):
        rows = [p for p in prof if int(p["tahun_program"]) == t]
        punya_sh = any(p["penempatan"] == "SUBHOLDING" for p in rows)
        if not punya_sh:
            continue        # tahun tanpa entri subholding di katalog: kursinya dilebur
        sh = sum(int(p["diterima_target"]) for p in rows if p["penempatan"] == "SUBHOLDING")
        if sh != i["sub_diterima"]:
            meleset_sh.append(f"{t}: {sh} vs {i['sub_diterima']}")
    cek("kursi subholding = sub_diterima kohort", not meleset_sh,
        "; ".join(meleset_sh) or "tiap tahun berentri subholding cocok")


def main() -> int:
    print(f"Verifikasi keluaran di {MASTER}")
    R = {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(RULES.glob("*.yaml"))}

    pagu = baca("pagu_rekrutmen.csv")
    usulan = baca("usulan_kebutuhan.csv")
    unit = baca("unit_induk.csv")
    proyeksi = baca("proyeksi_kekosongan.csv")
    ringkas = baca("kekosongan_ringkas.csv")
    gel = baca("gelombang.csv")
    prog = baca("program.csv")
    prof = baca("profesi.csv")
    prodi = baca("profesi_prodi.csv")
    if gagal:
        print("\nInput belum lengkap -- hentikan.")
        return 1

    cek_struktural(R, pagu, usulan)
    cek_grade_masuk(R, pagu)
    cek_total_pagu(R, pagu)
    cek_rujukan(pagu, usulan, unit)
    cek_angka(usulan, proyeksi, ringkas)
    cek_katalog(R, gel, prog, prof, prodi)
    cek_pii()

    print("\n" + "=" * 60)
    if gagal:
        print(f"{len(gagal)} CEK GAGAL:")
        for g in gagal:
            print(f"  - {g}")
        return 1
    print("SEMUA CEK LULUS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
