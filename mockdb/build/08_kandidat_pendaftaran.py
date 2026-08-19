"""Kandidat (akun lifetime) & pendaftaran: siapa yang melamar, dan apa hasilnya.

Urutan kausal (rules/README.md): kohort (diterima, nyata) -> funnel (berapa harus
mendaftar) -> demografi (siapa mereka) -> administrasi (siapa gugur, KENAPA).
Skrip ini mengeksekusi urutan itu SUNGGUHAN per kandidat, bukan mengundi label:

  1. `diterima_target` per profesi (dari langkah 06) DIKURANGI dulu porsi ikatan
     dinas per tahun (F-078) -- ikatan dinas TIDAK PERNAH mendaftar (funnel.yaml:
     funnel_ikatan_dinas.pendaftaran = tidak_ada), jadi harus dikeluarkan sebelum
     dipakai membalik hitung jumlah pendaftar.
  2. Jumlah pendaftar per profesi = diterima_pendaftaran / end_to_end_pct arketipe
     funnel (nasional_mandiri / afirmasi_remote / rbb -- F-064, F-075).
  3. Untuk jalur MANDIRI: biodata (umur, IPK, prodi, status kawin, kelengkapan
     berkas) dibangkitkan dulu dari demografi.yaml (dikalibrasi supaya laju lulus
     administrasi ALAMI mendekati 64%), lalu kriteria administrasi.yaml DIJALANKAN
     SUNGGUHAN -- alasan_gagal bukan label tempelan. Sisa pendaftar yang lulus
     administrasi disebar ke tahap berikutnya (adaptif..wawancara) memakai proporsi
     funnel, KECUALI persis `diterima_pendaftaran` yang dipaksa ke hasil DITERIMA
     (itu jangkar kerasnya).
  4. Untuk jalur RBB: tidak ada tahap administrasi PLN (titik masuk = akademik_
     inggris, F-046) -- langsung disebar 4 tahap PLN via proporsi funnel_rbb.
  5. Pendaftaran dikelompokkan jadi akun KANDIDAT (lifetime, F-025) memakai sebaran
     `lamaran_per_akun`, dengan batas 1 profesi per gelombang per akun. Ditambah
     akun yang tak pernah melamar (`akun_tanpa_lamaran`).
  6. Sub-tabel kandidat_pendidikan/sertifikasi/keluarga/berkas dibangkitkan memakai
     kurva kelengkapan.yaml PER TAHUN (jangan mengisi mundur) -- jalur RBB kena
     pengali 0,75 & berkas_unggahan permanen kosong (kelengkapan.yaml per_jalur.rbb).

Input  : rules/{kohort,funnel,demografi,administrasi,kelengkapan}.yaml
         out/master/{profesi,gelombang,program_studi,profesi_prodi}.csv
Output : out/master/{kandidat,pendaftaran,kandidat_pendidikan,kandidat_sertifikasi,
                      kandidat_keluarga,kandidat_berkas}.csv

Jalankan: python mockdb/build/08_kandidat_pendaftaran.py
"""
from __future__ import annotations

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

SEED = 20260915
rng = np.random.default_rng(SEED)

JENJANG_SINGKAT = {"SMK": "SMK", "D-III": "D3", "S1/D-IV": "S1", "S2": "S2"}
AFIRMASI_REGION = {"81": "OAP", "86": "MALUKU_NUSRA", "91": "OAP"}  # F-006, dicek manual dari kota_rekrutmen

PROVINSI_NASIONAL = [  # bobot kasar condong Jawa -- proksi ASUMSI, unit_induk.csv tak punya kolom provinsi
    ("Jawa Barat", 16), ("Jawa Timur", 15), ("Jawa Tengah", 13), ("DKI Jakarta", 9),
    ("Banten", 6), ("Sumatera Utara", 6), ("Sumatera Selatan", 3), ("Sumatera Barat", 3),
    ("Riau", 3), ("Lampung", 3), ("Kalimantan Timur", 3), ("Kalimantan Selatan", 2),
    ("Kalimantan Barat", 2), ("Sulawesi Selatan", 4), ("Sulawesi Utara", 2), ("Bali", 3),
    ("Nusa Tenggara Barat", 2), ("Nusa Tenggara Timur", 2), ("Aceh", 2), ("Jambi", 1),
    ("Bengkulu", 1), ("Kepulauan Riau", 1), ("Kalimantan Tengah", 1), ("Sulawesi Tengah", 1),
    ("Sulawesi Tenggara", 1), ("Gorontalo", 1), ("Sulawesi Barat", 1), ("Maluku", 1),
    ("Maluku Utara", 1), ("Papua", 1), ("DI Yogyakarta", 2),
]
PROV_OAP = ["Papua", "Papua Barat", "Papua Selatan", "Papua Tengah", "Papua Pegunungan", "Papua Barat Daya"]
PROV_MALUKU_NUSRA = ["Maluku", "Maluku Utara", "Nusa Tenggara Timur", "Nusa Tenggara Barat"]

NAMA_DEPAN_P = ["Ahmad", "Budi", "Dedi", "Eko", "Fajar", "Gilang", "Hendra", "Irfan", "Joko", "Kurniawan",
                "Lukman", "Muhammad", "Nanda", "Oki", "Putra", "Rian", "Satria", "Taufik", "Umar", "Wahyu",
                "Yusuf", "Zulkifli", "Agus", "Bayu", "Candra", "Dimas", "Firman", "Guntur", "Hadi", "Ivan"]
NAMA_DEPAN_W = ["Ayu", "Bella", "Citra", "Dewi", "Eka", "Fitri", "Gita", "Hana", "Indah", "Juwita",
                "Kartika", "Lestari", "Mega", "Nadia", "Oktavia", "Putri", "Ratna", "Sari", "Tantri", "Utami",
                "Vina", "Wulan", "Yuni", "Zahra", "Anisa", "Bunga", "Cahya", "Dinda", "Erika", "Farah"]
