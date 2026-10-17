#!/usr/bin/env python3
"""Genera 42-badge.svg con tus datos de la intra de 42 (foto, nivel, proyectos).

    FT_UID=... FT_SECRET=... FT_LOGIN=pmendez- python3 generate_badge.py
    python3 generate_badge.py --demo      # con datos de ejemplo, sin API

Solo usa la librería estándar de Python. La foto va incrustada en base64
porque GitHub no carga imágenes externas dentro de un SVG.
"""

import base64
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

API = "https://api.intra.42.fr"
OUTPUT = os.environ.get("OUTPUT", "42-badge.svg")

# Colores (tema oscuro con acento verde)
BG, CARD_BORDER = "#0d1117", "#30363d"
TEXT, MUTED, ACCENT, BAR_BG = "#e6edf3", "#8b949e", "#00e88f", "#21262d"


# ----------------------------------------------------------------------------
# API de 42
# ----------------------------------------------------------------------------

def get_token(uid, secret):
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials", "client_id": uid, "client_secret": secret,
    }).encode()
    with urllib.request.urlopen(API + "/oauth/token", data=data, timeout=30) as r:
        return json.load(r)["access_token"]


def get_user(login, token):
    req = urllib.request.Request(API + "/v2/users/" + urllib.parse.quote(login),
                                 headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def photo_data_uri(url):
    if not url:
        return ""
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            mime = r.headers.get_content_type() or "image/jpeg"
            return "data:%s;base64,%s" % (mime, base64.b64encode(r.read()).decode())
    except Exception:  # noqa: BLE001  (sin foto, el badge se genera igual)
        return ""


def extract(user):
    """Saca de la respuesta de la API solo lo que pinta el badge."""
    cursus = [c for c in user.get("cursus_users", []) if c["cursus"]["slug"] == "42cursus"]
    cursus = cursus[0] if cursus else (user.get("cursus_users") or [{}])[-1]
    cursus_id = (cursus.get("cursus") or {}).get("id")

    done = [p for p in user.get("projects_users", [])
            if p.get("validated?") and p.get("marked_at")
            and (cursus_id is None or cursus_id in p.get("cursus_ids", []))]
    done.sort(key=lambda p: p["marked_at"], reverse=True)

    image = user.get("image") or {}
    photo_url = (image.get("versions") or {}).get("medium") or image.get("link")
    campus = (user.get("campus") or [{}])[0].get("name", "")

    return {
        "login": user.get("login", ""),
        "name": user.get("usual_full_name") or user.get("displayname") or user.get("login", ""),
        "campus": campus,
        "level": float(cursus.get("level") or 0),
        "grade": cursus.get("grade") or "",
        "projects": [(p["project"]["name"], p.get("final_mark")) for p in done[:3]],
        "photo": photo_data_uri(photo_url),
    }


# ----------------------------------------------------------------------------
# SVG
# ----------------------------------------------------------------------------

def render(d):
    width, height = 520, 190
    level_int = int(d["level"])
    progress = d["level"] - level_int
    bar_x, bar_w = 160, 330

    photo = ""
    if d["photo"]:
        photo = ('<clipPath id="c"><circle cx="85" cy="95" r="58"/></clipPath>'
                 '<image href="%s" x="27" y="37" width="116" height="116" '
                 'preserveAspectRatio="xMidYMid slice" clip-path="url(#c)"/>' % d["photo"])
    photo += '<circle cx="85" cy="95" r="58" fill="none" stroke="%s" stroke-width="3"/>' % ACCENT

    lines = []
    for i, (name, mark) in enumerate(d["projects"]):
        mark_txt = "" if mark is None else str(mark)
        lines.append(
            '<text x="%d" y="%d" class="small"><tspan fill="%s">✔</tspan> %s'
            '<tspan fill="%s"> %s</tspan></text>'
            % (bar_x, 140 + i * 17, ACCENT, escape(name), MUTED, mark_txt))

    subtitle = " · ".join(escape(x) for x in [d["login"], d["campus"]] if x)
    grade = (' <tspan fill="%s">%s</tspan>' % (MUTED, escape(d["grade"]))) if d["grade"] else ""

    return """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
  text {{ font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: {text}; }}
  .name {{ font-size: 20px; font-weight: 700; }}
  .sub {{ font-size: 13px; fill: {muted}; }}
  .level {{ font-size: 14px; font-weight: 600; }}
  .small {{ font-size: 12.5px; }}
  .date {{ font-size: 10px; fill: {muted}; }}
  .logo {{ font-size: 15px; font-weight: 800; fill: {accent}; }}
</style>
<rect x="0.5" y="0.5" width="{w1}" height="{h1}" rx="12" fill="{bg}" stroke="{border}"/>
{photo}
<text x="{bx}" y="52" class="name">{name}</text>
<text x="{bx}" y="72" class="sub">{subtitle}</text>
<text x="{logo_x}" y="30" class="logo" text-anchor="end">42</text>
<text x="{bx}" y="100" class="level">Level {lvl}{grade}</text>
<text x="{bar_end}" y="100" class="sub" text-anchor="end">{pct}%</text>
<rect x="{bx}" y="108" width="{bw}" height="8" rx="4" fill="{bar_bg}"/>
<rect x="{bx}" y="108" width="{fill}" height="8" rx="4" fill="{accent}"/>
{projects}
<text x="{logo_x}" y="{h_date}" class="date" text-anchor="end">updated {date}</text>
</svg>
""".format(w=width, h=height, w1=width - 1, h1=height - 1, bg=BG, border=CARD_BORDER,
           text=TEXT, muted=MUTED, accent=ACCENT, bar_bg=BAR_BG, photo=photo,
           bx=bar_x, bw=bar_w, bar_end=bar_x + bar_w, logo_x=width - 18,
           fill=max(8, int(bar_w * progress)), name=escape(d["name"]), subtitle=subtitle,
           lvl="%.2f" % d["level"], grade=grade, pct=int(round(progress * 100)),
           projects="\n".join(lines), h_date=height - 12,
           date=datetime.date.today().isoformat())


# ----------------------------------------------------------------------------

def main():
    if "--demo" in sys.argv:
        data = {"login": "pmendez-", "name": "Paula Méndez", "campus": "Telefónica",
                "level": 7.42, "grade": "Member",
                "projects": [("webserv", 125), ("Inception", 100), ("cpp-module-09", 100)],
                "photo": ""}
        if os.environ.get("DEMO_PHOTO"):        # foto local para probar el diseño
            with open(os.environ["DEMO_PHOTO"], "rb") as f:
                data["photo"] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    else:
        uid, secret = os.environ.get("FT_UID"), os.environ.get("FT_SECRET")
        login = os.environ.get("FT_LOGIN", "pmendez-")
        if not uid or not secret:
            sys.exit("Faltan FT_UID y FT_SECRET (ver README.md)")
        data = extract(get_user(login, get_token(uid, secret)))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(render(data))
    print("Badge generado: %s (level %.2f)" % (OUTPUT, data["level"]))


if __name__ == "__main__":
    main()
