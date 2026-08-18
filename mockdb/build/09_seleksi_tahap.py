"""Tahapan seleksi per kandidat: perjalanan tiap pendaftaran lewat tahap_ref.

Urutan kausal (rules/README.md): pendaftaran (langkah 08, SIAPA gugur & KAPAN --
`tahap_gugur`/`hasil_akhir` sudah final) -> tahapan.yaml (bagaimana PERJALANANNYA).
Langkah ini TIDAK mengubah lagi siapa diterima/gugur -- itu jangkar keras dari
langkah 08. Ia hanya menjabarkan pendaftaran.csv jadi baris per-tahap:

  1. Jalur MANDIRI lewat 6 tahap (administrasi..wawancara); jalur RBB lewat 4 tahap
     PLN saja (akademik_inggris..wawancara, titik_masuk F-046) -- tahap FHCI di
     depannya TIDAK per-kandidat (HANDOFF butir 3b), direkap terpisah di
     `seleksi_tahap_agregat.csv`.
  2. Tahap SEBELUM titik gugur (atau semua tahap kalau DITERIMA) = HADIR + LULUS,
     karena pendaftaran.csv sudah memastikan itu. Di titik gugur sendiri, HADIR vs
     TIDAK_HADIR diundi dari hadir_pct/lulus_pct funnel.yaml (bobot no-show relatif
     terhadap gagal-setelah-hadir), supaya no-show tidak seragam disamakan dengan
     gagal tes.
  3. Skor SELURUHNYA DIMODELKAN (F-028: tidak ada passing grade di regulasi manapun)
     -- dikalibrasi supaya konsisten dgn ambang tahapan.yaml.passing_grade dan dgn
     hasil LULUS/GAGAL yang sudah final. Tahap kategorikal (psikologi/fisik_mcu/
     wawancara) diberi label, bukan skor numerik.
  4. Kota tes & vendor VENDOR-owned (psikologi/fisik_mcu) dikunci SEKALI per
     pendaftaran (F-024: lokasi tes terkunci saat daftar) dan dipakai ulang di
     seluruh tahap offline pendaftaran itu.

Input  : rules/{tahapan,funnel,kohort}.yaml, out/master/{profesi,pendaftaran,
         tahap_ref,kota,vendor}.csv
Output : out/master/{seleksi_tahap,seleksi_tahap_agregat}.csv

Jalankan: python mockdb/build/09_seleksi_tahap.py
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

SEED = 20260915
rng = np.random.default_rng(SEED)

KOTA_OFFLINE_UTAMA = ["Jakarta", "Medan", "Surabaya", "Makassar", "Palembang", "Balikpapan"]
PREFIX_KOTA = ["Kota Administrasi ", "Kabupaten Administrasi ", "Kota ", "Kabupaten ", "Administrasi "]


def baca_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def muat_yaml(nama: str) -> dict:
    return yaml.safe_load((RULES / nama).read_text(encoding="utf-8"))


def normalisasi_kota(nama: str) -> str:
    n = nama.strip()
    for pre in PREFIX_KOTA:
        if n.startswith(pre):
            return n[len(pre):]
    return n


print("Langkah 09: tahapan seleksi\n")

tahapan = muat_yaml("tahapan.yaml")
funnel = muat_yaml("funnel.yaml")
kohort_yaml = muat_yaml("kohort.yaml")

profesi = {r["profesi_id"]: r for r in baca_csv(MASTER / "profesi.csv")}
pendaftaran = baca_csv(MASTER / "pendaftaran.csv")
tahap_ref = {r["tahap_kode"]: r for r in baca_csv(MASTER / "tahap_ref.csv")}
kota_master = [r["nama"] for r in baca_csv(MASTER / "kota.csv")]
vendor = baca_csv(MASTER / "vendor.csv")

VENDOR_FISIK = [v for v in vendor if v["tipe_layanan"] == "fisik_mcu"]
VENDOR_PSIKO = [v for v in vendor if v["tipe_layanan"] == "psikologi"]

# ---------------------------------------------------------------------------
# 1. Urutan tahap per jalur (dari tahapan.yaml, disaring masuk_mandiri/masuk_rbb)
# ---------------------------------------------------------------------------
seleksi_urut = sorted(tahapan["tahap_seleksi"], key=lambda t: t["urutan"])
MANDIRI_ORDER = [t["kode"] for t in seleksi_urut if t["masuk_mandiri"]]
RBB_ORDER = [t["kode"] for t in seleksi_urut if t["masuk_rbb"]]

peta_arketipe = funnel["pemilihan_arketipe"]["peta"]
default_residu = funnel["pemilihan_arketipe"]["default_residu"]
funnel_mandiri = funnel["funnel_mandiri"]
rbb_tahapan = funnel["funnel_rbb"]["pln_per_kandidat"]["tahapan"]

RATES_RBB = {t["tahap"]: (t["hadir_pct"], t["lulus_pct"]) for t in rbb_tahapan}
RATES_MANDIRI = {
    ark: {t["tahap"]: (t["hadir_pct"], t["lulus_pct"]) for t in cfg["tahapan"]}
    for ark, cfg in funnel_mandiri.items()
}

DURASI = kohort_yaml["durasi_hari_setelah_tutup"]

PASSING = tahapan["passing_grade"]


# ---------------------------------------------------------------------------
# 2. Skor DIMODELKAN per tahap, konsisten dgn hasil LULUS/GAGAL yang sudah final
# ---------------------------------------------------------------------------
def skor_adaptif(lulus: bool) -> float:
    amb = PASSING["adaptif"]["ambang_total"]
    return round(float(rng.uniform(amb, 100) if lulus else rng.uniform(20, amb - 0.1)), 1)


def skor_akademik(lulus: bool, jalur: str) -> float:
    amb = PASSING["akademik_inggris"]["ambang_total_rbb" if jalur == "rbb" else "ambang_total"]
    return round(float(rng.uniform(amb, 100) if lulus else rng.uniform(20, amb - 0.1)), 1)


def kategori_psikologi(lulus: bool) -> str:
    if not lulus:
        return "TIDAK_DISARANKAN"
    return str(rng.choice(["DISARANKAN", "DISARANKAN_DENGAN_PERTIMBANGAN"], p=[0.7, 0.3]))


def kategori_fisik(lulus: bool) -> str:
    if not lulus:
        return "UNFIT"
    return str(rng.choice(["FIT", "FIT_WITH_NOTE"], p=[0.75, 0.25]))


def skor_wawancara(lulus: bool) -> tuple[float, str]:
    amb = PASSING["wawancara"]["ambang_rata2"]
    if lulus:
        skor = round(float(rng.uniform(amb, 5.0)), 2)
        kat = str(rng.choice(["DISARANKAN", "DISARANKAN_DENGAN_PERTIMBANGAN"], p=[0.7, 0.3]))
    else:
        skor = round(float(rng.uniform(1.0, amb - 0.01)), 2)
        kat = "TIDAK_DISARANKAN"
    return skor, kat


def pilih_kota(kota_rekrutmen: str) -> str:
    norm = normalisasi_kota(kota_rekrutmen)
    for k in kota_master:
        if k.lower() == norm.lower():
            return k
    if rng.random() < 0.8:
        return str(rng.choice(KOTA_OFFLINE_UTAMA))
    return str(rng.choice(kota_master))


def pilih_vendor(daftar: list[dict], kota_tes: str) -> str:
    cocok = [v for v in daftar if v["kota_basis"].lower() == kota_tes.lower()]
    if cocok:
        return str(rng.choice([v["vendor_id"] for v in cocok]))
    nasional = [v["vendor_id"] for v in daftar if v["kota_basis"] == "nasional"]
    if nasional:
        return str(rng.choice(nasional))
    return str(rng.choice([v["vendor_id"] for v in daftar]))


# ===========================================================================
# 3. LOOP UTAMA -- satu baris output per (pendaftaran, tahap tercapai)
# ===========================================================================
print("  menulis seleksi_tahap.csv ...")
n_baris = 0
n_mandiri = n_rbb = 0
tahap_id = 0
with (MASTER / "seleksi_tahap.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tahap_id", "pendaftaran_id", "kandidat_id", "profesi_id", "gelombang_id",
                "tahap_kode", "urutan", "tanggal_tahap", "mode", "lokasi_kota", "pemilik_proses",
                "sistem_sumber", "status_hadir", "hasil", "skor_total", "kategori_hasil",
                "vendor_id", "sumber_skor"])

    for row in pendaftaran:
        prow = profesi[row["profesi_id"]]
        jalur = row["sumber_rekrutmen"]
        if jalur == "mandiri":
            arketipe = peta_arketipe.get(prow["jenis_program"], default_residu)
            order = MANDIRI_ORDER
            rates = RATES_MANDIRI[arketipe]
        else:
            order = RBB_ORDER
            rates = RATES_RBB

        hasil_akhir = row["hasil_akhir"]
        if hasil_akhir == "DITERIMA":
            reached = order
        else:
            idx_gugur = order.index(row["tahap_gugur"])
            reached = order[: idx_gugur + 1]

        tgl_tutup = prow["tgl_tutup"] or f"{prow['tahun_program']}-12-31"
        d_tutup = dt.date.fromisoformat(tgl_tutup)

        butuh_kota = any(tahap_ref[s]["lokasi"] == "kota_terkunci" for s in reached)
        kota_tes = pilih_kota(prow["kota_rekrutmen"]) if butuh_kota else ""

        for i, kode in enumerate(reached):
            tref = tahap_ref[kode]
            is_terakhir = i == len(reached) - 1
            gagal_di_sini = is_terakhir and hasil_akhir == "GAGAL" and kode != "administrasi"

            status_hadir = ""
            skor_total = ""
            kategori_hasil = ""
            vendor_id = ""
            lokasi_kota = kota_tes if tref["lokasi"] == "kota_terkunci" else ""

            if kode == "administrasi":
                lulus = row["alasan_gagal"] == ""
                hasil = "LULUS" if lulus else "GAGAL"
            else:
                hadir_pct, lulus_pct = rates[kode]
                if gagal_di_sini:
                    p_noshow = (1 - hadir_pct) / max(1 - hadir_pct * lulus_pct, 1e-9)
                    tidak_hadir = rng.random() < p_noshow
                    status_hadir = "TIDAK_HADIR" if tidak_hadir else "HADIR"
                    hasil = "GAGAL"
                    lulus = False
                    hadir_untuk_skor = not tidak_hadir
                else:
                    status_hadir = "HADIR"
                    hasil = "LULUS"
                    lulus = True
                    hadir_untuk_skor = True

                if hadir_untuk_skor:
                    if kode == "adaptif":
                        skor_total = skor_adaptif(lulus)
                    elif kode == "akademik_inggris":
                        skor_total = skor_akademik(lulus, jalur)
                    elif kode == "psikologi":
                        kategori_hasil = kategori_psikologi(lulus)
                        vendor_id = pilih_vendor(VENDOR_PSIKO, kota_tes)
                    elif kode == "fisik_mcu":
                        kategori_hasil = kategori_fisik(lulus)
                        vendor_id = pilih_vendor(VENDOR_FISIK, kota_tes)
                    elif kode == "wawancara":
                        skor_total, kategori_hasil = skor_wawancara(lulus)

            durasi = DURASI[kode]
            off = int(rng.integers(durasi["mulai"], durasi["selesai"] + 1))
            tanggal_tahap = (d_tutup + dt.timedelta(days=off)).isoformat()

            tahap_id += 1
            w.writerow([
                tahap_id, row["pendaftaran_id"], row["kandidat_id"], row["profesi_id"],
                row["gelombang_id"], kode, tref["urutan"], tanggal_tahap, tref["mode"],
                lokasi_kota, tref["pemilik_proses"], tref["sistem_sumber"], status_hadir,
                hasil, skor_total, kategori_hasil, vendor_id, "DIMODELKAN",
            ])
            n_baris += 1
        if jalur == "mandiri":
            n_mandiri += len(reached)
        else:
            n_rbb += len(reached)

print(f"  tulis seleksi_tahap.csv  ({n_baris:,} baris -- mandiri {n_mandiri:,}, rbb {n_rbb:,}, "
      f"rata2 {n_baris / len(pendaftaran):.2f} tahap/pendaftaran)")

# ===========================================================================
# 4. seleksi_tahap_agregat.csv -- tahap FHCI, tanpa kandidat (HANDOFF butir 3b)
# ===========================================================================
print("  menulis seleksi_tahap_agregat.csv ...")
fhci_cfg = tahapan["tahap_agregat_fhci"]
fhci_tahapan = funnel["funnel_rbb"]["fhci_agregat"]["tahapan"]  # administrasi/online1/online2

tahun_serah_terima: dict[int, int] = {}
for row in pendaftaran:
    if row["sumber_rekrutmen"] != "rbb":
        continue
    tahun = int(profesi[row["profesi_id"]]["tahun_program"])
    tahun_serah_terima[tahun] = tahun_serah_terima.get(tahun, 0) + 1

with (MASTER / "seleksi_tahap_agregat.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tahun_program", "tahap_kode", "nama", "urutan", "jumlah_masuk", "jumlah_lulus",
                "tanggal_estimasi", "pemilik_proses", "status_sumber"])
    for tahun, serah_terima in sorted(tahun_serah_terima.items()):
        lulus_online2 = serah_terima
        masuk_online2 = round(lulus_online2 / fhci_tahapan[2]["lulus_pct"])
        lulus_online1 = masuk_online2
        masuk_online1 = round(lulus_online1 / fhci_tahapan[1]["lulus_pct"])
        lulus_admin = masuk_online1
        masuk_admin = round(lulus_admin / fhci_tahapan[0]["lulus_pct"])

        rincian = [
            ("fhci_administrasi", "Seleksi Administrasi (FHCI)", masuk_admin, lulus_admin, 15),
            ("fhci_tes_online_1", "Tes Online 1: TKD, AKHLAK, TWK", masuk_online1, lulus_online1, 45),
            ("fhci_tes_online_2", "Tes Online 2: Inggris, Learning Agility", masuk_online2, lulus_online2, 75),
        ]
        for kode, nama, masuk, lulus, hari in rincian:
            tgl = f"{tahun}-{1 + hari // 30:02d}-{1 + hari % 30:02d}"
            urutan = next(t["urutan"] for t in fhci_cfg["tahapan"] if t["kode"] == kode)
            w.writerow([tahun, kode, nama, urutan, masuk, lulus, tgl, "FHCI", "AGREGAT_TANPA_NAMA"])

print(f"  tulis seleksi_tahap_agregat.csv  ({3 * len(tahun_serah_terima)} baris, "
      f"{len(tahun_serah_terima)} tahun RBB: {sorted(tahun_serah_terima)})")

print("\nSelesai langkah 09.")
print(f"  seleksi_tahap: {n_baris:,} baris")
print(f"  seleksi_tahap_agregat: {3 * len(tahun_serah_terima)} baris")