NAMA_BELAKANG = ["Saputra", "Wijaya", "Kusuma", "Pratama", "Santoso", "Setiawan", "Nugroho", "Hidayat",
                  "Firmansyah", "Ramadhan", "Gunawan", "Susanto", "Halim", "Permata", "Handayani", "Wardani",
                  "Simanjuntak", "Sitorus", "Situmorang", "Panjaitan", "Siregar", "Manik", "Silalahi",
                  "Tampubolon", "Purnomo", "Wibowo", "Prasetyo", "Nurhayati", "Ningsih", "Rahayu"]
STREET = ["Merdeka", "Sudirman", "Diponegoro", "Ahmad Yani", "Gatot Subroto", "Veteran", "Pahlawan",
          "Kartini", "Melati", "Mawar", "Anggrek", "Cendana", "Flamboyan", "Kenanga", "Cempaka"]
EMAIL_DOMAIN = [("gmail.com", 70), ("yahoo.com", 15), ("outlook.com", 8), ("ymail.com", 5), ("rocketmail.com", 2)]


def baca_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def muat_yaml(nama: str) -> dict:
    return yaml.safe_load((RULES / nama).read_text(encoding="utf-8"))


def weighted_choice_table(pairs: list[tuple]) -> tuple[list, np.ndarray]:
    keys = [p[0] for p in pairs]
    w = np.array([p[1] for p in pairs], dtype=float)
    return keys, w / w.sum()


def largest_remainder(bobot: list[float], total: int) -> list[int]:
    s = sum(bobot)
    if s <= 0 or total <= 0:
        return [0] * len(bobot)
    raw = [b * total / s for b in bobot]
    base = [int(x) for x in raw]
    sisa = total - sum(base)
    order = sorted(range(len(raw)), key=lambda i: -(raw[i] - base[i]))
    for i in order[:sisa]:
        base[i] += 1
    return base


def beta_ab_dari_moment(mean: float, sd: float) -> tuple[float, float]:
    var = sd * sd
    common = mean * (1 - mean) / var - 1
    return max(mean * common, 0.5), max((1 - mean) * common, 0.5)


def acak_tanggal(mulai: str, akhir: str, n: int) -> list[str]:
    d0 = dt.date.fromisoformat(mulai)
    d1 = dt.date.fromisoformat(akhir)
    span = max((d1 - d0).days, 0)
    offs = rng.integers(0, span + 1, size=n) if span > 0 else np.zeros(n, dtype=int)
    return [(d0 + dt.timedelta(days=int(o))).isoformat() for o in offs]


def singkat_prodi(nama: str) -> str:
    kata = "".join(ch for ch in nama.upper() if ch.isalnum() or ch == " ").split()
    return (kata[0][:3] if kata else "UMU")


def buat_nama(gender: np.ndarray) -> list[str]:
    out = []
    for g in gender:
        depan = NAMA_DEPAN_P if g == "P" else NAMA_DEPAN_W
        out.append(f"{depan[rng.integers(len(depan))]} {NAMA_BELAKANG[rng.integers(len(NAMA_BELAKANG))]}")
    return out


print("Langkah 08: kandidat & pendaftaran\n")

R = {p.stem: muat_yaml(p.name) for p in RULES.glob("*.yaml")}
kohort = R["kohort"]["kohort_per_tahun_program"]
demografi = R["demografi"]
administrasi = R["administrasi"]
kelengkapan = R["kelengkapan"]
funnel = R["funnel"]

profesi = baca_csv(MASTER / "profesi.csv")
prodi_katalog = [r for r in baca_csv(MASTER / "program_studi.csv") if int(r["n_profesi"]) > 0 or int(r["n_program"]) > 0]
profesi_prodi_rows = baca_csv(MASTER / "profesi_prodi.csv")

# ---------------------------------------------------------------------------
# 1. Katalog prodi (49, F-004) + bobot + peta bidang
# ---------------------------------------------------------------------------
BOBOT_TERATAS = demografi["program_studi"]["bobot_teratas"]
prodi_nama = [r["program_studi"] for r in prodi_katalog]
prodi_bidang = {r["program_studi"]: r["bidang"] for r in prodi_katalog}
prodi_bobot = np.array([BOBOT_TERATAS.get(p, 3) for p in prodi_nama], dtype=float)
prodi_bobot /= prodi_bobot.sum()

profesi_prodi: dict[str, dict[str, float]] = defaultdict(dict)
for r in profesi_prodi_rows:
    profesi_prodi[r["profesi_id"]][r["program_studi"]] = float(r["min_ipk"])

PAYUNG_BIDANG = {"PROGRAM STUDI LAINNYA TEKNIK": "TEKNIK", "PROGRAM STUDI LAINNYA NON TEKNIK": "NON-TEKNIK"}


def sesuai_set(profesi_id: str) -> tuple[set[str], set[str]]:
    """(prodi literal diterima, bidang diterima lewat payung)."""
    daftar = profesi_prodi.get(profesi_id, {})
    literal = set(daftar) - set(PAYUNG_BIDANG)
    bidang = {PAYUNG_BIDANG[p] for p in daftar if p in PAYUNG_BIDANG}
    return literal, bidang


# ---------------------------------------------------------------------------
# 2. diterima_target -> diterima_pendaftaran (kurangi porsi ikatan dinas -- F-078)
# ---------------------------------------------------------------------------
ikatan_dinas_per_tahun: dict[int, int] = {}
for row in kohort:
    ikatan_dinas_per_tahun[row["tahun"]] = sum(
        k["diterima"] for k in row.get("komposisi_jalur", []) if k["sumber"] == "ikatan_dinas"
    )

per_tahun_rows: dict[int, list[dict]] = defaultdict(list)
for p in profesi:
    if int(p["diterima_target"]) > 0:
        per_tahun_rows[int(p["tahun_program"])].append(p)

diterima_pendaftaran: dict[str, int] = {}
for tahun, rows in per_tahun_rows.items():
    total = sum(int(r["diterima_target"]) for r in rows)
    idn = ikatan_dinas_per_tahun.get(tahun, 0)
    keep = max(0, total - idn)
    if idn == 0:
        for r in rows:
            diterima_pendaftaran[r["profesi_id"]] = int(r["diterima_target"])
    else:
        bobot = [int(r["diterima_target"]) for r in rows]
        hasil = largest_remainder(bobot, keep)
        for r, v in zip(rows, hasil):
            diterima_pendaftaran[r["profesi_id"]] = v

