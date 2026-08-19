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
    # kandidat.csv/kandidat_keluarga.csv SENGAJA berbentuk PII (nama/email/KTP/alamat) --
    # itu skema aslinya (F-034, kamus_data.md), tapi 100% SINTETIS (demografi.yaml
    # meta.peringatan_pii). Guard kolom/nilai di bawah tidak berlaku utk keduanya; sebagai
    # gantinya kita pastikan generatornya SENDIRI tidak pernah membaca sumber PII asli.
    FILE_PII_SINTETIS = {"kandidat.csv", "kandidat_keluarga.csv"}
    tersangka_kolom: list[str] = []
    tersangka_nilai: list[str] = []
    for path in sorted(MASTER.glob("*.csv")):
        if path.name in FILE_PII_SINTETIS:
            continue
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

    # `nama_lengkap` di unit_pelaksana.csv/updl.csv adalah nama UNIT, bukan orang -- itu
    # pengecualian yang sudah ditelusuri. Selain itu, temuan apa pun harus diperiksa manual.
    KECUALI = {"unit_pelaksana.csv:nama_lengkap", "updl.csv:nama_lengkap"}
    tersangka_kolom = [t for t in tersangka_kolom if t not in KECUALI]
    cek("tidak ada kolom berbau PII di out/master (di luar kandidat.csv/kandidat_keluarga.csv)",
        not tersangka_kolom,
        f"{tersangka_kolom[:5]}" if tersangka_kolom else "sudah dikurangi pengecualian unit_pelaksana")
    cek("tidak ada nilai berpola email/NIK (di luar kandidat.csv/kandidat_keluarga.csv)",
        not tersangka_nilai, f"{tersangka_nilai[:3]}")

    sumber_08 = (ROOT / "mockdb" / "build" / "08_kandidat_pendaftaran.py").read_text(encoding="utf-8")
    TERLARANG = ["data sintetis", "rekrutmen_pln/akun", "rekrutmen_pln\\akun"]
    ditemukan = [t for t in TERLARANG if t in sumber_08]
    cek("generator kandidat (08) tidak pernah membaca sumber PII asli (DAPEG/dump akun)",
        not ditemukan, f"{ditemukan}")


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


# ---------------------------------------------------------------------------
# 8. Kota / UPDL / vendor / tahap_ref (langkah 07)
# ---------------------------------------------------------------------------
def cek_vendor_lokasi(R: dict, kota: list[dict], updl: list[dict], vendor: list[dict],
                       tahap_ref: list[dict]) -> None:
    print("\n[ kota / updl / vendor / tahap_ref ]")
    cek("kota.csv = 43 baris (F-019)", len(kota) == 43, f"{len(kota)}")
    cek("tidak ada nama kota kembar", len({k["nama"] for k in kota}) == len(kota))

    cek("updl.csv = 11 baris", len(updl) == 11, f"{len(updl)}")
    cek(
        "updl.csv persis subset unit_pelaksana.csv (jenis_unit=UPDL)",
        {u["updl_id"] for u in updl} == {r["kode_unit_pelaksana"] for r in baca("unit_pelaksana.csv")
                                          if r.get("jenis_unit") == "UPDL"},
    )

    cek("tidak ada vendor_id kembar", len({v["vendor_id"] for v in vendor}) == len(vendor))
    tipe = {v["tipe_layanan"] for v in vendor}
    cek("vendor mencakup psikologi & fisik_mcu", {"psikologi", "fisik_mcu"} <= tipe, f"{tipe}")
    dimodelkan = [v for v in vendor if v["status_sumber"] == "DIMODELKAN"]
    cek("vendor DIMODELKAN punya catatan", all(v["rujukan"] for v in dimodelkan))

    cek("tahap_ref.csv = 16 baris (6 seleksi + 3 fhci + 7 pasca)", len(tahap_ref) == 16, f"{len(tahap_ref)}")
    kode_ref = {t["tahap_kode"] for t in tahap_ref}
    kode_funnel = {t["tahap"] for t in R["funnel"]["funnel_mandiri"]["nasional_mandiri"]["tahapan"]}
    cek("kode tahap seleksi di tahap_ref cocok dgn funnel.yaml", kode_funnel <= kode_ref, f"selisih {kode_funnel - kode_ref}")


