#!/usr/bin/env python3
"""Genera las tarjetas SVG del perfil (estadísticas, lenguajes y proyectos destacados).

    python3 generate_stats.py                      # API pública de GitHub
    GITHUB_TOKEN=... python3 generate_stats.py     # en la Action (más límite de peticiones)
    STATS_TOKEN=...  python3 generate_stats.py     # token personal: cuenta también los repos privados

Las genera en assets/. Sustituye a github-readme-stats, cuyo servidor público
suele estar caído. Mismo estilo que 42-badge.svg. Solo librería estándar.
"""

import json
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "pauss12"
OUT = "assets"
FEATURED = ["42_WEBSERVER", "Inception", "Minishell", "CUB3D"]
# Nombre bonito y descripción para las tarjetas (si no, se usa la del repo).
TITLES = {"42_WEBSERVER": "Webserv", "CUB3D": "Cub3D"}
DESCRIPTIONS = {
    "42_WEBSERVER": "Servidor HTTP/1.1 desde cero en C++98: I/O no bloqueante, CGI y configuración estilo NGINX.",
    "Inception": "Infraestructura con Docker Compose: NGINX con TLS, WordPress y MariaDB en contenedores propios.",
    "Minishell": "Shell propia tipo bash: parser, pipes, redirecciones, heredoc, variables de entorno y señales.",
    "CUB3D": "Motor 3D por raycasting al estilo de los primeros shooters en primera persona, con MiniLibX.",
}
IGNORE_LANGS = {"Makefile"}
# Repos que no cuentan para los lenguajes (p. ej. con librerías/venv subidos).
IGNORE_LANG_REPOS = {USER, "Paradigmas_Programacion"}

BG, BORDER = "#0d1117", "#30363d"
TEXT, MUTED, ACCENT, BAR_BG = "#e6edf3", "#8b949e", "#00e88f", "#21262d"
LANG_COLORS = {
    "C": "#555555", "C++": "#f34b7d", "Shell": "#89e051", "Python": "#3572A5",
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#663399", "Kotlin": "#A97BFF",
    "Java": "#b07219", "Dockerfile": "#384d54", "PHP": "#4F5D95", "TypeScript": "#3178c6",
}
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER + "-readme"}
    token = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def card(w, h, body):
    return """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
  text {{ font-family: {font}; fill: {text}; }}
  .title {{ font-size: 17px; font-weight: 700; fill: {accent}; }}
  .label {{ font-size: 13.5px; fill: {muted}; }}
  .value {{ font-size: 13.5px; font-weight: 700; }}
  .desc {{ font-size: 12.5px; fill: {muted}; }}
  .small {{ font-size: 12px; fill: {muted}; }}
</style>
<rect x="0.5" y="0.5" width="{w1}" height="{h1}" rx="12" fill="{bg}" stroke="{border}"/>
{body}
</svg>
""".format(w=w, h=h, w1=w - 1, h1=h - 1, font=FONT, text=TEXT, muted=MUTED,
           accent=ACCENT, bg=BG, border=BORDER, body=body)


def stats_card(repos, commits, langs):
    private = sum(1 for r in repos if r["private"])
    rows = [("Repositorios" + (" (%d privados)" % private if private else ""), len(repos)),
            ("Commits", commits),
            ("Estrellas", sum(r["stargazers_count"] for r in repos)),
            ("Lenguajes", len(langs))]
    body = ['<text x="25" y="38" class="title">Estadísticas de GitHub</text>']
    for i, (label, value) in enumerate(rows):
        y = 75 + i * 28
        body.append('<circle cx="31" cy="%d" r="4" fill="%s"/>' % (y - 5, ACCENT))
        body.append('<text x="45" y="%d" class="label">%s</text>' % (y, label))
        body.append('<text x="375" y="%d" class="value" text-anchor="end">%s</text>'
                    % (y, "{:,}".format(value).replace(",", ".")))
    return card(400, 185, "\n".join(body))


def langs_card(langs):
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]
    body = ['<text x="25" y="38" class="title">Lenguajes más usados</text>',
            '<clipPath id="bar"><rect x="25" y="55" width="350" height="8" rx="4"/></clipPath>',
            '<g clip-path="url(#bar)"><rect x="25" y="55" width="350" height="8" fill="%s"/>' % BAR_BG]
    x = 25.0
    for name, size in top:
        w = 350 * size / total
        body.append('<rect x="%.1f" y="55" width="%.1f" height="8" fill="%s"/>'
                    % (x, w, LANG_COLORS.get(name, MUTED)))
        x += w
    body.append("</g>")
    for i, (name, size) in enumerate(top):
        cx, cy = 25 + (i % 2) * 180, 95 + (i // 2) * 28
        body.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>'
                    % (cx + 5, cy - 4, LANG_COLORS.get(name, MUTED)))
        body.append('<text x="%d" y="%d" class="label"><tspan fill="%s">%s</tspan> %.1f%%</text>'
                    % (cx + 17, cy, TEXT, escape(name), 100.0 * size / total))
    return card(400, 185, "\n".join(body))


def wrap(text, width=56, lines=2):
    words, out, cur = text.split(), [], ""
    for word in words:
        if len(cur) + len(word) + 1 > width:
            out.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1].rstrip(".,") + "…"
    return out


def project_card(repo):
    name = TITLES.get(repo["name"], repo["name"])
    desc = DESCRIPTIONS.get(repo["name"]) or repo.get("description") or ""
    lang = repo.get("language") or ""
    body = ['<text x="25" y="38" class="title">%s</text>' % escape(name)]
    for i, line in enumerate(wrap(desc)):
        body.append('<text x="25" y="%d" class="desc">%s</text>' % (64 + i * 18, escape(line)))
    if lang:
        body.append('<circle cx="31" cy="111" r="6" fill="%s"/>' % LANG_COLORS.get(lang, MUTED))
        body.append('<text x="44" y="115" class="small">%s</text>' % escape(lang))
    body.append('<text x="375" y="115" class="small" text-anchor="end">★ %d</text>'
                % repo["stargazers_count"])
    return card(400, 135, "\n".join(body))


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("generado", os.path.join(OUT, name))


def main():
    os.makedirs(OUT, exist_ok=True)
    if os.environ.get("STATS_TOKEN"):   # incluye privados
        repos = api("/user/repos?per_page=100&affiliation=owner&visibility=all")
    else:
        repos = api("/users/%s/repos?per_page=100" % USER)
    repos = [r for r in repos if not r["fork"]]

    langs = {}
    for r in repos:
        if r["name"] in IGNORE_LANG_REPOS:
            continue
        for name, size in api("/repos/%s/languages" % r["full_name"]).items():
            if name not in IGNORE_LANGS:
                langs[name] = langs.get(name, 0) + size

    commits = api("/search/commits?q=author:%s&per_page=1" % USER)["total_count"]

    write("stats.svg", stats_card(repos, commits, langs))
    write("langs.svg", langs_card(langs))
    by_name = {r["name"]: r for r in repos if not r["private"]}
    for name in FEATURED:
        if name in by_name:
            write("card-%s.svg" % name, project_card(by_name[name]))


if __name__ == "__main__":
    main()