total_dp = sum(diterima_pendaftaran.values())
print(f"  diterima_pendaftaran total (setelah kurangi ikatan dinas {sum(ikatan_dinas_per_tahun.values())}): {total_dp}")
assert total_dp == funnel["volume_target"]["status_per_15sep2026"]["lulus_wawancara"], "harus = lulus_wawancara F-075"

# ---------------------------------------------------------------------------
# 3. Struktur funnel per arketipe
# ---------------------------------------------------------------------------
peta_arketipe = funnel["pemilihan_arketipe"]["peta"]
default_residu = funnel["pemilihan_arketipe"]["default_residu"]
funnel_mandiri = funnel["funnel_mandiri"]
funnel_rbb_tahapan = funnel["funnel_rbb"]["pln_per_kandidat"]["tahapan"]

cum = 1.0
RBB_STAGES: list[tuple[str, float]] = []
for t in funnel_rbb_tahapan:
    cum *= t["hadir_pct"] * t["lulus_pct"]
    RBB_STAGES.append((t["tahap"], cum))
END_RBB = RBB_STAGES[-1][1]


def stages_mandiri(arketipe: str) -> list[tuple[str, float]]:
    return [(t["tahap"], t["multiplier_lulus"]) for t in funnel_mandiri[arketipe]["tahapan"]]


# ---------------------------------------------------------------------------
# 4. Kurva kelengkapan & administrasi
# ---------------------------------------------------------------------------
KUALITAS_KOHORT = kelengkapan["kualitas_kohort"]
BLOK = kelengkapan["blok"]
PENGALI_RBB = kelengkapan["per_jalur"]["rbb"]["pengali_kelengkapan_biodata"]
FIELD_KOSONG_RBB = set(kelengkapan["per_jalur"]["rbb"]["field_kosong_permanen"])

UMUR_MAKS = administrasi["umur_maks_saat_daftar"]
IPK_MIN = administrasi["ipk_min"]
STATUS_SEBARAN = demografi["status_perkawinan"]["sebaran_pelamar"]
USIA = demografi["usia_saat_daftar"]
IPK_CFG = demografi["ipk"]
IPK_A, IPK_B = beta_ab_dari_moment(
    (IPK_CFG["rata2"] - IPK_CFG["rentang"][0]) / (IPK_CFG["rentang"][1] - IPK_CFG["rentang"][0]),
    IPK_CFG["sd"] / (IPK_CFG["rentang"][1] - IPK_CFG["rentang"][0]),
)


def prob_lengkap(blok_nama: str, tahun: int, jalur: str) -> float:
    p = BLOK[blok_nama]["per_tahun"][tahun]
    return p * PENGALI_RBB if jalur == "rbb" else p


# ===========================================================================
# 5. LOOP UTAMA per profesi -- bangun "slot" pendaftaran
# ===========================================================================
slot_cols = ["profesi_id", "gelombang_id", "angkatan", "tahun_program", "jalur", "jenis_program",
             "jenjang", "sumber_prodi", "ipk", "status_perkawinan", "berkas_lengkap", "umur", "gender",
             "alasan_gagal", "tahap_gugur", "hasil_akhir", "titik_masuk", "kode_profesi",
             "tgl_buka", "tgl_tutup", "is_afirmasi"]
slots: dict[str, list] = {c: [] for c in slot_cols}