# ---------------------------------------------------------------------------
# 9b. Tahapan seleksi per kandidat (langkah 09)
# ---------------------------------------------------------------------------
def cek_seleksi_tahap(R: dict, seleksi_tahap: list[dict], seleksi_agregat: list[dict],
                       pendaftaran: list[dict], profesi: list[dict]) -> None:
    print("\n[ tahapan seleksi (langkah 09) ]")

    pendaftaran_id = {r["pendaftaran_id"] for r in pendaftaran}
    asing = [r["pendaftaran_id"] for r in seleksi_tahap if r["pendaftaran_id"] not in pendaftaran_id]
    cek("seleksi_tahap.pendaftaran_id semua ada di pendaftaran.csv", not asing, f"{len(asing)} baris asing")

    kode_valid = {t["kode"] for t in R["tahapan"]["tahap_seleksi"]}
    asing_kode = {r["tahap_kode"] for r in seleksi_tahap} - kode_valid
    cek("tahap_kode semuanya dikenal di tahapan.yaml", not asing_kode, f"asing: {asing_kode}")

    # jalur mandiri wajib mulai dari administrasi, RBB dari akademik_inggris (F-046).
    per_pendaftaran: dict[str, list[str]] = defaultdict(list)
    for r in seleksi_tahap:
        per_pendaftaran[r["pendaftaran_id"]].append(r["tahap_kode"])
    jalur_map = {r["pendaftaran_id"]: r["sumber_rekrutmen"] for r in pendaftaran}
    salah_masuk = [
        pid for pid, kodes in per_pendaftaran.items()
        if (jalur_map[pid] == "mandiri" and "administrasi" not in kodes)
        or (jalur_map[pid] == "rbb" and "administrasi" in kodes)
    ]
    cek("titik masuk sesuai jalur (mandiri->administrasi, rbb->akademik_inggris)",
        not salah_masuk, f"{len(salah_masuk)} pendaftaran menyimpang, mis. {salah_masuk[:3]}")

    # wawancara LULUS harus persis = jumlah DITERIMA -- jangkar keras yang sama dgn langkah 08.
    n_wawancara_lulus = sum(1 for r in seleksi_tahap if r["tahap_kode"] == "wawancara" and r["hasil"] == "LULUS")
    n_diterima = sum(1 for r in pendaftaran if r["hasil_akhir"] == "DITERIMA")
    cek("wawancara LULUS = DITERIMA di pendaftaran.csv", n_wawancara_lulus == n_diterima,
        f"{n_wawancara_lulus} vs {n_diterima}")

    # setiap pendaftaran GAGAL harus berhenti tepat di tahap_gugur-nya (baris terakhir GAGAL,
    # baris sebelumnya semua LULUS).
    salah_urut = []
    hasil_per_pendaftaran: dict[str, list[tuple]] = defaultdict(list)
    urutan_map = {t["kode"]: t["urutan"] for t in R["tahapan"]["tahap_seleksi"]}
    for r in seleksi_tahap:
        hasil_per_pendaftaran[r["pendaftaran_id"]].append((int(r["urutan"]), r["hasil"]))
    for pid, lst in hasil_per_pendaftaran.items():
        lst.sort()
        gagal_di = [i for i, (_, h) in enumerate(lst) if h == "GAGAL"]
        if gagal_di and (gagal_di != [len(lst) - 1]):
            salah_urut.append(pid)
    cek("baris GAGAL hanya di tahap TERAKHIR yang tercapai (tidak ada gugur ganda/di tengah)",
        not salah_urut, f"{len(salah_urut)} pendaftaran, mis. {salah_urut[:3]}")

    cek("seleksi_tahap_agregat hanya utk tahun berjalur RBB",
        {r["tahun_program"] for r in seleksi_agregat} <=
        {r["tahun_program"] for r in profesi if r["sumber_rekrutmen"] == "rbb"})
    cek("seleksi_tahap_agregat: jumlah_lulus tak pernah > jumlah_masuk",
        all(int(r["jumlah_lulus"]) <= int(r["jumlah_masuk"]) for r in seleksi_agregat))


