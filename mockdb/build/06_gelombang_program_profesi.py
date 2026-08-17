"""Gelombang -> program (entri penempatan) -> profesi: katalog rekrutmen 2019-2025.

Tiga level menurut `angkatan.yaml` -> struktur:
    gelombang     = satu nomor angkatan (satu tanggal buka)
    program_entri = pecahan per subholding penempatan / per kota
    profesi       = UNIT GRANULAR PENDAFTARAN (F-010) -- di sinilah tanggal, kota,
                    IPK minimal dan batas umur sesungguhnya melekat

⚠️ ATURAN KERAS: **tidak ada judul program yang boleh dikarang.** Semua judul berasal dari
programs.csv (31) / programs_historis.csv (111, arsip Wayback) / lowongan_pln_rbb.csv (20).
Gelombang yang tidak punya judul sama sekali diberi penanda eksplisit
"(tidak terekam di katalog PLN)" -- lihat `sumber_judul` di angkatan.yaml.

Input  : rules/angkatan.yaml, kohort.yaml, demografi.yaml, administrasi.yaml
         knowledge/sources/rekrutmen_pln/{programs,profesi}.csv
         knowledge/sources/rekrutmen_pln/wayback/programs_historis.csv
         knowledge/sources/rbb_fhci/lowongan_pln_rbb.csv
Output : out/master/gelombang.csv · program.csv · profesi.csv · profesi_prodi.csv

Jalankan: python mockdb/build/06_gelombang_program_profesi.py
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"
SRC = ROOT / "knowledge" / "sources"

TANPA_JUDUL = "(tidak terekam di katalog PLN)"

BULAN_ID = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
}

# Urutan PENTING: dievaluasi dari atas. "S2 Pro Hire ICE" harus jatuh ke PRO_HIRE,
# bukan ke S2; "S2 Indonesia Career Evening" harus jatuh ke S2, bukan ke CAMPUS.
POLA_JENIS = [
    ("PRO_HIRE", r"PRO ?HIRE"),
    ("DIASPORA", r"DIASPORA"),
    ("AFIRMASI", r"PAPUA|MALUKU|NUSA TENGGARA|\bOAP\b"),
    ("BIDANG", r"MATEMATIKA|BIDANG HUKUM|\bHUKUM\b"),
    ("S2", r"\bS2\b|CAREER EVENING"),
    ("CAMPUS", r"CAREER FAIR|CAREER DAY|BURSA KARIR"),
]


def baca_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tulis(path: Path, kolom: list[str], baris: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=kolom, extrasaction="ignore")
        w.writeheader()
        w.writerows(baris)
    print(f"  tulis {path.relative_to(ROOT)}  ({len(baris)} baris)")


def parse_tgl(teks: str) -> str:
    """'05 Oktober 2025 23:59 WIB' -> '2025-10-05'. String kosong kalau tak terbaca."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", teks or "")
    if not m:
        return ""
    bln = BULAN_ID.get(m.group(2).lower())
    return f"{m.group(3)}-{bln:02d}-{int(m.group(1)):02d}" if bln else ""


def jenis_program(judul: str, jalur: str) -> str:
    if jalur == "rbb":
        return "RBB"
    besar = (judul or "").upper()
    for kode, pola in POLA_JENIS:
        if re.search(pola, besar):
            return kode
    return "REGULER"


def bagi_sisa_terbesar(bobot: list[float], total: int) -> list[int]:
    """Bagi `total` bulat menurut `bobot`, dijamin berjumlah persis `total`."""
    jum = sum(bobot)
    if jum <= 0 or total <= 0:
        return [0] * len(bobot)
    mentah = [b / jum * total for b in bobot]
    hasil = [int(x) for x in mentah]
    kurang = total - sum(hasil)
    # Urut menurun berdasar pecahan; indeks jadi pemutus seri supaya hasilnya deterministik.
    urut = sorted(range(len(bobot)), key=lambda i: (-(mentah[i] - hasil[i]), i))
    for i in urut[:kurang]:
        hasil[i] += 1
    return hasil


