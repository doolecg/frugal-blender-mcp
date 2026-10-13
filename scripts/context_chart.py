"""Draw the README's fixed-context chart from docs/tool-context.json as one self-contained SVG."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The chart carries its own background, so the same file reads well in GitHub's light and dark themes.
COLORS = {
    "card": "#0d1117",
    "border": "#30363d",
    "text": "#e6edf3",
    "muted": "#9198a1",
    "bar": "#3d444d",
    "ours": "#f5922a",
}
LABELS = {"Blender Astra": "Blender Astra MCP", "Blender Lab": "Blender Lab official", "ahujasid": "ahujasid"}
W, LEFT, BAR_MAX, ROW, PAD = 820, 250, 340, 56, 20


def label(row):
    return next(v for k, v in LABELS.items() if row["label"].startswith(k))


def svg(rows):
    c = COLORS
    ours = rows[0]["total_tokens"]["o200k_base"]
    top = max(r["total_tokens"]["o200k_base"] for r in rows)
    height = 24 + ROW * len(rows) + 2 * PAD
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
        'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
        "<title>Fixed context per request: tool definitions plus server instructions (tiktoken o200k)</title>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="12" fill="{c["card"]}" '
        f'stroke="{c["border"]}"/>',
    ]
    for i, r in enumerate(rows):
        y = PAD + 16 + i * ROW
        total = r["total_tokens"]["o200k_base"]
        width = max(6, round(BAR_MAX * total / top))
        mine = i == 0
        weight = "700" if mine else "500"
        out += [
            f'<text x="{LEFT - 16}" y="{y + 17}" text-anchor="end" font-size="16" font-weight="{weight}" '
            f'fill="{c["text"]}">{label(r)}</text>',
            f'<text x="{LEFT - 16}" y="{y + 36}" text-anchor="end" font-size="13" fill="{c["muted"]}">'
            f"{r['tools']} tools</text>",
            f'<rect x="{LEFT}" y="{y + 6}" width="{width}" height="26" rx="5" '
            f'fill="{c["ours"] if mine else c["bar"]}"/>',
            f'<text x="{LEFT + width + 12}" y="{y + 25}" font-size="16" font-weight="{weight}" '
            f'fill="{c["ours"] if mine else c["text"]}">{total:,} tokens'
            + (
                ""
                if mine
                else f'<tspan dx="10" fill="{c["muted"]}" font-weight="400">{total / ours:.1f}x more</tspan>'
            )
            + "</text>",
        ]
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    rows = json.loads((ROOT / "docs/tool-context.json").read_text(encoding="utf-8"))
    rows.sort(key=lambda r: r["total_tokens"]["o200k_base"])
    path = ROOT / "docs/assets/context.svg"
    path.parent.mkdir(exist_ok=True)
    path.write_text(svg(rows), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
