#!/usr/bin/env bash
# Turn the hidden bugs on and off. For the mentor (and for solo practice).
#
#   instructor/bug.sh random 1      turn on 1 random bug; it does not say which
#   instructor/bug.sh on 03 07      turn on bugs 03 and 07
#   instructor/bug.sh off 03        turn bug 03 off
#   instructor/bug.sh list          show which bugs are on
#   instructor/bug.sh reset         turn every bug off
#
# Restart the API after a change. On Windows, run this in Git Bash.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUGS="$ROOT/instructor/bugs"
STATE="$ROOT/instructor/.active-bugs"
cd "$ROOT"
touch "$STATE"

all_bugs() { for f in "$BUGS"/*.patch; do basename "$f" .patch; done; }
is_on() { grep -qx "$1" "$STATE"; }

turn_on() {
  local bug="$1"
  [[ -f "$BUGS/$bug.patch" ]] || { echo "No bug $bug. Bugs: $(all_bugs | tr '\n' ' ')"; exit 1; }
  if is_on "$bug"; then return; fi
  if ! git apply "$BUGS/$bug.patch"; then
    echo "Bug $bug does not apply: the code changed. Run '$0 reset' or commit your work first."
    exit 1
  fi
  echo "$bug" >> "$STATE"
}

turn_off() {
  local bug="$1"
  if ! is_on "$bug"; then return; fi
  if git apply -R --check "$BUGS/$bug.patch" 2>/dev/null; then
    git apply -R "$BUGS/$bug.patch"
  elif git apply --check "$BUGS/$bug.patch" 2>/dev/null; then
    echo "Bug $bug was already fixed by hand. Nice."
  else
    echo "Bug $bug: the code around it changed too much to undo. Fix by hand or use git checkout."
    return 1
  fi
  grep -vx "$bug" "$STATE" > "$STATE.tmp" || true
  mv "$STATE.tmp" "$STATE"
}

command="${1:-list}"
shift || true

case "$command" in
  on)
    for bug in "$@"; do turn_on "$bug"; done
    echo "On: $(sort "$STATE" | tr '\n' ' ')"
    ;;
  off)
    for bug in "$@"; do turn_off "$bug"; done
    echo "On: $(sort "$STATE" | tr '\n' ' ')"
    ;;
  random)
    count="${1:-1}"
    mapfile -t candidates < <(for b in $(all_bugs); do is_on "$b" || echo "$b"; done | shuf -n "$count")
    for bug in "${candidates[@]}"; do turn_on "$bug"; done
    echo "${#candidates[@]} bug(s) turned on. Restart the API. Good hunting."
    ;;
  list)
    if [[ -s "$STATE" ]]; then echo "On: $(sort "$STATE" | tr '\n' ' ')"; else echo "No bugs on."; fi
    ;;
  reset)
    while read -r bug; do [[ -n "$bug" ]] && turn_off "$bug"; done < <(sort -r "$STATE")
    echo "All bugs off."
    ;;
  *)
    echo "Usage: $0 {random N | on NN... | off NN... | list | reset}"
    exit 1
    ;;
esac