n_profesi_diproses = 0
for p in profesi:
    dp = diterima_pendaftaran.get(p["profesi_id"], 0)
    if dp <= 0:
        continue
    n_profesi_diproses += 1
    jalur = p["sumber_rekrutmen"]
    jenis = p["jenis_program"]
    is_afirmasi = jenis == "AFIRMASI"
    jenjang = p["jenjang"]
    tahun = int(p["tahun_program"])

    if jalur == "mandiri":
        arketipe = peta_arketipe.get(jenis, default_residu)
        stages = stages_mandiri(arketipe)
    else:
        arketipe = "rbb"
        stages = RBB_STAGES
    end_to_end = stages[-1][1]
    n_pendaftar = max(dp, round(dp / end_to_end))

    literal_ok, bidang_ok = sesuai_set(p["profesi_id"])
    umur_maks = int(p["umur_maks"]) if p["umur_maks"] else 99
    ipk_min_fallback = float(p["min_ipk"]) if p["min_ipk"] else IPK_MIN["default"]
    if is_afirmasi:
        ipk_min_fallback = min(ipk_min_fallback, 2.50)

    # --- biodata vektor untuk n_pendaftar slot ---
    usia_cfg = USIA.get(jenjang, USIA["S1/D-IV"])
    umur = rng.normal(usia_cfg["mode"], usia_cfg["sd"], n_pendaftar)
    umur = np.clip(np.round(umur), usia_cfg["min"], usia_cfg["maks"]).astype(int)

    ipk = IPK_CFG["rentang"][0] + rng.beta(IPK_A, IPK_B, n_pendaftar) * (IPK_CFG["rentang"][1] - IPK_CFG["rentang"][0])
    ipk = np.round(ipk, 2)

    marital_keys, marital_w = weighted_choice_table(list(STATUS_SEBARAN.items()))
    marital = rng.choice(marital_keys, size=n_pendaftar, p=marital_w)

    # prodi: 82% dari set sesuai (literal + payung bidang), 18% dari luar
    luar_pct = demografi["program_studi"]["prodi_di_luar_daftar_pct"]
    idx_sesuai = [i for i, nm in enumerate(prodi_nama) if nm in literal_ok or prodi_bidang.get(nm) in bidang_ok]
    idx_luar = [i for i in range(len(prodi_nama)) if i not in idx_sesuai]
    prodi_idx = np.empty(n_pendaftar, dtype=int)
    if not idx_sesuai:
        # profesi ini tidak punya entri profesi_prodi.csv sama sekali -- tidak ada acuan
        # buat menilai cocok/tidak, jadi jangan dihukum "jurusan_tidak_sesuai" (F-078).
        sesuai_mask = np.ones(n_pendaftar, dtype=bool)
        prodi_idx[:] = rng.choice(len(prodi_nama), size=n_pendaftar, p=prodi_bobot)
    elif not idx_luar:
        sesuai_mask = np.ones(n_pendaftar, dtype=bool)
        w = prodi_bobot[idx_sesuai] / prodi_bobot[idx_sesuai].sum()
        prodi_idx[:] = rng.choice(idx_sesuai, size=n_pendaftar, p=w)
    else:
        sesuai_mask = rng.random(n_pendaftar) >= luar_pct
        w_ok = prodi_bobot[idx_sesuai] / prodi_bobot[idx_sesuai].sum()
        w_luar = prodi_bobot[idx_luar] / prodi_bobot[idx_luar].sum()
        prodi_idx[sesuai_mask] = rng.choice(idx_sesuai, size=sesuai_mask.sum(), p=w_ok)
        prodi_idx[~sesuai_mask] = rng.choice(idx_luar, size=(~sesuai_mask).sum(), p=w_luar)
    sumber_prodi = np.array(prodi_nama)[prodi_idx]

    # gender EMERGES dari bauran bidang prodi (demografi.yaml: "jangan paksa target di
    # sisi pelamar") -- bukan dari target diterima_per_tahun_program.
    gmix = demografi["gender"]["variasi_per_bidang"]
    p_baseline = demografi["gender"]["pelamar"]["P"]
    bidang_slot = np.array([prodi_bidang.get(nm, "") for nm in sumber_prodi])
    p_pria = np.where(bidang_slot == "TEKNIK", gmix["TEKNIK"]["P"],
                       np.where(bidang_slot == "NON-TEKNIK", gmix["NON-TEKNIK"]["P"], p_baseline))
    gender = np.where(rng.random(n_pendaftar) < p_pria, "P", "W")

    berkas_p = prob_lengkap("berkas_dokumen", tahun, jalur)
    berkas_lengkap = rng.random(n_pendaftar) < berkas_p

    if jalur == "mandiri":
        alasan = [[] for _ in range(n_pendaftar)]
        for i in range(n_pendaftar):
            a = alasan[i]
            if umur[i] > umur_maks:
                a.append("umur_melebihi_batas")
            eff_min = profesi_prodi.get(p["profesi_id"], {}).get(sumber_prodi[i], ipk_min_fallback)
            if ipk[i] < eff_min:
                a.append("ipk_di_bawah_minimum")
            if not sesuai_mask[i]:
                a.append("jurusan_tidak_sesuai")
            if marital[i] != "BELUM MENIKAH":
                a.append("status_menikah")
            if not berkas_lengkap[i]:
                a.append("berkas_tidak_lengkap")
        lulus_admin = np.array([len(a) == 0 for a in alasan])

        idx_pass = np.flatnonzero(lulus_admin)
        idx_fail = np.flatnonzero(~lulus_admin)
        if len(idx_pass) < dp:
            # sangat jarang (N kecil) -- longgarkan: paksa cukup banyak status lulus dgn membersihkan alasan
            kurang = dp - len(idx_pass)
            tambahan = rng.choice(idx_fail, size=min(kurang, len(idx_fail)), replace=False) if len(idx_fail) else np.array([], dtype=int)
            for i in tambahan:
                alasan[i] = []
            idx_pass = np.concatenate([idx_pass, tambahan]) if len(tambahan) else idx_pass
            idx_fail = np.array([i for i in idx_fail if i not in set(tambahan.tolist())], dtype=int)

        rng.shuffle(idx_pass)
        idx_diterima = idx_pass[:dp]
        idx_pass_gagal = idx_pass[dp:]

        # sebar sisa admin-pass ke tahap berikutnya (proporsional, ditutup ke jangkar F-019/F-064)
        stage_labels = [s[0] for s in stages[1:]]  # tanpa 'administrasi'
        stage_cum = [s[1] for s in stages]
        deltas = [stage_cum[i] - stage_cum[i + 1] for i in range(len(stage_labels))]
        counts = largest_remainder(deltas, len(idx_pass_gagal))
        pos = 0
        tahap_gugur = np.array([""] * n_pendaftar, dtype=object)
        hasil = np.array([""] * n_pendaftar, dtype=object)
        for lbl, cnt in zip(stage_labels, counts):
            for i in idx_pass_gagal[pos:pos + cnt]:
                tahap_gugur[i] = lbl
                hasil[i] = "GAGAL"
            pos += cnt
        for i in idx_diterima:
            tahap_gugur[i] = ""
            hasil[i] = "DITERIMA"
        for i in idx_fail:
            tahap_gugur[i] = "administrasi"
            hasil[i] = "GAGAL"
        titik_masuk = "administrasi"
        alasan_str = [";".join(a) for a in alasan]
    else:
        idx_all = np.arange(n_pendaftar)
        rng.shuffle(idx_all)
        idx_diterima = idx_all[:dp]
        idx_gagal = idx_all[dp:]
        stage_labels = [s[0] for s in RBB_STAGES]
        stage_cum = [1.0] + [s[1] for s in RBB_STAGES]
        deltas = [stage_cum[i] - stage_cum[i + 1] for i in range(len(stage_labels))]
        counts = largest_remainder(deltas, len(idx_gagal))
        pos = 0
        tahap_gugur = np.array([""] * n_pendaftar, dtype=object)
        hasil = np.array([""] * n_pendaftar, dtype=object)
        for lbl, cnt in zip(stage_labels, counts):
            for i in idx_gagal[pos:pos + cnt]:
                tahap_gugur[i] = lbl
                hasil[i] = "GAGAL"
            pos += cnt
        for i in idx_diterima:
            tahap_gugur[i] = ""
            hasil[i] = "DITERIMA"
        titik_masuk = "akademik_inggris"
        alasan_str = [""] * n_pendaftar  # RBB: administrasi dikerjakan FHCI, tidak dievaluasi di sini (F-046)

    slots["profesi_id"].extend([p["profesi_id"]] * n_pendaftar)
    slots["gelombang_id"].extend([p["gelombang_id"]] * n_pendaftar)
    slots["angkatan"].extend([p["angkatan"]] * n_pendaftar)
    slots["tahun_program"].extend([tahun] * n_pendaftar)
    slots["jalur"].extend([jalur] * n_pendaftar)
    slots["jenis_program"].extend([jenis] * n_pendaftar)
    slots["jenjang"].extend([jenjang] * n_pendaftar)
    slots["sumber_prodi"].extend(sumber_prodi.tolist())
    slots["ipk"].extend(ipk.tolist())
    slots["status_perkawinan"].extend(marital.tolist())
    slots["berkas_lengkap"].extend(berkas_lengkap.tolist())
    slots["umur"].extend(umur.tolist())
    slots["gender"].extend(gender.tolist())
    slots["alasan_gagal"].extend(alasan_str)
    slots["tahap_gugur"].extend(tahap_gugur.tolist())
    slots["hasil_akhir"].extend(hasil.tolist())
    slots["titik_masuk"].extend([titik_masuk] * n_pendaftar)
    slots["kode_profesi"].extend([p["kode_profesi"]] * n_pendaftar)
    slots["tgl_buka"].extend([p["tgl_buka"]] * n_pendaftar)
    slots["tgl_tutup"].extend([p["tgl_tutup"]] * n_pendaftar)
    slots["is_afirmasi"].extend([is_afirmasi] * n_pendaftar)

