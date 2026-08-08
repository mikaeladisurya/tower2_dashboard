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


def list_llm_profiles() -> list[dict[str, str]]:
    profiles: list[dict[str, str]] = []
    try:
        import streamlit as st

        raw = st.secrets.get("llm")
    except Exception:
        raw = None
    if raw:
        for profile_id, cfg in raw.items():
            profiles.append(
                {
                    "id": profile_id,
                    "label": cfg.get("label", profile_id),
                    "icon": cfg.get("icon", "🤖"),
                    "note": cfg.get("note", ""),
                    "api_key": cfg.get("api_key"),
                    "base_url": cfg.get("base_url"),
                    "model": cfg.get("model"),
                }
            )
    if not profiles:
        key, base_url, model = _secret("LLM_API_KEY"), _secret("LLM_BASE_URL"), _secret("LLM_MODEL")
        if key and base_url and model:
            profiles.append(
                {
                    "id": "default",
                    "label": model,
                    "icon": "🤖",
                    "note": "",
                    "api_key": key,
                    "base_url": base_url,
                    "model": model,
                }
            )
    return profiles


def profile_is_configured(profile: dict[str, str] | None) -> bool:
    if not profile:
        return False
    values = [profile.get("api_key"), profile.get("base_url"), profile.get("model")]
    return all(values) and not any("YOUR_" in str(value) for value in values)


LLM_REQUEST_TIMEOUT = 30.0
LLM_PING_TIMEOUT = 10.0


def check_llm_connection(profile: dict[str, str] | None, timeout: float = LLM_PING_TIMEOUT) -> tuple[bool, str]:
    """Send one minimal request to verify the endpoint responds and the key is valid."""
    if not profile_is_configured(profile):
        return False, "Kredensial belum lengkap"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=profile["api_key"], base_url=profile["base_url"], timeout=timeout)
        # Reasoning models (gpt-5.x, o1, ...) spend some of the token budget on hidden reasoning
        # tokens before producing visible output, so a budget of 1 fails even when the call itself
        # is valid - give it enough headroom to actually answer "ping".
        ping_budget = 16
        try:
            client.chat.completions.create(
                model=profile["model"],
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=ping_budget,
            )
        except Exception as exc:
            # Newer OpenAI reasoning models reject `max_tokens` and require `max_completion_tokens`
            # instead; other OpenAI-compatible endpoints accept the old name.
            if "max_completion_tokens" in str(exc):
                client.chat.completions.create(
                    model=profile["model"],
                    messages=[{"role": "user", "content": "ping"}],
                    max_completion_tokens=ping_budget,
                )
            else:
                raise
        return True, "Terhubung"
    except Exception as exc:
        return False, str(exc)


def _format_turn(question: str, response: dict[str, Any]) -> str:
    parts = [f"User: {question}"]
    text = (response.get("text") or "").strip()
    if text:
        parts.append(f"Asisten: {text}")
    if response.get("sql"):
        parts.append(f"SQL: {response['sql']}")
    return "\n".join(parts)


def _format_turns(turns: list[tuple[str, dict[str, Any]]]) -> str:
    return "\n\n".join(_format_turn(question, response) for question, response in turns)


def build_conversation_context(summary: str, buffer_turns: list[tuple[str, dict[str, Any]]]) -> str:
    """Combine the rolling summary with the last few turns verbatim, so follow-up questions
    ("itu gimana kalau...") can resolve references to earlier turns without resending the
    whole transcript."""
    parts = []
    if summary:
        parts.append(f"Ringkasan percakapan sebelumnya: {summary}")
    if buffer_turns:
        parts.append("Percakapan beberapa giliran terakhir:\n" + _format_turns(buffer_turns))
    return "\n\n".join(parts)


SUMMARY_SYSTEM_PROMPT = """Anda merangkum riwayat percakapan chatbot analitik rekrutmen PLN menjadi satu ringkasan singkat.
Gabungkan ringkasan sebelumnya dengan giliran percakapan baru menjadi SATU ringkasan Bahasa Indonesia,
maksimal 4 kalimat. Fokus pada topik, filter (wilayah/prodi/metode/dsb), dan angka penting yang mungkin
direferensikan kembali oleh user pada pertanyaan berikutnya. Jangan mengarang informasi yang tidak ada."""


