"""Kota, UPDL, vendor & referensi tahapan: tabel master area seleksi.

Langkah ini murni MEMATERIALKAN aturan/master yang sudah ada jadi tabel referensi --
belum ada penugasan per-kandidat (itu langkah 09). Empat tabel:

    kota      = 43 kota penyelenggara tes (F-019), dari rules/tahapan.yaml
    updl      = 11 unit pelaksana diklat, difilter dari out/master/unit_pelaksana.csv
    vendor    = ±10 vendor psikologi/fisik-MCU, dari rules/vendor.yaml
    tahap_ref = 16 tahap (6 seleksi + 3 FHCI + 7 pasca), dari rules/tahapan.yaml

Input  : rules/tahapan.yaml, rules/vendor.yaml, out/master/unit_pelaksana.csv
Output : out/master/kota.csv · updl.csv · vendor.csv · tahap_ref.csv

Jalankan: python mockdb/build/07_vendor_lokasi.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"


def baca_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tulis(path: Path, kolom: list[str], baris: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kolom, extrasaction="ignore")
        w.writeheader()
        w.writerows(baris)
    print(f"  tulis {path.relative_to(ROOT)}  ({len(baris)} baris)")


def muat_yaml(nama: str) -> dict:
    return yaml.safe_load((RULES / nama).read_text(encoding="utf-8"))


def bangun_kota(tahapan: dict) -> list[dict]:
    kt = tahapan["kota_penyelenggara"]
    kelompok_per_kunci = {
        "dari_arsip_2017_smk": "arsip_2017_smk",
        "dari_arsip_2019_reguler": "arsip_2019_reguler",
        "dari_afirmasi_papua": "afirmasi_papua",
        "turunan_ibukota_provinsi_lain": "turunan_ibukota",
    }
    offline_utama = set(kt["kota_offline_utama"])
    baris = []
    i = 1
    for kunci, kelompok in kelompok_per_kunci.items():
        for nama in kt[kunci]:
            baris.append({
                "kota_id": f"K{i:03d}",
                "nama": nama,
                "kelompok_sumber": kelompok,
                "offline_utama": nama in offline_utama,
                "rujukan": "F-019, F-031/F-032/F-006/F-024" if kelompok != "turunan_ibukota" else "TURUNAN (melengkapi ke 43, F-019)",
            })
            i += 1
    return baris


def bangun_updl() -> list[dict]:
    up = baca_csv(MASTER / "unit_pelaksana.csv")
    baris = [row for row in up if row.get("jenis_unit") == "UPDL"]
    return [
        {
            "updl_id": row["kode_unit_pelaksana"],
            "nama": row["nama_pendek"],
            "nama_lengkap": row["nama_lengkap"],
            "unit_induk": row["unit_induk"],
            "jumlah_pegawai": row["jumlah_pegawai"],
        }
        for row in baris
    ]


def bangun_vendor(vendor_yaml: dict) -> list[dict]:
    baris = []
    for v in vendor_yaml["vendor"]:
        baris.append({
            "vendor_id": v["kode"],
            "nama": v["nama"],
            "tipe_layanan": v["tipe_layanan"],
            "kota_basis": v["kota_basis"],
            "status_sumber": v.get("status_sumber") or "",
            "rujukan": v.get("rujukan") or v.get("catatan") or "",
        })
    return baris


def bangun_tahap_ref(tahapan: dict) -> list[dict]:
    baris = []
    for t in tahapan["tahap_seleksi"]:
        baris.append({
            "tahap_kode": t["kode"],
            "nama": t["nama"],
            "kategori": "seleksi",
            "urutan": t["urutan"],
            "mode": t["mode"],
            "lokasi": t["lokasi"],
            "pemilik_proses": t["pemilik_proses"],
            "sistem_sumber": t["sistem_sumber"],
            "ada_kehadiran": t["ada_kehadiran"],
            "skor_ada_di_sistem_asli": t["skor_ada_di_sistem_asli"],
            "masuk_mandiri": t["masuk_mandiri"],
            "masuk_rbb": t["masuk_rbb"],
        })
    for t in tahapan["tahap_agregat_fhci"]["tahapan"]:
        baris.append({
            "tahap_kode": t["kode"],
            "nama": t["nama"],
            "kategori": "fhci_agregat",
            "urutan": t["urutan"],
            "mode": "online",
            "lokasi": "n/a",
            "pemilik_proses": t["pemilik_proses"],
            "sistem_sumber": t["sistem_sumber"],
            "ada_kehadiran": False,
            "skor_ada_di_sistem_asli": False,
            "masuk_mandiri": False,
            "masuk_rbb": True,
        })
    for i, t in enumerate(tahapan["tahap_pasca"], start=100):
        baris.append({
            "tahap_kode": t["kode"],
            "nama": t["nama"],
            "kategori": "pasca",
            "urutan": i,
            "mode": "",
            "lokasi": "",
            "pemilik_proses": t["pemilik_proses"],
            "sistem_sumber": t["sistem_sumber"],
            "ada_kehadiran": "",
            "skor_ada_di_sistem_asli": "",
            "masuk_mandiri": True,
            "masuk_rbb": True,
        })
    return baris


def main() -> None:
    print("Langkah 07: kota, UPDL, vendor & tahap_ref\n")
    tahapan = muat_yaml("tahapan.yaml")
    vendor_yaml = muat_yaml("vendor.yaml")

    kota = bangun_kota(tahapan)
    tulis(MASTER / "kota.csv", ["kota_id", "nama", "kelompok_sumber", "offline_utama", "rujukan"], kota)
    assert len(kota) == 43, f"kota harus 43, dapat {len(kota)}"

    updl = bangun_updl()
    tulis(MASTER / "updl.csv", ["updl_id", "nama", "nama_lengkap", "unit_induk", "jumlah_pegawai"], updl)
    assert len(updl) == 11, f"updl harus 11, dapat {len(updl)}"

    vendor = bangun_vendor(vendor_yaml)
    tulis(MASTER / "vendor.csv", ["vendor_id", "nama", "tipe_layanan", "kota_basis", "status_sumber", "rujukan"], vendor)

    tahap_ref = bangun_tahap_ref(tahapan)
    tulis(
        MASTER / "tahap_ref.csv",
        ["tahap_kode", "nama", "kategori", "urutan", "mode", "lokasi", "pemilik_proses",
         "sistem_sumber", "ada_kehadiran", "skor_ada_di_sistem_asli", "masuk_mandiri", "masuk_rbb"],
        tahap_ref,
    )
    assert len(tahap_ref) == 16, f"tahap_ref harus 16, dapat {len(tahap_ref)}"

    print("\nSelesai.")


if __name__ == "__main__":
    main()