def muat_aturan() -> dict:
    return {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(RULES.glob("*.yaml"))}


# ---------------------------------------------------------------------------
# 1. Rangkai daftar gelombang dari angkatan.yaml
# ---------------------------------------------------------------------------
def susun_gelombang(R: dict) -> list[dict]:
    koh = {r["tahun"]: r for r in R["kohort"]["kohort_per_tahun_program"] if r.get("ada_gelombang", True)}
    jeda = R["kohort"]["jeda_pipeline"]
    tambah = jeda["tahun"] if isinstance(jeda, dict) and "tahun" in jeda else 1

    keluar: list[dict] = []
    for seri in ("utama", "khusus"):
        for angkatan, g in sorted(R["angkatan"]["seri"][seri]["gelombang"].items()):
            tahun = g["tahun"]
            if tahun not in koh:
                continue
            info = koh[tahun]
            jalur = g.get("jalur", info["jalur"])
            keluar.append({
                "gelombang_id": f"G{tahun}-{angkatan:03d}",
                "angkatan": angkatan,
                "seri": seri,
                "sumber_nomor": g["sumber_nomor"],
                "tahun_program": tahun,
                "tahun_masuk": tahun + tambah,
                "nama_gelombang": g["nama"],
                "tgl_buka_rencana": g["buka"],
                "jenis_program": jenis_program(g["nama"], jalur),
                "sumber_rekrutmen": jalur,
                "kualitas_kohort": info["kualitas"],
            })
    return sorted(keluar, key=lambda g: (g["tahun_program"], g["angkatan"]))