n_slot = len(slots["profesi_id"])
print(f"  {n_profesi_diproses} profesi diproses -> {n_slot:,} slot pendaftaran")
n_diterima_slot = sum(1 for h in slots["hasil_akhir"] if h == "DITERIMA")
assert n_diterima_slot == total_dp, f"diterima slot {n_diterima_slot} != target {total_dp}"

# ===========================================================================
# 6. Kelompokkan slot -> akun kandidat (lamaran_per_akun, F-025)
# ===========================================================================
sebaran_lamar = funnel["volume_target"]["lamaran_per_akun"]["sebaran"]
lamar_keys, lamar_w = weighted_choice_table([(int(k), v) for k, v in sebaran_lamar.items()])

order = rng.permutation(n_slot)
akun_of_slot = np.full(n_slot, -1, dtype=int)
akun_slots: list[list[int]] = []
current: list[int] = []
current_gel: set[str] = set()
current_target = int(rng.choice(lamar_keys, p=lamar_w))
leftover: list[int] = []

for idx in order:
    gel = slots["gelombang_id"][idx]
    if len(current) < current_target and gel not in current_gel:
        current.append(idx)
        current_gel.add(gel)
    else:
        if current:
            akun_slots.append(current)
        current = [idx]
        current_gel = {gel}
        current_target = int(rng.choice(lamar_keys, p=lamar_w))
if current:
    akun_slots.append(current)

for akun_id, idxs in enumerate(akun_slots):
    for i in idxs:
        akun_of_slot[i] = akun_id

n_akun_melamar = len(akun_slots)
print(f"  {n_akun_melamar:,} akun dgn >=1 lamaran (target rata2 {funnel['volume_target']['lamaran_per_akun']['rata2']}, "
      f"aktual {n_slot / n_akun_melamar:.2f})")

# anchor = slot bertahun paling awal per akun
anchor_of_akun = []
for idxs in akun_slots:
    anchor_of_akun.append(min(idxs, key=lambda i: slots["tahun_program"][i]))

# ===========================================================================
# 7. Akun tanpa lamaran (F-019/F-033)
# ===========================================================================
rasio_tanpa = funnel["volume_target"]["akun_tanpa_lamaran"]["rasio_terhadap_pelamar"]
rincian_tanpa = funnel["volume_target"]["akun_tanpa_lamaran"]["rincian"]
n_tanpa = round(n_akun_melamar * rasio_tanpa)
print(f"  {n_tanpa:,} akun tanpa lamaran (rasio {rasio_tanpa})")

tahun_list = sorted(per_tahun_rows.keys())
bobot_tahun = np.array([sum(diterima_pendaftaran.get(r["profesi_id"], 0) for r in per_tahun_rows[t]) for t in tahun_list], dtype=float)
bobot_tahun = np.maximum(bobot_tahun, 1.0)
bobot_tahun /= bobot_tahun.sum()
tahun_tanpa = rng.choice(tahun_list, size=n_tanpa, p=bobot_tahun)

n_kandidat = n_akun_melamar + n_tanpa
print(f"  total kandidat (akun): {n_kandidat:,}")

# ===========================================================================
# 8. Tabel KANDIDAT
# ===========================================================================
jenjang_per_tahun = demografi["jenjang_pelamar"]["per_tahun_program"]

anchor_tahun = np.array(
    [slots["tahun_program"][i] for i in anchor_of_akun] + tahun_tanpa.tolist(), dtype=int
)
anchor_jalur = np.array(
    [slots["jalur"][i] for i in anchor_of_akun] + ["mandiri"] * n_tanpa, dtype=object
)
anchor_jenjang = np.array(
    [slots["jenjang"][i] for i in anchor_of_akun]
    + list(rng.choice(list(JENJANG_SINGKAT.keys()), size=n_tanpa,
                       p=[demografi["jenjang_pelamar"][k] for k in JENJANG_SINGKAT])),
    dtype=object,
)
anchor_umur = np.array(
    [slots["umur"][i] for i in anchor_of_akun]
    + [int(np.clip(rng.normal(USIA[j]["mode"], USIA[j]["sd"]), USIA[j]["min"], USIA[j]["maks"])) for j in anchor_jenjang[n_akun_melamar:]],
    dtype=int,
)
anchor_afirmasi = np.array(
    [bool(slots["is_afirmasi"][i]) for i in anchor_of_akun] + [False] * n_tanpa
)
anchor_gel_afirmasi = np.array(
    [slots["angkatan"][i] if slots["is_afirmasi"][i] else "" for i in anchor_of_akun] + [""] * n_tanpa,
    dtype=object,
)
pernah_melamar = np.array([True] * n_akun_melamar + [False] * n_tanpa)

