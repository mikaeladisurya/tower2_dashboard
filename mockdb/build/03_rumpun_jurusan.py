"""Rumpun jurusan & jembatan jurusan -> sub bidang jabatan.

Menutup mata rantai yang hilang antara SISI PELAMAR (punya program studi) dan
SISI KURSI (posisi punya sub bidang). Tanpa ini generator penempatan cuma bisa
mengundi, dan lulusan Hukum bisa mendarat di Pemeliharaan Distribusi.

Input  : knowledge/sources/rekrutmen_pln/profesi.csv     (42 prodi asli -- F-004)
         knowledge/sources/rekrutmen_pln/programs.csv    (silang periksa + minat profesi -- F-005)
         knowledge/sources/rbb_fhci/lowongan_pln_rbb.csv (jurusan granular RBB -- F-043)
         out/master/jabatan_klasifikasi.csv              (sisi kursi, hasil langkah 02)
         rules/rumpun_jurusan.csv    (kata kunci -> rumpun, first-match-wins)
         rules/rumpun_subbidang.csv  (rumpun -> sub bidang + bobot)
         rules/minat_profesi.csv     (minat profesi -> sub bidang)

Output : out/master/program_studi.csv
         out/master/rumpun_jurusan.csv
         out/master/rumpun_subbidang.csv
         out/master/minat_profesi.csv
         + laporan cakupan aturan dan perbandingan PASOKAN vs PERMINTAAN per sub bidang

Yang TIDAK dilakukan di sini: memilih posisi untuk orang tertentu. Itu tugas langkah 11.
Di sini hanya dibangun tabel kemungkinan beserta bobotnya.

Jalankan: python mockdb/build/03_rumpun_jurusan.py
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "knowledge" / "sources"
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

# Jabatan struktural tidak pernah jadi sasaran rekrutmen pegawai baru (F-042).
# Filter WAJIB pakai kelompok_jabatan, BUKAN jenjang -- Team Leader juga G2.
STRUKTURAL = {
    "TEAM LEADER", "ASSISTANT MANAGER", "DEPUTY MANAGER", "MANAGER", "SENIOR MANAGER",
    "VICE PRESIDENT", "EXECUTIVE VICE PRESIDENT", "SENIOR EXECUTIVE VICE PRESIDENT",
    "GENERAL MANAGER",
}
GRADE_MASUK = {"G1", "G2"}

RUMPUN_PAYUNG = {"Lainnya Teknik": "TEKNIK", "Lainnya Non-Teknik": "NON-TEKNIK"}


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
# 1. Kumpulkan program studi dari seluruh sumber
# ---------------------------------------------------------------------------
def kumpulkan_prodi() -> tuple[Counter, Counter, dict[str, set[str]]]:
    """Kembalikan (hitungan per profesi, hitungan per program, sumber tiap prodi)."""
    per_profesi: Counter = Counter()
    per_program: Counter = Counter()
    sumber: dict[str, set[str]] = defaultdict(set)

    for r in baca(SOURCES / "rekrutmen_pln" / "profesi.csv"):
        for x in r["program_studi"].split(","):
            x = x.strip().upper()
            if x:
                per_profesi[x] += 1
                sumber[x].add("profesi")

    for r in baca(SOURCES / "rekrutmen_pln" / "programs.csv"):
        for x in r["program_studi"].split(","):
            x = x.strip().upper()
            if x:
                per_program[x] += 1
                sumber[x].add("programs")

    # RBB memberi jurusan jauh lebih granular (ratusan), dipisahkan koma.
    for r in baca(SOURCES / "rbb_fhci" / "lowongan_pln_rbb.csv"):
        for x in r.get("major_non_sma_custom", "").split(","):
            x = x.strip().upper()
            if x:
                sumber[x].add("rbb")

    return per_profesi, per_program, sumber


# ---------------------------------------------------------------------------
# 2. Klasifikasi prodi -> rumpun (first-match-wins)
# ---------------------------------------------------------------------------
def muat_aturan_rumpun() -> list[dict]:
    aturan = sorted(baca(RULES / "rumpun_jurusan.csv"), key=lambda r: int(r["urutan"]))
    for r in aturan:
        r["kata_kunci"] = r["kata_kunci"].upper()
    return aturan


def klasifikasi(prodi: str, aturan: list[dict]) -> tuple[str, str, str]:
    for r in aturan:
        if r["kata_kunci"] in prodi:
            return r["rumpun"], r["bidang"], r["kata_kunci"]
    return "", "", ""


# ---------------------------------------------------------------------------
# 3. Sisi kursi: headcount per sub bidang (G1/G2 non-struktural)
# ---------------------------------------------------------------------------
def headcount_sub_bidang() -> tuple[dict[str, int], dict[str, str]]:
    per_sub: Counter = Counter()
    bidang_dari_sub: dict[str, str] = {}
    for r in baca(MASTER / "jabatan_klasifikasi.csv"):
        if r["kelompok_jabatan"] in STRUKTURAL:
            continue
        if r["jenjang_utama"] not in GRADE_MASUK:
            continue
        sub = r["sub_bidang"]
        per_sub[sub] += int(r["jumlah_pegawai"])
        bidang_dari_sub[sub] = r["bidang"]
    return dict(per_sub), bidang_dari_sub


# ---------------------------------------------------------------------------
# 4. Bobot rumpun -> sub bidang, termasuk rumpun payung "Lainnya"
# ---------------------------------------------------------------------------
def muat_bobot(
    per_sub: dict[str, int], bidang_dari_sub: dict[str, str], rumpun_dipakai: set[str]
) -> tuple[list[dict], list[str]]:
    """Rumpun payung tidak ditulis tangan -- porsinya mengikuti sebaran kursi nyata."""
    keluar: list[dict] = []
    masalah: list[str] = []

    per_rumpun: dict[str, list[dict]] = defaultdict(list)
    for r in baca(RULES / "rumpun_subbidang.csv"):
        per_rumpun[r["rumpun"]].append(r)

    for rumpun, baris in per_rumpun.items():
        total = sum(float(b["bobot"]) for b in baris)
        if abs(total - 1) > 0.005:
            masalah.append(f"bobot rumpun '{rumpun}' berjumlah {total:.3f}, seharusnya 1,000")
        for b in baris:
            if b["sub_bidang"] not in per_sub:
                masalah.append(f"sub bidang '{b['sub_bidang']}' (rumpun {rumpun}) tidak ada di jabatan_klasifikasi")
            keluar.append(
                {
                    "rumpun": rumpun,
                    "sub_bidang": b["sub_bidang"],
                    "bidang_sub": bidang_dari_sub.get(b["sub_bidang"], ""),
                    "bobot": f"{float(b['bobot']):.4f}",
                    "sumber_bobot": "aturan",
                    "catatan": b.get("catatan", ""),
                }
            )

    # Rumpun payung: sebar proporsional terhadap kursi nyata di bidang yang sama.
    for rumpun, bidang in RUMPUN_PAYUNG.items():
        if rumpun not in rumpun_dipakai:
            continue
        kandidat = {s: n for s, n in per_sub.items() if bidang_dari_sub[s] == bidang}
        total = sum(kandidat.values())
        for sub, n in sorted(kandidat.items(), key=lambda kv: -kv[1]):
            keluar.append(
                {
                    "rumpun": rumpun,
                    "sub_bidang": sub,
                    "bidang_sub": bidang,
                    "bobot": f"{n / total:.4f}",
                    "sumber_bobot": "proporsional_headcount",
                    "catatan": f"{n} pegawai G1+G2 dari {total} di bidang {bidang}",
                }
            )

    for rumpun in sorted(rumpun_dipakai):
        if rumpun not in per_rumpun and rumpun not in RUMPUN_PAYUNG:
            masalah.append(f"rumpun '{rumpun}' dipakai prodi tapi tidak punya bobot sub bidang")

    return keluar, masalah


# ---------------------------------------------------------------------------
# 5. Minat profesi -> sub bidang
# ---------------------------------------------------------------------------
def olah_minat(per_sub: dict[str, int]) -> tuple[list[dict], list[str]]:
    aturan = {r["minat_profesi"]: r for r in baca(RULES / "minat_profesi.csv")}
    masalah = [
        f"minat '{m}' menunjuk sub bidang '{r['sub_bidang']}' yang tidak ada di jabatan_klasifikasi"
        for m, r in aturan.items()
        if r["sub_bidang"] not in per_sub
    ]

    hitung: Counter = Counter()
    for r in baca(SOURCES / "rekrutmen_pln" / "programs.csv"):
        for x in r["minat_profesi"].split(","):
            x = x.strip()
            if x:
                hitung[x] += 1

    keluar: list[dict] = []
    tak_dikenal: list[str] = []
    for minat, n in hitung.most_common():
        if minat in aturan:
            a = aturan[minat]
            keluar.append(
                {
                    "minat_profesi": minat,
                    "tipe": "profesi",
                    "sub_bidang": a["sub_bidang"],
                    "bidang_pembidangan": a["bidang_pembidangan"],
                    "n_program": n,
                }
            )
        elif minat.startswith(("Proyeksi", "Rekrutmen")):
            # Bukan profesi -- ini keterangan penempatan/gelombang yang ikut terbawa
            # di kolom yang sama. Disimpan supaya jelas kenapa jumlahnya tidak cocok.
            keluar.append(
                {
                    "minat_profesi": minat,
                    "tipe": "keterangan_penempatan",
                    "sub_bidang": "",
                    "bidang_pembidangan": "",
                    "n_program": n,
                }
            )
        else:
            tak_dikenal.append(f"{minat} ({n}x)")

    if tak_dikenal:
        masalah.append("minat profesi tanpa aturan: " + "; ".join(tak_dikenal))
    return keluar, masalah


# ---------------------------------------------------------------------------
# 6. Pasokan vs permintaan
# ---------------------------------------------------------------------------
def banding_pasokan_permintaan(
    prodi_baris: list[dict], bobot: list[dict], per_sub: dict[str, int]
) -> list[tuple[str, float, float]]:
    """Pasokan = minat pelamar (diproksi jumlah profesi yang membuka prodi) x bobot.

    Permintaan = sebaran kursi G1/G2 non-struktural yang nyata.
    Selisihnya penting: kalau pasokan jauh di bawah permintaan, generator penempatan
    akan kehabisan kandidat yang sah untuk sub bidang itu.
    """
    bobot_map: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for b in bobot:
        bobot_map[b["rumpun"]].append((b["sub_bidang"], float(b["bobot"])))

    pasokan: Counter = Counter()
    for p in prodi_baris:
        n = int(p["n_profesi"])
        if not n or not p["rumpun"]:
            continue
        for sub, w in bobot_map.get(p["rumpun"], []):
            pasokan[sub] += n * w

    total_p = sum(pasokan.values()) or 1
    total_d = sum(per_sub.values()) or 1
    return sorted(
        ((s, pasokan.get(s, 0) / total_p, n / total_d) for s, n in per_sub.items()),
        key=lambda t: -t[2],
    )


def main() -> int:
    print("03 — rumpun jurusan & mapping posisi<->jurusan\n")
    masalah: list[str] = []

    per_profesi, per_program, sumber = kumpulkan_prodi()
    aturan = muat_aturan_rumpun()
    per_sub, bidang_dari_sub = headcount_sub_bidang()

    prodi_baris: list[dict] = []
    tak_kena: list[str] = []
    for prodi in sorted(sumber):
        rumpun, bidang, kunci = klasifikasi(prodi, aturan)
        if not rumpun:
            tak_kena.append(prodi)
        prodi_baris.append(
            {
                "program_studi": prodi,
                "rumpun": rumpun,
                "bidang": bidang,
                "kata_kunci_pemicu": kunci,
                "n_profesi": per_profesi.get(prodi, 0),
                "n_program": per_program.get(prodi, 0),
                "sumber": "|".join(sorted(sumber[prodi])),
            }
        )

    # Cakupan dihitung dua kali: per baris prodi, dan tertimbang permintaan.
    # Yang kedua lebih jujur -- prodi granular RBB banyak tapi bobotnya kecil.
    inti = [p for p in prodi_baris if p["n_profesi"]]
    kena_inti = sum(1 for p in inti if p["rumpun"])
    bobot_total = sum(p["n_profesi"] for p in inti)
    bobot_kena = sum(p["n_profesi"] for p in inti if p["rumpun"])
    kena_semua = sum(1 for p in prodi_baris if p["rumpun"])

    print(f"  prodi terkumpul      : {len(prodi_baris)} ({len(inti)} dipakai profesi.csv)")
    print(f"  cakupan prodi inti   : {kena_inti}/{len(inti)} ({kena_inti / len(inti):.1%})")
    print(f"  cakupan tertimbang   : {bobot_kena}/{bobot_total} ({bobot_kena / bobot_total:.1%})")
    print(f"  cakupan semua sumber : {kena_semua}/{len(prodi_baris)} ({kena_semua / len(prodi_baris):.1%})")

    if any(not p["rumpun"] for p in inti):
        masalah.append(
            "prodi inti (dipakai profesi.csv) tanpa rumpun: "
            + "; ".join(p["program_studi"] for p in inti if not p["rumpun"])
        )

    rumpun_dipakai = {p["rumpun"] for p in prodi_baris if p["rumpun"]}
    bobot, m2 = muat_bobot(per_sub, bidang_dari_sub, rumpun_dipakai)
    masalah += m2

    minat, m3 = olah_minat(per_sub)
    masalah += m3

    # ---- ringkasan rumpun ----
    print("\n  Rumpun (diurut permintaan program):")
    ringkas: list[dict] = []
    agg: dict[str, dict] = defaultdict(lambda: {"n_prodi": 0, "n_profesi": 0, "bidang": ""})
    for p in prodi_baris:
        if not p["rumpun"]:
            continue
        a = agg[p["rumpun"]]
        a["n_prodi"] += 1
        a["n_profesi"] += p["n_profesi"]
        a["bidang"] = p["bidang"]
    total_prof = sum(a["n_profesi"] for a in agg.values()) or 1
    for rumpun, a in sorted(agg.items(), key=lambda kv: -kv[1]["n_profesi"]):
        porsi = a["n_profesi"] / total_prof
        print(f"    {a['n_profesi']:4d} ({porsi:5.1%})  [{a['bidang']:10s}] {rumpun:32s} {a['n_prodi']:4d} prodi")
        ringkas.append(
            {
                "rumpun": rumpun,
                "bidang": a["bidang"],
                "n_prodi": a["n_prodi"],
                "n_profesi": a["n_profesi"],
                "porsi_permintaan": f"{porsi:.4f}",
            }
        )

    # ---- pasokan vs permintaan ----
    print("\n  Pasokan (minat pelamar) vs permintaan (kursi G1+G2 nyata):")
    print(f"    {'sub bidang':36s} {'pasokan':>8s} {'kursi':>8s} {'selisih':>9s}")
    banding = banding_pasokan_permintaan(prodi_baris, bobot, per_sub)
    for sub, p, d in banding:
        tanda = "  <-- kurang" if p < d - 0.03 else ("  <-- lebih" if p > d + 0.03 else "")
        print(f"    {sub:36s} {p:7.1%} {d:8.1%} {p - d:+8.1%}{tanda}")

    # ---- tulis ----
    print()
    tulis(
        MASTER / "program_studi.csv",
        ["program_studi", "rumpun", "bidang", "kata_kunci_pemicu", "n_profesi", "n_program", "sumber"],
        prodi_baris,
    )
    tulis(MASTER / "rumpun_jurusan.csv", ["rumpun", "bidang", "n_prodi", "n_profesi", "porsi_permintaan"], ringkas)
    tulis(
        MASTER / "rumpun_subbidang.csv",
        ["rumpun", "sub_bidang", "bidang_sub", "bobot", "sumber_bobot", "catatan"],
        bobot,
    )
    tulis(MASTER / "minat_profesi.csv", ["minat_profesi", "tipe", "sub_bidang", "bidang_pembidangan", "n_program"], minat)

    if masalah:
        print("\n  MASALAH:")
        for m in masalah:
            print(f"    - {m}")
        return 1
    print("\n  Semua aturan konsisten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