# ---------------------------------------------------------------------------
# 2. Kumpulkan judul ASLI dan tempelkan ke gelombang
# ---------------------------------------------------------------------------
def kumpulkan_judul(gelombang: list[dict]) -> tuple[list[dict], dict[str, int]]:
    per_id = {g["gelombang_id"]: g for g in gelombang}
    per_angkatan = {g["angkatan"]: g for g in gelombang}
    # Beberapa gelombang berbagi tahun; pencocokan tanggal dipakai untuk entri yang
    # kolom `angkatan`-nya kosong di programs.csv (mis. Diaspora 2023, Matematika/EPI 2025).
    per_tgl: dict[str, dict] = {}
    for g in gelombang:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", g["tgl_buka_rencana"]):
            per_tgl.setdefault(g["tgl_buka_rencana"], g)

    entri: list[dict] = []
    hitung = defaultdict(int)
    judul_terpakai: set[str] = set()

    def norm(j: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", (j or "").upper())

    # --- (a) programs.csv: katalog live, 31 judul ---
    for r in baca_csv(SRC / "rekrutmen_pln" / "programs.csv"):
        buka = parse_tgl(r["tgl_buka"])
        g = per_angkatan.get(int(r["angkatan"])) if r["angkatan"].strip().isdigit() else per_tgl.get(buka)
        if g is None:
            hitung["programs_tak_tertempel"] += 1
            continue
        judul_terpakai.add(norm(r["title"]))
        entri.append({
            "gelombang": g, "judul": r["title"], "sumber_judul": "programs.csv",
            "lokasi_tes": r["lokasi_tes"], "status": r["status"],
            "tgl_buka": buka, "tgl_tutup": parse_tgl(r["tgl_tutup"]),
            "pdf_brosur": r["pdf_files"], "program_id_asli": r["program_id"],
        })
        hitung["dari_programs"] += 1

    # --- (b) arsip Wayback: satu-satunya sumber judul 2019 ---
    # Ditempelkan lewat BULAN kemunculan pertama. Itu sah karena gelombang 2019 memang
    # dibedakan oleh bulan buka (Jul/Agu/Sep/Nov) -- lihat angkatan.yaml.
    per_bulan = {g["tgl_buka_rencana"]: g for g in gelombang
                 if re.fullmatch(r"\d{4}-\d{2}", g["tgl_buka_rencana"]) and g["seri"] == "utama"}
    khusus_2019 = next((g for g in gelombang if g["seri"] == "khusus" and g["tahun_program"] == 2019), None)

    for r in baca_csv(SRC / "rekrutmen_pln" / "wayback" / "programs_historis.csv"):
        if norm(r["judul"]) in judul_terpakai:      # PPB Papua muncul di kedua sumber
            hitung["wayback_duplikat"] += 1
            continue
        bulan = (r["pertama_terlihat"] or "")[:7]
        thn_judul = (r["tahun_di_judul"] or "").strip()
        # `pertama_terlihat` adalah tanggal SNAPSHOT ARSIP, bukan tanggal program dibuka.
        # Program 2017/2018 yang baru pertama kali ter-crawl pada 2019 akan lolos kalau
        # disaring dengan snapshot saja -- itu menyeret 12 program SMK 2017 dan 4 program
        # 2018 ke gelombang 2019. Maka tahun DI JUDUL yang menentukan; snapshot hanya
        # dipakai untuk judul yang memang tidak mencantumkan tahun.
        if thn_judul:
            if thn_judul != "2019":
                hitung["wayback_di_luar_horison"] += 1
                continue
        elif not bulan.startswith("2019"):
            hitung["wayback_di_luar_horison"] += 1
            continue
        elif re.match(r"REKRUTMEN UMUM", r["judul"].strip(), re.I):
            # Judul tanpa tahun DAN berpenamaan lama "REKRUTMEN UMUM" -> tidak bisa
            # ditanggalkan. F-032: konvensi itu dipakai 2017-2019; F-063 membuktikan
            # "Bursa Karir ITS ke-33" di dalamnya sebenarnya April 2017. Kelompok ini
            # memuat KOTA BERULANG dalam tiga gaya penulisan berbeda (Manado, Pekanbaru,
            # Lampung, Kupang masing-masing dua kali) -- ciri beberapa tahun rekrutmen
            # yang menumpuk di katalog, bukan satu gelombang. Karena `pertama_terlihat`
            # cuma batas ATAS (kapan crawler pertama menangkap, bukan kapan dibuka),
            # tidak ada cara memisahkannya. Dibuang daripada menggemukkan 2019.
            hitung["wayback_tak_bertanggal"] += 1
            continue
        # Jaring pengaman kedua: angkatan.yaml -> smk_pelaksana.dimodelkan = false.
        if re.search(r"\bSMK\b|TINGKAT SMA", r["judul"].upper()):
            hitung["wayback_smk_ditolak"] += 1
            continue
        g = khusus_2019 if re.search(r"PRO ?HIRE", r["judul"].upper()) else per_bulan.get(bulan)
        if g is None:
            hitung["wayback_tak_tertempel"] += 1
            continue
        judul_terpakai.add(norm(r["judul"]))
        entri.append({
            "gelombang": g, "judul": r["judul"], "sumber_judul": "wayback",
            "lokasi_tes": "", "status": "CLOSED",
            "tgl_buka": "", "tgl_tutup": "", "pdf_brosur": "", "program_id_asli": "",
        })
        hitung["dari_wayback"] += 1

    # --- (c) RBB/FHCI 2024: 20 lowongan PLN Group ---
    # Semuanya ditempel ke batch I. angkatan.yaml sendiri mengaku jumlah batch RBB 2024
    # tidak diketahui; membagi 20 lowongan ke dua batch berarti mengarang lowongan mana
    # milik batch mana. Batch II dibiarkan tanpa judul.
    rbb_g = next((g for g in gelombang if g["sumber_rekrutmen"] == "rbb" and g["tahun_program"] == 2024), None)
    if rbb_g is not None:
        for r in baca_csv(SRC / "rbb_fhci" / "lowongan_pln_rbb.csv"):
            entri.append({
                "gelombang": rbb_g, "judul": r["vacancy_name"], "sumber_judul": "rbb_fhci",
                "lokasi_tes": "Seluruh Indonesia", "status": "CLOSED",
                "tgl_buka": "", "tgl_tutup": "", "pdf_brosur": "", "program_id_asli": r["vacancy_id"],
                "perusahaan": r["tenant_name"], "rbb": r,
            })
            hitung["dari_rbb"] += 1

    # --- (d) gelombang yang tetap kosong: penanda eksplisit, BUKAN judul karangan ---
    berisi = {id(e["gelombang"]) for e in entri}
    for g in gelombang:
        if id(g) not in berisi:
            entri.append({
                "gelombang": g, "judul": f"{g['nama_gelombang']} {TANPA_JUDUL}",
                "sumber_judul": "tidak_terekam", "lokasi_tes": "", "status": "CLOSED",
                "tgl_buka": "", "tgl_tutup": "", "pdf_brosur": "", "program_id_asli": "",
            })
            hitung["tanpa_judul"] += 1

    _ = per_id
    return entri, dict(hitung)


# ---------------------------------------------------------------------------
# 3. Profesi -- pakai profesi.csv kalau ada, kalau tidak turunkan dari bauran jenjang
# ---------------------------------------------------------------------------
def parse_ipk_prodi(teks: str) -> list[tuple[str, float]]:
    """'TEKNIK ELEKTRO minimal 3 TEKNIK MESIN minimal 3' -> [(prodi, ipk), ...]"""
    hasil = []
    for m in re.finditer(r"([A-Z][A-Z0-9\s&/\.\-]*?)\s*minimal\s*([\d]+(?:[.,]\d+)?)", teks or ""):
        nama = m.group(1).strip(" ,;")
        if nama:
            hasil.append((nama, float(m.group(2).replace(",", "."))))
    return hasil


def pola_subholding(R: dict) -> re.Pattern:
    """Pengenal entri penempatan SUBHOLDING, dirakit dari daftar di kohort.yaml.

    Dipakai untuk memisahkan kursi induk dari kursi subholding. Ini bukan hiasan:
    `sub_diterima` di kohort.yaml justru DITURUNKAN dari jumlah entri penempatan
    subholding per gelombang (F-003). Kalau alokasi tidak memakai pemisahan yang sama,
    gelombang bisa menerima lebih sedikit orang daripada angka yang diturunkan darinya
    sendiri -- persis yang terjadi pada angkatan 92 (dapat 542, padahal 950 kursi
    subholding 2025 berasal dari lima entri penempatannya).
    """
    kata: list[str] = []
    for s in R["kohort"]["subholding"]["daftar"]:
        nama = re.sub(r"^PT\s+", "", s["nama"])
        nama = re.sub(r"\s*\(.*?\)", "", nama).strip()
        kata.append(re.escape(nama))
        kata.append(re.escape(s["kode"]))
    kata += [re.escape(x) for x in ("Icon Plus", "Icon+", "COMNETS", "HALEYORA", "PLN BATAM")]
    return re.compile("|".join(kata), re.I)


def bauran_jenjang(R: dict, tahun: int) -> dict[str, float]:
    """Porsi D3/S1/S2 tahun itu dari demografi.yaml.

    Kunci tahun di YAML terbaca sebagai INT, bukan string. Mengambilnya dengan
    `.get(str(tahun))` diam-diam mengembalikan {} -- tidak error, tapi seluruh bauran
    pendidikan lalu jatuh ke nilai bawaan dan aturan demografi tak pernah terpakai.
    """
    tabel = R["demografi"]["jenjang_pelamar"]["per_tahun_program"]
    isi = tabel.get(tahun) or tabel.get(str(tahun)) or {}
    return {k: float(v) for k, v in isi.items() if isinstance(v, (int, float))}


def umur_maks(R: dict, jalur: str, jenjang: str, jenis: str) -> int:
    tabel = R["administrasi"]["umur_maks_saat_daftar"]
    if jenis == "PRO_HIRE":
        return tabel["pro_hire"]["umur_maks"]
    grup = tabel.get("rbb" if jalur == "rbb" else "mandiri", {})
    return grup.get(jenjang, grup.get("S1/D-IV", 27))


def ipk_min(R: dict, jenis: str, bawaan: str = "") -> float:
    if bawaan:
        try:
            return float(str(bawaan).replace(",", "."))
        except ValueError:
            pass
    aturan = R["administrasi"]["ipk_min"]
    for p in aturan["pengecualian"]:
        if p["tipe"] == "OAP" and jenis == "AFIRMASI":
            return float(p["nilai"])
    return float(aturan["default"])


def main() -> int:
    print("06 — gelombang, program & profesi\n")
    R = muat_aturan()

    gelombang = susun_gelombang(R)
    print(f"  Gelombang di horison: {len(gelombang)} "
          f"({sum(1 for g in gelombang if g['seri'] == 'utama')} utama, "
          f"{sum(1 for g in gelombang if g['seri'] == 'khusus')} khusus)")
    lubang = R["angkatan"]["seri"]["utama"]["lubang"]
    print(f"  Nomor angkatan sengaja dikosongkan: {lubang} ({len(lubang)} nomor)")

    entri, hitung = kumpulkan_judul(gelombang)
    print("\n  Asal-usul judul program (tidak satu pun dikarang):")
    for k in ("dari_programs", "dari_wayback", "dari_rbb", "tanpa_judul",
              "wayback_duplikat", "wayback_di_luar_horison", "wayback_tak_bertanggal", "wayback_smk_ditolak", "programs_tak_tertempel",
              "wayback_tak_tertempel"):
        if hitung.get(k):
            print(f"    {k:26s} {hitung[k]:4d}")

    # ---- program.csv ----
    profesi_asli = defaultdict(list)
    for r in baca_csv(SRC / "rekrutmen_pln" / "profesi.csv"):
        if r["angkatan"].strip().isdigit():
            profesi_asli[int(r["angkatan"])].append(r)

    program_baris: list[dict] = []
    per_gelombang: dict[str, list[dict]] = defaultdict(list)
    for i, e in enumerate(sorted(entri, key=lambda x: (x["gelombang"]["tahun_program"],
                                                       x["gelombang"]["angkatan"], x["judul"])), 1):
        g = e["gelombang"]
        b = {
            "program_id": f"P{i:04d}",
            "gelombang_id": g["gelombang_id"],
            "angkatan": g["angkatan"],
            "tahun_program": g["tahun_program"],
            "judul": e["judul"],
            "sumber_judul": e["sumber_judul"],
            "perusahaan_penempatan": e.get("perusahaan", ""),
            "lokasi_tes": e["lokasi_tes"],
            "status": e["status"],
            "tgl_buka": e["tgl_buka"],
            "tgl_tutup": e["tgl_tutup"],
            "pdf_brosur": e["pdf_brosur"],
            "jenis_program": jenis_program(e["judul"], g["sumber_rekrutmen"]),
        }
        program_baris.append(b)
        per_gelombang[g["gelombang_id"]].append({**b, "_rbb": e.get("rbb")})

    # ---- profesi.csv ----
    profesi_baris: list[dict] = []
    prodi_baris: list[dict] = []
    n = 0
    for g in gelombang:
        prog = per_gelombang[g["gelombang_id"]]
        asli = profesi_asli.get(g["angkatan"], [])
        if asli:
            # Sumber asli: satu profesi = satu baris profesi.csv, ditempel ke program
            # yang judulnya sama; kalau tak ketemu, ke program pertama gelombang.
            for r in asli:
                n += 1
                induk = next((p for p in prog if p["judul"] == r["program_title"]), prog[0])
                jenj = r["jenjang"] or "S1/D-IV"
                jenis = jenis_program(r["program_title"] or induk["judul"], g["sumber_rekrutmen"])
                pid = f"F{n:05d}"
                profesi_baris.append({
                    "profesi_id": pid, "program_id": induk["program_id"],
                    "gelombang_id": g["gelombang_id"], "angkatan": g["angkatan"],
                    "tahun_program": g["tahun_program"],
                    "kode_profesi": r["kode_profesi"], "nama_profesi": r["nama_profesi"],
                    "jenjang": jenj, "kota_rekrutmen": r["kota_rekrutmen"],
                    "tgl_buka": parse_tgl(r["tgl_buka"]), "tgl_tutup": parse_tgl(r["tgl_tutup"]),
                    "min_ipk": ipk_min(R, jenis, r["min_ipk"]),
                    "umur_maks": umur_maks(R, g["sumber_rekrutmen"], jenj, jenis),
                    "sumber_rekrutmen": g["sumber_rekrutmen"],
                    "jenis_program": jenis, "status_sumber": "NYATA",
                })
                for nama, ipk in parse_ipk_prodi(r["minimal_ipk"]):
                    prodi_baris.append({"profesi_id": pid, "program_studi": nama, "min_ipk": ipk})
            continue

        # Tidak ada profesi asli -> turunkan dari bauran jenjang tahun itu (demografi.yaml).
        # Gelombang RBB memakai jenjang & syarat dari JSON lowongan FHCI, yang justru
        # lebih kaya dari katalog PLN: batas umur dan IPK per lowongan ada di sana.
        mix = bauran_jenjang(R, g["tahun_program"])
        for p in prog:
            rbb = p.get("_rbb")
            if rbb:
                jenjang_p = [j for j, kol in (("D-III", "allow_d3"), ("S1/D-IV", "allow_s1"),
                                              ("S2", "allow_s2")) if rbb.get(kol) == "1"]
            else:
                jenjang_p = [j for j in mix if mix[j] > 0]
                if g["jenis_program"] in ("S2", "PRO_HIRE"):
                    jenjang_p = ["S2"]
            for j in jenjang_p or ["S1/D-IV"]:
                n += 1
                kol_ipk = {"D-III": "lowest_ipk_d3", "S1/D-IV": "lowest_ipk_s1", "S2": "lowest_ipk_s2"}
                kol_umur = {"D-III": "highest_age_d3", "S1/D-IV": "highest_age_s1", "S2": "highest_age_s2"}
                jenis = p["jenis_program"]
                profesi_baris.append({
                    "profesi_id": f"F{n:05d}", "program_id": p["program_id"],
                    "gelombang_id": g["gelombang_id"], "angkatan": g["angkatan"],
                    "tahun_program": g["tahun_program"],
                    "kode_profesi": f"{g['angkatan']}.{n}", "nama_profesi": p["judul"],
                    "jenjang": j, "kota_rekrutmen": p["lokasi_tes"] or "Seluruh Indonesia",
                    "tgl_buka": p["tgl_buka"], "tgl_tutup": p["tgl_tutup"],
                    "min_ipk": ipk_min(R, jenis, (rbb or {}).get(kol_ipk[j], "")),
                    "umur_maks": int((rbb or {}).get(kol_umur[j]) or 0)
                                 or umur_maks(R, g["sumber_rekrutmen"], j, jenis),
                    "sumber_rekrutmen": g["sumber_rekrutmen"],
                    "jenis_program": jenis,
                    "status_sumber": "NYATA_RBB" if rbb else "DIMODELKAN",
                })

    # ---- alokasi diterima per profesi ----
    # Dijangkar ke angka kohort NYATA per tahun, lalu dibagi menurut bauran jenjang
    # demografi.yaml -- jadi bauran pendidikan hasil langkah ini mengunci ke aturan,
    # bukan jatuh sebagai efek samping pembulatan.
    koh = {r["tahun"]: r for r in R["kohort"]["kohort_per_tahun_program"] if r.get("ada_gelombang", True)}
    per_tahun = defaultdict(list)
    for p in profesi_baris:
        per_tahun[p["tahun_program"]].append(p)

    # Tandai tiap profesi: penempatannya ke INDUK atau ke SUBHOLDING. Diambil dari judul
    # program ("... Penempatan : PT PLN Indonesia Power") atau kolom perusahaan (RBB).
    pola_sh = pola_subholding(R)
    peta_prog = {p["program_id"]: p for p in program_baris}
    for p in profesi_baris:
        induk_prog = peta_prog[p["program_id"]]
        teks = f"{induk_prog['judul']} {induk_prog['perusahaan_penempatan']}"
        p["penempatan"] = "SUBHOLDING" if pola_sh.search(teks) else "INDUK"

    print("\n  Alokasi diterima per tahun (dijangkar ke kohort nyata):")
    print(f"    {'thn':4s} {'gel':>4s} {'prog':>5s} {'profesi':>8s} {'induk':>6s} {'sub':>5s} {'group':>6s}")
    for tahun, daftar in sorted(per_tahun.items()):
        info = koh[tahun]
        target = info["induk_diterima"] + info["sub_diterima"]
        mix = bauran_jenjang(R, tahun)
        # Pro hire dikeluarkan dari alokasi: langkah 05 sudah mengeluarkan level SPC dari
        # pagu, jadi memberinya kursi di sini akan membuat kedua langkah bertengkar.
        layak = [p for p in daftar if p["jenis_program"] != "PRO_HIRE"]

        # Kursi induk dan kursi subholding dibagi DI KOLAM MASING-MASING. Kalau digabung,
        # gelombang yang tidak punya entri subholding tetap bisa menyedot kursi subholding
        # hanya karena barisnya banyak -- dan jumlah baris profesi itu ukuran cakupan
        # geografis (afirmasi pecah per kota), bukan ukuran jumlah orang.
        kolam = {
            "SUBHOLDING": ([p for p in layak if p["penempatan"] == "SUBHOLDING"], info["sub_diterima"]),
            "INDUK": ([p for p in layak if p["penempatan"] == "INDUK"], info["induk_diterima"]),
        }
        if not kolam["SUBHOLDING"][0] and info["sub_diterima"]:
            # Tahun tanpa satu pun entri penempatan subholding di katalog (2019, 2023):
            # kursinya dilebur ke kolam induk daripada hilang.
            kolam = {"INDUK": (kolam["INDUK"][0], target)}
        for anggota, jatah in kolam.values():
            if not anggota:
                continue
            bobot = [mix.get(p["jenjang"], 0.01)
                     / max(1, sum(1 for q in anggota if q["jenjang"] == p["jenjang"]))
                     for p in anggota]
            for p, v in zip(anggota, bagi_sisa_terbesar(bobot, jatah)):
                p["diterima_target"] = v
        for p in daftar:
            p.setdefault("diterima_target", 0)
            # `kuota` sengaja disamakan dengan diterima. Tidak ada satu pun sumber yang
            # memuat kuota per profesi (F-017/F-027/F-043), jadi membedakan keduanya
            # berarti mengarang laju pemenuhan yang tidak punya jangkar.
            p["kuota"] = p["diterima_target"]
        n_gel = len({p["gelombang_id"] for p in daftar})
        n_pro = len({p["program_id"] for p in daftar})
        print(f"    {tahun:4d} {n_gel:4d} {n_pro:5d} {len(daftar):8d} "
              f"{info['induk_diterima']:6,} {info['sub_diterima']:5,} {target:6,}")

    # ---- ringkasan gelombang ----
    for g in gelombang:
        pro = [p for p in profesi_baris if p["gelombang_id"] == g["gelombang_id"]]
        g["n_program"] = len(per_gelombang[g["gelombang_id"]])
        g["n_profesi"] = len(pro)
        g["diterima_target"] = sum(p["diterima_target"] for p in pro)
        g["tgl_buka"] = min((p["tgl_buka"] for p in pro if p["tgl_buka"]), default="")
        g["tgl_tutup"] = max((p["tgl_tutup"] for p in pro if p["tgl_tutup"]), default="")

    # ---- diagnostik: di mana katalog tidak sanggup menopang kohort ----
    # Bukan cacat generator, melainkan temuan tentang DATANYA. Kalau katalog satu tahun
    # tidak memuat program berjenjang tertentu, bauran demografi tahun itu mustahil
    # tercapai -- dan seluruh kursi jenjang lain menumpuk di segelintir gelombang.
    print("\n  ! Diagnostik keterbatasan katalog:")
    ada_masalah = False
    for tahun, daftar in sorted(per_tahun.items()):
        mix = bauran_jenjang(R, tahun)
        tersedia = {p["jenjang"] for p in daftar if p["jenis_program"] != "PRO_HIRE"}
        hilang = [j for j, v in mix.items() if v > 0 and j not in tersedia]
        per_gel = defaultdict(int)
        for p in daftar:
            per_gel[p["gelombang_id"]] += p["diterima_target"]
        tot = sum(per_gel.values()) or 1
        gid, terbesar = max(per_gel.items(), key=lambda kv: kv[1])
        if hilang or terbesar / tot > 0.75:
            ada_masalah = True
            catatan = []
            if hilang:
                catatan.append(f"katalog tidak punya program {'/'.join(hilang)}")
            if terbesar / tot > 0.75:
                catatan.append(f"{terbesar / tot:.0%} kursi menumpuk di {gid}")
            print(f"    {tahun}: " + "; ".join(catatan))
    if not ada_masalah:
        print("    (tidak ada)")

    total = sum(g["diterima_target"] for g in gelombang)
    target = sum(i["induk_diterima"] + i["sub_diterima"] for i in koh.values())
    print(f"\n  Total diterima {total:,} vs kohort Group {target:,} "
          f"(selisih {total - target:+,})")

    nyata = sum(1 for p in profesi_baris if p["status_sumber"] == "NYATA")
    print(f"  Profesi dari sumber asli: {nyata:,} dari {len(profesi_baris):,} "
          f"({nyata / len(profesi_baris):.0%})")
    dikarang = [p for p in program_baris if p["sumber_judul"] == "tidak_terekam"]
    print(f"  Program tanpa judul asli: {len(dikarang)} "
          f"(diberi penanda '{TANPA_JUDUL}', bukan judul karangan)")

    print()
    tulis(MASTER / "gelombang.csv",
          ["gelombang_id", "angkatan", "seri", "sumber_nomor", "tahun_program", "tahun_masuk",
           "nama_gelombang", "jenis_program", "sumber_rekrutmen", "kualitas_kohort",
           "tgl_buka", "tgl_tutup", "n_program", "n_profesi", "diterima_target"], gelombang)
    tulis(MASTER / "program.csv",
          ["program_id", "gelombang_id", "angkatan", "tahun_program", "judul", "sumber_judul",
           "jenis_program", "perusahaan_penempatan", "lokasi_tes", "status",
           "tgl_buka", "tgl_tutup", "pdf_brosur"], program_baris)
    tulis(MASTER / "profesi.csv",
          ["profesi_id", "program_id", "gelombang_id", "angkatan", "tahun_program",
           "kode_profesi", "nama_profesi", "jenjang", "kota_rekrutmen", "tgl_buka", "tgl_tutup",
           "min_ipk", "umur_maks", "sumber_rekrutmen", "jenis_program", "penempatan", "status_sumber",
           "kuota", "diterima_target"], profesi_baris)
    tulis(MASTER / "profesi_prodi.csv", ["profesi_id", "program_studi", "min_ipk"], prodi_baris)
    return 0


if __name__ == "__main__":
    sys.exit(main())
