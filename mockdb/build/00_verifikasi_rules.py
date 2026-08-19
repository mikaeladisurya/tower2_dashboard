"""Verifikasi silang file aturan di mockdb/rules/.

Aturan tersebar di 9 file YAML dan saling bergantung: kalau ukuran kohort diubah tanpa
menyetel laju funnel, seluruh volume database jadi ngawur tanpa ada yang error. Skrip ini
menangkap hal semacam itu sebelum generator dijalankan.

Jalankan:  python mockdb/build/00_verifikasi_rules.py
Keluar 0 kalau semua cek lulus, 1 kalau ada yang gagal.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

TOL = 5e-4      # toleransi untuk rantai perkalian funnel
TOL_SUM = 5e-3  # toleransi untuk sebaran yang harus berjumlah 1

gagal: list[str] = []


def cek(nama: str, kondisi: bool, detail: str = "") -> None:
    if kondisi:
        print(f"  OK    {nama}" + (f" -- {detail}" if detail else ""))
    else:
        gagal.append(f"{nama}: {detail}")
        print(f"  GAGAL {nama} -- {detail}")


def cek_jumlah_satu(nama: str, sebaran: dict) -> None:
    angka = {k: v for k, v in sebaran.items() if isinstance(v, (int, float))}
    total = sum(angka.values())
    cek(nama, abs(total - 1) < TOL_SUM, f"jumlah = {total:.4f}")


def total_group(R: dict) -> int:
    """Ambil total diterima Group dari totals_cek tanpa mengunci nama kuncinya.

    Kuncinya memuat rentang horison (mis. `group_2019_2025`), jadi ia berubah setiap
    horison digeser. Dicari berdasarkan awalan supaya perluasan horison tidak
    memaksa skrip ini ikut diedit.
    """
    c = R["kohort"]["totals_cek"]
    return next(v for k, v in c.items() if k.startswith("group_"))


def muat() -> dict:
    aturan = {}
    for path in sorted(RULES_DIR.glob("*.yaml")):
        try:
            aturan[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            gagal.append(f"parse {path.name}: {exc}")
            print(f"  GAGAL parse {path.name} -- {exc}")
    return aturan


def cek_kohort(R: dict) -> None:
    print("\n[1] Kohort -- total per tahun cocok dengan totals_cek")
    baris = R["kohort"]["kohort_per_tahun_program"]
    induk = sum(r["induk_diterima"] for r in baris)
    sub = sum(r["sub_diterima"] for r in baris)
    c = R["kohort"]["totals_cek"]
    # Kunci totals_cek memuat rentang horison, mis. `induk_2019_2025`.
    kunci = {k.split("_")[0]: k for k in c if k != "keterangan"}
    cek("induk", induk == c[kunci["induk"]], f"{induk} vs {c[kunci['induk']]}")
    cek("subholding", sub == c[kunci["sub"]], f"{sub} vs {c[kunci['sub']]}")
    cek("group", induk + sub == c[kunci["group"]], f"{induk + sub} vs {c[kunci['group']]}")

    awal_g, akhir_g = R["kohort"]["meta"]["horison_gelombang"]
    cek(
        "nama kunci totals_cek cocok dengan horison gelombang",
        kunci["group"] == f"group_{awal_g}_{akhir_g}",
        kunci["group"],
    )

    tahun = [r["tahun"] for r in baris]
    awal, akhir = R["kohort"]["meta"]["horison"]
    cek("horison lengkap", tahun == list(range(awal, akhir + 1)), f"{tahun}")

    for r in baris:
        if "komposisi_jalur" not in r:
            continue
        komposisi = sum(k["diterima"] for k in r["komposisi_jalur"])
        cek(
            f"komposisi_jalur {r['tahun']} = induk_diterima",
            komposisi == r["induk_diterima"],
            f"{komposisi} vs {r['induk_diterima']}",
        )
        cek(
            f"komposisi_jalur {r['tahun']} semua diterima >= 0",
            all(k["diterima"] >= 0 for k in r["komposisi_jalur"]),
            str([k["diterima"] for k in r["komposisi_jalur"]]),
        )


def rantai_arketipe(nama: str, tahapan: list[dict]) -> float:
    """Kalikan laju tiap tahap dan pastikan cocok dengan multiplier yang tertulis."""
    m = 1.0
    for t in tahapan:
        cek(
            f"[{nama}] multiplier undangan {t['tahap']}",
            abs(m - t["multiplier_undangan"]) < TOL,
            f"hitung {m:.4f} vs tertulis {t['multiplier_undangan']}",
        )
        hadir = t["hadir_pct"]
        m = m * t["lulus_pct"] if hadir is None else m * hadir * t["lulus_pct"]
        cek(
            f"[{nama}] multiplier lulus    {t['tahap']}",
            abs(m - t["multiplier_lulus"]) < TOL,
            f"hitung {m:.4f} vs tertulis {t['multiplier_lulus']}",
        )
    return m


def cek_funnel(R: dict) -> None:
    print("\n[2] Funnel mandiri -- dua arketipe (F-064), nasional_mandiri mendarat di jangkar F-019")
    arketipe = R["funnel"]["funnel_mandiri"]

    m_nasional = rantai_arketipe("nasional_mandiri", arketipe["nasional_mandiri"]["tahapan"])
    jangkar = R["funnel"]["meta"]["jangkar_keras"]
    cek(
        "nasional_mandiri end-to-end = jangkar F-019",
        abs(m_nasional - jangkar["end_to_end_pct"]) < TOL,
        f"{m_nasional:.4f} vs {jangkar['end_to_end_pct']}",
    )
    rasio = R["funnel"]["meta"]["rasio_pelamar_diterima"]
    cek("rasio pelamar:diterima", abs(1 / m_nasional - rasio) < 1.0, f"1:{1 / m_nasional:.0f} vs 1:{rasio}")

    m_afirmasi = rantai_arketipe("afirmasi_remote", arketipe["afirmasi_remote"]["tahapan"])
    cek(
        "afirmasi_remote end-to-end = tertulis (bukan jangkar keras)",
        abs(m_afirmasi - arketipe["afirmasi_remote"]["validasi"]["end_to_end"]) < TOL,
        f"{m_afirmasi:.4f} vs {arketipe['afirmasi_remote']['validasi']['end_to_end']}",
    )
    cek(
        "afirmasi_remote jauh lebih longgar dari nasional_mandiri",
        m_afirmasi > m_nasional * 5,
        f"{m_afirmasi:.4f} vs {m_nasional:.4f}",
    )

    tahap_nasional = [t["tahap"] for t in arketipe["nasional_mandiri"]["tahapan"]]
    tahap_afirmasi = [t["tahap"] for t in arketipe["afirmasi_remote"]["tahapan"]]
    cek("kosakata tahap sama di dua arketipe", tahap_nasional == tahap_afirmasi,
        f"{tahap_nasional} vs {tahap_afirmasi}")

    peta = R["funnel"]["pemilihan_arketipe"]["peta"]
    dikenal = {"nasional_mandiri", "afirmasi_remote"}
    cek("peta arketipe hanya menunjuk arketipe yang ada", set(peta.values()) <= dikenal,
        f"{set(peta.values()) - dikenal}")
    cek("default_residu menunjuk arketipe yang ada",
        R["funnel"]["pemilihan_arketipe"]["default_residu"] in dikenal)

    print("\n[3] Funnel RBB -- rantai laju & rasio gabungan")
    rbb = R["funnel"]["funnel_rbb"]
    m_pln = 1.0
    for t in rbb["pln_per_kandidat"]["tahapan"]:
        m_pln *= t["hadir_pct"] * t["lulus_pct"]
    cek(
        "end-to-end sisi PLN",
        abs(m_pln - rbb["pln_per_kandidat"]["end_to_end_pct"]) < TOL,
        f"hitung {m_pln:.4f} vs tertulis {rbb['pln_per_kandidat']['end_to_end_pct']}",
    )

    ag = rbb["fhci_agregat"]
    m_fhci = 1.0
    for t in ag["tahapan"]:
        m_fhci *= t["lulus_pct"]
    cek(
        "lolos kumulatif FHCI",
        abs(m_fhci - ag["lolos_kumulatif_fhci"]) < TOL,
        f"hitung {m_fhci:.4f} vs tertulis {ag['lolos_kumulatif_fhci']}",
    )
    gabungan = 1 / (m_fhci * m_pln)
    cek(
        "rasio gabungan RBB = rujukan nasional",
        abs(gabungan - ag["rasio_nasional_rujukan"]) < 6,
        f"1:{gabungan:.0f} vs 1:{ag['rasio_nasional_rujukan']} (F-043)",
    )


def cek_volume(R: dict) -> None:
    print("\n[4] Volume -- pendaftaran x laju harus menghasilkan jumlah diterima")
    v = R["funnel"]["volume_target"]
    m = R["funnel"]["meta"]["jangkar_keras"]["end_to_end_pct"]
    m_rbb = R["funnel"]["funnel_rbb"]["pln_per_kandidat"]["end_to_end_pct"]

    hitung_mandiri = v["rincian_pendaftaran"]["mandiri"] * m
    target_mandiri = v["rincian_diterima"]["mandiri"]
    cek(
        "mandiri",
        abs(hitung_mandiri - target_mandiri) / target_mandiri < 0.02,
        f"{hitung_mandiri:.0f} vs {target_mandiri}",
    )

    hitung_rbb = v["rincian_pendaftaran"]["rbb_serah_terima"] * m_rbb
    target_rbb = v["rincian_diterima"]["rbb"]
    cek(
        "rbb",
        abs(hitung_rbb - target_rbb) / target_rbb < 0.02,
        f"{hitung_rbb:.0f} vs {target_rbb}",
    )

    total = sum(v["rincian_diterima"].values())
    cek(
        "diterima total = kohort.yaml",
        total == total_group(R),
        f"{total} vs {total_group(R)}",
    )
    cek(
        "rincian pendaftaran = pendaftaran_total",
        abs(sum(v["rincian_pendaftaran"].values()) - v["pendaftaran_total"]) < 1000,
        f"{sum(v['rincian_pendaftaran'].values())} vs {v['pendaftaran_total']}",
    )

    # Tahun mana pun yang punya komponen rbb/ppb_papua di komposisi_jalur (BUKAN cuma
    # field `jalur` mentah -- F-071 membuktikan tahun jalur:mandiri bisa juga punya
    # porsi RBB) harus konsisten dengan tahapan.yaml.
    tahun_ada_rbb = {
        r["tahun"]
        for r in R["kohort"]["kohort_per_tahun_program"]
        for k in r.get("komposisi_jalur", [])
        if k["sumber"] in ("rbb", "ppb_papua")
    }
    tahun_agregat = set(R["tahapan"]["tahap_agregat_fhci"]["berlaku_tahun"])
    cek("tahun RBB konsisten kohort vs tahapan", tahun_ada_rbb == tahun_agregat, f"{sorted(tahun_ada_rbb)} vs {sorted(tahun_agregat)}")

    cek(
        "lulus_wawancara + ikatan_dinas_langsung = total_masuk_pasca_seleksi",
        v["status_per_15sep2026"]["lulus_wawancara"] + v["status_per_15sep2026"]["ikatan_dinas_langsung"]
        == v["status_per_15sep2026"]["total_masuk_pasca_seleksi"],
        f"{v['status_per_15sep2026']}",
    )

    print("\n[4b] Status pada tanggal potong -- harus menurun monoton")
    st = v["status_per_15sep2026"]
    urut = ["total_masuk_pasca_seleksi", "ttd_kontrak", "lulus_samapta", "sudah_sk_penempatan"]
    nilai = [st[k] for k in urut]
    cek("menurun monoton", all(a >= b for a, b in zip(nilai, nilai[1:])), f"{nilai}")
    cek(
        "total_masuk_pasca_seleksi = diterima_selesai",
        st["total_masuk_pasca_seleksi"] == v["diterima_selesai"],
        f"{st['total_masuk_pasca_seleksi']} vs {v['diterima_selesai']}",
    )
    cek(
        "sudah_sk + sedang_ojt <= lulus_samapta",
        st["sudah_sk_penempatan"] + st["sedang_ojt"] <= st["lulus_samapta"],
        f"{st['sudah_sk_penempatan']} + {st['sedang_ojt']} vs {st['lulus_samapta']}",
    )


def cek_gelombang(R: dict) -> None:
    """Tahun yang punya gelombang harus punya nomor angkatan, dan sebaliknya.

    Dipisah karena inilah yang rusak diam-diam saat gelombang 2026 dibuang: nomor
    angkatan, sebaran jenjang pelamar, dan volume pendaftaran semuanya menggantung.
    """
    print("\n[4c] Gelombang -- tahun tanpa gelombang tidak boleh punya angkatan/pelamar")
    baris = R["kohort"]["kohort_per_tahun_program"]
    ada = {r["tahun"] for r in baris if r.get("ada_gelombang", True)}
    tanpa = {r["tahun"] for r in baris} - ada

    tahun_angkatan = set()
    for seri in R["angkatan"]["seri"].values():
        if "alokasi_horison" not in seri:
            continue  # ikatan_dinas & siluman: ada_gelombang:false, tidak punya seri katalog
        tahun_angkatan |= set(seri["alokasi_horison"])
    cek("semua tahun bergelombang punya nomor angkatan", ada <= tahun_angkatan, f"{sorted(ada - tahun_angkatan)}")
    cek("tahun tanpa gelombang tidak punya nomor angkatan", not (tanpa & tahun_angkatan), f"{sorted(tanpa)}")

    jenjang = {
        t for t in R["demografi"]["jenjang_pelamar"]["per_tahun_program"] if isinstance(t, int)
    }
    cek("sebaran jenjang hanya untuk tahun bergelombang", jenjang == ada, f"{sorted(jenjang)}")

    for r in baris:
        if not r.get("ada_gelombang", True):
            cek(
                f"{r['tahun']} tidak menerima siapa pun",
                r["induk_diterima"] == 0 and r["sub_diterima"] == 0,
                f"fase {r.get('fase')}",
            )


def cek_jabatan(R: dict) -> None:
    print("\n[5] Jabatan -- bobot pembidangan")
    pb = R["jabatan"]["pembidangan"]
    bobot = pb["bobot_holding"]
    total_pegawai = sum(x["pegawai"] for x in bobot.values())
    cek("total pegawai", total_pegawai == pb["total_pegawai"], f"{total_pegawai}")
    cek_jumlah_satu("porsi holding", {k: v["porsi"] for k, v in bobot.items()})
    for nama, isi in bobot.items():
        cek(
            f"porsi konsisten {nama}",
            abs(isi["porsi"] - isi["pegawai"] / total_pegawai) < 5e-4,
            f"{isi['porsi']} vs {isi['pegawai'] / total_pegawai:.4f}",
        )
    for kode, isi in pb["bobot_subholding"].items():
        if kode == "status_sumber":
            continue
        cek_jumlah_satu(f"porsi subholding {kode}", isi)

    print("\n[6] Jabatan -- larangan struktural")
    ls = R["jabatan"]["larangan_struktural"]
    cek("filter pakai kelompok_jabatan", ls["filter_pakai_kolom"] == "kelompok_jabatan")
    cek("Team Leader ada di daftar terlarang", "TEAM LEADER" in ls["kelompok_jabatan_terlarang"])
    grade = R["jabatan"]["grade_masuk"]["pemetaan"]
    cek("S1/D-IV -> G2 (bukan G1)", grade["S1/D-IV"]["grade"] == "G2")
    cek("S2 -> G3", grade["S2"]["grade"] == "G3")


def cek_sebaran(R: dict) -> None:
    print("\n[7] Sebaran -- semua harus berjumlah 1")
    cek_jumlah_satu("sebab keluar", R["attrition"]["sebab_keluar"]["porsi"])
    cek_jumlah_satu("alasan gagal administrasi", R["administrasi"]["alasan_gagal"]["bobot_target"])
    cek_jumlah_satu("agama", R["demografi"]["agama"]["sebaran"])
    cek_jumlah_satu("status perkawinan", R["demografi"]["status_perkawinan"]["sebaran_pelamar"])
    cek_jumlah_satu("gender pelamar", R["demografi"]["gender"]["pelamar"])
    cek_jumlah_satu("gender diterima", R["demografi"]["gender"]["diterima_target"])
    cek_jumlah_satu("jenjang pelamar", R["demografi"]["jenjang_pelamar"])
    cek_jumlah_satu("visus", R["demografi"]["fisik"]["visus"]["sebaran"])
    cek_jumlah_satu(
        "lamaran per akun",
        R["funnel"]["volume_target"]["lamaran_per_akun"]["sebaran"],
    )
    per_tahun = R["demografi"]["jenjang_pelamar"]["per_tahun_program"]
    for tahun, sebaran in per_tahun.items():
        if tahun in {"status_sumber", "catatan"}:
            continue
        cek_jumlah_satu(f"jenjang {tahun}", sebaran)

    print("\n[7b] Gender per tahun -- runtun nyata dari SR (F-048)")
    gender = R["demografi"]["gender"]["diterima_per_tahun_program"]
    for tahun, sebaran in gender.items():
        cek_jumlah_satu(f"gender {tahun}", sebaran)
    tahun_gelombang = {
        r["tahun"] for r in R["kohort"]["kohort_per_tahun_program"] if r.get("ada_gelombang", True)
    }
    cek("gender mencakup semua tahun bergelombang", set(gender) == tahun_gelombang, f"{sorted(gender)}")
    nyata = [t for t, s in gender.items() if s["status"] == "NYATA"]
    cek("mayoritas tahun berjangkar angka nyata", len(nyata) >= 5, f"{len(nyata)}/{len(gender)} nyata")

    print("\n[7c] Patahan definisi turnover (F-049) -- wajib ada penandanya")
    pd = R["attrition"]["patahan_definisi_turnover"]
    definisi = {e["definisi"] for e in pd["edisi"]}
    cek("dua definisi terdokumentasi", definisi == {"SEMPIT", "LUAS"}, f"{sorted(definisi)}")
    cek("aturan wajib tercatat", len(pd["aturan_wajib"]) >= 3, f"{len(pd['aturan_wajib'])} aturan")


def cek_tahapan(R: dict) -> None:
    print("\n[8] Tahapan -- kota, urutan, titik masuk RBB")
    kt = R["tahapan"]["kota_penyelenggara"]
    nama_kota = []
    for kunci in (
        "dari_arsip_2017_smk",
        "dari_arsip_2019_reguler",
        "dari_afirmasi_papua",
        "turunan_ibukota_provinsi_lain",
    ):
        nama_kota += kt[kunci]
    cek("jumlah kota = target F-019", len(nama_kota) == kt["jumlah_target"], f"{len(nama_kota)}")
    cek("tidak ada kota kembar", len(set(nama_kota)) == len(nama_kota))

    tahap = R["tahapan"]["tahap_seleksi"]
    urutan = [t["urutan"] for t in tahap]
    cek("urutan tahap 1..n tanpa lompatan", urutan == list(range(1, len(tahap) + 1)), f"{urutan}")

    kode_funnel = [t["tahap"] for t in R["funnel"]["funnel_mandiri"]["nasional_mandiri"]["tahapan"]]
    cek("kosakata tahap sama di tahapan.yaml & funnel.yaml", [t["kode"] for t in tahap] == kode_funnel)

    masuk_rbb = [t["kode"] for t in tahap if t["masuk_rbb"]]
    titik = R["funnel"]["funnel_rbb"]["pln_per_kandidat"]["titik_masuk"]
    cek("titik masuk RBB = tahap RBB pertama", masuk_rbb[0] == titik, f"{masuk_rbb[0]}")
    cek(
        "tahap RBB di funnel = tahap RBB di tahapan",
        [t["tahap"] for t in R["funnel"]["funnel_rbb"]["pln_per_kandidat"]["tahapan"]] == masuk_rbb,
    )
    cek(
        "administrasi & adaptif TIDAK dilalui RBB",
        not any(t["masuk_rbb"] for t in tahap if t["kode"] in {"administrasi", "adaptif"}),
    )


def cek_angkatan(R: dict) -> None:
    """Lubang di deret angkatan DISENGAJA (bukti katalog publik tidak lengkap).

    Jadi yang diuji bukan "deret rapat", melainkan: alokasi + lubang bersama-sama
    membentuk rentang utuh, dan keduanya tidak tumpang tindih.
    """
    print("\n[9] Angkatan -- alokasi, lubang, jangkar asli, kronologi")
    for nama_seri, isi in R["angkatan"]["seri"].items():
        if "alokasi_horison" not in isi:
            continue  # ikatan_dinas & siluman: bukan seri katalog nomor-integer
        alokasi = isi["alokasi_horison"]
        datar = sorted(n for tahun in alokasi for n in alokasi[tahun])
        lubang = isi.get("lubang", [])

        cek(f"[{nama_seri}] tidak ada nomor kembar", len(datar) == len(set(datar)))
        cek(
            f"[{nama_seri}] lubang tidak tumpang tindih alokasi",
            not (set(datar) & set(lubang)),
            f"lubang {lubang}",
        )
        gabung = sorted(datar + lubang)
        cek(
            f"[{nama_seri}] alokasi + lubang = rentang utuh",
            gabung == list(range(gabung[0], gabung[-1] + 1)),
            f"{gabung[0]}..{gabung[-1]} = {len(datar)} terpakai + {len(lubang)} lubang",
        )
        cek(
            f"[{nama_seri}] tiap nomor terpakai punya entri gelombang",
            set(datar) == set(isi["gelombang"]),
            f"selisih {set(datar) ^ set(isi['gelombang'])}",
        )

        # Nomor angkatan harus naik seiring waktu buka.
        urut = sorted(isi["gelombang"].items())
        tanggal = [str(g["buka"]) for _, g in urut]
        cek(f"[{nama_seri}] nomor naik searah tanggal buka", tanggal == sorted(tanggal), f"{tanggal}")

        # Tahun yang tercatat di tiap gelombang harus cocok dengan alokasinya.
        for nomor, g in isi["gelombang"].items():
            cek(
                f"[{nama_seri}] {nomor} konsisten tahun",
                nomor in alokasi.get(g["tahun"], []),
                f"gelombang bilang {g['tahun']}",
            )

        for jangkar in isi["jangkar_asli"]:
            tahun, nomor = jangkar["tahun"], jangkar["angkatan"]
            if tahun in alokasi:
                cek(f"[{nama_seri}] jangkar asli {nomor} -> {tahun}", nomor in alokasi[tahun])
                cek(
                    f"[{nama_seri}] jangkar {nomor} ditandai nyata",
                    isi["gelombang"][nomor]["sumber_nomor"] == "nyata",
                )

    # Seri yang sengaja tidak dimodelkan tidak boleh menyelinap masuk.
    cek(
        "SMK tidak dimodelkan di horison ini",
        R["angkatan"]["smk_pelaksana"]["dimodelkan"] is False,
    )
    cek(
        "sebaran jenjang tidak memuat SMK",
        all(
            "SMK" not in s
            for t, s in R["demografi"]["jenjang_pelamar"]["per_tahun_program"].items()
            if t != "status_sumber"
        ),
    )


def cek_kelengkapan(R: dict) -> None:
    print("\n[10] Kelengkapan -- kurva pengisian tidak boleh menurun")
    for nama_blok, isi in R["kelengkapan"]["blok"].items():
        per_tahun = isi["per_tahun"]
        nilai = [per_tahun[t] for t in sorted(per_tahun)]
        cek(
            f"{nama_blok} naik monoton",
            all(a <= b + 1e-9 for a, b in zip(nilai, nilai[1:])),
            f"{nilai}",
        )
        cek(f"{nama_blok} dalam [0,1]", all(0 <= v <= 1 for v in nilai))

    tahun_kohort = set(R["kelengkapan"]["kualitas_kohort"]) - {"aturan"}
    tahun_program = {r["tahun"] for r in R["kohort"]["kohort_per_tahun_program"]}
    cek("kualitas_kohort mencakup semua tahun", tahun_kohort == tahun_program, f"{sorted(tahun_kohort)}")


def cek_ikatan_dinas_siluman(R: dict) -> None:
    print("\n[11] Ikatan dinas & siluman -- angkatan.yaml harus cocok dengan komposisi_jalur")
    seri = R["angkatan"]["seri"]
    baris = R["kohort"]["kohort_per_tahun_program"]

    def komposisi_per_sumber(tahun: int, sumber: str) -> int:
        row = next(r for r in baris if r["tahun"] == tahun)
        return sum(k["diterima"] for k in row.get("komposisi_jalur", []) if k["sumber"] == sumber)

    id_per_tahun: dict[int, int] = {}
    for kode, info in seri["ikatan_dinas"]["kohort"].items():
        id_per_tahun[info["tahun_program"]] = id_per_tahun.get(info["tahun_program"], 0) + info["diterima"]
    for tahun, jumlah in id_per_tahun.items():
        target = komposisi_per_sumber(tahun, "ikatan_dinas")
        cek(f"ikatan_dinas {tahun}: angkatan.yaml vs komposisi_jalur", jumlah == target, f"{jumlah} vs {target}")

    for kode, info in seri["siluman"]["kohort"].items():
        target = komposisi_per_sumber(info["tahun_program"], "tidak_diketahui")
        cek(
            f"siluman {kode} ({info['tahun_program']}): diterima vs komposisi_jalur",
            info["diterima"] == target,
            f"{info['diterima']} vs {target}",
        )
        sebaran = sum(info["jenjang_sebaran"].values())
        cek(
            f"siluman {kode}: jenjang_sebaran = diterima",
            sebaran == info["diterima"],
            f"{sebaran} vs {info['diterima']}",
        )

    v = R["funnel"]["volume_target"]["rincian_diterima"]
    total_id = sum(info["diterima"] for info in seri["ikatan_dinas"]["kohort"].values())
    cek("total ikatan_dinas angkatan.yaml = funnel.yaml volume_target", total_id == v["ikatan_dinas"], f"{total_id} vs {v['ikatan_dinas']}")


def cek_vendor(R: dict) -> None:
    print("\n[12] Vendor -- tipe layanan & konsistensi dgn tahapan.yaml")
    daftar = R["vendor"]["vendor"]
    kode = [v["kode"] for v in daftar]
    cek("tidak ada kode vendor kembar", len(kode) == len(set(kode)))
    cek(
        "tipe_layanan vendor hanya psikologi/fisik_mcu",
        all(v["tipe_layanan"] in ("psikologi", "fisik_mcu") for v in daftar),
    )
    tahap = R["tahapan"]["tahap_seleksi"]
    tahap_vendor = {t["kode"] for t in tahap if t["pemilik_proses"] == "VENDOR"}
    cek(
        "tiap tahap VENDOR di tahapan.yaml punya tipe_layanan vendor yg cocok",
        tahap_vendor == {"psikologi", "fisik_mcu"},
        f"{tahap_vendor}",
    )
    tanpa_rujukan = [
        v["kode"] for v in daftar if v.get("status_sumber") != "DIMODELKAN" and not v.get("rujukan")
    ]
    cek("vendor nyata (bukan DIMODELKAN) punya rujukan", not tanpa_rujukan, f"{tanpa_rujukan}")
    ada_psikologi = any(v["tipe_layanan"] == "psikologi" for v in daftar)
    ada_mcu = any(v["tipe_layanan"] == "fisik_mcu" for v in daftar)
    cek("ada minimal 1 vendor psikologi & 1 fisik_mcu", ada_psikologi and ada_mcu)


def main() -> int:
    print(f"Verifikasi aturan di {RULES_DIR}")
    R = muat()
    if gagal:
        print("\nAda file yang gagal diparse -- hentikan.")
        return 1

    cek_kohort(R)
    cek_funnel(R)
    cek_volume(R)
    cek_gelombang(R)
    cek_jabatan(R)
    cek_sebaran(R)
    cek_tahapan(R)
    cek_angkatan(R)
    cek_kelengkapan(R)
    cek_ikatan_dinas_siluman(R)
    cek_vendor(R)

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