def update_chat_summary(
    existing_summary: str, new_turns: list[tuple[str, dict[str, Any]]], profile: dict[str, str] | None
) -> str:
    """Fold turns that just fell out of the recent-turns buffer into the rolling summary, so
    older context survives without resending the full transcript on every question."""
    if not new_turns:
        return existing_summary
    if not profile_is_configured(profile):
        return existing_summary
    try:
        from openai import OpenAI

        client = OpenAI(api_key=profile["api_key"], base_url=profile["base_url"], timeout=LLM_REQUEST_TIMEOUT)
        response = client.chat.completions.create(
            model=profile["model"],
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Ringkasan sebelumnya: {existing_summary or '(belum ada)'}\n\n"
                        f"Giliran percakapan baru:\n{_format_turns(new_turns)}"
                    ),
                },
            ],
        )
        return (response.choices[0].message.content or "").strip() or existing_summary
    except Exception:
        return existing_summary


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

ALLOWED_CHART_TYPES = {"bar", "line", "pie", "scatter"}

AGENTIC_SYSTEM_PROMPT = """Anda adalah asisten analitik rekrutmen PLN. Jawab dalam Bahasa Indonesia, singkat dan jelas.

Anda punya akses ke tool berikut:
- run_sql_query: jalankan satu query SQL SELECT (dialek DuckDB) ke tabel data di bawah untuk mengambil angka/data nyata.
- render_chart: buat chart dari hasil run_sql_query sebelumnya (dirujuk lewat result_id), kalau memang membantu menjawab.

Aturan:
- Kalau pertanyaan butuh angka/data spesifik dari tabel, WAJIB panggil run_sql_query dulu - jangan pernah mengarang angka.
- Kalau pertanyaan bersifat umum/definisi/sapaan yang tidak butuh data tabel, jawab langsung tanpa memanggil tool apapun.
- SQL: hanya gunakan tabel & kolom yang benar-benar ada pada skema di bawah, jangan mengarang nama kolom/tabel. Nama kolom berspasi HARUS dibungkus tanda kutip dua, misal "NAMA REKRUTMEN". Hanya satu statement SELECT (boleh diawali WITH untuk CTE), tanpa titik koma ganda. Batasi hasil ke maksimal 200 baris (tambahkan LIMIT jika query berpotensi mengembalikan banyak baris).
- Kalau run_sql_query gagal (error atau ditolak), coba perbaiki query sekali berdasarkan pesan errornya; kalau masih gagal, jelaskan keterbatasannya ke user alih-alih mengarang jawaban.
- Setelah dapat hasil query, jawab pertanyaan user berdasarkan hasil (preview) itu saja.
- render_chart bersifat opsional - panggil hanya kalau chart benar-benar menambah nilai (hasil query lebih dari 1 baris dan ada kolom kategori/nilai yang bermakna divisualisasikan).

Skema tabel:
{schema}

Contoh pertanyaan dan SQL:
{examples}
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": (
                "Jalankan satu query SQL SELECT (dialek DuckDB) terhadap tabel data rekrutmen PLN untuk "
                "mendapatkan angka/data yang dibutuhkan menjawab pertanyaan user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "Satu statement SQL SELECT (boleh diawali WITH untuk CTE).",
                    }
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_chart",
            "description": (
                "Render chart dari hasil run_sql_query sebelumnya. Panggil hanya kalau user butuh "
                "visualisasi dan datanya cocok divisualisasikan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "result_id": {
                        "type": "string",
                        "description": "result_id dari hasil run_sql_query yang mau divisualisasikan.",
                    },
                    "chart_type": {"type": "string", "enum": sorted(ALLOWED_CHART_TYPES)},
                    "x": {"type": "string", "description": "Nama kolom untuk sumbu x (kategori untuk pie)."},
                    "y": {"type": "string", "description": "Nama kolom untuk sumbu y (nilai untuk pie)."},
                    "color": {"type": "string", "description": "Nama kolom untuk pengelompokan warna (opsional)."},
                    "title": {"type": "string", "description": "Judul singkat chart (opsional)."},
                },
                "required": ["result_id", "chart_type", "x", "y"],
            },
        },
    },
]

MAX_TOOL_ITERATIONS = 4


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


def _build_chart(spec: dict[str, Any], table: pd.DataFrame) -> Any | None:
    """Render a chart from a validated LLM-provided spec. Only whitelisted chart types and
    columns that actually exist on `table` are ever passed to Plotly - the LLM never supplies
    code, just a declarative spec, so there's nothing here to execute or inject."""
    if not spec.get("should_plot"):
        return None
    chart_type = spec.get("chart_type")
    if chart_type not in ALLOWED_CHART_TYPES:
        return None
    columns = set(table.columns)
    x, y = spec.get("x"), spec.get("y")
    if x not in columns or y not in columns:
        return None
    color = spec.get("color")
    if color not in columns:
        color = None
    title = spec.get("title") or None
    try:
        import plotly.express as px

        if chart_type == "bar":
            return px.bar(table, x=x, y=y, color=color, title=title)
        if chart_type == "line":
            return px.line(table, x=x, y=y, color=color, title=title)
        if chart_type == "scatter":
            return px.scatter(table, x=x, y=y, color=color, title=title)
        if chart_type == "pie":
            return px.pie(table, names=x, values=y, title=title)
    except Exception:
        return None
    return None


