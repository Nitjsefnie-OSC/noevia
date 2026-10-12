#!/usr/bin/env bash
# #1148: the Diary tag cowork-diary:<DIARY_VERSION> names the image the live Diary runs. On
# 2026-10-07 a from-scratch build (a full compose build that included diary) retagged it while
# the running image was the 2026-10-05 overlay. Only deploy/examples/diary-overlay.sh may build
# or tag cowork-diary:*; it sets NOEVIA_DIARY_OVERLAY=1 around its own docker calls.
#
# Sourced by release/build helpers (up.sh, build-web-release.sh), not executed:
#   guard_diary_image docker <args as they would be passed to docker>   -> 0 allowed, 3 refused
# Refused: `docker build|buildx build` with a cowork-diary tag, `docker tag` to a cowork-diary
# target, `docker compose build` with no service list or with diary in it, and any compose
# command with --build (compose builds dependencies too, and web depends on diary). Anything
# else, including a compose build of a named non-diary service, is allowed.
# This is an accident guard for the helpers in this repo, not a security boundary.

_diary_image_refusal() {
  echo "error: refusing to build or tag cowork-diary:* here (#1148). Only deploy/examples/diary-overlay.sh may do that, so the running Diary image is never retagged by accident." >&2
  return 3
}

_is_diary_image() {
  case "$1" in cowork-diary|cowork-diary:*) return 0 ;; esac
  return 1
}

# Value-taking options of `docker compose build` (their values are not service names).
_compose_build_value_opts=' --build-arg -m --memory --progress --builder --ssh --platform --provenance --sbom --set --metadata-file --cache-from --cache-to '

guard_diary_image() {
  [ "${NOEVIA_DIARY_OVERLAY:-}" = 1 ] && return 0
  [ "${1:-}" = docker ] || return 0
  shift
  local arg last="" sub skip=0
  case "${1:-}" in
    tag)
      shift
      for arg; do last=$arg; done
      _is_diary_image "$last" && { _diary_image_refusal; return 3; }
      return 0
      ;;
    buildx)
      [ "${2:-}" = build ] || return 0
      shift 2
      ;;
    build)
      shift
      ;;
    compose)
      shift
      # Global compose options come before the subcommand.
      while [ $# -gt 0 ]; do
        case "$1" in
          -f|--file|-p|--project-name|--env-file|--profile|--project-directory|--parallel|--ansi|--progress) shift; [ $# -gt 0 ] && shift ;;
          -*) shift ;;
          *) break ;;
        esac
      done
      sub="${1:-}"
      [ $# -gt 0 ] && shift
      for arg; do
        [ "$arg" = --build ] && { echo "error: refusing 'docker compose $sub --build' here (#1148): it rebuilds every service it starts, diary included, and retags cowork-diary:*. Run 'docker compose build <service>' for a non-diary service, then start without --build." >&2; return 3; }
      done
      [ "$sub" = build ] || return 0
      local services=0 names=""
      for arg; do
        if [ "$skip" = 1 ]; then skip=0; continue; fi
        case "$arg" in
          -*) case "$_compose_build_value_opts" in *" $arg "*) skip=1 ;; esac ;;
          *) services=$((services+1)); names="$names $arg" ;;
        esac
      done
      if [ "$services" -eq 0 ]; then
        echo "error: 'docker compose build' with no service list would build diary and retag cowork-diary:* (#1148). Name the services to build." >&2
        return 3
      fi
      for arg in $names; do
        [ "$arg" = diary ] && { _diary_image_refusal; return 3; }
      done
      return 0
      ;;
    *) return 0 ;;
  esac
  # docker build / docker buildx build: refuse a cowork-diary tag.
  while [ $# -gt 0 ]; do
    case "$1" in
      -t|--tag) [ $# -gt 1 ] && _is_diary_image "$2" && { _diary_image_refusal; return 3; }; shift ;;
      --tag=*) _is_diary_image "${1#--tag=}" && { _diary_image_refusal; return 3; } ;;
    esac
    shift
  done
  return 0
}
