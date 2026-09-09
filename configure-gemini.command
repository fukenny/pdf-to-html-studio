#!/bin/sh
cd "$(dirname "$0")" || exit 1
printf '\nPDF to HTML Studio — Gemini setup\n\n'
printf 'Paste your NEW Gemini API key below. It will not appear while you type.\n'
printf 'Gemini API key: '
stty -echo
IFS= read -r gemini_key
stty echo
printf '\n'

if [ -z "$gemini_key" ]; then
  printf 'No key was entered. Nothing changed.\n'
  printf 'Press Return to close.'
  read -r ignored
  exit 1
fi

umask 077
printf 'GEMINI_API_KEY=%s\n' "$gemini_key" > .env
chmod 600 .env
unset gemini_key
printf 'Gemini is configured for this local project.\n'
printf 'Restart start-demo.command, then try Apply with Gemini again.\n\n'
printf 'Press Return to close.'
read -r ignored
