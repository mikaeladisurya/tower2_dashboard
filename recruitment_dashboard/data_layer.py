from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


STAGE_ORDER = [
    "REGISTRATION",
    "ADMINISTRATION",
    "ACADEMIC_ENGLISH",
    "ADAPTIVE_TEST",
    "MCU",
    "INTERVIEW",
    "CONTRACT",
]

STAGE_LABELS = {
    "REGISTRATION": "Pendaftar",
    "ADMINISTRATION": "Administrasi",
    "ACADEMIC_ENGLISH": "Akademik & English",
    "ADAPTIVE_TEST": "Tes Adaptif",
    "MCU": "MCU",
    "INTERVIEW": "Wawancara",
    "CONTRACT": "Kontrak",
}


def _read_csv(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False, **kwargs)


def _email_key(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_demo_data(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)

    admin = _read_csv(data_dir / "Rekrutment_Administrasi.csv", dtype={"ID_PENDAFTARAN": "string", "EMAIL": "string"})
    academic = _read_csv(data_dir / "Rekrutment_Akademik_English.csv", dtype={"EMAIL": "string", "NO TES": "string"})
    adaptive = _read_csv(data_dir / "Rekrutment_Tes_Adaptif.csv", dtype={"EMAIL": "string", "NO TES": "string"})
    mcu = _read_csv(data_dir / "Rekrutment_MCU.csv", dtype={"EMAIL": "string", "NO TES": "string"})
    interview = _read_csv(data_dir / "Rekrutment_Wawancara.csv", dtype={"EMAIL": "string", "NO TES": "string"})
    vacancies = _read_csv(data_dir / "Recruitment_Vacancy_Plan.csv", dtype={"VACANCY_ID": "string"})
    contracts = _read_csv(
        data_dir / "Recruitment_Contract_Placement.csv",
        dtype={"ID_PENDAFTARAN": "string", "EMAIL": "string", "NO_TES": "string"},
    )
    pipeline = _read_csv(
        data_dir / "Recruitment_Pipeline_History.csv",
        dtype={"ID_PENDAFTARAN": "string", "NO_TES": "string", "VACANCY_ID": "string"},
    )

    for frame in [admin, academic, adaptive, mcu, interview, contracts]:
        frame["EMAIL_KEY"] = _email_key(frame["EMAIL"])

    pipeline["ENTERED_AT"] = pd.to_datetime(pipeline["ENTERED_AT"], errors="coerce")
    pipeline["COMPLETED_AT"] = pd.to_datetime(pipeline["COMPLETED_AT"], errors="coerce")
    contracts["CONTRACT_DATE"] = pd.to_datetime(contracts["CONTRACT_DATE"], errors="coerce")

    apps = admin[
        [
            "ID_PENDAFTARAN",
            "EMAIL_KEY",
            "NAMA REKRUTMEN",
            "JENJANG",
            "PRODI",
            "NEM/IPK",
            "JENIS KELAMIN",
            "KOTA KTP",
        ]
    ].copy()
    apps = apps.rename(columns={"NEM/IPK": "GPA"})

    academic_small = academic[["EMAIL_KEY", "Ak Skor", "En Skor", "TOTAL SKOR AKDING"]].drop_duplicates("EMAIL_KEY")
    adaptive_small = adaptive[
        ["EMAIL_KEY", "KATEGORI", "ABSTRACT_REASONING", "VERBAL_REASONING", "NUMERICAL_REASONING", "TOTAL"]
    ].drop_duplicates("EMAIL_KEY")
    adaptive_small = adaptive_small.rename(columns={"TOTAL": "ADAPTIVE_TOTAL"})
    mcu_small = mcu[["EMAIL_KEY", "Hasil"]].drop_duplicates("EMAIL_KEY").rename(columns={"Hasil": "MCU_RESULT"})
    interview_small = interview[["EMAIL_KEY", "SKOR", "REKOMENDASI", "HASIL"]].drop_duplicates("EMAIL_KEY")
    interview_small = interview_small.rename(
        columns={"SKOR": "INTERVIEW_SCORE", "HASIL": "INTERVIEW_RESULT"}
    )

    apps = apps.merge(academic_small, on="EMAIL_KEY", how="left")
    apps = apps.merge(adaptive_small, on="EMAIL_KEY", how="left")
    apps = apps.merge(mcu_small, on="EMAIL_KEY", how="left")
    apps = apps.merge(interview_small, on="EMAIL_KEY", how="left")

    contract_cols = [
        "ID_PENDAFTARAN",
        "NO_TES",
        "VACANCY_ID_PLAN",
        "MATCH_SCORE_PLAN",
        "MATCH_CATEGORY_PLAN",
        "CONTRACT_STATUS",
        "CONTRACT_DATE",
        "CONTRACT_REJECTION_REASON",
        "ACTUAL_VACANCY_ID",
        "ACTUAL_POSITION_NAME",
        "ACTUAL_UNIT_NAME",
        "ACTUAL_LOCATION",
    ]
    apps = apps.merge(contracts[contract_cols], on="ID_PENDAFTARAN", how="left")

    method_dim = (
        pipeline.sort_values("STAGE_SEQUENCE")
        .drop_duplicates("ID_PENDAFTARAN")
        [["ID_PENDAFTARAN", "RECRUITMENT_METHOD"]]
    )
    apps = apps.merge(method_dim, on="ID_PENDAFTARAN", how="left")

    plan_dim = vacancies[
        [
            "VACANCY_ID",
            "POSITION_NAME",
            "JOB_FAMILY",
            "UNIT_NAME",
            "LOCATION_PLAN",
            "REGION",
            "REMOTE_FLAG",
            "VACANCY_PRIORITY",
            "QUOTA",
        ]
    ].rename(
        columns={
            "VACANCY_ID": "VACANCY_ID_PLAN",
            "POSITION_NAME": "POSITION_PLAN",
            "JOB_FAMILY": "JOB_FAMILY_PLAN",
            "UNIT_NAME": "UNIT_PLAN",
            "LOCATION_PLAN": "LOCATION_PLAN_NAME",
            "REGION": "REGION_PLAN",
            "QUOTA": "VACANCY_QUOTA",
        }
    )
    apps = apps.merge(plan_dim, on="VACANCY_ID_PLAN", how="left")

    actual_dim = vacancies[
        ["VACANCY_ID", "POSITION_NAME", "JOB_FAMILY", "UNIT_NAME", "LOCATION_PLAN", "REGION"]
    ].rename(
        columns={
            "VACANCY_ID": "ACTUAL_VACANCY_ID",
            "POSITION_NAME": "POSITION_ACTUAL_REF",
            "JOB_FAMILY": "JOB_FAMILY_ACTUAL",
            "UNIT_NAME": "UNIT_ACTUAL_REF",
            "LOCATION_PLAN": "LOCATION_ACTUAL_REF",
            "REGION": "REGION_ACTUAL",
        }
    )
    apps = apps.merge(actual_dim, on="ACTUAL_VACANCY_ID", how="left")
    apps["EXACT_PLACEMENT_MATCH"] = apps["VACANCY_ID_PLAN"].eq(apps["ACTUAL_VACANCY_ID"])

    return {
        "applications": apps,
        "vacancies": vacancies,
        "contracts": contracts,
        "pipeline": pipeline,
    }


def selected_application_ids(
    applications: pd.DataFrame,
    programs: list[str] | None = None,
    regions: list[str] | None = None,
    methods: list[str] | None = None,
) -> set[str]:
    mask = pd.Series(True, index=applications.index)
    if programs:
        mask &= applications["NAMA REKRUTMEN"].isin(programs)
    if regions:
        mask &= applications["REGION_PLAN"].isin(regions)
    if methods:
        mask &= applications["RECRUITMENT_METHOD"].isin(methods)
    return set(applications.loc[mask, "ID_PENDAFTARAN"])


def build_funnel(pipeline: pd.DataFrame, ids: set[str]) -> pd.DataFrame:
    scoped = pipeline[pipeline["ID_PENDAFTARAN"].isin(ids)]
    rows = []
    previous = None
    for stage in STAGE_ORDER:
        stage_rows = scoped[scoped["STAGE_CODE"].eq(stage)]
        if stage == "REGISTRATION":
            count = stage_rows["ID_PENDAFTARAN"].nunique()
        else:
            count = stage_rows.loc[stage_rows["STAGE_RESULT"].eq("PASSED"), "ID_PENDAFTARAN"].nunique()
        conversion = count / previous if previous else 1.0
        rows.append(
            {
                "STAGE_CODE": stage,
                "STAGE": STAGE_LABELS[stage],
                "COUNT": int(count),
                "CONVERSION": conversion,
            }
        )
        previous = count
    return pd.DataFrame(rows)


def stage_performance(pipeline: pd.DataFrame, ids: set[str]) -> pd.DataFrame:
    scoped = pipeline[pipeline["ID_PENDAFTARAN"].isin(ids)].copy()
    rows = []
    for stage in STAGE_ORDER:
        part = scoped[scoped["STAGE_CODE"].eq(stage)]
        completed = part["STAGE_STATUS"].eq("COMPLETED")
        rows.append(
            {
                "STAGE_CODE": stage,
                "Tahap": STAGE_LABELS[stage],
                "Peserta": int(part["ID_PENDAFTARAN"].nunique()),
                "Pass Rate": part["STAGE_RESULT"].eq("PASSED").mean() if len(part) else np.nan,
                "Median Hari": part["DURATION_DAYS"].median(),
                "P90 Hari": part["DURATION_DAYS"].quantile(0.90),
                "Target SLA": part["SLA_TARGET_DAYS"].median(),
                "SLA Compliance": part["SLA_STATUS"].eq("WITHIN_SLA").mean() if len(part) else np.nan,
                "Aktif": int((~completed).sum()),
                "Over SLA": int(part["SLA_STATUS"].eq("OVER_SLA").sum()),
            }
        )
    return pd.DataFrame(rows)


def method_performance(applications: pd.DataFrame, pipeline: pd.DataFrame, ids: set[str]) -> pd.DataFrame:
    apps = applications[applications["ID_PENDAFTARAN"].isin(ids)].copy()
    duration = (
        pipeline[pipeline["ID_PENDAFTARAN"].isin(ids)]
        .groupby("ID_PENDAFTARAN")["DURATION_DAYS"]
        .sum()
        .rename("TOTAL_DAYS")
    )
    apps = apps.merge(duration, on="ID_PENDAFTARAN", how="left")
    apps["SIGNED"] = apps["CONTRACT_STATUS"].eq("SIGNED")
    apps["ALIGNED"] = apps["SIGNED"] & apps["EXACT_PLACEMENT_MATCH"]

    summary = apps.groupby("RECRUITMENT_METHOD", dropna=False).agg(
        Applicants=("ID_PENDAFTARAN", "size"),
        Contracts=("SIGNED", "sum"),
        Median_Days=("TOTAL_DAYS", "median"),
        Aligned=("ALIGNED", "sum"),
    )
    summary["Conversion"] = summary["Contracts"] / summary["Applicants"]
    summary["Placement Alignment"] = summary["Aligned"] / summary["Contracts"].replace(0, np.nan)
    return summary.reset_index().rename(
        columns={"RECRUITMENT_METHOD": "Metode", "Median_Days": "Median Total Hari"}
    )


def method_stage_matrix(pipeline: pd.DataFrame, ids: set[str], metric: str) -> pd.DataFrame:
    scoped = pipeline[pipeline["ID_PENDAFTARAN"].isin(ids)].copy()
    if metric == "Median Hari":
        grouped = scoped.groupby(["RECRUITMENT_METHOD", "STAGE_CODE"])["DURATION_DAYS"].median()
    elif metric == "Pass Rate":
        grouped = scoped.assign(VALUE=scoped["STAGE_RESULT"].eq("PASSED")).groupby(
            ["RECRUITMENT_METHOD", "STAGE_CODE"]
        )["VALUE"].mean()
    else:
        grouped = scoped.assign(VALUE=scoped["SLA_STATUS"].eq("WITHIN_SLA")).groupby(
            ["RECRUITMENT_METHOD", "STAGE_CODE"]
        )["VALUE"].mean()
    matrix = grouped.unstack("STAGE_CODE").reindex(columns=STAGE_ORDER)
    return matrix.rename(columns=STAGE_LABELS)


def vacancy_fulfilment(
    vacancies: pd.DataFrame,
    applications: pd.DataFrame,
    ids: set[str],
    programs: list[str] | None = None,
    regions: list[str] | None = None,
) -> pd.DataFrame:
    scoped_vacancies = vacancies.copy()
    if programs:
        scoped_vacancies = scoped_vacancies[scoped_vacancies["NAMA_REKRUTMEN"].isin(programs)]
    if regions:
        scoped_vacancies = scoped_vacancies[scoped_vacancies["REGION"].isin(regions)]

    signed = applications[
        applications["ID_PENDAFTARAN"].isin(ids) & applications["CONTRACT_STATUS"].eq("SIGNED")
    ]
    counts = signed["ACTUAL_VACANCY_ID"].value_counts().rename("SIGNED")
    result = scoped_vacancies.merge(counts, left_on="VACANCY_ID", right_index=True, how="left")
    result["SIGNED"] = result["SIGNED"].fillna(0).astype(int)
    result["GAP"] = result["QUOTA"] - result["SIGNED"]
    result["FILL_RATE"] = result["SIGNED"] / result["QUOTA"]
    return result


def region_fulfilment(vacancy_fill: pd.DataFrame) -> pd.DataFrame:
    result = vacancy_fill.groupby("REGION", as_index=False).agg(QUOTA=("QUOTA", "sum"), SIGNED=("SIGNED", "sum"))
    result["GAP"] = result["QUOTA"] - result["SIGNED"]
    result["FILL_RATE"] = result["SIGNED"] / result["QUOTA"]
    return result.sort_values("FILL_RATE")


def placement_detail(applications: pd.DataFrame, ids: set[str]) -> pd.DataFrame:
    signed = applications[
        applications["ID_PENDAFTARAN"].isin(ids) & applications["CONTRACT_STATUS"].eq("SIGNED")
    ].copy()
    exact = signed["VACANCY_ID_PLAN"].eq(signed["ACTUAL_VACANCY_ID"])
    partial = (
        signed["POSITION_PLAN"].eq(signed["POSITION_ACTUAL_REF"])
        | signed["UNIT_PLAN"].eq(signed["UNIT_ACTUAL_REF"])
        | signed["REGION_PLAN"].eq(signed["REGION_ACTUAL"])
    )
    signed["ALIGNMENT_CATEGORY"] = np.select(
        [exact, ~exact & partial],
        ["Fully Aligned", "Partially Aligned"],
        default="Not Aligned",
    )
    return signed


def score_candidates_for_vacancy(applications: pd.DataFrame, vacancy: pd.Series, pool: str) -> pd.DataFrame:
    candidates = applications.copy()
    if pool == "Lolos Wawancara":
        candidates = candidates[candidates["INTERVIEW_RESULT"].eq("LOLOS")]
    elif pool == "Belum Kontrak":
        candidates = candidates[
            candidates["INTERVIEW_RESULT"].eq("LOLOS") & ~candidates["CONTRACT_STATUS"].eq("SIGNED")
        ]

    required_levels = set(str(vacancy["JENJANG_REQUIRED"]).split("|"))
    required_prodi = set(str(vacancy["PRODI_REQUIRED"]).split("|"))

    level_match = candidates["JENJANG"].isin(required_levels)
    prodi_match = candidates["PRODI"].isin(required_prodi)
    gpa = pd.to_numeric(candidates["GPA"], errors="coerce")
    akding = pd.to_numeric(candidates["TOTAL SKOR AKDING"], errors="coerce")
    adaptive = pd.to_numeric(candidates["ADAPTIVE_TOTAL"], errors="coerce")

    score = np.where(level_match, 25.0, 0.0)
    score += np.where(prodi_match, 35.0, 5.0)
    score += np.where(
        gpa >= vacancy["MIN_IPK"],
        15.0,
        np.maximum(0.0, 15.0 * gpa.fillna(0) / vacancy["MIN_IPK"] - 3.0),
    )
    score += np.minimum(15.0, 15.0 * akding.fillna(0) / vacancy["MIN_AKDING_SCORE"])
    score += np.minimum(10.0, 10.0 * adaptive.fillna(0) / vacancy["MIN_ADAPTIVE_SCORE"])

    result = candidates[
        ["ID_PENDAFTARAN", "JENJANG", "PRODI", "GPA", "TOTAL SKOR AKDING", "ADAPTIVE_TOTAL", "CONTRACT_STATUS"]
    ].copy()
    result["MATCH_SCORE"] = np.round(np.minimum(score, 100), 1)
    result["MATCH_CATEGORY"] = pd.cut(
        result["MATCH_SCORE"],
        bins=[-np.inf, 65, 80, np.inf],
        labels=["LOW_MATCH", "MODERATE_MATCH", "STRONG_MATCH"],
        right=False,
    ).astype("string")

    gaps = []
    for idx in candidates.index:
        row_gaps = []
        if not level_match.loc[idx]:
            row_gaps.append("Jenjang")
        if not prodi_match.loc[idx]:
            row_gaps.append("Prodi")
        if pd.isna(gpa.loc[idx]) or gpa.loc[idx] < vacancy["MIN_IPK"]:
            row_gaps.append("IPK")
        if pd.isna(akding.loc[idx]) or akding.loc[idx] < vacancy["MIN_AKDING_SCORE"]:
            row_gaps.append("Akding")
        if pd.isna(adaptive.loc[idx]) or adaptive.loc[idx] < vacancy["MIN_ADAPTIVE_SCORE"]:
            row_gaps.append("Adaptif")
        gaps.append(", ".join(row_gaps) if row_gaps else "Tidak ada gap utama")
    result["MATCH_GAPS"] = gaps
    return result.sort_values(["MATCH_SCORE", "ID_PENDAFTARAN"], ascending=[False, True])
