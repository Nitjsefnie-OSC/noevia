#!/usr/bin/env bash
# Compose global options precede --; up options follow it. Run on the Docker host.
set -euo pipefail
preflight_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
compose_args=()
up_args=()
reading_up=false
for argument in "$@"; do
  if [[ "$reading_up" == false && "$argument" == -- ]]; then
    reading_up=true
  elif [[ "$reading_up" == true ]]; then
    up_args+=("$argument")
  else
    compose_args+=("$argument")
  fi
done
# #1148: refuse any compose build of the diary image (the running Diary tag must not be retagged).
if [[ ! -f "$preflight_dir/diary-image-guard.sh" ]]; then
  echo "error: diary-image-guard.sh is missing next to up.sh; not starting (#1148)" >&2
  exit 2
fi
# shellcheck source=diary-image-guard.sh
source "$preflight_dir/diary-image-guard.sh"
guard_diary_image docker compose ${compose_args[@]+"${compose_args[@]}"} up ${up_args[@]+"${up_args[@]}"} || exit $?
# Compose resolves the project (compose file, .env, project name) from the cwd, so
# a caller in the wrong directory used to fail closed with a confusing error (#574).
# Resolve it here: COWORK_PROJECT_DIR, else the Compose Manager default when it
# exists, else the caller's cwd only if it holds a Compose file. Skipped when the
# caller already pins the project with -f/--file/--project-directory.
default_project_dir=/boot/config/plugins/compose.manager/projects/Cowork
pinned=false
for argument in "${compose_args[@]+"${compose_args[@]}"}"; do
  case "$argument" in -f|--file|-f?*|--file=*|--project-directory|--project-directory=*) pinned=true ;; esac
done
if [[ "$pinned" == false ]]; then
  project_dir="${COWORK_PROJECT_DIR:-}"
  if [[ -z "$project_dir" && -d "$default_project_dir" ]]; then
    project_dir="$default_project_dir"
  fi
  if [[ -n "$project_dir" ]]; then
    if [[ ! -d "$project_dir" ]]; then
      echo "error: Compose project directory not found: $project_dir" >&2
      exit 2
    fi
    cd -- "$project_dir"
  elif ! compgen -G 'compose.y*ml' >/dev/null && ! compgen -G 'docker-compose.y*ml' >/dev/null; then
    echo "error: no Compose file in $PWD and $default_project_dir does not exist; set COWORK_PROJECT_DIR to the project directory" >&2
    exit 2
  fi
fi
expect_args=()
# The live Compose file is a hand-maintained third copy; a key dropped while
# copying it turns MCP off silently. Advisory only — it never blocks the start.
if [[ -f "$preflight_dir/web-env-keys.txt" ]]; then
  expect_args=(--expect-env "$preflight_dir/web-env-keys.txt")
fi
# ${arr[@]+...} keeps empty arrays safe under set -u on bash 3.2 (macOS).
docker compose ${compose_args[@]+"${compose_args[@]}"} config --format json \
  | php "$preflight_dir/check.php" --config-json - ${expect_args[@]+"${expect_args[@]}"}
# #1843: services assigned to another Inference machine. Inert unless NOEVIA_REMOTE_SERVICES is set,
# advisory only (never blocks, never fatal), and bounded: one health probe per listed service, a few
# seconds at most, LAN/Tailscale hosts only. A stopped local sidecar is not an error for these.
# The library is tools/remote-services.sh (server layout: next to tools/preflight/; checkout: deploy/tools/).
if [[ -n "${NOEVIA_REMOTE_SERVICES:-}" || -n "${NOEVIA_REMOTE_ENV_FILE:-}" ]]; then
  remote_lib=""
  for candidate in "${REMOTE_SERVICES_SCRIPT:-}" "$preflight_dir/../remote-services.sh" "$preflight_dir/../tools/remote-services.sh"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then remote_lib="$candidate"; break; fi
  done
  if [[ -z "$remote_lib" ]]; then
    echo "WARN: NOEVIA_REMOTE_SERVICES is set but remote-services.sh was not found; remote services are not checked (set REMOTE_SERVICES_SCRIPT)" >&2
  else
    # shellcheck source=../tools/remote-services.sh
    source "$remote_lib"
    remote_load_env
    remote_report || true
    # An assigned service whose sidecar is still enabled in this Compose project will start locally too.
    # remote_services prints roles; remote_local_service names the Compose service behind each one.
    active_services="$(docker compose ${compose_args[@]+"${compose_args[@]}"} config --services 2>/dev/null || true)"
    while IFS= read -r remote_name; do
      [[ -n "$remote_name" ]] || continue
      local_name="$(remote_local_service "$remote_name")"
      if [[ -n "$local_name" ]] && printf '%s\n' "$active_services" | grep -qx -- "$local_name"; then
        echo "WARN: $remote_name is assigned to another machine but its local sidecar is still enabled in this Compose project and will also start here (docs/deployment.md, \"Services on other Inference machines\")" >&2
      fi
    done < <(remote_services 2>/dev/null)
  fi
fi
docker compose ${compose_args[@]+"${compose_args[@]}"} up ${up_args[@]+"${up_args[@]}"}
# A successful up is a known deploy: re-baseline the restart alert if installed
# (../sidecar-restart-alert.sh). Set SIDECAR_ALERT_ACK=0 to skip. Never fatal.
# The default path only resolves in the server layout, where deploy/tools/ is installed as
# $base/tools/ next to $base/tools/preflight/ (so ../sidecar-restart-alert.sh exists). In a repo
# checkout the script lives at deploy/tools/sidecar-restart-alert.sh, the default does not exist,
# and the ack is silently skipped; point SIDECAR_ALERT_SCRIPT at it to ack from a checkout.
alert_script="${SIDECAR_ALERT_SCRIPT:-$preflight_dir/../sidecar-restart-alert.sh}"
if [[ "${SIDECAR_ALERT_ACK:-1}" != 0 && -x "$alert_script" ]]; then
  "$alert_script" --ack || echo "warning: sidecar-restart-alert --ack failed" >&2
fi
