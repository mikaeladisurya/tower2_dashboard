"""R1-login — Ambil SKEMA biodata/CV dari akun sendiri di rekrutmen.pln.co.id.

Human-in-the-loop: skrip membuka browser (terlihat), KAMU yang login + isi captcha.
Setelah terdeteksi masuk, skrip mengambil alih dan merekam STRUKTUR halaman.

PRIVASI: tujuannya SKEMA (nama field/label/opsi dropdown), bukan isi data pribadi.
Nilai input sengaja TIDAK diekstrak ke ringkasan skema. Dump HTML & screenshot tetap
disimpan untuk verifikasi manual, tapi foldernya di-gitignore -> jangan pernah di-commit.

Output -> knowledge/sources/rekrutmen_pln/akun/   (GITIGNORED)
    <slug>.html / <slug>.png     dump mentah tiap halaman
    skema_form.md                daftar field/label/opsi hasil ekstraksi

Jalankan:
  recruitment_dashboard/.venv/Scripts/python.exe knowledge/build/r1d_login_skema_cv.py
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://rekrutmen.pln.co.id"
LOGIN_URL = f"{BASE}/member/jobseeker/index"
PAGES = [
    ("beranda-akun", f"{BASE}/member/jobseeker/index"),
    ("pratayang-cv", f"{BASE}/member/jobseeker/view/t/pratayang-cv"),
    ("rekap-lamaran", f"{BASE}/vacancy/member/recap/t/rekap-lamaran"),
]

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "knowledge" / "sources" / "rekrutmen_pln" / "akun"
PROFILE = ROOT / "knowledge" / "sources" / "rekrutmen_pln" / ".browser_profile"
LOGIN_TIMEOUT = 15 * 60  # detik


def is_logged_in(page) -> bool:
    """Terdeteksi masuk kalau ada tautan logout / menu member khas area login."""
    try:
        html = page.content().lower()
    except Exception:  # noqa: BLE001
        return False
    if any(k in html for k in ("/site/logout", "keluar akun", "logout")):
        return True
    return any(k in html for k in ("rekap lamaran", "pratayang cv", "pratayang-cv"))


def extract_schema(page, slug: str) -> list[str]:
    """Kumpulkan STRUKTUR form: label, nama field, tipe, opsi select. Bukan nilainya."""
    lines = [f"\n## Halaman: {slug}", f"URL: {page.url}\n"]

    labels = page.eval_on_selector_all(
        "label", "els => els.map(e => e.innerText.trim()).filter(t => t)")
    if labels:
        lines.append("### Label yang tampil")
        for t in dict.fromkeys(labels):
            lines.append(f"- {t}")

    fields = page.eval_on_selector_all(
        "input, select, textarea",
        """els => els.map(e => ({
             tag: e.tagName.toLowerCase(),
             type: e.getAttribute('type') || '',
             name: e.getAttribute('name') || '',
             id: e.getAttribute('id') || '',
             required: e.hasAttribute('required'),
             opts: e.tagName.toLowerCase() === 'select'
                   ? Array.from(e.options).map(o => o.text.trim()).slice(0, 40) : []
           })).filter(f => f.name || f.id)""")
    if fields:
        lines.append("\n### Field form (nama/tipe — TANPA nilai)")
        for f in fields:
            if f["type"] in ("hidden", "submit", "button", "csrf"):
                continue
            req = " *(wajib)*" if f["required"] else ""
            lines.append(f"- `{f['name'] or f['id']}` — {f['tag']}/{f['type']}{req}")
            if f["opts"]:
                lines.append(f"    - opsi: {', '.join(o for o in f['opts'] if o)[:400]}")

    heads = page.eval_on_selector_all(
        "th, .panel-heading, h1, h2, h3, h4, legend",
        "els => els.map(e => e.innerText.trim()).filter(t => t && t.length < 90)")
    if heads:
        lines.append("\n### Judul bagian / kolom tabel")
        for t in dict.fromkeys(heads):
            lines.append(f"- {t}")
    return lines


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), headless=False,
            viewport={"width": 1440, "height": 950},
            args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("=" * 72)
        print(" BROWSER TERBUKA — giliran kamu:")
        print("   1. Login pakai akunmu sendiri")
        print("   2. Selesaikan captcha kalau muncul")
        print("   3. Biarkan browser terbuka; skrip lanjut otomatis setelah terdeteksi masuk")
        print(f"   (batas tunggu {LOGIN_TIMEOUT // 60} menit)")
        print("=" * 72, flush=True)

        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        deadline = time.time() + LOGIN_TIMEOUT
        ok = False
        while time.time() < deadline:
            if is_logged_in(page):
                ok = True
                break
            time.sleep(3)
        if not ok:
            print("\nBelum terdeteksi login sampai batas waktu. Skrip berhenti; tidak ada data diambil.")
            ctx.close()
            return 1

        print("\n>> Terdeteksi sudah masuk. Mengambil struktur halaman ...\n", flush=True)
        schema: list[str] = ["# Skema form akun rekrutmen.pln.co.id",
                             "\n> Diambil dari akun milik user sendiri. Berisi STRUKTUR (label/field/opsi),",
                             "> bukan nilai data pribadi.\n"]
        for slug, url in PAGES:
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
            except Exception:  # noqa: BLE001
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            (OUT / f"{slug}.html").write_text(page.content(), encoding="utf-8")
            page.screenshot(path=str(OUT / f"{slug}.png"), full_page=True)
            schema += extract_schema(page, slug)
            print(f"   [ok] {slug}  <- {page.url}", flush=True)

        # tautan lain di area member (mungkin ada sub-form biodata terpisah)
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.getAttribute('href')).filter(h => h && h.includes('/member/'))")
        uniq = sorted(dict.fromkeys(links))
        if uniq:
            schema.append("\n## Tautan area member yang terdeteksi")
            schema += [f"- {h}" for h in uniq[:60]]

        (OUT / "skema_form.md").write_text("\n".join(schema), encoding="utf-8")
        print(f"\nselesai -> {OUT}")
        print("   skema_form.md  (struktur field)")
        print("   *.html / *.png (dump mentah — JANGAN di-commit)")
        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