# ---------------------------------------------------------------------------
# 9c. Pasca-seleksi: kontrak/SAMAPTA/pembidangan/OJT/SK (langkah 10)
# ---------------------------------------------------------------------------
def cek_pasca_tahap(R: dict, pasca: list[dict], pendaftaran: list[dict]) -> None:
    print("\n[ pasca-seleksi (langkah 10) ]")

    diterima_id = {r["pendaftaran_id"] for r in pendaftaran if r["hasil_akhir"] == "DITERIMA"}
    asing = [r["pendaftaran_id"] for r in pasca if r["pendaftaran_id"] not in diterima_id]
    cek("pasca_tahap.pendaftaran_id semua berasal dari pendaftaran DITERIMA",
        not asing, f"{len(asing)} baris asing")

    kode_valid = {t["kode"] for t in R["tahapan"]["tahap_pasca"]}
    asing_kode = {r["tahap_kode"] for r in pasca} - kode_valid
    cek("tahap_kode semuanya dikenal di tahapan.yaml.tahap_pasca", not asing_kode, f"asing: {asing_kode}")

    ORDER = [t["kode"] for t in R["tahapan"]["tahap_pasca"]]
    per_pendaftaran: dict[str, list[str]] = defaultdict(list)
    for r in sorted(pasca, key=lambda r: int(r["urutan"])):
        per_pendaftaran[r["pendaftaran_id"]].append(r["tahap_kode"])
    bukan_prefiks = [
        pid for pid, kodes in per_pendaftaran.items() if kodes != ORDER[: len(kodes)]
    ]
    cek("tiap pendaftaran menempuh tahap_pasca sbg PREFIKS berurutan (tidak ada yang dilompati)",
        not bukan_prefiks, f"{len(bukan_prefiks)} pendaftaran, mis. {bukan_prefiks[:3]}")

    cek("setiap pendaftaran DITERIMA punya >=1 baris pasca_tahap (pengumuman min. sudah lewat cutoff)",
        diterima_id <= set(per_pendaftaran), f"{len(diterima_id - set(per_pendaftaran))} tanpa baris")

    # sk_penempatan cuma boleh muncul kalau ketujuh tahap sebelumnya juga ada (prefiks penuh)
    ber_sk = [pid for pid, kodes in per_pendaftaran.items() if "sk_penempatan" in kodes]
    cek("pendaftaran ber-sk_penempatan menempuh ketujuh tahap pasca secara penuh",
        all(len(per_pendaftaran[pid]) == len(ORDER) for pid in ber_sk),
        f"{sum(1 for pid in ber_sk if len(per_pendaftaran[pid]) != len(ORDER))} pendaftaran tidak penuh")

    # OJT BERJALAN harus jadi baris TERAKHIR pendaftaran itu (belum lanjut ke ujian_ojt/sk)
    ojt_berjalan = [r for r in pasca if r["tahap_kode"] == "ojt" and r["status"] == "BERJALAN"]
    bukan_terakhir = [r["pendaftaran_id"] for r in ojt_berjalan
                       if per_pendaftaran[r["pendaftaran_id"]][-1] != "ojt"]
    cek("OJT BERJALAN selalu jadi tahap terakhir yang tercapai (belum ujian_ojt/sk)",
        not bukan_terakhir, f"{len(bukan_terakhir)} pendaftaran, mis. {bukan_terakhir[:3]}")

    progres_aneh = [r["pasca_id"] for r in pasca if not 0.0 <= float(r["progres"]) <= 1.0]
    cek("progres selalu di rentang [0,1]", not progres_aneh, f"{len(progres_aneh)} baris")

    progres_bukan_ojt = [
        r["pasca_id"] for r in pasca if r["tahap_kode"] != "ojt" and float(r["progres"]) != 1.0
    ]
    cek("tahap bertitik-tunggal (bukan ojt) selalu progres=1.0 (SELESAI)",
        not progres_bukan_ojt, f"{len(progres_bukan_ojt)} baris")


