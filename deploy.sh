#!/usr/bin/env bash
# Deploy to a mounted CircuitPython board.
#
# Usage: ./deploy.sh scoreboard [--libs] [--dry-run] [MOUNT_POINT]
#        ./deploy.sh remote --player 1|2 [--dry-run] [MOUNT_POINT]
#
#   scoreboard  The Matrix Portal S3 driving the LED matrix.
#   remote      A QT Py ESP32-S3 wireless arcade-button remote.
#   --player N  Which player the remote belongs to (saved in its settings.toml).
#   --libs      Also copy the libraries listed in requirements-circuitpython.txt
#               from the local adafruit-circuitpython-bundle-*/lib into CIRCUITPY/lib.
#   --dry-run   Show what would change without writing to the board.
#   MOUNT_POINT Defaults to $CIRCUITPY, then to the one mounted CircuitPython
#               drive whose boot_out.txt matches the target board.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$PROJECT_DIR/src"
PACKAGE="tt_scoreboard"
# Loose modules on the scoreboard from before the code moved into the package.
LEGACY_FILES=(scoring.py screens.py gestures.py name_selection.py)

usage() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; }
fail() { echo "$*" >&2; exit 1; }

target=""
player=""
copy_libs=false
dry_run=false
mount_point="${CIRCUITPY:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        scoreboard|remote) target="$1" ;;
        --player) player="${2:-}"; shift ;;
        --player=*) player="${1#*=}" ;;
        --libs) copy_libs=true ;;
        --dry-run) dry_run=true ;;
        -h|--help) usage; exit 0 ;;
        -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
        *) mount_point="$1" ;;
    esac
    shift
done

case "$target" in
    scoreboard)
        board_pattern="adafruit_matrixportal_s3"
        [[ -z "$player" ]] || fail "--player only applies to remotes"
        ;;
    remote)
        board_pattern="adafruit_qtpy_esp32s3*"
        [[ "$player" == 1 || "$player" == 2 ]] || fail "Remotes need --player 1 or --player 2"
        $copy_libs && fail "Remotes use only built-in modules; --libs is not needed"
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

board_id() {
    sed -n 's/.*Board ID:\([^[:space:]]*\).*/\1/p' "$1/boot_out.txt" 2>/dev/null | head -n 1
}

# shellcheck disable=SC2053  # board_pattern is a glob on purpose
matches_target() { [[ "$(board_id "$1")" == $board_pattern ]]; }

if [[ -n "$mount_point" ]]; then
    [[ -f "$mount_point/boot_out.txt" ]] || fail "$mount_point is not a CircuitPython drive"
    matches_target "$mount_point" \
        || fail "$mount_point has board ID $(board_id "$mount_point"), not a $target board"
else
    candidates=()
    while read -r mount; do
        [[ -f "$mount/boot_out.txt" ]] && matches_target "$mount" && candidates+=("$mount")
    done < <(findmnt -rn -t vfat -o TARGET)
    if [[ ${#candidates[@]} -eq 0 ]]; then
        fail "No $target board found. Is it plugged in, and does its CIRCUITPY drive show up?"
    elif [[ ${#candidates[@]} -gt 1 ]]; then
        fail "Several $target boards are mounted (${candidates[*]}); pass the mount point."
    fi
    mount_point="${candidates[0]}"
fi

rsync_opts=(--recursive --times --modify-window=2 --delete --itemize-changes
            --exclude=__pycache__ --exclude='*.pyc')
$dry_run && rsync_opts+=(--dry-run)

run() {
    if $dry_run; then echo "[dry-run] $*"; else "$@"; fi
}

echo "Deploying $target to $mount_point ($(board_id "$mount_point"))"

if [[ "$target" == remote ]]; then
    # Written before the code so the remote never starts without a player number.
    settings="$mount_point/settings.toml"
    if [[ -f "$settings" ]] && grep -q '^[[:space:]]*TT_PLAYER[[:space:]]*=' "$settings"; then
        run sed -i "s/^[[:space:]]*TT_PLAYER[[:space:]]*=.*/TT_PLAYER = $player/" "$settings"
    elif $dry_run; then
        echo "[dry-run] append TT_PLAYER = $player to $settings"
    else
        # Make sure an existing last line is terminated before appending.
        [[ -s "$settings" && -n "$(tail -c 1 "$settings")" ]] && echo >> "$settings"
        echo "TT_PLAYER = $player" >> "$settings"
    fi
    echo "Player set to $player"
fi

# Copy the package before code.py: CircuitPython reloads on each write, and the
# launcher should only run once the code it imports is in place.
rsync "${rsync_opts[@]}" "$SRC_DIR/$PACKAGE/" "$mount_point/$PACKAGE/"
rsync "${rsync_opts[@]}" "$SRC_DIR/$target/code.py" "$mount_point/code.py"

if [[ "$target" == scoreboard ]]; then
    for file in "${LEGACY_FILES[@]}"; do
        if [[ -f "$mount_point/$file" ]]; then
            echo "Removing legacy $file"
            run rm "$mount_point/$file"
        fi
    done
fi

if $copy_libs; then
    bundle_lib="$(ls -d "$PROJECT_DIR"/adafruit-circuitpython-bundle-*/lib 2>/dev/null | sort | tail -n 1)"
    [[ -n "$bundle_lib" ]] || fail "No adafruit-circuitpython-bundle-*/lib found in $PROJECT_DIR"
    run mkdir -p "$mount_point/lib"
    while read -r lib || [[ -n "$lib" ]]; do
        lib="${lib%%#*}"
        lib="${lib//[[:space:]]/}"
        [[ -z "$lib" ]] && continue
        if [[ -d "$bundle_lib/$lib" ]]; then
            rsync "${rsync_opts[@]}" "$bundle_lib/$lib/" "$mount_point/lib/$lib/"
        elif [[ -f "$bundle_lib/$lib.mpy" ]]; then
            rsync "${rsync_opts[@]}" "$bundle_lib/$lib.mpy" "$mount_point/lib/$lib.mpy"
        else
            fail "Library $lib not found in $bundle_lib"
        fi
    done < "$PROJECT_DIR/requirements-circuitpython.txt"
fi

# FAT drives buffer writes; flush so the board is safe to unplug.
run sync -f "$mount_point"
echo "Done."
