"""Usulan kebutuhan unit -> penetapan pagu rekrutmen, mengikuti skema asli tim HR.

Rantai lanjutan dari langkah 04:
    kekosongan (04) + gap FTK  ->  USULAN unit  -> dipotong pusat ->  PAGU
    lalu pagu dipecah per posisi x jurusan x jenjang pendidikan.

⚠️ Keluaran mengikuti SKEMA ASLI `Sample-04-Penetapan Pagu Rekrutmen_2026.xlsx` (F-054):
    NO · HOLDING/AP SH · HOLDING/SUBHOLDING · UNIT PELAKSANA · JABATAN ·
    JURUSAN PENDIDIKAN · JUMLAH · PENDIDIKAN · KETERANGAN
Bentuknya nyata; ISINYA tetap dimodelkan (sampel HR dianonimkan & cuma 20 baris).

Input  : out/master/proyeksi_kekosongan.csv, unit_induk.csv, posisi_unit_induk.csv
         out/master/rumpun_subbidang.csv, jabatan_klasifikasi.csv
         rules/attrition.yaml, rules/kohort.yaml, rules/jabatan.yaml
Output : out/master/usulan_kebutuhan.csv   (sebelum dipotong)
         out/master/pagu_rekrutmen.csv     (skema HR, sesudah dipotong)

Jalankan: python mockdb/build/05_usulan_pagu.py
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

# Jenjang pendidikan yang boleh masuk di tiap level tangga jabatan (F-042, tervalidasi F-054).
#
# Level 4 (SPC/SSP) SENGAJA TIDAK ADA. Di `jabatan.yaml` satu-satunya jalur masuk ke SPC
# adalah PRO_HIRE, dan user memutuskan pro hire di luar cakupan ("fokus di rekrutmen
# pegawai non jabatan"). Sebelum ini level 4 ikut terbawa dan menghasilkan 10 orang
# fresh graduate S2 berjabatan Specialist/Assistant Manager.
PENDIDIKAN_LEVEL = {1: "D3", 2: "S1", 3: "S2"}

# Provinsi/unit dengan penempatan 3T -- menentukan kolom KETERANGAN (F-054).
KATA_3T = ("PAPUA", "MALUKU", "NUSA TENGGARA", "KALIMANTAN", "SULAWESI", "ACEH", "BENGKULU")


def baca(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tulis(path: Path, kolom: list[str], baris: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kolom)
        w.writeheader()
        w.writerows(baris)
    print(f"  tulis {path.relative_to(ROOT)}  ({len(baris)} baris)")


def angka(x: str) -> int:
    x = (x or "").strip().replace(",", "")
    try:
        return int(float(x))
    except ValueError:
        return 0


def sebutan(nama_posisi: str, kelompok: str) -> str:
    """Potong prefiks kelompok dari nama posisi -> kolom SEBUTAN JABATAN gaya Sample-02.

    HR memecah nama jabatan jadi dua kolom: NAMA JABATAN ("Officer") dan SEBUTAN JABATAN
    ("Pengelolaan Aset Distribusi"). Master kita menyimpannya tergabung, jadi di sini
    prefiksnya dilepas kembali. Huruf besar dipertahankan mengikuti konvensi DAPEG.
    """
    n, k = nama_posisi.strip(), (kelompok or "").strip()
    return n[len(k):].strip() if k and n.startswith(k) else n


def jurusan_untuk(sub_bidang: str, pendidikan: str, rumpun_map: dict, prodi_map: dict) -> str:
    """Susun teks bergaya HR: 'D3 Teknik Listrik/Teknik Elektro'.

    Sampel HR menyebut NAMA PROGRAM STUDI asli, bukan nama rumpun internal kita.
    Jadi: sub bidang -> rumpun teratas (langkah 03) -> dua prodi tersibuk di rumpun itu.
    """
    kandidat = sorted(rumpun_map.get(sub_bidang, []), key=lambda t: -t[1])
    if not kandidat:
        return f"{pendidikan} Semua Jurusan"
    prodi = prodi_map.get(kandidat[0][0], [])[:2]
    if len(prodi) < 2 and len(kandidat) > 1:
        prodi += prodi_map.get(kandidat[1][0], [])[:1]
    if not prodi:
        return f"{pendidikan} {kandidat[0][0]}"
    return f"{pendidikan} " + "/".join(x.title() for x in prodi[:2])


def main() -> int:
    print("05 — usulan kebutuhan unit & penetapan pagu rekrutmen\n")
    attr = yaml.safe_load((RULES / "attrition.yaml").read_text(encoding="utf-8"))
    koh = yaml.safe_load((RULES / "kohort.yaml").read_text(encoding="utf-8"))
    jab = yaml.safe_load((RULES / "jabatan.yaml").read_text(encoding="utf-8"))

    # Daftar terlarang DIBACA dari aturan, tidak ditulis ulang di sini -- kalau tidak,
    # rules dan generator bisa menyimpang diam-diam.
    terlarang = {s.strip().upper() for s in jab["larangan_struktural"]["kelompok_jabatan_terlarang"]}

    kohort = {
        r["tahun"]: r for r in koh["kohort_per_tahun_program"] if r.get("ada_gelombang", True)
    }
    kaskade = attr["kaskade_promosi"]
    peluang = {int(k): float(v) for k, v in kaskade["peluang_diisi_promosi"].items()}

    # ---- sisi kursi & kekosongan ----
    proyeksi = baca(MASTER / "proyeksi_kekosongan.csv")
    unit = {r["unit_induk"]: r for r in baca(MASTER / "unit_induk.csv")}

    # rumpun per sub bidang (dibalik dari langkah 03)
    rumpun_map: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for r in baca(MASTER / "rumpun_subbidang.csv"):
        if not r["rumpun"].startswith("Lainnya"):
            rumpun_map[r["sub_bidang"]].append((r["rumpun"], float(r["bobot"])))

    # rumpun -> nama prodi asli, diurut dari yang paling sering diminta program
    prodi_kasar: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for r in baca(MASTER / "program_studi.csv"):
        if r["rumpun"] and not r["program_studi"].startswith("PROGRAM STUDI LAINNYA"):
            prodi_kasar[r["rumpun"]].append((r["program_studi"], int(r["n_profesi"])))
    prodi_map = {
        k: [nama for nama, _ in sorted(v, key=lambda t: -t[1])] for k, v in prodi_kasar.items()
    }

    # ---- gap FTK: NYATA untuk 2024 & 2025, dimodelkan untuk tahun lain ----
    ftk24 = sum(angka(u["ftk_2024"]) for u in unit.values())
    ftk25 = sum(angka(u["ftk_2025"]) for u in unit.values())
    real_des25 = sum(angka(u["realisasi_des_2025"]) for u in unit.values())
    real_mar26 = sum(angka(u["realisasi_mar_2026"]) for u in unit.values())
    gap_pct_nyata = {
        2024: (ftk24 - 37897) / ftk24,      # realisasi Des-2024 dari runtun bulanan
        2025: (ftk25 - real_des25) / ftk25,
        2026: (ftk25 - real_mar26) / ftk25,  # FTK 2026 belum ada; dipakai FTK 2025
    }
    gap_pct = {2019: 0.080, 2020: 0.070, 2021: 0.065, 2022: 0.055, 2023: 0.050, **gap_pct_nyata}
    print("  Gap FTK per tahun (porsi terhadap FTK):")
    for t in sorted(gap_pct):
        tanda = "NYATA" if t in gap_pct_nyata else "dimodelkan"
        print(f"    {t}  {gap_pct[t]:6.2%}   {tanda}")

    # bobot gap per unit dari pola NYATA 2025 -- unit yang kurang terisi tetap kurang terisi
    gap_bobot: dict[str, float] = {}
    for nama, u in unit.items():
        f, r = angka(u["ftk_2025"]), angka(u["realisasi_des_2025"])
        gap_bobot[nama] = max(0.0, (f - r) / f) if f else 0.0
    rerata_bobot = sum(gap_bobot.values()) / len(gap_bobot)

    # ---- kebutuhan per unit x level x tahun (kaskade), lalu ditebar ke posisi ----
    kosong: dict[tuple[str, int, int], float] = defaultdict(float)   # (unit, tahun, level)
    kursi: dict[tuple[str, int], list[dict]] = defaultdict(list)     # (unit, level) -> posisi
    seen: set[tuple[str, str]] = set()
    ditolak_struktural = 0
    for p in proyeksi:
        t, lv, un = int(p["tahun"]), int(p["level"]), p["unit_induk"]
        # Kekosongannya TETAP dihitung -- posisi struktural memang kosong dan tetap harus
        # masuk kaskade promosi. Yang dilarang cuma menjadikannya TUJUAN rekrutmen luar.
        kosong[(un, t, lv)] += float(p["kekosongan"])
        if (un, p["nama_posisi"]) in seen:
            continue
        seen.add((un, p["nama_posisi"]))
        # LARANGAN KERAS jabatan.yaml: pegawai baru tidak pernah masuk jabatan struktural.
        # Disaring pakai kelompok_jabatan, BUKAN jenjang/level -- justru inilah jebakan yang
        # diperingatkan aturan itu, dan yang sebelumnya terinjak di sini: TEAM LEADER
        # bergrade G2 (sama dengan OFFICER) dan ASSISTANT MANAGER bergrade G3 (sama dengan
        # SENIOR OFFICER), jadi saringan berbasis grade meloloskan keduanya.
        if p["kelompok_jabatan"].strip().upper() in terlarang:
            ditolak_struktural += 1
            continue
        kursi[(un, lv)].append(p)
    print(f"\n  Posisi struktural dikeluarkan dari sasaran rekrutmen: {ditolak_struktural:,} "
          f"posisi x unit (kekosongannya tetap masuk kaskade promosi)")

    usulan_baris: list[dict] = []
    pagu_mentah: dict[int, list[dict]] = defaultdict(list)
    usulan_total: dict[int, float] = defaultdict(float)   # dihitung SEBELUM dipecah per posisi
    luar_cakupan = 0.0    # sisa rekrutmen luar di level 4+ (jalur pro hire, di luar cakupan)

    for tahun_program, info in sorted(kohort.items()):
        t_isi = info["masuk_di"]          # kekosongan tahun kapan yang mau diisi
        for nama, u in unit.items():
            hc = angka(u["realisasi_des_2025"]) or angka(u["jumlah_pegawai"])
            # kaskade: kekosongan level L -> rekrutmen luar di level L
            rekrut_level: dict[int, float] = defaultdict(float)
            sisa = {lv: kosong.get((nama, t_isi, lv), 0.0) for lv in range(1, 8)}
            for lv in sorted(sisa, reverse=True):
                n = sisa[lv]
                if n <= 0:
                    continue
                p = peluang.get(lv, 0.0)
                rekrut_level[lv] += n * (1 - p)
                if p > 0 and lv > 1:
                    sisa[lv - 1] = sisa.get(lv - 1, 0.0) + n * p
            # gap FTK unit: porsi nasional x intensitas unit
            gap_unit = hc * gap_pct[tahun_program] * (
                gap_bobot[nama] / rerata_bobot if rerata_bobot else 1
            )
            total_rekrut = sum(rekrut_level.values())
            luar_cakupan += sum(
                n for lv, n in rekrut_level.items() if lv not in PENDIDIKAN_LEVEL and n > 0
            )
            # Ditelusuri per level cakupan, BUKAN per level yang kebetulan berkekosongan.
            # Bedanya: level tanpa kebutuhan pun tetap memancarkan baris ber-usulan 0,
            # meniru Sample-02 yang mempertahankan baris FTK 0. "Formasi nol" dan "posisi
            # tidak ada di unit ini" adalah dua cerita berbeda, dan sebelumnya keduanya
            # sama-sama tak terlihat.
            for lv in sorted(PENDIDIKAN_LEVEL):
                daftar = kursi.get((nama, lv), [])
                if not daftar:
                    continue
                n = rekrut_level.get(lv, 0.0)
                bagian_gap = gap_unit * (n / total_rekrut) if total_rekrut else 0.0
                usulan = n + bagian_gap
                usulan_total[tahun_program] += usulan
                bobot_total = sum(int(k["pegawai"]) for k in daftar) or 1
                for k in daftar:
                    porsi = int(k["pegawai"]) / bobot_total
                    nilai = usulan * porsi
                    baris = {
                        "tahun_program": tahun_program,
                        "unit_induk": nama,
                        "jenis_unit": u["jenis_unit"],
                        "nama_posisi": k["nama_posisi"],
                        "kelompok_jabatan": k["kelompok_jabatan"],
                        "sebutan_jabatan": sebutan(k["nama_posisi"], k["kelompok_jabatan"]),
                        "kode_grade": k["jenjang"],
                        "sub_bidang": k["sub_bidang"],
                        "level": lv,
                        "pendidikan": PENDIDIKAN_LEVEL[lv],
                        "kekosongan": round(n * porsi, 3),
                        "gap_ftk": round(bagian_gap * porsi, 3),
                        "usulan": round(nilai, 3),
                    }
                    usulan_baris.append(baris)
                    if nilai >= 0.001:      # baris nol tidak ikut pembagian pagu
                        pagu_mentah[tahun_program].append(baris)

    # ---- pemotongan: total pagu harus mendarat di ukuran kohort nyata ----
    # Faktor bisa >1: di tahun-tahun terakhir PLN merekrut MELEBIHI kebutuhan pengganti,
    # menutup defisit yang menumpuk dari 2019-2022 (F-052). Jadi ini "penyesuaian",
    # bukan semata "pemotongan".
    print("\n  Usulan unit vs pagu ditetapkan (faktor DIHITUNG dari kohort nyata, bukan diasumsikan):")
    print(f"    {'thn':4s} {'usulan':>8s} {'pagu':>7s} {'faktor':>7s}  arah")
    pagu_baris: list[dict] = []
    nomor = 0
    kum_usulan = kum_pagu = 0.0
    for tahun_program, info in sorted(kohort.items()):
        baris = pagu_mentah[tahun_program]
        total_usulan = usulan_total[tahun_program]
        target = info["induk_diterima"]
        faktor = target / total_usulan if total_usulan else 0
        kum_usulan += total_usulan
        kum_pagu += target
        arah = "dipotong" if faktor < 0.98 else ("ditambah" if faktor > 1.02 else "pas")
        print(f"    {tahun_program:4d} {total_usulan:8.0f} {target:7,} {faktor:7.2f}  {arah}")

        # Pembagian ke posisi memakai metode SISA TERBESAR supaya jumlahnya persis
        # = target. Pembulatan biasa membocorkan ratusan orang.
        #
        # Dialokasikan BERTINGKAT PER JENJANG PENDIDIKAN. Kalau semua baris bersaing
        # dalam satu kolam, baris S2 selalu kalah: jumlahnya kecil-kecil sehingga
        # pecahannya rendah, dan S2 lenyap jadi 0,1% padahal semestinya ~4%. Stratifikasi
        # menjaga bauran D3/S1/S2 tetap sesuai kaskade, bukan hasil sampingan pembulatan.
        dasar: list[tuple[dict, int, float]] = []
        per_pend: dict[str, list[dict]] = defaultdict(list)
        for b in baris:
            per_pend[b["pendidikan"]].append(b)
        total_semua = sum(b["usulan"] for b in baris) or 1
        sisa_target = target
        strata = sorted(per_pend.items(), key=lambda kv: -sum(b["usulan"] for b in kv[1]))
        for i, (pend, grup) in enumerate(strata):
            porsi = sum(b["usulan"] for b in grup) / total_semua
            jatah = sisa_target if i == len(strata) - 1 else round(target * porsi)
            sisa_target -= jatah
            sub_total = sum(b["usulan"] for b in grup) or 1
            skala = [(b, b["usulan"] / sub_total * jatah) for b in grup]
            lokal = [(b, int(v), v - int(v)) for b, v in skala]
            kurang = jatah - sum(d[1] for d in lokal)
            lokal.sort(key=lambda d: -d[2])
            for j in range(len(lokal)):
                if kurang <= 0:
                    break
                lokal[j] = (lokal[j][0], lokal[j][1] + 1, lokal[j][2])
                kurang -= 1
            dasar += lokal

        for b, jml, _ in sorted(dasar, key=lambda d: -d[1]):
            if jml < 1:
                continue
            nomor += 1
            nama_unit = unit[b["unit_induk"]]["nama_pendek"]
            ket = "3T" if any(k in b["unit_induk"].upper() for k in KATA_3T) else f"Rekrut {tahun_program}"
            pagu_baris.append(
                {
                    "no": nomor,
                    "tahun_program": tahun_program,
                    "holding_ap_sh": "HOLDING",
                    "holding_subholding": nama_unit,
                    "unit_pelaksana": "",     # master kita berhenti di unit pelaksana; ULP tidak tersedia
                    "jabatan": b["nama_posisi"],
                    "nama_jabatan": b["kelompok_jabatan"],   # kolom NAMA JABATAN Sample-02
                    "sebutan_jabatan": b["sebutan_jabatan"],  # kolom SEBUTAN JABATAN Sample-02
                    "kode_grade": b["kode_grade"],            # kolom JENJANG JABATAN Sample-02
                    "jurusan_pendidikan": jurusan_untuk(
                        b["sub_bidang"], b["pendidikan"], rumpun_map, prodi_map
                    ),
                    "jumlah": jml,
                    "pendidikan": b["pendidikan"],
                    "keterangan": ket,
                    "sub_bidang": b["sub_bidang"],
                    "level": b["level"],
                    "usulan_sebelum_potong": b["usulan"],
                }
            )
    print(f"    {'KUM':4s} {kum_usulan:8.0f} {kum_pagu:7,.0f} {kum_pagu / kum_usulan:7.2f}  rata-rata terisi")
    print("    ! Jangan baca selisih kumulatif sebagai 'defisit pegawai'. Gap FTK adalah")
    print("      STOK kursi kosong yang DIUSULKAN ULANG tiap tahun oleh unit, jadi ia")
    print("      terhitung berkali-kali. Yang boleh dibaca lintas tahun cuma komponen")
    print("      kekosongan (aliran), dan itu sudah dilaporkan di langkah 04.")

    # ---- laporan ----
    print("\n  Unit dengan pemotongan terbesar (usulan vs pagu, seluruh horison):")
    per_unit: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for b in usulan_baris:
        per_unit[b["unit_induk"]][0] += b["usulan"]
    for b in pagu_baris:
        per_unit[b["holding_subholding"]][1] += b["jumlah"]
    nm = {unit[k]["nama_pendek"]: k for k in unit}
    gab = defaultdict(lambda: [0.0, 0.0])
    for k, v in per_unit.items():
        kunci = unit[k]["nama_pendek"] if k in unit else k
        gab[kunci][0] += v[0]
        gab[kunci][1] += v[1]
    urut = sorted((v[1] / v[0] if v[0] else 1, k, v) for k, v in gab.items() if v[0] > 50)
    for r, k, v in urut[:6]:
        print(f"    {k:34s} usulan {v[0]:7.0f} -> pagu {v[1]:6.0f}  ({r:.0%})")

    # Sebelumnya baris ber-nilai < 0,01 dibuang sebagai "debu numerik". Itu keliru:
    # baris begitu justru padanan baris FTK 0 di Sample-02 -- posisi ADA di unit, tapi
    # formasinya nol tahun itu. Kalau dibuang, "formasi nol" jadi tak bisa dibedakan dari
    # "posisi tidak ada di unit ini". Sekarang dipertahankan.
    tipis = sum(1 for b in usulan_baris if b["usulan"] < 0.01)
    kosong_pagu = sum(1 for b in usulan_baris if b["usulan"] < 0.5)
    print(f"\n  Baris berformasi nol dipertahankan: {tipis:,} baris < 0,01 (dulu dibuang) "
          f"dari {len(usulan_baris):,}")
    print(f"  Baris yang tidak menghasilkan satu orang pun di pagu: {kosong_pagu:,} "
          f"({kosong_pagu / len(usulan_baris):.0%}) -- ini 'formasi nol' gaya Sample-02")
    print(f"  Sisa rekrutmen luar di level 4+ yang DIBUANG: {luar_cakupan:,.0f} orang "
          f"seluruh horison -- itu jalur pro hire (SPC/SSP), di luar cakupan.")

    total_pagu = sum(b["jumlah"] for b in pagu_baris)
    total_kohort = sum(i["induk_diterima"] for i in kohort.values())
    print(f"\n  Total pagu {total_pagu:,} vs kohort induk {total_kohort:,} "
          f"(selisih {total_pagu - total_kohort:+,} = pembulatan per baris)")
    print(f"  Rata-rata kuota per baris: {total_pagu / len(pagu_baris):.2f} orang "
          f"(sampel HR: {30/20:.2f})")

    print()
    tulis(
        MASTER / "usulan_kebutuhan.csv",
        ["tahun_program", "unit_induk", "jenis_unit", "nama_posisi", "kelompok_jabatan",
         "sebutan_jabatan", "kode_grade", "sub_bidang", "level", "pendidikan",
         "kekosongan", "gap_ftk", "usulan"],
        usulan_baris,
    )
    tulis(
        MASTER / "pagu_rekrutmen.csv",
        ["no", "tahun_program", "holding_ap_sh", "holding_subholding", "unit_pelaksana",
         "jabatan", "nama_jabatan", "sebutan_jabatan", "kode_grade", "jurusan_pendidikan",
         "jumlah", "pendidikan", "keterangan", "sub_bidang", "level", "usulan_sebelum_potong"],
        pagu_baris,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
