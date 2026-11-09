#!/usr/bin/env bash
# Actualiza el perfil desde tu ordenador (sin GitHub Actions) y lo sube.
#
#   ./actualizar.sh            # genera todo, hace commit y push
#   ./actualizar.sh --no-push  # solo genera, para revisarlo antes
#
# Lee las claves de un fichero .env en esta carpeta (no se sube a GitHub):
#   STATS_TOKEN=github_pat_...   token de GitHub (solo lectura)
#   FT_UID=...                   aplicación de la intra de 42
#   FT_SECRET=...
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then set -a; . ./.env; set +a; fi
# Sin token, la API de GitHub solo deja 60 peticiones/hora por IP,
# y en el campus todos compartís la misma IP.
if [ -z "${STATS_TOKEN:-}" ]; then
  echo "Falta STATS_TOKEN. Crea el .env:  cp .env.example .env  y rellénalo."
  echo "Token: https://github.com/settings/personal-access-tokens/new"
  exit 1
fi
export GITHUB_TOKEN="$STATS_TOKEN"

[ "${1:-}" != "--no-push" ] && git pull --rebase --autostash --quiet

if [ -n "${FT_UID:-}" ] && [ -n "${FT_SECRET:-}" ]; then
  FT_LOGIN=pmendez- python3 generate_badge.py
else
  echo "Aviso: sin FT_UID/FT_SECRET en .env, no actualizo el badge de 42"
fi
python3 generate_stats.py
python3 update_projects.py

[ "${1:-}" = "--no-push" ] && { echo "Listo (sin subir)."; exit 0; }

git add README.md assets 42-badge.svg 2>/dev/null || git add README.md assets
if git diff --cached --quiet; then
  echo "Nada nuevo que subir."
else
  git commit -q -m "chore: update profile"
  git push -q
  echo "Perfil actualizado en https://github.com/pauss12"
fi
