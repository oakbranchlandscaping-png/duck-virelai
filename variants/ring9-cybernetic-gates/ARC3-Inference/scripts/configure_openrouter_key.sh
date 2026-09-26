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

printf 'Paste the OpenRouter API key (input is hidden): '
stty -echo
IFS= read -r openrouter_key
stty echo
printf '\n'

case "$openrouter_key" in
    sk-or-v1-*) ;;
    *)
        printf 'That does not look like an OpenRouter key; nothing was written.\n' >&2
        exit 1
        ;;
esac

prefix_count=$(printf '%s' "$openrouter_key" | awk -F 'sk-or-v1-' '{print NF-1}')
if [ "$prefix_count" -ne 1 ]; then
    printf 'The pasted value contains more than one OpenRouter key; nothing was written. Paste the key once.\n' >&2
    exit 1
fi

umask 077
if [ -f "$env_file" ]; then
    awk '!/^OPENROUTER_API_KEY=/' "$env_file" > "$tmp_file"
else
    : > "$tmp_file"
fi
printf 'OPENROUTER_API_KEY=%s\n' "$openrouter_key" >> "$tmp_file"
mv "$tmp_file" "$env_file"
chmod 600 "$env_file"
unset openrouter_key

trap - EXIT HUP INT TERM
printf 'OpenRouter key stored in %s with owner-only permissions.\n' "$env_file"
