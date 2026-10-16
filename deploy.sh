#!/usr/bin/env bash
# Deploy the scoreboard to a mounted CIRCUITPY drive.
#
# Usage: ./deploy.sh [--libs] [--dry-run] [MOUNT_POINT]
#
#   --libs      Also copy the libraries listed in requirements-circuitpython.txt
#               from the local adafruit-circuitpython-bundle-*/lib into CIRCUITPY/lib.
#   --dry-run   Show what would change without writing to the board.
#   MOUNT_POINT Defaults to $CIRCUITPY, then to the mounted volume labelled CIRCUITPY.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$PROJECT_DIR/src"
PACKAGE="tt_scoreboard"
# Loose modules from before the code moved into the package.
LEGACY_FILES=(scoring.py screens.py gestures.py name_selection.py)

copy_libs=false
dry_run=false
mount_point="${CIRCUITPY:-}"

for arg in "$@"; do
    case "$arg" in
        --libs) copy_libs=true ;;
        --dry-run) dry_run=true ;;
        -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) echo "Unknown option: $arg" >&2; exit 2 ;;
        *) mount_point="$arg" ;;
    esac
done

if [[ -z "$mount_point" ]]; then
    mount_point="$(findmnt -rn -S LABEL=CIRCUITPY -o TARGET | head -n 1 || true)"
fi
if [[ -z "$mount_point" || ! -f "$mount_point/boot_out.txt" ]]; then
    echo "CIRCUITPY drive not found. Is the board plugged in and mounted?" >&2
    echo "Pass the mount point as an argument or set \$CIRCUITPY." >&2
    exit 1
fi

rsync_opts=(--recursive --times --modify-window=2 --delete --itemize-changes
            --exclude=__pycache__ --exclude='*.pyc')
$dry_run && rsync_opts+=(--dry-run)

run() {
    if $dry_run; then echo "[dry-run] $*"; else "$@"; fi
}

echo "Deploying to $mount_point"

# Copy the package before code.py: CircuitPython reloads on each write, and the
# launcher should only run once the code it imports is in place.
rsync "${rsync_opts[@]}" "$SRC_DIR/$PACKAGE/" "$mount_point/$PACKAGE/"
rsync "${rsync_opts[@]}" "$SRC_DIR/code.py" "$mount_point/code.py"

for file in "${LEGACY_FILES[@]}"; do
    if [[ -f "$mount_point/$file" ]]; then
        echo "Removing legacy $file"
        run rm "$mount_point/$file"
    fi
done

if $copy_libs; then
    bundle_lib="$(ls -d "$PROJECT_DIR"/adafruit-circuitpython-bundle-*/lib 2>/dev/null | sort | tail -n 1)"
    if [[ -z "$bundle_lib" ]]; then
        echo "No adafruit-circuitpython-bundle-*/lib found in $PROJECT_DIR" >&2
        exit 1
    fi
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
            echo "Library $lib not found in $bundle_lib" >&2
            exit 1
        fi
    done < "$PROJECT_DIR/requirements-circuitpython.txt"
fi

# FAT drives buffer writes; flush so the board is safe to unplug.
run sync -f "$mount_point"
echo "Done."
