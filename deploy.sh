#!/usr/bin/env bash
# Deploy to a mounted CircuitPython board.
#
# Usage: ./deploy.sh scoreboard [--libs] [--dry-run] [MOUNT_POINT]
#        ./deploy.sh remote --side left|right [--dry-run] [MOUNT_POINT]
#
#   scoreboard  The Matrix Portal S3 driving the LED matrix.
#               Player names come from players.txt (one per line), saved as
#               TT_PLAYERS in the board's settings.toml.
#   remote      A QT Py ESP32-S3 wireless arcade-button remote.
#   --side SIDE Which end of the table the remote is mounted at, left or right
#               (saved in its settings.toml).
#   --libs      Also copy the libraries listed in requirements-circuitpython.txt
#               from the local adafruit-circuitpython-bundle-*/lib into CIRCUITPY/lib.
#   --dry-run   Show what would change without writing to the board.
#   MOUNT_POINT Defaults to $CIRCUITPY, then to the one mounted CircuitPython
#               drive whose boot_out.txt matches the target board.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$PROJECT_DIR/src"
PACKAGE="tt_scoreboard"
PLAYERS_FILE="$PROJECT_DIR/players.txt"
# Loose modules on the scoreboard from before the code moved into the package.
LEGACY_FILES=(scoring.py screens.py gestures.py name_selection.py)

usage() { sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; }
fail() { echo "$*" >&2; exit 1; }

target=""
side=""
copy_libs=false
dry_run=false
mount_point="${CIRCUITPY:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        scoreboard|remote) target="$1" ;;
        --side) side="${2:-}"; shift ;;
        --side=*) side="${1#*=}" ;;
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
        [[ -z "$side" ]] || fail "--side only applies to remotes"
        ;;
    remote)
        board_pattern="adafruit_qtpy_esp32s3*"
        [[ "$side" == left || "$side" == right ]] || fail "Remotes need --side left or --side right"
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

# Set KEY = "VALUE" in the board's settings.toml, keeping any other settings.
set_setting() {
    local key="$1" value="$2" settings="$mount_point/settings.toml"
    if [[ -f "$settings" ]] && grep -q "^[[:space:]]*$key[[:space:]]*=" "$settings"; then
        run sed -i "s/^[[:space:]]*$key[[:space:]]*=.*/$key = \"$value\"/" "$settings"
    elif $dry_run; then
        echo "[dry-run] append $key = \"$value\" to $settings"
    else
        # Make sure an existing last line is terminated before appending.
        [[ -s "$settings" && -n "$(tail -c 1 "$settings")" ]] && echo >> "$settings"
        echo "$key = \"$value\"" >> "$settings"
    fi
}

# Written before the code so the board never starts without its settings.
if [[ "$target" == remote ]]; then
    set_setting TT_SIDE "$side"
    # Remotes used to belong to a player rather than a side.
    settings="$mount_point/settings.toml"
    if [[ -f "$settings" ]] && grep -q '^[[:space:]]*TT_PLAYER[[:space:]]*=' "$settings"; then
        echo "Removing legacy TT_PLAYER setting"
        run sed -i '/^[[:space:]]*TT_PLAYER[[:space:]]*=/d' "$settings"
    fi
    echo "Side set to $side"
elif [[ -f "$PLAYERS_FILE" ]]; then
    players=()
    while read -r name || [[ -n "$name" ]]; do
        name="${name%%#*}"
        name="${name#"${name%%[![:space:]]*}"}"  # Trim leading whitespace,
        name="${name%"${name##*[![:space:]]}"}"  # then trailing.
        [[ -z "$name" ]] && continue
        [[ "$name" =~ ^[A-Za-z0-9\ ._\'-]+$ ]] \
            || fail "Unsupported character in player name \"$name\" (use letters, digits, spaces, . _ ' -)"
        players+=("$name")
    done < "$PLAYERS_FILE"
    [[ ${#players[@]} -ge 2 ]] || fail "$PLAYERS_FILE needs at least two names"
    set_setting TT_PLAYERS "$(IFS=,; echo "${players[*]}")"
    echo "Players set to ${players[*]}"
else
    echo "No players.txt; leaving the board's player names as they are."
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