def _dispatch_tool_call(
    name: str,
    args: dict[str, Any],
    dataframes: dict[str, pd.DataFrame],
    results: dict[str, pd.DataFrame],
) -> tuple[dict[str, Any], pd.DataFrame | None, Any | None]:
    """Execute one tool call. Returns (payload sent back to the LLM, table produced, chart produced)."""
    if name == "run_sql_query":
        sql = _extract_sql(str(args.get("sql", "")))
        if not _is_safe_select(sql):
            return (
                {"error": "Query ditolak: hanya satu statement SELECT/WITH ke tabel yang tersedia yang diperbolehkan."},
                None,
                None,
            )
        try:
            table = _execute_sql(sql, dataframes)
        except Exception as exc:
            return {"error": f"Query SQL gagal dieksekusi: {exc}", "sql": sql}, None, None
        result_id = f"result_{len(results) + 1}"
        results[result_id] = table
        payload = {
            "result_id": result_id,
            "sql": sql,
            "row_count": int(table.shape[0]),
            "columns": list(table.columns),
            "preview": table.head(20).to_dict(orient="records"),
        }
        return payload, table, None

    if name == "render_chart":
        result_id = args.get("result_id")
        table = results.get(result_id)
        if table is None:
            return (
                {"error": f"result_id '{result_id}' tidak ditemukan. Panggil run_sql_query dulu sebelum render_chart."},
                None,
                None,
            )
        spec = {
            "should_plot": True,
            "chart_type": args.get("chart_type"),
            "x": args.get("x"),
            "y": args.get("y"),
            "color": args.get("color") or None,
            "title": args.get("title") or None,
        }
        chart = _build_chart(spec, table)
        if chart is None:
            return (
                {
                    "error": (
                        "Parameter chart tidak valid: pastikan chart_type salah satu dari "
                        f"{sorted(ALLOWED_CHART_TYPES)} dan x/y adalah nama kolom hasil query."
                    )
                },
                None,
                None,
            )
        return {"chart_ready": True}, None, chart

    return {"error": f"Tool '{name}' tidak dikenal."}, None, None


# Tool identifiers should never appear in a legitimate natural-language answer. Some
# OpenAI-compatible endpoints accept the `tools` param but don't actually implement function
# calling - they just fold the tool definitions into the prompt, and the model echoes them back
# (sometimes with hallucinated code) instead of returning structured tool_calls. Surfacing that
# leaked internal prompt to the user would be worse than an honest error.
_TOOL_LEAK_MARKERS = ("run_sql_query", "render_chart")


