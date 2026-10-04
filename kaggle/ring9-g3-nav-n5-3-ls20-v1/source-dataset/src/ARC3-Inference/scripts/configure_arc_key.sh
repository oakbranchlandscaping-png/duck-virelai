#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
env_file="$project_root/.env"
tmp_file="$env_file.tmp.$$"

restore_terminal() {
    stty echo 2>/dev/null || true
    rm -f "$tmp_file"
}
trap restore_terminal EXIT HUP INT TERM

printf 'Paste the ARC API key (input is hidden): '
stty -echo
IFS= read -r arc_key
stty echo
printf '\n'

if [ "${#arc_key}" -lt 12 ]; then
    printf 'The ARC key was empty or unexpectedly short; nothing was written.\n' >&2
    exit 1
fi

umask 077
if [ -f "$env_file" ]; then
    awk '!/^ARC_API_KEY=/' "$env_file" > "$tmp_file"
else
    : > "$tmp_file"
fi
printf 'ARC_API_KEY=%s\n' "$arc_key" >> "$tmp_file"
mv "$tmp_file" "$env_file"
chmod 600 "$env_file"
unset arc_key

trap - EXIT HUP INT TERM
printf 'ARC key stored in %s with owner-only permissions.\n' "$env_file"
