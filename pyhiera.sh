#!/bin/sh
set -e

main() {
  local cmd="$( which pyhiera )"
  set -x
  "$cmd" --traceback "$@"
}

main "$@"