def _create_chat_completion(client: Any, **kwargs: Any) -> Any:
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as exc:
        # Some reasoning models (e.g. gpt-5.x variants) apply a default reasoning_effort that's
        # incompatible with function calling on /v1/chat/completions; retry once with it disabled.
        if "reasoning_effort" in str(exc) and "reasoning_effort" not in kwargs:
            return client.chat.completions.create(**kwargs, reasoning_effort="none")
        raise


def llm_answer(
    question: str,
    dataframes: dict[str, pd.DataFrame] | None,
    profile: dict[str, str] | None,
    conversation_context: str = "",
) -> dict[str, Any] | None:
    """Agentic loop: the model decides whether/when to call run_sql_query and render_chart,
    can see tool errors (e.g. a failed query) and retry, and writes the final answer itself
    once it has what it needs - no separate generate-SQL/narrate/chart-spec calls."""
    if not profile_is_configured(profile) or not dataframes:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=profile["api_key"], base_url=profile["base_url"], timeout=LLM_REQUEST_TIMEOUT)
        schema_prompt = _build_schema_prompt(dataframes)
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": AGENTIC_SYSTEM_PROMPT.format(schema=schema_prompt, examples=SQL_FEW_SHOT),
            }
        ]
        if conversation_context:
            messages.append(
                {"role": "user", "content": f"Konteks percakapan sebelumnya:\n{conversation_context}"}
            )
        messages.append({"role": "user", "content": question})

        results: dict[str, pd.DataFrame] = {}
        last_sql: str | None = None
        last_table: pd.DataFrame | None = None
        last_chart: Any | None = None

        for _ in range(MAX_TOOL_ITERATIONS):
            response = _create_chat_completion(
                client, model=profile["model"], messages=messages, tools=TOOLS, tool_choice="auto"
            )
            message = response.choices[0].message
            tool_calls = message.tool_calls or []
            if not tool_calls:
                text = (message.content or "").strip()
                if any(marker in text for marker in _TOOL_LEAK_MARKERS):
                    return {
                        "text": (
                            "Model ini sepertinya belum mendukung tool-calling dengan baik (definisi "
                            "tool internal bocor ke jawaban, bukan benar-benar dipanggil). Coba pilih "
                            "model lain."
                        ),
                        "sql": None,
                        "table": None,
                        "chart": None,
                    }
                return {
                    "text": text or "Maaf, saya tidak berhasil menyusun jawaban.",
                    "sql": last_sql,
                    "table": last_table,
                    "chart": last_chart,
                }

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                payload, table, chart = _dispatch_tool_call(tc.function.name, args, dataframes, results)
                if table is not None:
                    last_sql = payload.get("sql", last_sql)
                    last_table = table
                if chart is not None:
                    last_chart = chart
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(payload, default=str)}
                )

        return {
            "text": "Maaf, permintaan ini butuh terlalu banyak langkah untuk dijawab. Coba pertanyaan yang lebih spesifik.",
            "sql": last_sql,
            "table": last_table,
            "chart": last_chart,
        }
    except Exception as exc:
        return {"text": f"Koneksi chatbot belum berhasil: {exc}", "sql": None, "table": None, "chart": None}


def answer_question(
    question: str,
    context: dict[str, Any],
    dataframes: dict[str, pd.DataFrame] | None = None,
    profile: dict[str, str] | None = None,
    conversation_context: str = "",
) -> dict[str, Any]:
    if profile_is_configured(profile):
        llm_result = llm_answer(question, dataframes, profile, conversation_context)
        if llm_result:
            return {"kind": "llm", **llm_result}

    deterministic = local_answer(question, context)
    if deterministic:
        return {"kind": "local", "text": deterministic, "sql": None, "table": None, "chart": None}

    return {
        "kind": "fallback",
        "text": (
            "Untuk demo tanpa API, saya dapat menjawab pertanyaan tentang konversi kontrak, bottleneck, "
            "perbandingan metode, kesesuaian penempatan, vacancy kritis, dan sebaran wilayah. "
            "Konfigurasikan kredensial LLM untuk pertanyaan yang lebih fleksibel."
        ),
        "sql": None,
        "table": None,
        "chart": None,
    }