# jenis_kelamin: akun pernah-melamar mewarisi gender slot anchornya (sudah emergent dari
# bauran bidang prodi -- lihat langkah 5); akun tanpa lamaran pakai baseline pelamar flat
# (tidak terikat prodi/profesi apa pun, karena memang tidak pernah melamar).
p_baseline = demografi["gender"]["pelamar"]["P"]
gender = np.array(
    [slots["gender"][i] for i in anchor_of_akun]
    + list(np.where(rng.random(n_tanpa) < p_baseline, "P", "W")),
    dtype=object,
)
nama_lengkap = buat_nama(gender)

domain, domain_w = weighted_choice_table(EMAIL_DOMAIN)
email_domain = rng.choice(domain, size=n_kandidat, p=domain_w)
email = [f"{nama_lengkap[i].lower().replace(' ', '.')}{rng.integers(1, 999)}@{email_domain[i]}" for i in range(n_kandidat)]

no_ktp = ["".join(str(d) for d in rng.integers(0, 10, size=16)) for _ in range(n_kandidat)]
no_hp = ["08" + "".join(str(d) for d in rng.integers(0, 10, size=10)) for _ in range(n_kandidat)]

kota_master = [r["nama"] for r in baca_csv(MASTER / "kota.csv")]
tempat_lahir = rng.choice(kota_master, size=n_kandidat)

tahun_lahir = anchor_tahun - anchor_umur
tanggal_lahir = [f"{int(ty)}-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 29)):02d}" for ty in tahun_lahir]

agama_keys, agama_w = weighted_choice_table(list(demografi["agama"]["sebaran"].items()))
agama = rng.choice(agama_keys, size=n_kandidat, p=agama_w)

marital_keys, marital_w = weighted_choice_table(list(STATUS_SEBARAN.items()))
status_kawin = rng.choice(marital_keys, size=n_kandidat, p=marital_w)

prov_keys, prov_w = weighted_choice_table(PROVINSI_NASIONAL)
prov_domisili = rng.choice(prov_keys, size=n_kandidat, p=prov_w)
kota_domisili = rng.choice(kota_master, size=n_kandidat)

email_aktif = np.ones(n_kandidat, dtype=bool)
sisa = rng.random(n_tanpa)
belum_aktif = sisa < rincian_tanpa["belum_aktivasi_email_pct"]
email_aktif[n_akun_melamar:] = ~belum_aktif

kualitas = [KUALITAS_KOHORT[int(t)]["label"] for t in anchor_tahun]

alamat_domisili = [f"Jl. {STREET[rng.integers(len(STREET))]} No. {rng.integers(1, 200)}" for _ in range(n_kandidat)]
kode_pos = ["".join(str(d) for d in rng.integers(0, 10, size=5)) for _ in range(n_kandidat)]

alamat_p = np.array([prob_lengkap("alamat_domisili", int(t), j) for t, j in zip(anchor_tahun, anchor_jalur)])
punya_alamat = rng.random(n_kandidat) < alamat_p

asal_p = np.array([prob_lengkap("alamat_asal", int(t), j) for t, j in zip(anchor_tahun, anchor_jalur)])
punya_asal = rng.random(n_kandidat) < asal_p
prov_asal = prov_domisili.copy()
for i in range(n_kandidat):
    if anchor_afirmasi[i]:
        region = AFIRMASI_REGION.get(str(anchor_gel_afirmasi[i]), "OAP")
        pilihan = PROV_OAP if region == "OAP" else PROV_MALUKU_NUSRA
        prov_asal[i] = pilihan[rng.integers(len(pilihan))]

fisik_p = np.array([prob_lengkap("fisik_dasar", int(t), j) for t, j in zip(anchor_tahun, anchor_jalur)])
punya_fisik = rng.random(n_kandidat) < fisik_p
fisik_lanjut_p = np.array([prob_lengkap("fisik_lanjut", int(t), j) for t, j in zip(anchor_tahun, anchor_jalur)])
punya_fisik_lanjut = rng.random(n_kandidat) < fisik_lanjut_p

fisik_cfg = demografi["fisik"]
tinggi = np.where(gender == "P",
                   rng.normal(fisik_cfg["tinggi_cm"]["P"]["rata2"], fisik_cfg["tinggi_cm"]["P"]["sd"], n_kandidat),
                   rng.normal(fisik_cfg["tinggi_cm"]["W"]["rata2"], fisik_cfg["tinggi_cm"]["W"]["sd"], n_kandidat))
berat = np.where(gender == "P",
                  rng.normal(fisik_cfg["berat_kg"]["P"]["rata2"], fisik_cfg["berat_kg"]["P"]["sd"], n_kandidat),
                  rng.normal(fisik_cfg["berat_kg"]["W"]["rata2"], fisik_cfg["berat_kg"]["W"]["sd"], n_kandidat))
tinggi = np.clip(np.round(tinggi), 145, 195).astype(int)
berat = np.clip(np.round(berat), 40, 130).astype(int)
bmi = np.round(berat / ((tinggi / 100) ** 2), 1)

ukuran_baju = rng.choice(["S", "M", "L", "XL"], size=n_kandidat)
ukuran_celana = rng.choice(["28", "29", "30", "31", "32", "33", "34"], size=n_kandidat)
ukuran_sepatu = rng.integers(38, 44, size=n_kandidat)

visus_keys, visus_w = weighted_choice_table(list(fisik_cfg["visus"]["sebaran"].items()))
visus_kiri = rng.choice(visus_keys, size=n_kandidat, p=visus_w)
visus_kanan = rng.choice(visus_keys, size=n_kandidat, p=visus_w)
silinder = rng.random(n_kandidat) < fisik_cfg["visus"]["silinder_pct"]
lingkar = np.where(gender == "P",
                    rng.normal(fisik_cfg["lingkar_perut_cm"]["P"]["rata2"], fisik_cfg["lingkar_perut_cm"]["P"]["sd"], n_kandidat),
                    rng.normal(fisik_cfg["lingkar_perut_cm"]["W"]["rata2"], fisik_cfg["lingkar_perut_cm"]["W"]["sd"], n_kandidat))
lingkar = np.round(lingkar).astype(int)
tatto = rng.random(n_kandidat) < fisik_cfg["tato_pct"]
buta_warna_p = np.where(gender == "P", 0.035, 0.004)
buta_warna = rng.random(n_kandidat) < buta_warna_p

