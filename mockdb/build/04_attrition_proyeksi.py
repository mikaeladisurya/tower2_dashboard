"""Attrition, kaskade promosi, dan proyeksi kekosongan per unit x posisi x tahun.

Menjawab ReqGathering#1 (Bu Dewi): kebutuhan rekrutmen harus jadi FUNGSI dari
pensiun + APS + mutasi + tugas karya, bukan angka sporadis. Karena itu kekosongan
dibangkitkan dari MEKANISME BERNAMA, lalu dikaskadekan turun ke jenjang masuk.

Rantai sebabnya:
    pensiun/APS/PHK di jenjang N  ->  diisi promosi dari N-1  ->  kosong di N-1
    ->  ... turun sampai jenjang masuk  ->  ITU kebutuhan rekrutmen.

Input  : out/master/unit_induk.csv, posisi_unit_induk.csv, jabatan_klasifikasi.csv
         rules/attrition.yaml
Output : out/master/proyeksi_kekosongan.csv   (unit x posisi x tahun x sebab)
         out/master/kekosongan_ringkas.csv    (unit x tahun, siap dipakai langkah 05)
         out/master/profil_usia.csv           (sebaran usia sintetis per jenjang)
         + validasi identitas headcount & perbandingan kebutuhan vs kohort nyata

⚠️  Semua angka usia DIREKA (DAPEG tidak punya kolom usia). Yang nyata: jumlah pensiun
    & keluar per tahun, headcount per tahun, dan sebaran posisi per unit.

Jalankan: python mockdb/build/04_attrition_proyeksi.py
"""
from __future__ import annotations

import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

SEBAB = ["pensiun", "mengundurkan_diri", "meninggal_dunia", "phk"]


