"""Penempatan: bidang OJT (pembidangan) + unit/posisi definitif (SK) per kandidat DITERIMA.

Urutan kausal (rules/README.md): pendaftaran.csv (langkah 08) + pasca_tahap.csv
(langkah 10, `sk_penempatan` = jangkar "sudah jadi pegawai penuh" vs "masih OJT")
-> jabatan.yaml (KE MANA mereka ditempatkan). Dua sumbu independen digabung di sini
(F-064): volume per tahap (sudah final dari langkah 08-10) TIDAK diutak-atik lagi;
langkah ini murni menambahkan atribut "ke mana".

METODE (mengikuti jabatan.yaml -> penempatan.urutan_keputusan):
  1. `bidang_pembidangan`+`sub_bidang` (bidang fungsional, dipakai jg utk lokasi OJT)
     ditentukan dari `nama_profesi` -> minat_profesi.csv (107/176 profesi INDUK cocok
     langsung -- itulah literally apa yang dipilih pelamar, F-005). Profesi yang TIDAK
     cocok langsung (gelombang generik "REKRUTMEN ... LOKASI X") jatuh ke fallback:
     klasifikasi TEKNIK/NON-TEKNIK dari `program_studi` kandidat sendiri, lalu sampel
     tertimbang `rumpun_subbidang.csv` x `rumpun_jurusan.csv` (bobot rumpun asli
     langkah 03, BUKAN bobot baru).
  2. Kandidat INDUK yang SUDAH ber-`sk_penempatan` (jangkar keras dari langkah 10)
     dapat unit+posisi DEFINITIF: satu kursi ditarik dari `pagu_rekrutmen.csv`
     (tahun_program + kode_grade WAJIB cocok -- larangan keras jabatan.yaml; sub_bidang
     lebih disukai tapi boleh longgar kalau kursi persis habis). Kandidat yang MASIH OJT
     (belum SK) cuma dapat bidang_pembidangan -- unit/posisi biarkan kosong (F-018,
     "diterima != sudah jadi pegawai").
  3. Kursi `pagu_rekrutmen` per tahun SELALU lebih banyak dari kandidat per-orang yang
     tersedia (pagu = seluruh induk_diterima TERMASUK ikatan dinas, F-054; kandidat
     per-orang di pendaftaran.csv TIDAK termasuk ikatan dinas, F-078) -- sisa kursi tak
     terpakai itu memang representasi headcount ikatan dinas yang tidak dimodelkan
     per-kandidat. Dilaporkan sbg cek konsistensi, bukan dipaksa habis.
  4. Kecenderungan KTP (DIMODELKAN, jabatan.yaml) diterapkan sbg bobot lunak: kalau ada
     >1 kursi sama-sama valid (tahun+grade+sub_bidang), yang nama unit_induk-nya memuat
     propinsi_asal kandidat diberi bobot lebih besar, dilipatkan lagi utk perempuan.
  5. Kandidat SUBHOLDING tidak diberi unit/posisi granular (DECISION-01, "holding kaya,
     subholding ringkas") -- cuma nama perusahaan (dari nama_profesi kalau tersurat,
     else sampel tertimbang) + bidang_pembidangan dari `bobot_subholding` perusahaan itu
     (arahnya TERBALIK dari holding -- Pembangkitan dominan di IP/NP, jabatan.yaml).
  6. Lokasi OJT (`updl_id`) disampel tertimbang oleh `jumlah_pegawai` UPDL (DIMODELKAN --
     tidak ada data rute bidang->UPDL spesifik di sumber manapun).

Input  : rules/jabatan.yaml, rules/kohort.yaml, out/master/{profesi,pendaftaran,
         pasca_tahap,pagu_rekrutmen,minat_profesi,rumpun_subbidang,rumpun_jurusan,
         kandidat,kandidat_pendidikan,unit_induk,updl}.csv
Output : out/master/penempatan.csv

Jalankan: python mockdb/build/11_penempatan.py
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

SEED = 20260915
rng = np.random.default_rng(SEED)


def baca_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def muat_yaml(nama: str) -> dict:
    return yaml.safe_load((RULES / nama).read_text(encoding="utf-8"))


print("Langkah 11: penempatan (bidang OJT + unit/posisi definitif)\n")

jabatan_yaml = muat_yaml("jabatan.yaml")
kohort_yaml = muat_yaml("kohort.yaml")

profesi = {r["profesi_id"]: r for r in baca_csv(MASTER / "profesi.csv")}
pendaftaran = baca_csv(MASTER / "pendaftaran.csv")
pasca_tahap = baca_csv(MASTER / "pasca_tahap.csv")
pagu = baca_csv(MASTER / "pagu_rekrutmen.csv")
minat_profesi = baca_csv(MASTER / "minat_profesi.csv")
rumpun_subbidang = baca_csv(MASTER / "rumpun_subbidang.csv")
rumpun_jurusan = {r["rumpun"]: r for r in baca_csv(MASTER / "rumpun_jurusan.csv")}
kandidat = {r["kandidat_id"]: r for r in baca_csv(MASTER / "kandidat.csv")}
kand_didik = baca_csv(MASTER / "kandidat_pendidikan.csv")
unit_induk = baca_csv(MASTER / "unit_induk.csv")
updl = baca_csv(MASTER / "updl.csv")

# ---------------------------------------------------------------------------
# 1. Tabel bantu
# ---------------------------------------------------------------------------
NAMA_PENDEK_KE_PENUH = {u["nama_pendek"]: u["unit_induk"] for u in unit_induk}

SUB_BIDANG_KE_PEMBIDANGAN = {m["sub_bidang"]: m["bidang_pembidangan"] for m in minat_profesi if m["sub_bidang"]}
# sub_bidang yang tidak muncul di minat_profesi.csv (K3, Audit, Komunikasi, Proteksi, SDM murni)
# -- pemetaan tambahan DIMODELKAN, keyakinan rendah, dipetakan ke bucket bidang_pembidangan terdekat.
SUB_BIDANG_KE_PEMBIDANGAN.setdefault("Proteksi dan Kontrol", "Proteksi dan Kontrol")
SUB_BIDANG_KE_PEMBIDANGAN.setdefault("Sumber Daya Manusia", "SDM")
SUB_BIDANG_KE_PEMBIDANGAN.setdefault("K3 dan Lingkungan", "SDM")
SUB_BIDANG_KE_PEMBIDANGAN.setdefault("Audit dan Risiko", "Keuangan")
SUB_BIDANG_KE_PEMBIDANGAN.setdefault("Komunikasi dan Umum", "SDM")

NAMA_PROFESI_KE_SUBBIDANG = {m["minat_profesi"]: m["sub_bidang"] for m in minat_profesi if m["minat_profesi"]}

# distribusi sub_bidang tertimbang per bidang_sub (TEKNIK/NON-TEKNIK), dari rumpun_subbidang x rumpun_jurusan
bobot_per_bidang_sub: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
for r in rumpun_subbidang:
    porsi_rumpun = float(rumpun_jurusan.get(r["rumpun"], {}).get("porsi_permintaan", 0.0))
    bobot_per_bidang_sub[r["bidang_sub"]][r["sub_bidang"]] += float(r["bobot"]) * porsi_rumpun
FALLBACK_SUBBIDANG: dict[str, tuple[list[str], list[float]]] = {}
for bidang_sub, dist in bobot_per_bidang_sub.items():
    subs = list(dist.keys())
    bobot = np.array(list(dist.values()))
    FALLBACK_SUBBIDANG[bidang_sub] = (subs, bobot / bobot.sum())

GRADE_MASUK = jabatan_yaml["grade_masuk"]["pemetaan"]
BOBOT_SUB = jabatan_yaml["pembidangan"]["bobot_subholding"]

SUBHOLDING = {s["kode"]: s for s in kohort_yaml["subholding"]["daftar"]}
SUB_MANDIRI = [k for k, v in SUBHOLDING.items() if not v.get("hanya_jalur")]
SUB_RBB = ["ICON", "BTM", "HLY"]           # F-016 catatan 2024: Icon Plus 7, Batam 5, Haleyora 3
BOBOT_SUB_RBB = np.array([7, 5, 3], dtype=float)
BOBOT_SUB_RBB /= BOBOT_SUB_RBB.sum()

RE_PERUSAHAAN = {
    "IP": re.compile(r"indonesia power", re.I),
    "NP": re.compile(r"nusantara power", re.I),
    "ND": re.compile(r"nusa daya", re.I),
    "EPI": re.compile(r"energi primer", re.I),
    "ES": re.compile(r"electricity services", re.I),
    "ICON": re.compile(r"icon\s*\+|icon plus|comnets", re.I),
    "BTM": re.compile(r"\bbatam\b", re.I),
    "HLY": re.compile(r"haleyora", re.I),
}

# klasifikasi TEKNIK/NON-TEKNIK dari pendidikan TERAKHIR kandidat (dipakai jenjang tertinggi/aktif)
prodi_terakhir: dict[str, str] = {}
for r in kand_didik:
    if r["pendidikan_terakhir"] == "True":
        prodi_terakhir[r["kandidat_id"]] = r["program_studi"]


def bidang_sub_kandidat(kandidat_id: str) -> str:
    prodi = prodi_terakhir.get(kandidat_id, "")
    return "TEKNIK" if "TEKNIK" in prodi.upper() else "NON-TEKNIK"


def pilih_sub_bidang(nama_profesi: str, kandidat_id: str) -> str:
    langsung = NAMA_PROFESI_KE_SUBBIDANG.get(nama_profesi)
    if langsung:
        return langsung
    bs = bidang_sub_kandidat(kandidat_id)
    subs, bobot = FALLBACK_SUBBIDANG[bs]
    return str(rng.choice(subs, p=bobot))


def pilih_perusahaan_sub(nama_profesi: str, jalur: str) -> str:
    for kode, pat in RE_PERUSAHAAN.items():
        if pat.search(nama_profesi):
            return kode
    if jalur == "rbb":
        return str(rng.choice(SUB_RBB, p=BOBOT_SUB_RBB))
    return str(rng.choice(SUB_MANDIRI))


def sampel_bidang_pembidangan(bobot: dict[str, float]) -> str:
    kunci = list(bobot.keys())
    p = np.array(list(bobot.values()), dtype=float)
    return str(rng.choice(kunci, p=p / p.sum()))


# ---------------------------------------------------------------------------
# 2. Kursi pagu_rekrutmen per (tahun, grade) -- dikonsumsi satu-per-satu
# ---------------------------------------------------------------------------
kursi_per_tahun_grade: dict[tuple[str, str], list[dict]] = defaultdict(list)
for p in pagu:
    for _ in range(int(p["jumlah"])):
        kursi_per_tahun_grade[(p["tahun_program"], p["kode_grade"])].append(p)
kursi_awal = {k: len(v) for k, v in kursi_per_tahun_grade.items()}

status_sk: dict[str, str] = {}
for r in pasca_tahap:
    if r["tahap_kode"] == "sk_penempatan" and r["status"] == "SELESAI":
        status_sk[r["pendaftaran_id"]] = "SUDAH"

diterima = [r for r in pendaftaran if r["hasil_akhir"] == "DITERIMA"]


def tarik_kursi(tahun: str, grade: str, sub_bidang: str, propinsi_asal: str, perempuan: bool) -> dict | None:
    kandidat_kursi = kursi_per_tahun_grade.get((tahun, grade))
    if not kandidat_kursi:
        return None
    cocok = [k for k in kandidat_kursi if k["sub_bidang"] == sub_bidang] or kandidat_kursi
    bobot = []
    for k in cocok:
        unit_penuh = NAMA_PENDEK_KE_PENUH.get(k["holding_subholding"], k["holding_subholding"])
        w = 1.0
        if propinsi_asal and propinsi_asal.upper() in unit_penuh.upper():
            w *= 6.0 if perempuan else 3.0
        bobot.append(w)
    bobot_arr = np.array(bobot)
    idx = int(rng.choice(len(cocok), p=bobot_arr / bobot_arr.sum()))
    terpilih = cocok[idx]
    kandidat_kursi.remove(terpilih)
    return terpilih


# ===========================================================================
# 3. LOOP UTAMA
# ===========================================================================
print(f"  {len(diterima):,} pendaftaran DITERIMA diproses")
n_induk_sk = n_induk_ojt = n_sub = n_kursi_gagal = 0
penempatan_id = 0

with (MASTER / "penempatan.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["penempatan_id", "pendaftaran_id", "kandidat_id", "tahun_program", "jenis_penempatan",
                "status_sk", "sub_bidang", "bidang_pembidangan", "updl_id", "kode_grade",
                "unit_induk", "nama_posisi", "perusahaan_subholding", "sumber_penempatan"])

    for row in diterima:
        prow = profesi[row["profesi_id"]]
        kand = kandidat[row["kandidat_id"]]
        tahun = prow["tahun_program"]
        jenjang = prow["jenjang"]
        grade = GRADE_MASUK[jenjang]["grade"]
        sudah_sk = status_sk.get(row["pendaftaran_id"]) == "SUDAH"

        sub_bidang = pilih_sub_bidang(prow["nama_profesi"], row["kandidat_id"])
        bobot_updl = np.array([float(u["jumlah_pegawai"]) for u in updl])
        updl_id = str(rng.choice([u["updl_id"] for u in updl], p=bobot_updl / bobot_updl.sum()))

        if prow["penempatan"] == "SUBHOLDING":
            n_sub += 1
            perusahaan = pilih_perusahaan_sub(prow["nama_profesi"], row["sumber_rekrutmen"])
            bidang_pemb = sampel_bidang_pembidangan(BOBOT_SUB[perusahaan])
            penempatan_id += 1
            w.writerow([penempatan_id, row["pendaftaran_id"], row["kandidat_id"], tahun, "SUBHOLDING",
                        "SUDAH" if sudah_sk else "BELUM", sub_bidang, bidang_pemb, updl_id, grade,
                        "", "", perusahaan, "DIMODELKAN"])
            continue

        # INDUK
        bidang_pemb = SUB_BIDANG_KE_PEMBIDANGAN.get(sub_bidang, sub_bidang)
        unit_out = posisi_out = ""
        sumber = "DIMODELKAN"
        if sudah_sk:
            kursi = tarik_kursi(tahun, grade, sub_bidang, kand["propinsi_asal"], kand["jenis_kelamin"] == "P")
            if kursi is None:
                n_kursi_gagal += 1
            else:
                unit_out = NAMA_PENDEK_KE_PENUH.get(kursi["holding_subholding"], kursi["holding_subholding"])
                posisi_out = kursi["jabatan"]
                bidang_pemb = SUB_BIDANG_KE_PEMBIDANGAN.get(kursi["sub_bidang"], bidang_pemb)
                sub_bidang = kursi["sub_bidang"]
                sumber = "TURUNAN"
            n_induk_sk += 1
        else:
            n_induk_ojt += 1

        penempatan_id += 1
        w.writerow([penempatan_id, row["pendaftaran_id"], row["kandidat_id"], tahun, "INDUK",
                    "SUDAH" if sudah_sk else "BELUM", sub_bidang, bidang_pemb, updl_id, grade,
                    unit_out, posisi_out, "", sumber])

print(f"  tulis penempatan.csv  ({penempatan_id:,} baris)")
print(f"  induk ber-SK (unit+posisi definitif): {n_induk_sk - n_kursi_gagal:,}")
print(f"  induk ber-SK TAPI kursi pagu habis (fallback kosong): {n_kursi_gagal:,}")
print(f"  induk masih OJT (bidang saja, unit/posisi kosong): {n_induk_ojt:,}")
print(f"  subholding: {n_sub:,}")

print("\n  sisa kursi pagu_rekrutmen tak terpakai per tahun (representasi ikatan dinas, TIDAK dipaksa habis):")
sisa_per_tahun: dict[str, int] = defaultdict(int)
for (tahun, grade), lst in kursi_per_tahun_grade.items():
    sisa_per_tahun[tahun] += len(lst)
komposisi_id_per_tahun = {
    str(r["tahun"]): sum(k["diterima"] for k in r.get("komposisi_jalur", []) if k["sumber"] == "ikatan_dinas")
    for r in kohort_yaml["kohort_per_tahun_program"]
}
for tahun in sorted(sisa_per_tahun):
    print(f"    {tahun}: sisa={sisa_per_tahun[tahun]:>5}  vs  ikatan_dinas={komposisi_id_per_tahun.get(tahun, 0):>5}")

print("\nSelesai langkah 11.")
print(f"  penempatan: {penempatan_id:,} baris")
