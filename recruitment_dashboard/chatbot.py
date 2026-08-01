from __future__ import annotations

import json
import os
import re
from typing import Any

import pandas as pd


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def build_chat_context(
    overview: dict[str, Any],
    stage_summary: pd.DataFrame,
    method_summary: pd.DataFrame,
    region_summary: pd.DataFrame,
    vacancy_summary: pd.DataFrame,
) -> dict[str, Any]:
    bottleneck = stage_summary.sort_values(["SLA Compliance", "Median Hari"]).iloc[0]
    best_method = method_summary.sort_values("Conversion", ascending=False).iloc[0]
    worst_method = method_summary.sort_values("Conversion").iloc[0]
    lowest_regions = region_summary.sort_values("FILL_RATE").head(3)
    critical = vacancy_summary[vacancy_summary["VACANCY_PRIORITY"].eq("CRITICAL")].sort_values("FILL_RATE").head(5)

    return {
        "overview": overview,
        "bottleneck": bottleneck.to_dict(),
        "best_method": best_method.to_dict(),
        "worst_method": worst_method.to_dict(),
        "methods": method_summary.to_dict(orient="records"),
        "regions": lowest_regions.to_dict(orient="records"),
        "critical_vacancies": critical[
            ["VACANCY_ID", "POSITION_NAME", "LOCATION_PLAN", "QUOTA", "SIGNED", "FILL_RATE"]
        ].to_dict(orient="records"),
    }


def local_answer(question: str, context: dict[str, Any]) -> str | None:
    q = question.lower().strip()
    overview = context["overview"]

    if re.search(r"pendaftar.*kontrak|applicant.*contract|konversi.*kontrak", q):
        return (
            f"Dari {overview['applicants']:,} pendaftar, {overview['signed']:,} telah menandatangani kontrak. "
            f"Konversi pendaftar sampai kontrak adalah **{_pct(overview['applicant_to_contract'])}**."
        )

    if any(term in q for term in ["bottleneck", "hambatan", "paling lama", "over sla"]):
        row = context["bottleneck"]
        return (
            f"Tahap yang paling perlu perhatian adalah **{row['Tahap']}**. Median durasinya "
            f"{row['Median Hari']:.1f} hari dibanding target {row['Target SLA']:.1f} hari, dengan "
            f"SLA compliance **{_pct(row['SLA Compliance'])}** dan {int(row['Over SLA']):,} event over SLA."
        )

    if any(term in q for term in ["metode", "method", "channel", "paling efektif"]):
        best = context["best_method"]
        worst = context["worst_method"]
        return (
            f"Berdasarkan konversi kontrak, **{best['Metode']}** menjadi metode paling efektif "
            f"dengan conversion **{_pct(best['Conversion'])}**. **{worst['Metode']}** memiliki conversion "
            f"terendah, yaitu **{_pct(worst['Conversion'])}**. Interpretasi ini hanya berdasarkan conversion, "
            "belum memperhitungkan biaya rekrutmen."
        )

    if any(term in q for term in ["penempatan", "alignment", "sesuai rencana"]):
        return (
            f"Dari kandidat yang menandatangani kontrak, **{_pct(overview['placement_alignment'])}** ditempatkan "
            "pada vacancy yang sama persis dengan rencana awal. Gunakan halaman Sebaran & Penempatan untuk "
            "melihat perpindahan antarwilayah."
        )

    if any(term in q for term in ["kritis", "critical", "belum terpenuhi", "lowongan"]):
        rows = context["critical_vacancies"][:3]
        if not rows:
            return "Tidak ada vacancy kritis pada filter yang sedang aktif."
        items = [
            f"{r['POSITION_NAME']} – {r['LOCATION_PLAN']} ({_pct(r['FILL_RATE'])})"
            for r in rows
        ]
        return "Vacancy kritis dengan fulfilment terendah:\n\n- " + "\n- ".join(items)

    if any(term in q for term in ["wilayah", "region", "sebaran"]):
        rows = context["regions"]
        items = [f"{r['REGION']}: {_pct(r['FILL_RATE'])}" for r in rows]
        return "Wilayah dengan fulfilment terendah:\n\n- " + "\n- ".join(items)

    return None


def _secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name)
        return str(value) if value else None
    except Exception:
        return None


def llm_is_configured() -> bool:
    key = _secret("LLM_API_KEY")
    base_url = _secret("LLM_BASE_URL")
    model = _secret("LLM_MODEL")
    values = [key, base_url, model]
    return all(values) and not any("YOUR_" in str(value) for value in values)


