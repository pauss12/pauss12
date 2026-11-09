#!/usr/bin/env python3
"""Rellena la sección "Últimos proyectos" del README con tus repos más recientes.

    python3 update_projects.py            # usa la API pública de GitHub
    GITHUB_TOKEN=... python3 update_projects.py   # (opcional) más límite de peticiones

Reemplaza lo que haya entre <!-- PROJECTS:START --> y <!-- PROJECTS:END -->.
Solo usa la librería estándar de Python.
"""

import json
import os
import re
import urllib.request

USER = "pauss12"
README = "README.md"
LIMIT = 6
SKIP = {USER, "descarga"}  # repos que no quieres que salgan

# Descripción por defecto para repos que no tienen una en GitHub.
FALLBACK = {
    "Inception": "Infraestructura con Docker Compose: NGINX + TLS, WordPress y MariaDB en contenedores propios.",
    "42_WEBSERVER": "Servidor HTTP/1.1 en C++98 con I/O no bloqueante, CGI y configuración estilo NGINX.",
    "42_CPP": "Módulos de C++: POO, herencia, polimorfismo, templates y STL.",
    "42_PHILOSOPHERS": "El problema de los filósofos con threads, mutex y sincronización.",
    "NetPractice": "Ejercicios de redes: direccionamiento IP, subnetting y tablas de enrutamiento.",
    "CUB3D": "Motor de raycasting 3D al estilo de los primeros shooters, en C con MiniLibX.",
    "EXAM_RANK04": "Preparación del examen de rango 04 de 42.",
    "Minishell": "Shell propia en C: parser, pipes, redirecciones, variables de entorno y señales.",
    "42_PIPEX": "Reproducción de las pipes de la shell con fork, pipe y dup2.",
    "42_PUSH_SWAP": "Ordenación con dos pilas y el mínimo número de operaciones.",
    "42_SO_LONG": "Juego 2D en C con MiniLibX.",
    "42_LIBFT": "Mi propia librería de C, base de todos los proyectos de 42.",
    "42_PRINTF": "Reimplementación de printf con funciones variádicas.",
    "42_GET_NEXT_LINE": "Lectura línea a línea de un file descriptor con buffer estático.",
    "Android_Studio": "Apps Android en Kotlin.",
    "Web_Servidor": "Desarrollo web en servidor con JavaScript y Node.js.",
    "Utad_Web": "Proyecto web con HTML y CSS.",
}

START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"


def fetch_repos():
    url = "https://api.github.com/users/%s/repos?per_page=100&sort=pushed" % USER
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "%s-readme" % USER}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def render(repos):
    rows = ["| Proyecto | Descripción | Lenguaje | Actualizado |", "|---|---|---|---|"]
    for r in repos:
        desc = (r.get("description") or FALLBACK.get(r["name"], "")).replace("|", "\\|")
        rows.append("| [**%s**](%s) | %s | `%s` | %s |" % (
            r["name"], r["html_url"], desc, r.get("language") or "—", r["pushed_at"][:10]))
    return "\n".join(rows)


def main():
    repos = [r for r in fetch_repos()
             if not r["fork"] and not r["archived"] and r["name"] not in SKIP]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)
    table = render(repos[:LIMIT])

    with open(README, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(re.escape(START) + ".*?" + re.escape(END),
                 lambda _: "%s\n%s\n%s" % (START, table, END), text, flags=re.S)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README actualizado")
    else:
        print("Sin cambios")


if __name__ == "__main__":
    main()