tgl_daftar_akun = []
for i in range(n_kandidat):
    if i < n_akun_melamar:
        base = slots["tgl_buka"][anchor_of_akun[i]]
    else:
        base = f"{int(anchor_tahun[i])}-01-01"
    d0 = dt.date.fromisoformat(base) if base else dt.date(int(anchor_tahun[i]), 1, 1)
    off = int(rng.integers(-30, 1))
    tgl_daftar_akun.append((d0 + dt.timedelta(days=off)).isoformat())

print("  menulis kandidat.csv ...")
with (MASTER / "kandidat.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kandidat_id", "nama_lengkap", "email", "no_ktp", "no_handphone", "tempat_lahir",
                "tanggal_lahir", "jenis_kelamin", "agama", "status_perkawinan",
                "alamat_domisili", "kota_domisili", "propinsi_domisili", "kode_pos_domisili",
                "alamat_asal", "kota_asal", "propinsi_asal",
                "ukuran_baju", "ukuran_celana", "ukuran_sepatu", "body_height", "body_weight", "bmi",
                "visus_kiri", "visus_kanan", "tingkat_ketajaman", "silinder", "abdominal_circumference",
                "tatto", "buta_warna", "tanggal_daftar_akun", "email_teraktivasi", "pernah_melamar",
                "kualitas_kohort", "tahun_kohort", "jalur_anchor"])
    for i in range(n_kandidat):
        w.writerow([
            i + 1, nama_lengkap[i], email[i], no_ktp[i], no_hp[i], tempat_lahir[i], tanggal_lahir[i],
            gender[i], agama[i], status_kawin[i],
            alamat_domisili[i] if punya_alamat[i] else "", kota_domisili[i] if punya_alamat[i] else "",
            prov_domisili[i] if punya_alamat[i] else "", kode_pos[i] if punya_alamat[i] else "",
            alamat_domisili[i] if punya_asal[i] else "", kota_domisili[i] if punya_asal[i] else "",
            prov_asal[i] if punya_asal[i] else "",
            ukuran_baju[i] if punya_fisik[i] else "", ukuran_celana[i] if punya_fisik[i] else "",
            ukuran_sepatu[i] if punya_fisik[i] else "", tinggi[i] if punya_fisik[i] else "",
            berat[i] if punya_fisik[i] else "", bmi[i] if punya_fisik[i] else "",
            visus_kiri[i] if punya_fisik_lanjut[i] else "", visus_kanan[i] if punya_fisik_lanjut[i] else "",
            ("SILINDER" if silinder[i] else "NORMAL") if punya_fisik_lanjut[i] else "",
            silinder[i] if punya_fisik_lanjut[i] else "",
            lingkar[i] if punya_fisik_lanjut[i] else "", tatto[i] if punya_fisik_lanjut[i] else "",
            buta_warna[i] if punya_fisik_lanjut[i] else "",
            tgl_daftar_akun[i], bool(email_aktif[i]), bool(pernah_melamar[i]), kualitas[i],
            int(anchor_tahun[i]), anchor_jalur[i],
        ])
print(f"  tulis kandidat.csv  ({n_kandidat:,} baris)")

# ===========================================================================
# 9. Tabel PENDAFTARAN
# ===========================================================================
print("  menulis pendaftaran.csv ...")
urut_counter = 0
with (MASTER / "pendaftaran.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pendaftaran_id", "kandidat_id", "profesi_id", "gelombang_id", "nomor_tes", "tanggal_lamar",
                "status_lamaran", "sumber_rekrutmen", "titik_masuk", "hasil_akhir", "tahap_gugur", "alasan_gagal"])
    for akun_id, idxs in enumerate(akun_slots):
        kandidat_id = akun_id + 1
        for i in idxs:
            urut_counter += 1
            kode = str(slots["kode_profesi"][i])
            sh = kode.split(".")[0] if kode.split(".")[0].isalpha() else "PLN"
            jj = JENJANG_SINGKAT.get(slots["jenjang"][i], "S1")
            js = singkat_prodi(slots["sumber_prodi"][i])
            tgl = acak_tanggal(slots["tgl_buka"][i] or f"{slots['tahun_program'][i]}-01-01",
                                slots["tgl_tutup"][i] or f"{slots['tahun_program'][i]}-12-31", 1)[0]
            yymm = tgl[2:4] + tgl[5:7]
            nomor_tes = f"{yymm}/{sh}/{slots['angkatan'][i]}/{jj}-{js}/{urut_counter:06d}"
            w.writerow([
                f"REG{urut_counter:07d}", kandidat_id, slots["profesi_id"][i], slots["gelombang_id"][i],
                nomor_tes, tgl, "SELESAI", slots["jalur"][i], slots["titik_masuk"][i],
                slots["hasil_akhir"][i], slots["tahap_gugur"][i], slots["alasan_gagal"][i],
            ])
print(f"  tulis pendaftaran.csv  ({n_slot:,} baris)")

# ===========================================================================
# 10. Sub-tabel kandidat: pendidikan, sertifikasi, keluarga, berkas
# ===========================================================================
BARIS_PENDIDIKAN = demografi["pendidikan"]["baris_per_kandidat"]
UNIV = ["Universitas Indonesia", "Institut Teknologi Bandung", "Universitas Gadjah Mada",
        "Universitas Brawijaya", "Universitas Diponegoro", "Universitas Sumatera Utara",
        "Universitas Hasanuddin", "Institut Teknologi Sepuluh Nopember", "Universitas Padjadjaran",
        "Universitas Andalas", "Politeknik Negeri Jakarta", "Politeknik Negeri Bandung",
        "Universitas Negeri Yogyakarta", "Universitas Airlangga", "Universitas Sriwijaya"]
SMA_LIST = ["SMA Negeri 1", "SMA Negeri 2", "SMA Negeri 3", "SMK Negeri 1", "SMK Negeri 2"]