def llm_answer(question: str, context: dict[str, Any]) -> str | None:
    if not llm_is_configured():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=_secret("LLM_API_KEY"), base_url=_secret("LLM_BASE_URL"))
        response = client.chat.completions.create(
            model=_secret("LLM_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda adalah asisten analitik rekrutmen PLN. Jawab singkat dalam Bahasa Indonesia. "
                        "Gunakan hanya data JSON yang diberikan. Jangan mengarang angka atau data kandidat. "
                        "Jika data tidak tersedia, sampaikan keterbatasannya."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Konteks dashboard:\n{json.dumps(context, default=str)}\n\nPertanyaan: {question}",
                },
            ],
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"Koneksi chatbot belum berhasil: {exc}"


_FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|DETACH|COPY|CREATE|CALL|"
    r"EXPORT|IMPORT|INSTALL|LOAD|GRANT|VACUUM|SET|RESET)\b"
    # DuckDB catalog/metadata access (schema probing beyond the registered tables)
    r"|PRAGMA\w*|INFORMATION_SCHEMA|DUCKDB_\w*|SQLITE_MASTER"
    # table functions that read the local filesystem or network, bypassing the app's dataframes
    r"|READ_CSV\w*|READ_PARQUET\w*|READ_JSON\w*|READ_TEXT\w*|SNIFF_CSV\w*|"
    r"GLOB\s*\(|ICEBERG_SCAN|DELTA_SCAN|HTTPFS",
    re.IGNORECASE,
)

SQL_FEW_SHOT = """
Contoh 1:
Pertanyaan: Berapa kandidat prodi Teknik Elektro dengan IPK di atas 3.5 yang lolos wawancara di wilayah Jawa Barat?
SQL: SELECT COUNT(*) AS jumlah FROM applications WHERE PRODI = 'Teknik Elektro' AND GPA > 3.5 AND INTERVIEW_RESULT = 'LOLOS' AND REGION_PLAN = 'Jawa Barat';

Contoh 2:
Pertanyaan: Berapa rata-rata durasi tiap tahap pipeline untuk metode rekrutmen 'Kampus'?
SQL: SELECT STAGE_CODE, AVG(DURATION_DAYS) AS rata_rata_durasi FROM pipeline WHERE RECRUITMENT_METHOD = 'Kampus' GROUP BY STAGE_CODE ORDER BY rata_rata_durasi DESC;

Contoh 3:
Pertanyaan: Tampilkan 5 vacancy prioritas CRITICAL dengan kuota terbesar.
SQL: SELECT VACANCY_ID, POSITION_NAME, LOCATION_PLAN, QUOTA FROM vacancies WHERE VACANCY_PRIORITY = 'CRITICAL' ORDER BY QUOTA DESC LIMIT 5;

Contoh 4 (kolom dengan spasi harus dibungkus tanda kutip dua):
Pertanyaan: Berapa rata-rata TOTAL SKOR AKDING untuk pendaftar program 'Officer Development Program'?
SQL: SELECT AVG("TOTAL SKOR AKDING") AS rata_rata_skor FROM applications WHERE "NAMA REKRUTMEN" = 'Officer Development Program';
""".strip()

SQL_SYSTEM_PROMPT = """Anda adalah generator SQL untuk analitik data rekrutmen PLN memakai dialek DuckDB.
Tugas anda HANYA menghasilkan satu query SQL SELECT yang menjawab pertanyaan user berdasarkan skema tabel berikut.

Aturan:
- Hanya gunakan tabel dan kolom yang benar-benar ada pada skema di bawah, jangan mengarang nama kolom/tabel.
- Nama kolom yang mengandung spasi HARUS dibungkus tanda kutip dua, misal "NAMA REKRUTMEN".
- Hanya boleh satu statement, berupa SELECT (boleh diawali WITH untuk CTE). Dilarang keras INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/ATTACH/COPY/PRAGMA/SET atau statement lain.
- Jangan query metadata/katalog (information_schema, duckdb_*, sqlite_master) atau table function pembaca file/URL (read_csv, read_parquet, read_json, glob, httpfs). Hanya tabel pada skema di bawah yang boleh diakses.
- Jangan tambahkan penjelasan apapun, kembalikan SQL murni saja (boleh dibungkus code block ```sql ... ```).
- Batasi hasil ke maksimal 200 baris (tambahkan LIMIT jika query berpotensi mengembalikan banyak baris).

Skema tabel:
{schema}

Contoh pertanyaan dan SQL:
{examples}
"""


