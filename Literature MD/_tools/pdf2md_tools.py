# Edgar Danyael Arellano Hernandez
# 220448792
import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

TOOL_VERSION = "1.1-cloud"
TOOL_DIR = Path(__file__).resolve().parent
MD_ROOT = TOOL_DIR.parent
HOME_BASE = MD_ROOT.parent
SRC_ROOT = HOME_BASE / "Literature"
WORKSHOP = MD_ROOT / "_trabajo"
LEDGER = MD_ROOT / "00_CHECKPOINT.csv"
JOURNAL = MD_ROOT / "00_BITACORA.md"
RULEBOOK = MD_ROOT / "00_INSTRUCCION_PDF_a_MD.md"
KATEX_PROBE = TOOL_DIR / "katex_check.js"
COLUMNS = ["orden", "ref", "id", "pilar", "tipo", "lote", "pdf", "md", "paginas", "texto", "sha12",
           "estado", "paginas_hechas", "inicio", "fin", "agente", "qc", "notas"]
BATCH = {"articulo": 1, "preprint": 1, "patente": 1, "norma": 2, "guia": 2, "datasheet": 3, "libro": 4}
BLOCK_SIZE = 25
LONG_DOC = 40
CAPTION_RX = re.compile(r"^\s*(fig(?:ure)?s?\.?|table|tab\.|plate|scheme)\s*([0-9]+[a-z]?|[ivxlc]+)(?=$|[\s.:—–\-|)])", re.I)
EQNUM_RX = re.compile(r"\(\s*((?:[A-Z]\.?)?\d{1,3}[a-z]?|[A-Z]\.\d{1,2}[a-z]?)\s*\)\s*$")
GREEK = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ",
         "eta": "η", "theta": "θ", "vartheta": "θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν",
         "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ",
         "chi": "χ", "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
         "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω", "%": "%"}


def pdf_engine():
    try:
        import pymupdf
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-q", "pymupdf"], check=False)
        import pymupdf
    return pymupdf


