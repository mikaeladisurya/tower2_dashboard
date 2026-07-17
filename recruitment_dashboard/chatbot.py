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


def answer_question(question: str, context: dict[str, Any]) -> str:
    deterministic = local_answer(question, context)
    if deterministic:
        return deterministic
    llm_response = llm_answer(question, context)
    if llm_response:
        return llm_response
    return (
        "Untuk demo tanpa API, saya dapat menjawab pertanyaan tentang konversi kontrak, bottleneck, "
        "perbandingan metode, kesesuaian penempatan, vacancy kritis, dan sebaran wilayah. "
        "Konfigurasikan kredensial LLM untuk pertanyaan yang lebih fleksibel."
    )