# ---------------------------------------------------------------------------
# 9. Kandidat & pendaftaran (langkah 08)
# ---------------------------------------------------------------------------
def cek_kandidat_pendaftaran(R: dict, kandidat: list[dict], pendaftaran: list[dict],
                              kand_didik: list[dict], kand_sert: list[dict],
                              kand_kel: list[dict], kand_berkas: list[dict],
                              profesi: list[dict]) -> None:
    print("\n[ kandidat & pendaftaran (langkah 08) ]")

    kandidat_id = {r["kandidat_id"] for r in kandidat}
    profesi_id = {r["profesi_id"] for r in profesi}
    cek("semua pendaftaran.kandidat_id ada di kandidat.csv",
        all(r["kandidat_id"] in kandidat_id for r in pendaftaran))
    cek("semua pendaftaran.profesi_id ada di profesi.csv",
        all(r["profesi_id"] in profesi_id for r in pendaftaran))

    hasil_ctr = Counter(r["hasil_akhir"] for r in pendaftaran)
    n_diterima = hasil_ctr.get("DITERIMA", 0)
    target = R["funnel"]["volume_target"]["status_per_15sep2026"]["lulus_wawancara"]
    cek("total DITERIMA di pendaftaran = lulus_wawancara funnel.yaml (F-078)",
        n_diterima == target, f"{n_diterima} vs {target}")

    # diterima per profesi harus persis = diterima_target dikurangi porsi ikatan dinas
    id_per_tahun: dict[int, int] = {}
    for row in R["kohort"]["kohort_per_tahun_program"]:
        id_per_tahun[row["tahun"]] = sum(
            k["diterima"] for k in row.get("komposisi_jalur", []) if k["sumber"] == "ikatan_dinas"
        )
    per_tahun_rows: dict[int, list[dict]] = defaultdict(list)
    for p in profesi:
        if int(p["diterima_target"]) > 0:
            per_tahun_rows[int(p["tahun_program"])].append(p)
    diterima_per_profesi: dict[str, int] = {}
    for tahun, rows in per_tahun_rows.items():
        total = sum(int(r["diterima_target"]) for r in rows)
        idn = id_per_tahun.get(tahun, 0)
        keep = max(0, total - idn)
        if idn == 0:
            for r in rows:
                diterima_per_profesi[r["profesi_id"]] = int(r["diterima_target"])
        else:
            bobot = [int(r["diterima_target"]) for r in rows]
            s = sum(bobot)
            raw = [b * keep / s for b in bobot]
            base = [int(x) for x in raw]
            sisa = keep - sum(base)
            order = sorted(range(len(raw)), key=lambda i: -(raw[i] - base[i]))
            for i in order[:sisa]:
                base[i] += 1
            for r, v in zip(rows, base):
                diterima_per_profesi[r["profesi_id"]] = v
    diterima_aktual: Counter = Counter()
    for r in pendaftaran:
        if r["hasil_akhir"] == "DITERIMA":
            diterima_aktual[r["profesi_id"]] += 1
    selisih = {pid: (diterima_aktual.get(pid, 0), target_n)
               for pid, target_n in diterima_per_profesi.items() if diterima_aktual.get(pid, 0) != target_n}
    cek("DITERIMA per profesi = diterima_target (dikurangi ikatan dinas)", not selisih, f"{list(selisih.items())[:5]}")

    # 1 profesi per gelombang per akun
    per_akun_gel: dict[str, set] = defaultdict(set)
    dobel = []
    for r in pendaftaran:
        key = (r["kandidat_id"], r["gelombang_id"])
        if r["gelombang_id"] in per_akun_gel[r["kandidat_id"]]:
            dobel.append(r["kandidat_id"])
        per_akun_gel[r["kandidat_id"]].add(r["gelombang_id"])
    cek("tidak ada akun melamar >1 profesi di gelombang yang sama", not dobel, f"{dobel[:5]}")

    pernah_melamar_flag = {r["kandidat_id"]: r["pernah_melamar"] == "True" for r in kandidat}
    id_yang_melamar = {r["kandidat_id"] for r in pendaftaran}
    salah_true = [k for k in id_yang_melamar if not pernah_melamar_flag.get(k, False)]
    salah_false = [k for k, v in pernah_melamar_flag.items() if v and k not in id_yang_melamar]
    cek("kandidat.pernah_melamar konsisten dgn keberadaan di pendaftaran.csv",
        not salah_true and not salah_false, f"{len(salah_true)} salah-true, {len(salah_false)} salah-false")

    # RBB: berkas_unggahan permanen kosong (kelengkapan.yaml per_jalur.rbb)
    jalur_anchor = {r["kandidat_id"]: r["jalur_anchor"] for r in kandidat}
    id_rbb = {k for k, v in jalur_anchor.items() if v == "rbb"}
    berkas_rbb = [r for r in kand_berkas if r["kandidat_id"] in id_rbb]
    cek("kandidat_berkas kosong utk seluruh kandidat berjalur RBB (F-046/kelengkapan.yaml)",
        not berkas_rbb, f"{len(berkas_rbb)} baris ditemukan")

    for nama, rows in (("kandidat_pendidikan", kand_didik), ("kandidat_sertifikasi", kand_sert),
                        ("kandidat_keluarga", kand_kel), ("kandidat_berkas", kand_berkas)):
        asing = [r["kandidat_id"] for r in rows if r["kandidat_id"] not in kandidat_id]
        cek(f"{nama}.kandidat_id semua ada di kandidat.csv", not asing, f"{len(asing)} baris asing")

    gender_ctr = Counter(r["jenis_kelamin"] for r in kandidat)
    total_g = sum(gender_ctr.values())
    porsi_p = gender_ctr.get("P", 0) / total_g
    cek("gender kandidat tidak 50:50 & tidak condong ekstrem (rentang wajar 0,55-0,75 P)",
        0.55 <= porsi_p <= 0.75, f"P={porsi_p:.3f}")


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
    kota = baca("kota.csv")
    updl = baca("updl.csv")
    vendor = baca("vendor.csv")
    tahap_ref = baca("tahap_ref.csv")
    kandidat = baca("kandidat.csv")
    pendaftaran = baca("pendaftaran.csv")
    kand_didik = baca("kandidat_pendidikan.csv")
    kand_sert = baca("kandidat_sertifikasi.csv")
    kand_kel = baca("kandidat_keluarga.csv")
    kand_berkas = baca("kandidat_berkas.csv")
    seleksi_tahap = baca("seleksi_tahap.csv")
    seleksi_agregat = baca("seleksi_tahap_agregat.csv")
    pasca = baca("pasca_tahap.csv")
    if gagal:
        print("\nInput belum lengkap -- hentikan.")
        return 1

    cek_struktural(R, pagu, usulan)
    cek_grade_masuk(R, pagu)
    cek_total_pagu(R, pagu)
    cek_rujukan(pagu, usulan, unit)
    cek_angka(usulan, proyeksi, ringkas)
    cek_katalog(R, gel, prog, prof, prodi)
    cek_vendor_lokasi(R, kota, updl, vendor, tahap_ref)
    cek_kandidat_pendaftaran(R, kandidat, pendaftaran, kand_didik, kand_sert, kand_kel, kand_berkas, prof)
    cek_seleksi_tahap(R, seleksi_tahap, seleksi_agregat, pendaftaran, prof)
    cek_pasca_tahap(R, pasca, pendaftaran)
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