def stamp():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def emit(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if code:
        sys.exit(code)


def natural_key(text):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


def sha12(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def load_ledger():
    if not LEDGER.exists():
        return []
    with open(LEDGER, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def save_ledger(rows):
    staging = LEDGER.with_suffix(".tmp")
    with open(staging, "w", encoding="utf-8-sig", newline="") as fh:
        scribe = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        scribe.writeheader()
        for row in rows:
            scribe.writerow({k: row.get(k, "") for k in COLUMNS})
    os.replace(staging, LEDGER)


def journal(doc_id, event, detail=""):
    if not JOURNAL.exists():
        JOURNAL.write_text("# Bitácora de conversión PDF → MD\n\n| fecha | id | evento | detalle |\n|---|---|---|---|\n",
                           encoding="utf-8")
    tidy = detail.replace("|", "\\|").replace("\n", " ")
    with open(JOURNAL, "a", encoding="utf-8") as fh:
        fh.write(f"| {stamp()} | {doc_id} | {event} | {tidy} |\n")


def locate(rows, doc_id):
    for row in rows:
        if row["id"] == doc_id:
            return row
    emit({"ok": False, "mensaje": f"ID no encontrado en el checkpoint: {doc_id}"}, 2)


def classify(stem):
    low = stem.lower()
    if "datasheet" in low:
        return "datasheet"
    if re.search(r"\d{4}pat_", low):
        return "patente"
    if low.startswith("nom-"):
        return "norma"
    if "guideline" in low:
        return "guia"
    if "preprint" in low:
        return "preprint"
    if re.search(r"_\d+ed$", low):
        return "libro"
    return "articulo"


def sniff_text_layer(doc, pm):
    origin = " ".join(str(doc.metadata.get(k) or "") for k in ("producer", "creator"))
    total, scanned = 0, 0
    for page in doc:
        total += len(page.get_text("text").strip())
        area = abs(page.rect)
        for info in page.get_image_info():
            if abs(pm.Rect(info["bbox"]) & page.rect) >= 0.55 * area:
                scanned += 1
                break
    if total / max(1, len(doc)) < 40:
        return "no"
    if scanned >= 0.5 * len(doc) or re.search(r"(?i)capture|import plug-in|tiff2pdf|abbyy|omnipage|clearscan", origin):
        return "ocr"
    return "si"


def doc_paths(row):
    md_file = HOME_BASE / row["md"]
    return HOME_BASE / row["pdf"], md_file, md_file.parent, WORKSHOP / row["id"]


def parse_span(text):
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", text)
    if not m:
        m1 = re.fullmatch(r"\s*(\d+)\s*", text)
        if not m1:
            emit({"ok": False, "mensaje": f"rango inválido: {text}"}, 2)
        return int(m1.group(1)), int(m1.group(1))
    return int(m.group(1)), int(m.group(2))


def block_range(row):
    total, done = int(row["paginas"]), int(row["paginas_hechas"] or 0)
    start = done + 1 if done < total else 1
    if total <= LONG_DOC:
        return start, total
    end = start + BLOCK_SIZE - 1
    if total - end <= 5:
        end = total
    return start, min(end, total)


def cmd_sync(args):
    pm = pdf_engine()
    SRC_ROOT.mkdir(exist_ok=True)
    MD_ROOT.mkdir(exist_ok=True)
    unpacked = []
    for bundle in sorted(HOME_BASE.glob("Parte_*.zip"), key=lambda p: natural_key(p.name)):
        with zipfile.ZipFile(bundle) as zf:
            for info in zf.infolist():
                name = Path(info.filename)
                if info.filename.lower().endswith(".pdf"):
                    pillar = name.parts[0] if len(name.parts) > 1 else bundle.stem
                    target = SRC_ROOT / pillar / name.name
                    if not target.exists() or target.stat().st_size != info.file_size:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        unpacked.append(target.relative_to(HOME_BASE).as_posix())
                elif name.name.startswith("00_INSTRUCCION") and not RULEBOOK.exists():
                    RULEBOOK.write_bytes(zf.read(info))
    registry = {r["id"]: r for r in load_ledger()}
    added, changed = [], []
    for pdf in sorted(SRC_ROOT.rglob("*.pdf"), key=lambda p: natural_key(p.as_posix())):
        doc_id, pillar = pdf.stem, pdf.parent.name
        digest = sha12(pdf)
        if doc_id in registry and registry[doc_id]["sha12"] == digest:
            continue
        doc = pm.open(pdf)
        kind = classify(doc_id)
        fresh = {"ref": "", "id": doc_id, "pilar": pillar, "tipo": kind, "lote": str(BATCH[kind]),
                 "pdf": pdf.relative_to(HOME_BASE).as_posix(), "md": f"Literature MD/{pillar}/{doc_id}/{doc_id}.md",
                 "paginas": str(len(doc)), "texto": sniff_text_layer(doc, pm), "sha12": digest,
                 "estado": "PENDIENTE", "paginas_hechas": "0", "inicio": "", "fin": "", "agente": "", "qc": "",
                 "notas": ""}
        if doc_id in registry:
            fresh["notas"] = f"PDF cambió (sha12 anterior {registry[doc_id]['sha12']})"
            changed.append(doc_id)
        else:
            added.append(doc_id)
        registry[doc_id] = fresh
    ordered = sorted(registry.values(), key=lambda r: (natural_key(r["pilar"]), int(r["lote"]), natural_key(r["id"])))
    for i, row in enumerate(ordered, 1):
        row["orden"] = str(i)
    save_ledger(ordered)
    if added or changed:
        journal("-", "sync", f"{len(added)} nuevos, {len(changed)} cambiados, {len(ordered)} en cola")
    emit({"ok": True, "extraidos": len(unpacked), "nuevos": added, "cambiados": changed, "total": len(ordered)})


def cmd_next(args):
    rows = load_ledger()
    scope = [r for r in rows if not args.pilar or r["pilar"] == args.pilar]
    active = [r for r in rows if r["estado"] == "EN_PROCESO"]
    queue = [r for r in scope if r["estado"] in ("PENDIENTE", "PARCIAL")]
    if active:
        pick, action = active[0], "REANUDAR"
    elif queue:
        pick = queue[0]
        action = "REANUDAR" if pick["estado"] == "PARCIAL" else "INICIAR"
    else:
        emit({"accion": "COLA_TERMINADA", "revisar": [r["id"] for r in scope if r["estado"] in ("REVISAR", "ERROR")]})
        return
    pdf, md_file, _, shop = doc_paths(pick)
    a, b = block_range(pick)
    emit({"accion": action, "id": pick["id"], "orden": int(pick["orden"]), "total": len(rows), "pilar": pick["pilar"],
          "pdf": str(pdf), "md": str(md_file), "paginas": int(pick["paginas"]), "texto": pick["texto"],
          "tipo": pick["tipo"], "estado": pick["estado"], "paginas_hechas": int(pick["paginas_hechas"] or 0),
          "paginas_esta_llamada": f"{a}-{b}", "trabajo": str(shop), "sha12": pick["sha12"]})


def cmd_status(args):
    rows = load_ledger()
    tally = Counter(r["estado"] for r in rows)
    pages = sum(int(r["paginas"]) for r in rows)
    done_pages = sum(int(r["paginas_hechas"] or 0) for r in rows)
    headline = (f"Progreso: {tally.get('COMPLETO', 0)} de {len(rows)} documentos COMPLETO · {done_pages} de {pages} páginas"
                f" · EN_PROCESO {tally.get('EN_PROCESO', 0)} · PARCIAL {tally.get('PARCIAL', 0)} · REVISAR {tally.get('REVISAR', 0)}"
                f" · ERROR {tally.get('ERROR', 0)} · PENDIENTE {tally.get('PENDIENTE', 0)}")
    print(headline)
    pillars = {}
    for r in rows:
        pillars.setdefault(r["pilar"], Counter())[r["estado"]] += 1
    for name in sorted(pillars, key=natural_key):
        print(f"  {name}: " + ", ".join(f"{k} {v}" for k, v in sorted(pillars[name].items())))


def cmd_lock(args):
    rows = load_ledger()
    row = locate(rows, args.id)
    rival = [r for r in rows if r["estado"] == "EN_PROCESO" and r["id"] != args.id]
    if rival:
        emit({"ok": False, "mensaje": f"ya hay otro documento EN_PROCESO: {rival[0]['id']}", "id": rival[0]["id"]}, 2)
    if row["estado"] == "COMPLETO":
        emit({"ok": False, "mensaje": "el documento ya está COMPLETO"}, 2)
    row["estado"] = "EN_PROCESO"
    row["agente"] = args.agente
    row["inicio"] = row["inicio"] or stamp()
    save_ledger(rows)
    journal(args.id, "lock", args.agente)
    emit({"ok": True, "id": args.id, "estado": "EN_PROCESO"})


def cmd_unlock(args):
    rows = load_ledger()
    row = locate(rows, args.id)
    row["estado"] = "PARCIAL" if int(row["paginas_hechas"] or 0) > 0 else "PENDIENTE"
    row["notas"] = f"unlock: {args.motivo}"
    save_ledger(rows)
    journal(args.id, "unlock", args.motivo)
    emit({"ok": True, "id": args.id, "estado": row["estado"]})


def line_text(line):
    return "".join(s["text"] for s in line["spans"])


def reading_lines(page):
    width = page.rect.width
    mid = width / 2
    rows = []
    for bno, block in enumerate(page.get_text("dict")["blocks"]):
        for lno, line in enumerate(block.get("lines", [])):
            if not line_text(line).strip():
                continue
            x0, y0, x1, y1 = line["bbox"]
            lane = 0 if x1 <= mid + 0.02 * width else (1 if x0 >= mid - 0.02 * width else -1)
            rows.append({"lane": lane, "y": y0, "line": line, "block": bno, "first": lno == 0})
    if sum(r["lane"] == 0 for r in rows) < 5 or sum(r["lane"] == 1 for r in rows) < 5:
        return rows
    ordered, left, right = [], [], []
    for row in sorted(rows, key=lambda r: (r["y"], r["line"]["bbox"][0])):
        if row["lane"] == -1:
            ordered += sorted(left, key=lambda r: r["y"]) + sorted(right, key=lambda r: r["y"]) + [row]
            left, right = [], []
        else:
            (left if row["lane"] == 0 else right).append(row)
    return ordered + sorted(left, key=lambda r: r["y"]) + sorted(right, key=lambda r: r["y"])


def ordered_text(page):
    return "\n".join(line_text(r["line"]) for r in reading_lines(page))


def unmask(doc, xref, pix):
    try:
        if doc.xref_get_key(xref, "ImageMask")[1] == "true" and "1 0" not in doc.xref_get_key(xref, "Decode")[1]:
            pix.invert_irect(pix.irect)
    except Exception:
        pass
    return pix


def frac_box(rect, page):
    w, h = page.rect.width, page.rect.height
    return [round(max(0, rect[0]) / w, 4), round(max(0, rect[1]) / h, 4), round(min(w, rect[2]) / w, 4),
            round(min(h, rect[3]) / h, 4)]


def span_traits(span, anchor_y, anchor_size):
    flags, font = span["flags"], span["font"].lower()
    italic = bool(flags & 2) or any(k in font for k in ("italic", "oblique")) or bool(re.search(r"[-,](it|i|bi|boldit)$", font))
    bold = bool(flags & 16) or any(k in font for k in ("bold", "black", "heavy", "semibold", "demi")) or bool(
        re.search(r"[-,](b|bd|bi)$", font))
    small = span["size"] < 0.86 * anchor_size
    lift = span["origin"][1] - anchor_y
    sup = bool(flags & 1) or (small and lift < -0.12 * anchor_size)
    sub = (not sup) and small and lift > 0.08 * anchor_size
    return italic, bold, sup, sub


def md_escape(text):
    text = text.replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_")
    return text.replace("<", "&lt;")


def wrap_style(text, traits):
    italic, bold, sup, sub = traits
    lead = text[:len(text) - len(text.lstrip())]
    tail = text[len(text.rstrip()):]
    core = md_escape(text.strip())
    if not core:
        return text
    if sup:
        core = f"<sup>{core}</sup>"
    elif sub:
        core = f"<sub>{core}</sub>"
    if bold and italic:
        core = f"***{core}***"
    elif bold:
        core = f"**{core}**"
    elif italic:
        core = f"*{core}*"
    return lead + core + tail


def styled_line(line, plain=False):
    spans = [s for s in line["spans"] if s["text"]]
    if not spans:
        return "", "", False
    if plain:
        text = "".join(s["text"] for s in spans)
        return md_escape(text), text, False
    anchor = max(spans, key=lambda s: len(s["text"].strip()) * s["size"])
    groups = []
    for s in spans:
        traits = span_traits(s, anchor["origin"][1], anchor["size"])
        if not s["text"].strip():
            traits = groups[-1][1] if groups else traits
        if groups and groups[-1][1] == traits:
            groups[-1][0] += s["text"]
        else:
            groups.append([s["text"], traits])
    plain = "".join(s["text"] for s in spans)
    all_bold = all(g[1][1] for g in groups if g[0].strip())
    return "".join(wrap_style(t, tr) for t, tr in groups), plain, all_bold


def hyphen_verdict(left, right, corpus_low):
    joined = (left + right).lower()
    dashed = (left + "-" + right).lower()
    n_joined = len(re.findall(rf"(?<![\w-]){re.escape(joined)}(?![\w-])", corpus_low))
    n_dashed = len(re.findall(rf"(?<![\w-]){re.escape(dashed)}(?![\w-])", corpus_low))
    if n_joined and not n_dashed:
        return "unir", n_joined, n_dashed
    if n_dashed and not n_joined:
        return "conservar", n_joined, n_dashed
    return "ambiguo", n_joined, n_dashed


def flat_corpus(doc):
    pieces = []
    for page in doc:
        for line in page.get_text("text").split("\n"):
            pieces.append(line[:-1] if line.endswith(("-", "¬")) else line + " ")
    return "".join(pieces).lower()


def body_font_size(doc, a, b):
    sizes = Counter()
    for n in range(a, b + 1):
        for block in doc[n - 1].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for s in line["spans"]:
                    sizes[round(s["size"], 1)] += len(s["text"].strip())
    return sizes.most_common(1)[0][0] if sizes else 10.0


def page_draft(page, n, base_size, corpus_low, hyphen_log, plain=False):
    note = "capa OCR: sin estilos, tomarlos de la imagen" if plain else "guía de estilos"
    out = [f"<!-- BORRADOR AUTOMÁTICO p{n}: {note}; verificar todo contra la imagen -->", ""]
    blocks = [b for b in page.get_text("dict")["blocks"] if b["type"] == 0]
    for k, block in enumerate(blocks, 1):
        rendered = []
        bold_lines, sizes = [], []
        for line in block["lines"]:
            styled, bare, all_bold = styled_line(line, plain)
            if bare.strip():
                rendered.append([styled, bare])
                bold_lines.append(all_bold)
                sizes.extend(s["size"] for s in line["spans"] if s["text"].strip())
        if not rendered:
            continue
        text = rendered[0][0].rstrip()
        for i in range(1, len(rendered)):
            prev_plain, nxt = rendered[i - 1][1].rstrip(), rendered[i][0].lstrip()
            nxt_plain = rendered[i][1].lstrip()
            if prev_plain.endswith(("-", "¬")) and len(prev_plain) > 1 and prev_plain[-2].isalpha() and nxt_plain[:1].islower():
                left = re.findall(r"[\w]+$", prev_plain[:-1])
                right = re.findall(r"^[\w]+", nxt_plain)
                if left and right:
                    verdict, nj, nd = hyphen_verdict(left[0], right[0], corpus_low)
                    hyphen_log.append({"pagina": n, "bloque": k, "izquierda": left[0], "derecha": right[0],
                                       "unida": left[0] + right[0], "decision": verdict, "veces_unida": nj,
                                       "veces_con_guion": nd})
                    text = text[:-1] if text.endswith(("-", "¬")) else text
                    joint = {"unir": "", "conservar": "-", "ambiguo": "⟦-⟧"}[verdict]
                    text = text + joint + nxt
                    continue
            text = text + " " + nxt
        words = len(re.findall(r"\w+", "".join(r[1] for r in rendered)))
        big = statistics.mean(sizes) >= 1.12 * base_size if sizes else False
        heading = len(rendered) <= 3 and words <= 16 and (all(bold_lines) or big) and not plain
        box = frac_box(block["bbox"], page)
        out.append(f"<!-- b{k} [{box[0]:.3f} {box[1]:.3f} {box[2]:.3f} {box[3]:.3f}] -->")
        out.append(("§ " if heading else "") + re.sub(r"[ \t]+", " ", text).strip())
        out.append("")
    return "\n".join(out)


def graphic_regions(page, pm):
    zones = []
    for info in page.get_image_info(xrefs=True):
        r = pm.Rect(info["bbox"]) & page.rect
        if r.width > 8 and r.height > 8:
            zones.append(("imagen", r))
    try:
        clusters = page.cluster_drawings()
    except Exception:
        clusters = []
    for r in clusters:
        if r.width > 20 and r.height > 20:
            zones.append(("vector", pm.Rect(r)))
    return zones


def caption_hits(page):
    hits, seen = [], set()
    rows = reading_lines(page)
    for i, row in enumerate(rows):
        text = line_text(row["line"]).strip()
        if re.fullmatch(r"(?i)(fig(?:ure)?s?\.?|table|tab\.)", text) and i + 1 < len(rows):
            text = text + " " + line_text(rows[i + 1]["line"]).strip()
        m = CAPTION_RX.match(text)
        if not m:
            continue
        spans = [s for s in row["line"]["spans"] if s["text"].strip()]
        lead_bold = bool(spans) and (bool(spans[0]["flags"] & 16) or "bold" in spans[0]["font"].lower())
        if not (row["first"] or lead_bold or m.group(1).isupper()):
            continue
        kind = "tabla" if m.group(1).lower().startswith("tab") else "figura"
        key = (kind, m.group(2).lower())
        if key in seen:
            continue
        seen.add(key)
        hits.append({"tipo": kind, "etiqueta": f"{m.group(1)} {m.group(2)}".strip(), "num": m.group(2).lower(),
                     "texto": text[:90], "bbox": list(row["line"]["bbox"])})
    return hits


def crop_proposal(page, pm, hit, zones):
    cap = pm.Rect(hit["bbox"])
    h = page.rect.height
    if hit["tipo"] == "figura":
        above = [z for _, z in zones if z.y1 <= cap.y0 + 6 and z.y1 >= cap.y0 - 0.8 * h]
        below = [z for _, z in zones if z.y0 >= cap.y1 - 6 and z.y0 <= cap.y1 + 0.8 * h]
        pool = sorted(above, key=lambda z: -z.y1) if above else sorted(below, key=lambda z: z.y0)
        if not pool:
            return None
        union = pm.Rect(pool[0])
        for z in pool[1:]:
            gap = (union.y0 - z.y1) if above else (z.y0 - union.y1)
            if gap < 0.08 * h:
                union |= z
        for w in page.get_text("words"):
            wr = pm.Rect(w[:4])
            if wr.intersects(union + (-12, -12, 12, 12)) and not wr.intersects(cap):
                union |= wr
        return frac_box(union + (-4, -4, 4, 4), page)
    rules = [pm.Rect(d["rect"]) for d in page.get_drawings() if d["rect"].height < 2.5 and d["rect"].width > 30]
    under = sorted([r for r in rules if r.y0 >= cap.y0 - 4 and r.y0 <= cap.y1 + 0.85 * h], key=lambda r: r.y0)
    if not under:
        return frac_box(cap + (-4, -4, 4, 4), page)
    union = pm.Rect(cap)
    last = cap.y1
    for r in under:
        if r.y0 - last > 0.35 * h:
            break
        union |= r
        last = r.y1
    return frac_box(union + (-4, -4, 4, 40), page)


def numbered_equations(page):
    found = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            m = EQNUM_RX.search(text)
            if not m:
                continue
            body = text[:m.start()].strip()
            mathy = sum(1 for c in body if c in "=+−-×·/^_()[]∑∫√αβγδεθλμσφωΩ∞≤≥≈")
            words = re.findall(r"[A-Za-z]{4,}", body)
            if (not body) or (mathy >= 1 and len(words) <= 3):
                found.append({"etiqueta": m.group(1), "texto": text[:80], "bbox": frac_box(line["bbox"], page)})
    return found


def save_pixmap(pix, target, pm):
    if pix.colorspace and pix.colorspace.n >= 4:
        pix = pm.Pixmap(pm.csRGB, pix)
    if pix.alpha and str(target).lower().endswith((".jpg", ".jpeg")):
        pix = pm.Pixmap(pix, 0)
    if str(target).lower().endswith((".jpg", ".jpeg")):
        pix.save(str(target), jpg_quality=90)
    else:
        pix.save(str(target))
    return pix.width, pix.height


def cmd_prep(args):
    pm = pdf_engine()
    rows = load_ledger()
    row = locate(rows, args.id)
    pdf, md_file, doc_dir, shop = doc_paths(row)
    if sha12(pdf) != row["sha12"]:
        emit({"ok": False, "mensaje": "el sha12 del PDF no coincide con el checkpoint; corre sync"}, 2)
    doc = pm.open(pdf)
    a, b = parse_span(args.paginas) if args.paginas else block_range(row)
    b = min(b, len(doc))
    for sub in ("pag", "txt", "draft", "emb", "ocr", "zoom", "grid"):
        (shop / sub).mkdir(parents=True, exist_ok=True)
    (doc_dir / "img").mkdir(parents=True, exist_ok=True)
    corpus_low = flat_corpus(doc)
    base_size = body_font_size(doc, a, b)
    hyphen_log, pages_meta, seen = [], [], set()
    tesseract = shutil.which("tesseract")
    for n in range(a, b + 1):
        page = doc[n - 1]
        save_pixmap(page.get_pixmap(dpi=140), shop / "pag" / f"p{n:03d}.jpg", pm)
        raw = page.get_text("text")
        (shop / "txt" / f"p{n:03d}.txt").write_text(raw, encoding="utf-8")
        (shop / "draft" / f"p{n:03d}.md").write_text(
            page_draft(page, n, base_size, corpus_low, hyphen_log, row["texto"] != "si"), encoding="utf-8")
        pics = []
        for info in page.get_image_info(xrefs=True):
            xref = info.get("xref", 0)
            box = pm.Rect(info["bbox"]) & page.rect
            cover = abs(box) / abs(page.rect)
            dpi = round(info["width"] / max(box.width / 72, 1e-6)) if box.width else None
            pics.append({"xref": xref, "bbox": frac_box(box, page), "px": [info["width"], info["height"]],
                         "dpi_efectivo": dpi, "cobertura_pagina": round(cover, 3)})
            if xref and xref not in seen:
                seen.add(xref)
                try:
                    save_pixmap(unmask(doc, xref, pm.Pixmap(doc, xref)), shop / "emb" / f"p{n:03d}_x{xref}.png", pm)
                except Exception as exc:
                    pics[-1]["error_extraccion"] = str(exc)[:120]
        if args.ocr:
            if tesseract:
                tmp = shop / "ocr" / f"p{n:03d}_300.png"
                save_pixmap(page.get_pixmap(dpi=300), tmp, pm)
                subprocess.run([tesseract, str(tmp), str(shop / "ocr" / f"p{n:03d}"), "--psm", "3"],
                               capture_output=True)
            else:
                (shop / "ocr" / f"p{n:03d}.txt").write_text("tesseract no disponible: transcribir desde la imagen\n",
                                                             encoding="utf-8")
        zones = graphic_regions(page, pm)
        hits = caption_hits(page)
        for hit in hits:
            hit["propuesta_recorte"] = crop_proposal(page, pm, hit, zones)
            hit["bbox"] = frac_box(hit["bbox"], page)
        pages_meta.append({"pagina": n, "ancho_pt": round(page.rect.width, 1), "alto_pt": round(page.rect.height, 1),
                           "rotacion": page.rotation, "caracteres": len(raw.strip()), "imagenes": pics,
                           "graficos": [{"tipo": t, "bbox": frac_box(z, page)} for t, z in zones],
                           "leyendas": hits, "ecuaciones_numeradas": numbered_equations(page)})
    ambiguous = [h for h in hyphen_log if h["decision"] != "unir"]
    manifest = {"id": args.id, "pdf": str(pdf), "md": str(md_file), "paginas_pdf": len(doc), "rango": f"{a}-{b}",
                "texto": row["texto"], "tipo": row["tipo"], "sha12": row["sha12"], "tamano_letra_cuerpo": base_size,
                "metadatos_pdf": doc.metadata, "paginas": pages_meta,
                "propuestas_recorte": [dict(pagina=p["pagina"], **{k: h[k] for k in ("etiqueta", "propuesta_recorte")})
                                       for p in pages_meta for h in p["leyendas"]],
                "guiones_ambiguos": ambiguous, "guiones_fin_de_linea": hyphen_log, "herramienta": TOOL_VERSION}
    (shop / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    digest = [f"RESUMEN · {args.id}", f"PDF: {pdf}", f"MD destino: {md_file}", f"Tipo: {row['tipo']} · capa de texto: {row['texto']}",
              f"Páginas del PDF: {len(doc)} · rango preparado: {a}-{b}", f"sha12: {row['sha12']}",
              f"Productor: {doc.metadata.get('producer', '')} · creador: {doc.metadata.get('creator', '')}",
              f"Tamaño de letra del cuerpo: {base_size} pt", "", "Página · caracteres · imágenes (cobertura) · leyendas · ecuaciones numeradas"]
    for p in pages_meta:
        pics = ", ".join(f"x{i['xref']}({i['cobertura_pagina']})" for i in p["imagenes"]) or "-"
        caps = ", ".join(h["etiqueta"] for h in p["leyendas"]) or "-"
        eqs = ", ".join(e["etiqueta"] for e in p["ecuaciones_numeradas"]) or "-"
        digest.append(f"  p{p['pagina']:03d} · {p['caracteres']} · {pics} · {caps} · {eqs}")
    digest += ["", f"Guiones de fin de línea: {len(hyphen_log)} · a revisar (conservar/ambiguo): {len(ambiguous)}",
               "En draft/ los guiones dudosos aparecen como ⟦-⟧ y los posibles títulos con §.",
               "Carpetas: pag/ (140 dpi) · txt/ (capa de texto) · draft/ (borrador con estilos) · emb/ (imágenes nativas) · ocr/",
               f"Imágenes del .md: {doc_dir / 'img'}"]
    (shop / "RESUMEN.txt").write_text("\n".join(digest) + "\n", encoding="utf-8")
    journal(args.id, "prep", f"páginas {a}-{b}")
    emit({"ok": True, "id": args.id, "rango": f"{a}-{b}", "trabajo": str(shop), "resumen": str(shop / "RESUMEN.txt"),
          "guiones_a_revisar": len(ambiguous), "leyendas": sum(len(p["leyendas"]) for p in pages_meta)})


def render_page(page, pm, dpi):
    from PIL import Image
    pix = page.get_pixmap(dpi=dpi)
    if pix.colorspace and pix.colorspace.n >= 4:
        pix = pm.Pixmap(pm.csRGB, pix)
    mode = "RGB" if pix.n == 3 else ("L" if pix.n == 1 else "RGBA")
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def cmd_grid(args):
    from PIL import ImageDraw
    pm = pdf_engine()
    row = locate(load_ledger(), args.id)
    pdf, _, _, shop = doc_paths(row)
    page = pm.open(pdf)[args.pagina - 1]
    dpi = args.dpi or max(72, int(1600 / (max(page.rect.width, page.rect.height) / 72)))
    canvas = render_page(page, pm, dpi).convert("RGB")
    pen = ImageDraw.Draw(canvas)
    w, h = canvas.size
    for i in range(1, 20):
        f = i / 20
        tone = (220, 0, 0) if i % 2 == 0 else (255, 150, 150)
        pen.line([(f * w, 0), (f * w, h)], fill=tone, width=1)
        pen.line([(0, f * h), (w, f * h)], fill=tone, width=1)
        pen.text((f * w + 2, 2), f"{f:.2f}", fill=(0, 0, 200))
        pen.text((2, f * h + 2), f"{f:.2f}", fill=(0, 0, 200))
    target = shop / "grid" / f"p{args.pagina:03d}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)
    emit({"ok": True, "imagen": str(target), "px": [w, h]})


def cmd_crop(args):
    pm = pdf_engine()
    row = locate(load_ledger(), args.id)
    pdf, _, doc_dir, shop = doc_paths(row)
    page = pm.open(pdf)[args.pagina - 1]
    x0, y0, x1, y1 = args.x0, args.y0, args.x1, args.y1
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        emit({"ok": False, "mensaje": "coordenadas fuera de 0..1 o invertidas"}, 2)
    name = args.nombre if args.nombre.lower().endswith(".png") else args.nombre + ".png"
    target = (shop / "zoom" / name) if args.inspeccion else (doc_dir / "img" / name)
    if target.exists() and not args.inspeccion and not args.reemplazar:
        emit({"ok": False, "mensaje": f"ya existe {target}; usa --reemplazar si de verdad quieres sustituirla"}, 2)
    target.parent.mkdir(parents=True, exist_ok=True)
    if page.rotation == 0:
        r = page.rect
        clip = pm.Rect(x0 * r.width, y0 * r.height, x1 * r.width, y1 * r.height)
        pix = page.get_pixmap(dpi=args.dpi, clip=clip)
        save_pixmap(pix, target, pm)
        size = [pix.width, pix.height]
    else:
        canvas = render_page(page, pm, args.dpi)
        w, h = canvas.size
        piece = canvas.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        piece.save(target)
        size = list(piece.size)
    emit({"ok": True, "imagen": str(target), "px": size, "dpi": args.dpi})


def cmd_native(args):
    pm = pdf_engine()
    row = locate(load_ledger(), args.id)
    pdf, _, doc_dir, _ = doc_paths(row)
    doc = pm.open(pdf)
    name = args.nombre if args.nombre.lower().endswith(".png") else args.nombre + ".png"
    target = doc_dir / "img" / name
    if target.exists() and not args.reemplazar:
        emit({"ok": False, "mensaje": f"ya existe {target}; usa --reemplazar"}, 2)
    target.parent.mkdir(parents=True, exist_ok=True)
    pix = unmask(doc, args.xref, pm.Pixmap(doc, args.xref))
    smask = next((im[1] for page in doc for im in page.get_images(full=True) if im[0] == args.xref and im[1]), 0)
    if smask:
        try:
            pix = pm.Pixmap(pix, pm.Pixmap(doc, smask))
        except Exception:
            pass
    w, h = save_pixmap(pix, target, pm)
    emit({"ok": True, "imagen": str(target), "px": [w, h]})


def cmd_find(args):
    pm = pdf_engine()
    row = locate(load_ledger(), args.id)
    pdf, _, _, _ = doc_paths(row)
    page = pm.open(pdf)[args.pagina - 1]
    hits = [frac_box(r, page) for r in page.search_for(args.texto)]
    emit({"ok": True, "pagina": args.pagina, "texto": args.texto, "cajas": hits})


def split_front(raw):
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end != -1:
            return raw[4:end], raw[end + 5:]
    return None, raw


def body_digest(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def latex_plain(tex):
    tex = re.sub(r"\\(mathrm|mathbf|mathit|mathcal|mathsf|mathtt|text|textrm|textit|textbf|operatorname|boldsymbol|left|right|big|Big|bigg|Bigg)\b", "", tex)
    tex = re.sub(r"\\tag\{[^}]*\}", " ", tex)
    tex = re.sub(r"\\([A-Za-z]+)", lambda m: GREEK.get(m.group(1), " "), tex)
    tex = re.sub(r"\\(.)", r"\1", tex)
    return tex.replace("^", "").replace("_", "").replace("{", "").replace("}", "")


def inline_math_plain(text):
    return re.sub(r"(?<!\\)\$([^$\n]+?)(?<!\\)\$", lambda m: latex_plain(m.group(1)), text)


def tokens_of(text):
    t = re.sub(r"(?<=[^\W\d_])[\u00b4\u0060\u00a8\u02c6\u02dc\u00b8\u02d8\u02c7\u02d9\u02da\u02dd] ?(?=[^\W\d_])", "", text)
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("\u2212", "-").replace("\u2010", "-").replace("\u2011", "-").replace("\u00ad", "")
    t = t.lower()
    t = re.sub(r"[\u00b4\u0060\u00a8\u02c6\u02dc\u00b8\u02d8\u02c7\u02d9\u02da\u02dd]", "", t)
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    t = re.sub(r"(?<=[^\W_])[-¬][ \t]*\n[ \t]*(?=[^\W_])", "", t)
    t = re.sub(r"(?<=[^\W\d_])-+(?=[^\W\d_])", "", t)
    return re.findall(r"[^\W_]+", t)


def real_word(tok):
    return sum(c.isalpha() for c in tok) >= 2


def proseish(line):
    s = line.strip()
    if len(s) <= 3:
        return False
    toks = re.findall(r"[^\W_]+", s)
    if not toks:
        return False
    return sum(1 for t in toks if len(t) == 1) / len(toks) <= 0.5


def stitch(lines):
    merged = []
    for idx, line in enumerate(lines):
        if merged and re.search(r"[^\W\d_][-¬\u00ad]\s*$", merged[-1][1]) and line.strip()[:1].islower():
            merged[-1][1] = re.sub(r"[-¬\u00ad]\s*$", "", merged[-1][1]) + line.strip()
            continue
        merged.append([idx, line])
    return merged


def build_stream(lines):
    stream, owners = [], []
    for idx, line in stitch(lines):
        for tok in tokens_of(line):
            stream.append(tok)
            owners.append(idx)
    return stream, owners


def gram_bank(stream, top=5):
    bank = {n: set() for n in range(1, top + 1)}
    for n in range(1, top + 1):
        for i in range(len(stream) - n + 1):
            bank[n].add(tuple(stream[i:i + n]))
    return bank


def coverage_mask(stream, owners, bank, n):
    mask = [False] * len(stream)
    for i in range(len(stream) - n + 1):
        if tuple(stream[i:i + n]) in bank[n]:
            for j in range(i, i + n):
                mask[j] = True
    groups = {}
    for i, o in enumerate(owners):
        groups.setdefault(o, []).append(i)
    for idxs in groups.values():
        if len(idxs) < n and not all(mask[i] for i in idxs):
            gram = tuple(stream[i] for i in idxs)
            if gram in bank[len(gram)]:
                for i in idxs:
                    mask[i] = True
    return mask


def gap_runs(stream, mask, owners, labels, minimum=8):
    runs, i = [], 0
    while i < len(stream):
        if mask[i]:
            i += 1
            continue
        j = i
        while j < len(stream) and not mask[j]:
            j += 1
        piece = stream[i:j]
        if sum(real_word(t) for t in piece) >= minimum:
            runs.append({"donde": labels[owners[i]], "palabras": len(piece), "texto": " ".join(piece[:40])})
        i = j
    return runs


def number_set(text):
    t = unicodedata.normalize("NFKC", text)
    return set(re.findall(r"\d+(?:\.\d+)?", t))


def md_parts(body):
    comments = re.findall(r"<!--(.*?)-->", body, re.S)
    bare = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    display = re.findall(r"\$\$(.*?)\$\$", bare, re.S)
    prose = re.sub(r"\$\$.*?\$\$", " ", bare, flags=re.S)
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", prose)
    prose = re.sub(r"\[\^[^\]]+\]:?", " ", prose)
    prose = re.sub(r"<summary>.*?</summary>", " ", prose, flags=re.S | re.I)
    prose = re.sub(r"</(td|th|tr|li|p|div)>|<br\s*/?>", "\n", prose, flags=re.I)
    prose = re.sub(r"<[^>\n]*>", "", prose)
    prose = re.sub(r"(?<!\\)\|", "\n", prose)
    prose = re.sub(r"^\s*:?-{3,}:?\s*$", "", prose, flags=re.M)
    prose = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|$&<>])", r"\1", prose)
    prose = html.unescape(prose)
    return prose, comments, display


def page_slices(body):
    marks = list(re.finditer(r"<!--\s*página\s+(\d+)\b(.*?)-->", body, re.S))
    return marks


def katex_faults(items):
    node = shutil.which("node")
    if not node or not (TOOL_DIR / "node_modules" / "katex").exists():
        return None
    run = subprocess.run([node, str(KATEX_PROBE)], input=json.dumps(items), capture_output=True, text=True,
                         cwd=str(TOOL_DIR))
    try:
        return json.loads(run.stdout or "[]")
    except json.JSONDecodeError:
        return [{"tex": "", "error": "katex_check falló: " + run.stderr[:200]}]


def cmd_qc(args):
    pm = pdf_engine()
    rows = load_ledger()
    row = locate(rows, args.id)
    pdf, md_file, doc_dir, shop = doc_paths(row)
    if not md_file.exists():
        emit({"ok": False, "mensaje": f"no existe {md_file}"}, 2)
    doc = pm.open(pdf)
    total = len(doc)
    a, b = parse_span(args.paginas) if args.paginas else (1, total)
    whole = (a, b) == (1, total)
    scanned = row["texto"] in ("ocr", "no")
    raw = md_file.read_text(encoding="utf-8")
    faults, warnings = [], []
    if raw.startswith("\ufeff"):
        faults.append("el .md tiene BOM")
    if "\r" in raw:
        faults.append("el .md tiene saltos de línea CRLF")
    front, body = split_front(raw)
    meta = {}
    if front is None:
        faults.append("falta el front matter YAML")
    else:
        try:
            import yaml
            meta = yaml.safe_load(front) or {}
        except Exception as exc:
            faults.append(f"YAML inválido: {str(exc)[:120]}")
    for key in ("titulo", "autores", "fuente_pdf", "paginas_pdf", "sha12_pdf", "conversion"):
        if key not in meta or meta.get(key) in (None, "", []):
            faults.append(f"YAML: falta {key}")
    if meta.get("fuente_pdf") and meta.get("fuente_pdf") != row["pdf"]:
        faults.append(f"YAML: fuente_pdf no coincide con el checkpoint ({row['pdf']})")
    if meta.get("paginas_pdf") and int(meta.get("paginas_pdf")) != total:
        faults.append(f"YAML: paginas_pdf no coincide ({total})")
    if meta.get("sha12_pdf") and str(meta.get("sha12_pdf")) != row["sha12"]:
        faults.append(f"YAML: sha12_pdf no coincide ({row['sha12']})")
    marks = page_slices(body)
    seq = [int(m.group(1)) for m in marks]
    expected = list(range(a, b + 1))
    present = [p for p in seq if a <= p <= b]
    if present != expected:
        lost = sorted(set(expected) - set(present))
        dup = sorted(p for p, c in Counter(present).items() if c > 1)
        faults.append(f"marcadores de página: faltan {lost or '-'} · duplicados {dup or '-'} · orden {'ok' if present == sorted(present) else 'incorrecto'}")
    if any(p > total for p in seq):
        faults.append("hay marcadores de página mayores que paginas_pdf")
    start = next((m.start() for m in marks if int(m.group(1)) == a), 0 if whole else None)
    stop = next((m.start() for m in marks if int(m.group(1)) == b + 1), len(body))
    if start is None:
        start = 0
    segment = body if whole else body[start:stop]
    prose, comments, display = md_parts(segment)
    figure_notes = [c for c in comments if c.strip().lower().startswith("texto en la figura")]
    prose_lines = [inline_math_plain(l) for l in prose.split("\n")]
    md_stream, md_owners = build_stream(prose_lines)
    every_md = prose_lines + [inline_math_plain(c) for c in comments] + [latex_plain(d) for d in display]
    full_stream, _ = build_stream(every_md)
    n = 3 if scanned else 5
    md_bank = gram_bank(full_stream, n)
    pdf_lines, pdf_labels, pdf_all_lines = [], [], []
    for p in range(a, b + 1):
        for line in ordered_text(doc[p - 1]).split("\n"):
            if proseish(line):
                pdf_lines.append(line)
                pdf_labels.append(f"p{p}")
    lo, hi = max(1, a - 1), min(total, b + 1)
    pdf_numbers = set()
    for p in range(lo, hi + 1):
        page = doc[p - 1]
        text = page.get_text("text")
        pdf_all_lines.extend(ordered_text(page).split("\n"))
        pdf_numbers |= number_set(text)
        for blk in page.get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                for s in line["spans"]:
                    pdf_numbers |= number_set(s["text"])
    pdf_stream, pdf_owners = build_stream(pdf_lines)
    cov_mask = coverage_mask(pdf_stream, pdf_owners, md_bank, n)
    coverage = sum(cov_mask) / len(pdf_stream) if pdf_stream else 1.0
    ref_stream, _ = build_stream(pdf_all_lines)
    pdf_bank = gram_bank(ref_stream, n)
    md_labels = [f"línea md {i + 1}" for i in range(len(prose_lines))]
    pre_mask = coverage_mask(md_stream, md_owners, pdf_bank, n)
    precision = sum(pre_mask) / len(md_stream) if md_stream else 1.0
    good, soft = (0.90, 0.80) if scanned else (0.985, 0.96)
    for label, value in (("cobertura", coverage), ("precisión", precision)):
        if value < soft:
            faults.append(f"{label} {value:.4f} < {soft}")
        elif value < good:
            warnings.append(f"{label} {value:.4f} < {good}")
    missing = gap_runs(pdf_stream, cov_mask, pdf_owners, pdf_labels)
    extra = gap_runs(md_stream, pre_mask, md_owners, md_labels)
    if missing:
        faults.append(f"{len(missing)} pasajes faltantes (≥8 palabras)")
    if extra:
        faults.append(f"{len(extra)} pasajes añadidos (≥8 palabras)")
    prose_nums = set()
    for line in prose_lines:
        prose_nums |= number_set(line)
    stray = sorted(prose_nums - pdf_numbers, key=natural_key)
    if stray:
        (warnings if scanned else faults).append(f"números del .md que no están en el PDF: {stray[:40]}")
    md_numbers = set()
    for chunk in every_md:
        md_numbers |= number_set(chunk)
    pdf_core_numbers = set()
    for p in range(a, b + 1):
        pdf_core_numbers |= number_set(doc[p - 1].get_text("text"))
    absent = sorted(pdf_core_numbers - md_numbers, key=natural_key)
    if absent:
        warnings.append(f"números del PDF ausentes en el .md: {absent[:60]}")
    for target in re.findall(r"!\[[^\]]*\]\(([^)\s]+)", segment) + re.findall(r"<img[^>]+src=\"([^\"]+)\"", segment):
        if not (md_file.parent / target).exists():
            faults.append(f"imagen rota: {target}")
    pdf_caps = {}
    pdf_eqs = []
    for p in range(a, b + 1):
        page = doc[p - 1]
        for hit in caption_hits(page):
            pdf_caps.setdefault((hit["tipo"], hit["num"]), p)
        pdf_eqs += [e["etiqueta"] for e in numbered_equations(page)]
    md_lines = segment.split("\n")
    md_caps = {}
    for i, line in enumerate(md_lines):
        clean = re.sub(r"[*_]", "", line).lstrip(" >\t")
        m = CAPTION_RX.match(clean)
        if m and (i == 0 or not md_lines[i - 1].strip()):
            kind = "tabla" if m.group(1).lower().startswith("tab") else "figura"
            md_caps.setdefault((kind, m.group(2).lower()), i)
    for key, p in sorted(pdf_caps.items(), key=lambda kv: kv[1]):
        if key not in md_caps:
            warnings.append(f"{key[0]} {key[1]} (página {p}) sin leyenda en el .md")
    for (kind, num), i in md_caps.items():
        window = "\n".join(md_lines[max(0, i - 12): i + 40])
        if kind == "figura" and "![" not in "\n".join(md_lines[max(0, i - 12): i + 3]):
            warnings.append(f"leyenda de figura {num} sin imagen cercana (línea {i + 1})")
        if kind == "tabla" and not re.search(r"^\s*\||<table|!\[", window, re.M):
            warnings.append(f"leyenda de tabla {num} sin tabla cercana (línea {i + 1})")
    tags = re.findall(r"\\tag\{([^}]*)\}", segment)
    lost_tags = [e for e in dict.fromkeys(pdf_eqs) if e not in tags and f"Eq. {e}" not in tags]
    if lost_tags:
        warnings.append(f"números de ecuación del PDF sin \\tag: {lost_tags[:30]}")
    bare = re.sub(r"<!--.*?-->", " ", segment, flags=re.S)
    if bare.count("$$") % 2:
        faults.append("bloques $$ desbalanceados")
    for k, para in enumerate(re.split(r"\n\s*\n", re.sub(r"\$\$.*?\$\$", " ", bare, flags=re.S))):
        if len(re.findall(r"(?<!\\)\$", para)) % 2:
            faults.append(f"$ desbalanceado en el párrafo {k + 1}: {para.strip()[:70]}")
    table_run = []
    for i, line in enumerate(md_lines + [""]):
        if line.lstrip().startswith("|"):
            table_run.append((i, line))
            continue
        if table_run:
            widths = {len(re.findall(r"(?<!\\)\|", l.strip())) for _, l in table_run}
            if len(widths) > 1:
                faults.append(f"tabla GFM con columnas inconsistentes (línea {table_run[0][0] + 1})")
            if len(table_run) > 1 and not re.match(r"^\s*\|?\s*:?-{3,}", table_run[1][1]):
                faults.append(f"tabla GFM sin línea separadora (línea {table_run[0][0] + 1})")
            table_run = []
    for rx, label in ((r"\bTODO\b", "TODO"), (r"\[falta\]", "[falta]"), (r"\[pendiente\]", "[pendiente]"),
                      (r"(?i)lorem ipsum", "lorem"), (r"(?m)^§", "§ del borrador"), (r"BORRADOR AUTOMÁTICO", "BORRADOR"),
                      (r"\*\* \*\*", "estilo roto ** **"), (r"⟦", "guion dudoso ⟦-⟧"), (r"<!-- b\d+ \[", "caja del borrador")):
        if re.search(rx, segment):
            faults.append(f"marcador prohibido o resto del borrador: {label}")
    math_items = [{"tex": d, "display": True} for d in display]
    for line in re.sub(r"\$\$.*?\$\$", " ", bare, flags=re.S).split("\n"):
        for m in re.finditer(r"(?<!\\)\$([^$\n]+?)(?<!\\)\$", line):
            math_items.append({"tex": m.group(1), "display": False})
    errors = katex_faults(math_items)
    if errors is None:
        warnings.append("KaTeX no disponible: no se validaron las expresiones")
    elif errors:
        faults.append(f"{len(errors)} expresiones con error de KaTeX: " + "; ".join(e['tex'][:40] + " → " + e['error'][:60] for e in errors[:5]))
    figs_pdf = len({k for k in pdf_caps if k[0] == "figura"})
    tabs_pdf = len({k for k in pdf_caps if k[0] == "tabla"})
    figs_md = len(set(re.findall(r"\]\((img/fig[^)]+)\)", segment)))
    tabs_md = len(re.findall(r"<table", segment)) + sum(1 for i, l in enumerate(md_lines) if l.lstrip().startswith("|") and (i == 0 or not md_lines[i - 1].lstrip().startswith("|")))
    verdict = "FALLA" if faults else ("AVISO" if warnings else "PASS")
    report = {"id": args.id, "veredicto": verdict, "alcance": "completo" if whole else f"{a}-{b}", "fecha": stamp(),
              "herramienta": TOOL_VERSION, "capa": row["texto"], "ngrama": n,
              "metricas": {"cobertura": round(coverage, 4), "precision": round(precision, 4),
                           "figuras": f"{figs_md}/{figs_pdf}", "tablas": f"{tabs_md}/{tabs_pdf}",
                           "ecuaciones": f"{len(tags)}/{len(set(pdf_eqs))}", "palabras_pdf": len(pdf_stream),
                           "palabras_md": len(md_stream), "expresiones_katex": len(math_items)},
              "fallas": faults, "avisos": warnings, "pasajes_faltantes": missing[:30], "pasajes_anadidos": extra[:30],
              "cuerpo_sha": body_digest(body)}
    shop.mkdir(parents=True, exist_ok=True)
    (shop / "qc.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    journal(args.id, "qc", f"{verdict} {report['alcance']} cob {coverage:.4f} prec {precision:.4f}")
    emit(report)


def cmd_done(args):
    rows = load_ledger()
    row = locate(rows, args.id)
    pdf, md_file, _, shop = doc_paths(row)
    state = args.estado.upper()
    qc_file = shop / "qc.json"
    qc = json.loads(qc_file.read_text(encoding="utf-8")) if qc_file.exists() else None
    problems = []
    if state == "COMPLETO":
        if not md_file.exists():
            problems.append("no existe el .md")
        if not qc:
            problems.append("no hay qc")
        else:
            front, body = split_front(md_file.read_text(encoding="utf-8"))
            if qc["alcance"] != "completo":
                problems.append("el último qc no cubre el documento completo")
            if qc["veredicto"] == "FALLA" and not args.forzar:
                problems.append("el último qc es FALLA")
            if qc["veredicto"] == "AVISO" and not args.notas:
                problems.append("qc con AVISO: justifica cada aviso en --notas")
            if body_digest(body) != qc["cuerpo_sha"]:
                problems.append("el cuerpo del .md cambió después del último qc")
            try:
                import yaml
                conv = (yaml.safe_load(front or "") or {}).get("conversion") or {}
            except Exception:
                conv = {}
            for key in ("verificacion", "qc"):
                if not conv.get(key):
                    problems.append(f"YAML: falta conversion.{key}")
        if args.forzar and not args.notas:
            problems.append("--forzar exige --notas con la explicación")
        row["paginas_hechas"] = row["paginas"]
    elif state == "PARCIAL":
        if args.paginas_hechas is None:
            problems.append("PARCIAL exige --paginas-hechas N")
        else:
            row["paginas_hechas"] = str(args.paginas_hechas)
    elif state in ("REVISAR", "ERROR"):
        if not args.notas:
            problems.append(f"{state} exige --notas")
    else:
        problems.append("estado inválido (COMPLETO | PARCIAL | REVISAR | ERROR)")
    if problems:
        emit({"ok": False, "id": args.id, "rechazado": problems}, 2)
    row["estado"] = state
    row["fin"] = stamp()
    if qc:
        m = qc["metricas"]
        row["qc"] = f"{qc['veredicto']} ({qc['alcance']}) cob {m['cobertura']} prec {m['precision']} fig {m['figuras']} tab {m['tablas']} ec {m['ecuaciones']}"
    row["notas"] = ("[forzado] " if args.forzar else "") + (args.notas or "")
    save_ledger(rows)
    journal(args.id, f"done {state}", row["notas"][:300])
    emit({"ok": True, "id": args.id, "estado": state, "paginas_hechas": row["paginas_hechas"], "qc": row["qc"]})


def build_cli():
    cli = argparse.ArgumentParser(prog="pdf2md_tools", description="Cola y control de calidad PDF → MD ultrafiel")
    cli.add_argument("--version", action="version", version=TOOL_VERSION)
    sub = cli.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync", help="extrae los ZIP y actualiza la cola").set_defaults(fn=cmd_sync)
    p = sub.add_parser("next", help="siguiente documento")
    p.add_argument("--pilar")
    p.set_defaults(fn=cmd_next)
    sub.add_parser("status", help="progreso de la cola").set_defaults(fn=cmd_status)
    p = sub.add_parser("lock", help="marca EN_PROCESO")
    p.add_argument("id")
    p.add_argument("--agente", required=True)
    p.set_defaults(fn=cmd_lock)
    p = sub.add_parser("unlock", help="libera un EN_PROCESO")
    p.add_argument("id")
    p.add_argument("--motivo", required=True)
    p.set_defaults(fn=cmd_unlock)
    p = sub.add_parser("prep", help="prepara páginas, texto, borrador, imágenes y manifest")
    p.add_argument("id")
    p.add_argument("--paginas")
    p.add_argument("--ocr", action="store_true")
    p.set_defaults(fn=cmd_prep)
    p = sub.add_parser("grid", help="página con cuadrícula cada 0.05")
    p.add_argument("id")
    p.add_argument("pagina", type=int)
    p.add_argument("--dpi", type=int)
    p.set_defaults(fn=cmd_grid)
    p = sub.add_parser("crop", help="recorte de una región (fracciones 0..1)")
    p.add_argument("id")
    p.add_argument("pagina", type=int)
    for k in ("x0", "y0", "x1", "y1"):
        p.add_argument(k, type=float)
    p.add_argument("nombre")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--inspeccion", action="store_true")
    p.add_argument("--reemplazar", action="store_true")
    p.set_defaults(fn=cmd_crop)
    p = sub.add_parser("native", help="imagen incrustada a resolución original")
    p.add_argument("id")
    p.add_argument("xref", type=int)
    p.add_argument("nombre")
    p.add_argument("--reemplazar", action="store_true")
    p.set_defaults(fn=cmd_native)
    p = sub.add_parser("find", help="cajas (fracciones) de un texto en una página")
    p.add_argument("id")
    p.add_argument("pagina", type=int)
    p.add_argument("texto")
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser("qc", help="control de calidad del .md contra el PDF")
    p.add_argument("id")
    p.add_argument("--paginas")
    p.set_defaults(fn=cmd_qc)
    p = sub.add_parser("done", help="cierra el documento en el checkpoint")
    p.add_argument("id")
    p.add_argument("estado")
    p.add_argument("--notas")
    p.add_argument("--paginas-hechas", dest="paginas_hechas", type=int)
    p.add_argument("--forzar", action="store_true")
    p.set_defaults(fn=cmd_done)
    return cli


if __name__ == "__main__":
    parsed = build_cli().parse_args()
    parsed.fn(parsed)
