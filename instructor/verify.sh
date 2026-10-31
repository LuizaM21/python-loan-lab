#!/usr/bin/env bash
# Checks the lab is consistent. Run it after you change the app, a bug, or a reference test.
#
# For every bug:  it applies cleanly, the SAMPLE tests stay green (the bug is hidden),
#                 and the REFERENCE tests turn red (a good test suite finds it).
# Then: all bugs together still apply, and the reference tests pass on the correct code.
#
#   instructor/verify.sh            (writes instructor/verify.log)
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
LOG="$ROOT/instructor/verify.log"
: > "$LOG"
failures=0

run_tests() { "$PYTHON" -m pytest -q -p no:cacheprovider "$@" >> "$LOG" 2>&1; }

if [[ -s instructor/.active-bugs ]]; then
  echo "Bugs are on. Run instructor/bug.sh reset first."
  exit 1
fi

echo "== correct code ==" | tee -a "$LOG"
if run_tests tests && run_tests instructor/solutions/tests; then
  echo "ok   sample and reference tests pass" | tee -a "$LOG"
else
  echo "FAIL tests fail on the correct code" | tee -a "$LOG"
  exit 1
fi

echo "== bugs one by one ==" | tee -a "$LOG"
for patch in instructor/bugs/*.patch; do
  bug="$(basename "$patch" .patch)"
  if ! git apply "$patch" 2>> "$LOG"; then
    echo "FAIL $bug does not apply" | tee -a "$LOG"; failures=$((failures + 1)); continue
  fi
  echo "-- bug $bug --" >> "$LOG"
  if run_tests tests; then hidden=yes; else hidden=no; fi
  if run_tests instructor/solutions/tests; then caught=no; else caught=yes; fi
  git apply -R "$patch"
  if [[ $hidden == yes && $caught == yes ]]; then
    echo "ok   $bug hidden from the sample tests, caught by the reference tests" | tee -a "$LOG"
  else
    echo "FAIL $bug hidden=$hidden caught=$caught" | tee -a "$LOG"; failures=$((failures + 1))
  fi
done

echo "== all bugs together ==" | tee -a "$LOG"
applied=()
for patch in instructor/bugs/*.patch; do
  if git apply "$patch" 2>> "$LOG"; then applied+=("$patch"); else
    echo "FAIL $(basename "$patch") conflicts with an earlier bug" | tee -a "$LOG"; failures=$((failures + 1))
  fi
done
for (( i=${#applied[@]}-1; i>=0; i-- )); do git apply -R "${applied[$i]}"; done
[[ ${#applied[@]} -gt 0 ]] && echo "ok   ${#applied[@]} bugs apply together" | tee -a "$LOG"

if [[ $failures -eq 0 ]]; then echo "VERIFIED"; else echo "$failures problem(s). See $LOG"; exit 1; fi