print("  menulis kandidat_pendidikan.csv ...")
with (MASTER / "kandidat_pendidikan.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kandidat_id", "degree", "sekolah_universitas", "program_studi", "skhu_ipk",
                "pendidikan_terakhir", "tahun_masuk", "tahun_lulus"])
    for i in range(n_kandidat):
        kid = i + 1
        tahun = int(anchor_tahun[i])
        jalur = anchor_jalur[i]
        jenjang = anchor_jenjang[i]
        if i < n_akun_melamar:
            prodi_i = slots["sumber_prodi"][anchor_of_akun[i]]
            ipk_i = slots["ipk"][anchor_of_akun[i]]
        else:
            prodi_i = prodi_nama[int(rng.choice(len(prodi_nama), p=prodi_bobot))]
            ipk_i = round(IPK_CFG["rentang"][0] + rng.beta(IPK_A, IPK_B) * (IPK_CFG["rentang"][1] - IPK_CFG["rentang"][0]), 2)
        lama = {"S2": 2, "S1/D-IV": 4, "D-III": 3, "SMK": 3}.get(jenjang, 4)
        tahun_lulus_tinggi = tahun
        tahun_masuk_tinggi = tahun - lama
        if rng.random() < prob_lengkap("pendidikan_tinggi", tahun, jalur):
            w.writerow([kid, jenjang, UNIV[rng.integers(len(UNIV))], prodi_i, ipk_i, True,
                        tahun_masuk_tinggi, tahun_lulus_tinggi])
        if rng.random() < prob_lengkap("pendidikan_dasar", tahun, jalur):
            w.writerow([kid, "SMA/SMK", SMA_LIST[rng.integers(len(SMA_LIST))], "", "", False,
                        tahun_masuk_tinggi - 3, tahun_masuk_tinggi])
            if BARIS_PENDIDIKAN.get(jenjang, 4) >= 4:
                w.writerow([kid, "SMP", f"SMP Negeri {rng.integers(1, 20)}", "", "", False,
                            tahun_masuk_tinggi - 6, tahun_masuk_tinggi - 3])
                w.writerow([kid, "SD", f"SD Negeri {rng.integers(1, 30)}", "", "", False,
                            tahun_masuk_tinggi - 12, tahun_masuk_tinggi - 6])
print("  selesai kandidat_pendidikan.csv")

print("  menulis kandidat_sertifikasi.csv ...")
KATEGORI_SERT = demografi["sertifikasi"]["kategori_umum"]
with (MASTER / "kandidat_sertifikasi.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kandidat_id", "kategori_sertifikasi", "tahun", "skor"])
    for i in range(n_kandidat):
        kid = i + 1
        tahun = int(anchor_tahun[i])
        jalur = anchor_jalur[i]
        if rng.random() < prob_lengkap("sertifikasi", tahun, jalur):
            n_baris = int(rng.integers(1, 4))
            for _ in range(n_baris):
                kat = KATEGORI_SERT[rng.integers(len(KATEGORI_SERT))]
                skor = int(rng.integers(60, 100)) if kat != "Sertifikasi K3" else ""
                w.writerow([kid, kat, tahun - int(rng.integers(0, 3)), skor])
print("  selesai kandidat_sertifikasi.csv")

print("  menulis kandidat_keluarga.csv ...")
HUBUNGAN = demografi["kontak_keluarga"]["hubungan"]
PEKERJAAN = ["Wiraswasta", "PNS", "Karyawan Swasta", "Petani", "Ibu Rumah Tangga", "Pensiunan", "Guru", "Buruh"]
with (MASTER / "kandidat_keluarga.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kandidat_id", "hubungan_keluarga", "alamat", "no_telp", "pekerjaan"])
    for i in range(n_kandidat):
        kid = i + 1
        tahun = int(anchor_tahun[i])
        jalur = anchor_jalur[i]
        if rng.random() < prob_lengkap("kontak_keluarga", tahun, jalur):
            n_baris = int(rng.integers(1, 3))
            hub_pilih = rng.choice(HUBUNGAN, size=n_baris, replace=False) if n_baris <= len(HUBUNGAN) else rng.choice(HUBUNGAN, size=n_baris)
            for hub in hub_pilih:
                w.writerow([kid, hub, f"Jl. {STREET[rng.integers(len(STREET))]} No. {rng.integers(1, 200)}",
                            "08" + "".join(str(d) for d in rng.integers(0, 10, size=10)),
                            PEKERJAAN[rng.integers(len(PEKERJAAN))]])
print("  selesai kandidat_keluarga.csv")

print("  menulis kandidat_berkas.csv ...")
BERKAS_DOK = [b for b in administrasi["berkas_wajib"] if b["kode"] not in ("swafoto", "foto_full_body", "pasfoto")]
BERKAS_FOTO = [b for b in administrasi["berkas_wajib"] if b["kode"] in ("swafoto", "foto_full_body", "pasfoto")]
with (MASTER / "kandidat_berkas.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["kandidat_id", "kode_berkas", "nama_berkas", "terunggah", "tanggal_unggah", "valid"])
    for i in range(n_akun_melamar):  # hanya yg pernah melamar -- F-046 (RBB: berkas_unggahan permanen kosong)
        kid = i + 1
        tahun = int(anchor_tahun[i])
        jalur = anchor_jalur[i]
        if jalur == "rbb":
            continue
        tgl_ref = slots["tgl_buka"][anchor_of_akun[i]] or f"{tahun}-01-01"
        p_dok = prob_lengkap("berkas_dokumen", tahun, jalur)
        p_foto = prob_lengkap("berkas_foto", tahun, jalur)
        for b in BERKAS_DOK:
            terunggah = rng.random() < p_dok
            valid = terunggah and rng.random() > 0.03
            w.writerow([kid, b["kode"], b["nama"], terunggah,
                        tgl_ref if terunggah else "", valid])
        for b in BERKAS_FOTO:
            terunggah = rng.random() < p_foto
            valid = terunggah and rng.random() > 0.03
            w.writerow([kid, b["kode"], b["nama"], terunggah,
                        tgl_ref if terunggah else "", valid])
print("  selesai kandidat_berkas.csv")

print("\nSelesai langkah 08.")
print(f"  kandidat: {n_kandidat:,} ({n_akun_melamar:,} pernah melamar + {n_tanpa:,} tanpa lamaran)")
print(f"  pendaftaran: {n_slot:,} (diterima {n_diterima_slot:,})")