def _describe_table(name: str, df: pd.DataFrame, max_categories: int = 12) -> str:
    lines = [f"Tabel: {name}"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        note = ""
        if dtype == "object" or dtype.startswith("string"):
            uniques = df[col].dropna().unique()
            if 0 < len(uniques) <= max_categories:
                sample = ", ".join(sorted(str(v) for v in uniques))
                note = f" - nilai: {sample}"
        col_ident = f'"{col}"' if " " in col or "/" in col else col
        lines.append(f"  - {col_ident} ({dtype}){note}")
    return "\n".join(lines)


def _build_schema_prompt(dataframes: dict[str, pd.DataFrame]) -> str:
    return "\n\n".join(_describe_table(name, df) for name, df in dataframes.items())


def _extract_sql(raw: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    return text.strip()


def _is_safe_select(sql: str) -> bool:
    stripped = sql.strip().rstrip(";").strip()
    if not stripped or ";" in stripped:
        return False
    first_word = re.match(r"^\s*([A-Za-z]+)", stripped)
    if not first_word or first_word.group(1).upper() not in {"SELECT", "WITH"}:
        return False
    if _FORBIDDEN_SQL.search(stripped):
        return False
    return True


def _execute_sql(sql: str, dataframes: dict[str, pd.DataFrame], row_limit: int = 200) -> pd.DataFrame:
    import duckdb

    con = duckdb.connect(database=":memory:")
    try:
        for name, df in dataframes.items():
            con.register(name, df)
        # Lock the connection down before running untrusted, LLM-generated SQL: no filesystem/network
        # access, and the query itself cannot re-enable it since SET/RESET are already blocked upstream.
        con.execute("SET enable_external_access = false")
        con.execute("SET lock_configuration = true")
        result = con.execute(sql).df()
    finally:
        con.close()
    return result.head(row_limit)


def _generate_sql(question: str, schema_prompt: str) -> str | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=_secret("LLM_API_KEY"), base_url=_secret("LLM_BASE_URL"))
        response = client.chat.completions.create(
            model=_secret("LLM_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": SQL_SYSTEM_PROMPT.format(schema=schema_prompt, examples=SQL_FEW_SHOT),
                },
                {"role": "user", "content": question},
            ],
        )
        raw = response.choices[0].message.content or ""
        return _extract_sql(raw)
    except Exception:
        return None


def _narrate_result(question: str, sql: str, table: pd.DataFrame) -> str:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=_secret("LLM_API_KEY"), base_url=_secret("LLM_BASE_URL"))
        preview = table.head(20).to_dict(orient="records")
        response = client.chat.completions.create(
            model=_secret("LLM_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda asisten analitik rekrutmen PLN. Ringkas hasil query SQL berikut jadi "
                        "1-2 kalimat Bahasa Indonesia yang menjawab pertanyaan user. Gunakan hanya "
                        "angka yang ada pada hasil query, jangan mengarang."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Pertanyaan: {question}\nSQL: {sql}\n"
                        f"Hasil (JSON, maksimal 20 baris): {json.dumps(preview, default=str)}"
                    ),
                },
            ],
        )
        return (response.choices[0].message.content or "").strip()
    except Exception:
        return ""


def sql_answer(question: str, dataframes: dict[str, pd.DataFrame] | None) -> dict[str, Any] | None:
    if not llm_is_configured() or not dataframes:
        return None
    schema_prompt = _build_schema_prompt(dataframes)
    sql = _generate_sql(question, schema_prompt)
    if not sql or not _is_safe_select(sql):
        return None
    try:
        table = _execute_sql(sql, dataframes)
    except Exception as exc:
        return {"text": f"Query SQL gagal dieksekusi: {exc}", "sql": sql, "table": None}
    narration = _narrate_result(question, sql, table)
    return {"text": narration or "Berikut hasil query.", "sql": sql, "table": table}


def answer_question(
    question: str,
    context: dict[str, Any],
    dataframes: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    sql_result = sql_answer(question, dataframes)
    if sql_result:
        return {"kind": "sql", **sql_result}

    llm_response = llm_answer(question, context)
    if llm_response:
        return {"kind": "llm", "text": llm_response, "sql": None, "table": None}

    deterministic = local_answer(question, context)
    if deterministic:
        return {"kind": "local", "text": deterministic, "sql": None, "table": None}

    return {
        "kind": "fallback",
        "text": (
            "Untuk demo tanpa API, saya dapat menjawab pertanyaan tentang konversi kontrak, bottleneck, "
            "perbandingan metode, kesesuaian penempatan, vacancy kritis, dan sebaran wilayah. "
            "Konfigurasikan kredensial LLM untuk pertanyaan yang lebih fleksibel."
        ),
        "sql": None,
        "table": None,
    }