def baca(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tulis(path: Path, kolom: list[str], baris: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kolom)
        w.writeheader()
        w.writerows(baris)
    print(f"  tulis {path.relative_to(ROOT)}  ({len(baris)} baris)")


# ---------------------------------------------------------------------------
# 1. Bobot risiko pensiun per jenjang
# ---------------------------------------------------------------------------
def bobot_pensiun(profil: dict) -> dict[str, float]:
    """Peluang seorang pegawai jenjang X mencapai usia pensiun tahun ini.

    Diturunkan dari sebaran normal usia: fraksi yang berada di usia pensiun-1.
    Bukan simulasi per orang -- cukup bobot relatif, karena JUMLAH pensiun per tahun
    sudah dikunci angka nyata di runtun_keluar. Bobot ini hanya membagi ke mana.
    """
    pensiun = profil["usia_pensiun"]
    bobot: dict[str, float] = {}
    for jenjang, p in profil["rata2_per_jenjang"].items():
        mu, sd = p["rata2"], p["sd"]
        # kepadatan normal di usia (pensiun - 1), yaitu yang akan pensiun tahun depan
        z = (pensiun - 1 - mu) / sd
        bobot[jenjang] = math.exp(-0.5 * z * z) / (sd * math.sqrt(2 * math.pi))
    return bobot


# ---------------------------------------------------------------------------
# 2. Kaskade promosi
# ---------------------------------------------------------------------------
def peta_level(kaskade: dict) -> dict[str, int]:
    peta: dict[str, int] = {}
    for level, kelompok in kaskade["tangga"].items():
        for k in kelompok:
            peta[k] = int(level)
    return peta


def kaskade_ke_masuk(kekosongan_per_level: dict[int, float], kaskade: dict) -> dict[int, float]:
    """Turunkan kekosongan tiap level jadi kebutuhan rekrutmen per level masuk.

    Kekosongan di level L: sebagian p diisi promosi dari L-1 (yang lalu ikut kosong),
    sisanya (1-p) diisi dari luar = rekrutmen di level L.
    """
    peluang = {int(k): float(v) for k, v in kaskade["peluang_diisi_promosi"].items()}
    kosong = dict(kekosongan_per_level)
    rekrut: dict[int, float] = defaultdict(float)

    for level in sorted(kosong, reverse=True):
        n = kosong.get(level, 0.0)
        if n <= 0:
            continue
        p = peluang.get(level, 0.0)
        rekrut[level] += n * (1 - p)
        if p > 0 and level - 1 >= 1:
            kosong[level - 1] = kosong.get(level - 1, 0.0) + n * p
    return dict(rekrut)


def main() -> int:
    print("04 — attrition, kaskade promosi & proyeksi kekosongan\n")
    aturan = yaml.safe_load((RULES / "attrition.yaml").read_text(encoding="utf-8"))
    profil = aturan["profil_usia"]
    kaskade = aturan["kaskade_promosi"]
    runtun = {int(t): v for t, v in aturan["runtun_keluar"].items() if isinstance(v, dict)}
    porsi_sebab = aturan["sebab_keluar"]["porsi"]
    metrik = aturan["metrik_pegawai_baru"]

    level_dari_kelompok = peta_level(kaskade)
    risiko = bobot_pensiun(profil)

    # ---- sisi kursi: unit x posisi x jenjang ----
    posisi = baca(MASTER / "posisi_unit_induk.csv")
    klas = {r["nama_posisi"]: r for r in baca(MASTER / "jabatan_klasifikasi.csv")}

    tak_terpeta: Counter = Counter()
    baris_kursi: list[dict] = []
    for r in posisi:
        k = klas.get(r["nama_posisi"])
        if k is None:
            tak_terpeta[r["nama_posisi"]] += 1
            continue
        kel = k["kelompok_jabatan"]
        level = level_dari_kelompok.get(kel)
        if level is None:
            tak_terpeta[kel] += 1
            continue
        baris_kursi.append(
            {
                "unit_induk": r["unit_induk"],
                "nama_posisi": r["nama_posisi"],
                "jenjang": r["jenjang"],
                "kelompok_jabatan": kel,
                "sub_bidang": k["sub_bidang"],
                "level": level,
                "n": int(r["jumlah_pegawai"]),
            }
        )

    total_kursi = sum(b["n"] for b in baris_kursi)
    print(f"  kursi terpetakan : {total_kursi:,} dari {sum(int(r['jumlah_pegawai']) for r in posisi):,}")
    if tak_terpeta:
        print(f"  kelompok/posisi tanpa level: {len(tak_terpeta)} -> {list(tak_terpeta)[:5]}")

    # ---- bobot alokasi ----
    for b in baris_kursi:
        b["bobot_pensiun"] = b["n"] * risiko.get(b["jenjang"], risiko["G2"])
    total_bobot_pensiun = sum(b["bobot_pensiun"] for b in baris_kursi)

    # ---- alokasi keluar per tahun ----
    tahun_urut = sorted(runtun)
    proyeksi: list[dict] = []
    ringkas: dict[tuple[str, int], dict] = {}
    kebutuhan_per_tahun: dict[int, dict[int, float]] = {}

    for tahun in tahun_urut:
        n_pensiun = runtun[tahun]["pensiun"]
        n_total = runtun[tahun]["total"]
        n_lain = n_total - n_pensiun
        # sebab non-pensiun dibagi menurut porsinya sendiri, sebanding headcount
        porsi_lain = {s: porsi_sebab[s] for s in SEBAB if s != "pensiun"}
        jml_lain = sum(porsi_lain.values())

        kosong_level: dict[int, float] = defaultdict(float)
        for b in baris_kursi:
            bagian = {
                "pensiun": n_pensiun * b["bobot_pensiun"] / total_bobot_pensiun,
                **{
                    s: n_lain * (porsi_lain[s] / jml_lain) * b["n"] / total_kursi
                    for s in porsi_lain
                },
            }
            jml = sum(bagian.values())
            if jml < 0.005:
                continue
            kosong_level[b["level"]] += jml
            kunci = (b["unit_induk"], tahun)
            rk = ringkas.setdefault(
                kunci,
                {"unit_induk": b["unit_induk"], "tahun": tahun, "headcount": 0, **{s: 0.0 for s in SEBAB}},
            )
            rk["headcount"] += b["n"]
            for s, v in bagian.items():
                rk[s] += v
            proyeksi.append(
                {
                    "unit_induk": b["unit_induk"],
                    "nama_posisi": b["nama_posisi"],
                    "jenjang": b["jenjang"],
                    "kelompok_jabatan": b["kelompok_jabatan"],
                    "sub_bidang": b["sub_bidang"],
                    "level": b["level"],
                    "tahun": tahun,
                    "pegawai": b["n"],
                    **{s: round(bagian[s], 4) for s in SEBAB},
                    "kekosongan": round(jml, 4),
                }
            )
        kebutuhan_per_tahun[tahun] = kaskade_ke_masuk(dict(kosong_level), kaskade)

    # ---- validasi 1: identitas headcount ----
    print("\n  [1] Identitas headcount (pakai metrik 'direkrut' -- F-051):")
    hc = {int(t): v["induk"] for t, v in aturan["headcount"]["runtun"].items() if v["induk"]}
    direkrut = {int(t): v for t, v in metrik["pegawai_direkrut"]["runtun"].items()}
    carve = {
        int(k["tahun"]): int(k["carve_out_murni"])
        for k in aturan["carve_out"]["kejadian"]
        if k.get("carve_out_murni")
    }
    residu = []
    for t in sorted(hc):
        if t - 1 not in hc or t not in runtun or t not in direkrut:
            continue
        model = hc[t - 1] + direkrut[t] - runtun[t]["total"] - carve.get(t, 0)
        d = model - hc[t]
        tanda = "  (carve-out diperhitungkan)" if t in carve else ""
        if t not in carve:
            residu.append(abs(d) / hc[t])
        print(f"      {t}  model {model:,}  nyata {hc[t]:,}  selisih {d:+,} ({d / hc[t]:+.2%}){tanda}")
    if residu:
        print(f"      residu rata-rata {sum(residu) / len(residu):.2%} -> mutasi/tugas karya tak terlapor")
    for t, n in carve.items():
        anak = next(
            (k["anak_delta"] for k in aturan["carve_out"]["kejadian"] if int(k["tahun"]) == t), None
        )
        print(f"      carve-out {t}: {n:,} orang (turunan) vs kenaikan Anak Perusahaan +{anak:,} — selisih {anak - n:+,}")

    # ---- validasi 2: kebutuhan hasil kaskade vs kohort nyata ----
    print("\n  [2] Kebutuhan hasil kaskade, dipecah per jenjang masuk:")
    print(f"      {'tahun':6s} {'keluar':>7s} {'->L1':>6s} {'->L2':>6s} {'->L3':>6s} {'->L4':>5s} {'butuh':>7s}")
    for t in tahun_urut:
        k = kebutuhan_per_tahun[t]
        print(
            f"      {t:6d} {runtun[t]['total']:7,} {k.get(1, 0):6.0f} {k.get(2, 0):6.0f} "
            f"{k.get(3, 0):6.0f} {k.get(4, 0):5.0f} {sum(k.values()):7.0f}"
        )
    print("      Total selalu = jumlah keluar: tiap kekosongan akhirnya diisi seseorang,")
    print("      dan tiap rantai promosi berujung pada satu orang dari luar. Yang berubah")
    print("      karena kaskade adalah SEBARAN JENJANG-nya, bukan jumlahnya.")

    print("\n  [3] Apakah PLN mengisi kekosongannya? Dua sudut pandang:")
    prajab = {int(t): v for t, v in metrik["peserta_prajabatan"]["runtun"].items()}
    print(f"      {'tahun':6s} {'butuh':>7s} | {'ber-SK':>7s} {'%':>5s} | {'kohort':>7s} {'%':>5s}")
    for t in tahun_urut:
        butuh = sum(kebutuhan_per_tahun[t].values())
        d, k = direkrut.get(t), prajab.get(t)
        kol_sk = f"{d:7,} {d / butuh:4.0%}" if d is not None else f"{'—':>7s} {'—':>4s}"
        kol_koh = f"{k:7,} {k / butuh:4.0%}" if k is not None else f"{'—':>7s} {'—':>4s}"
        print(f"      {t:6d} {butuh:7.0f} | {kol_sk} | {kol_koh}")
    print("      'ber-SK'  = pegawai baru masuk headcount tahun itu (metrik direkrut)")
    print("      'kohort'  = orang yang menjalani seleksi & diklat tahun itu (prajabatan)")
    print()
    print("      Bacaan: sampai 2023 kohort JAUH di bawah kebutuhan (24-59%) -- itulah")
    print("      mekanisme penyusutan headcount. Sejak 2024 kohort justru MELAMPAUI")
    print("      kebutuhan (124%, 108%), tapi headcount masih turun karena efeknya belum")
    print("      masuk: mereka baru ber-SK setelah OJT selesai. Angka ber-SK 2025 yang")
    print("      cuma 7% BUKAN kegagalan merekrut -- itu jeda pipeline (F-051).")

    # ---- keluaran ----
    print()
    tulis(
        MASTER / "proyeksi_kekosongan.csv",
        ["unit_induk", "nama_posisi", "jenjang", "kelompok_jabatan", "sub_bidang", "level",
         "tahun", "pegawai", *SEBAB, "kekosongan"],
        proyeksi,
    )
    baris_ringkas = []
    for (unit, tahun), v in sorted(ringkas.items()):
        v = dict(v)
        for s in SEBAB:
            v[s] = round(v[s], 2)
        v["kekosongan"] = round(sum(v[s] for s in SEBAB), 2)
        baris_ringkas.append(v)
    tulis(
        MASTER / "kekosongan_ringkas.csv",
        ["unit_induk", "tahun", "headcount", *SEBAB, "kekosongan"],
        baris_ringkas,
    )
    tulis(
        MASTER / "profil_usia.csv",
        ["jenjang", "usia_rata2", "sd", "bobot_risiko_pensiun", "status_sumber"],
        [
            {
                "jenjang": j,
                "usia_rata2": p["rata2"],
                "sd": p["sd"],
                "bobot_risiko_pensiun": round(risiko[j] / max(risiko.values()), 4),
                "status_sumber": "DIMODELKAN",
            }
            for j, p in profil["rata2_per_jenjang"].items()
        ],
    )

    # ---- cek jumlah ----
    print()
    for t in (tahun_urut[0], tahun_urut[-1]):
        jml = sum(p["kekosongan"] for p in proyeksi if p["tahun"] == t)
        target = runtun[t]["total"]
        ok = abs(jml - target) / target < 0.01
        print(f"  cek alokasi {t}: {jml:,.0f} vs target {target:,}  {'OK' if ok else 'MELESET'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
