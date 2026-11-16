#!/usr/bin/env bash
# Builds site/parcels.pmtiles: Minnesota parcels with owner names, as one static tile file.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/work"; OUT="$ROOT/site"; mkdir -p "$WORK" "$OUT"; cd "$WORK"
UA="Mozilla/5.0 (HuntMap parcel build)"
note() { echo "$*"; echo "$*" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"; }

# turn any vector file into slim newline-delimited GeoJSON in lat/lng
convert() { # $1 = source file or folder, $2 = county label (optional), $3 = output
  local src="$1" layer
  layer="$(ogrinfo -ro -q "$src" 2>/dev/null | sed -E 's/^[0-9]+: //; s/ \(.*//' | grep -iv metadata | { grep -ix 'plan_parcels_open' || cat; } | { grep -i parcel || cat; } | head -1 || true)"
  [ -n "$layer" ] || layer="$(ogrinfo -ro -q "$src" | head -1 | sed -E 's/^[0-9]+: //; s/ \(.*//')"
  echo "  layer: $layer"
  ogr2ogr -f GeoJSONSeq /vsistdout/ "$src" "$layer" -t_srs EPSG:4326 -skipfailures -nlt PROMOTE_TO_MULTI 2>/dev/null | python3 "$ROOT/scripts/slim.py" "${2:-}" > "$3"
}

# ---- 1. the state's open parcel compilation (opt-in counties) ----
STATE_URL="${STATE_URL:-https://operations.gis.data.mn.gov/api/publicdownload/download/511/plan_parcels_open.gpkg}"
echo "Downloading the state open parcel dataset"
curl -fsSL --retry 3 --retry-delay 10 -A "$UA" -o open.bin "$STATE_URL"
ls -lh open.bin
rm -rf open && mkdir open
if unzip -tq open.bin >/dev/null 2>&1; then unzip -q -o open.bin -d open; else mv open.bin open/plan_parcels_open.gpkg; fi
SRC="$(find open -iname '*.gpkg' | head -1)"; [ -n "$SRC" ] || SRC="$(find open -type d -iname '*.gdb' | head -1)"
[ -n "$SRC" ] || { echo "No geopackage or geodatabase found in the state download"; exit 1; }
ogrinfo -ro -q "$SRC" || true
convert "$SRC" "" state.geojsonl
note "State open data: $(wc -l < state.geojsonl) parcels"
rm -rf open open.bin
FILES=(state.geojsonl)

# ---- 2. extra counties listed in scripts/counties.txt ----
while IFS='|' read -r NAME URL; do
  NAME="$(printf '%s' "$NAME" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"; URL="$(printf '%s' "${URL:-}" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  [ -n "$NAME" ] && [ -n "$URL" ] && [[ "$NAME" != \#* ]] || continue
  SLUG="$(echo "$NAME" | tr '[:upper:] ' '[:lower:]_')"
  (
    set -e
    if [[ "${URL,,}" != *.zip ]]; then
      curl -fsL --retry 2 -A "$UA" "$URL" -o "$SLUG.html"
      HREF="$(grep -oiE 'href="[^"]*parcel[^"]*\.zip"' "$SLUG.html" | head -1 | sed -E 's/^href="//I; s/"$//')"
      [ -n "$HREF" ] || { echo "no parcel .zip link found at $URL"; exit 1; }
      URL="$(python3 -c 'import sys,urllib.parse as u; print(u.urljoin(sys.argv[1], sys.argv[2]))' "$URL" "$HREF")"
    fi
    echo "Downloading $NAME County: $URL"
    curl -fsSL --retry 2 -A "$UA" -o "$SLUG.zip" "$URL"
    rm -rf "$SLUG" && mkdir "$SLUG" && unzip -q -o "$SLUG.zip" -d "$SLUG"
    S="$(find "$SLUG" -iname '*parcel*.shp' | head -1)"; [ -n "$S" ] || S="$(find "$SLUG" -iname '*.shp' | head -1)"
    [ -n "$S" ] || S="$(find "$SLUG" -type d -iname '*.gdb' | head -1)"; [ -n "$S" ] || S="$(find "$SLUG" -iname '*.gpkg' | head -1)"
    [ -n "$S" ] || { echo "no shapefile or geodatabase inside the $NAME download"; exit 1; }
    convert "$S" "$NAME" "$SLUG.geojsonl"
    [ -s "$SLUG.geojsonl" ]
  ) && { FILES+=("$SLUG.geojsonl"); note "$NAME County: $(wc -l < "$SLUG.geojsonl") parcels"; } || note "WARNING: $NAME County could not be added (see the log above)"
done < "$ROOT/scripts/counties.txt"

# ---- 3. tiles; step down the zoom range until the file fits GitHub Pages ----
for Z in 12 13 14; do
  tippecanoe --force -q -P -o "$OUT/parcels.pmtiles" -l parcels -Z"$Z" -z14 --drop-densest-as-needed --maximum-tile-bytes=1200000 \
    --name="Minnesota parcels" --attribution="MnGeo open parcels and county data" "${FILES[@]}"
  SIZE=$(stat -c%s "$OUT/parcels.pmtiles"); note "parcels.pmtiles at zoom $Z to 14: $((SIZE/1048576)) MB"
  [ "$SIZE" -lt 900000000 ] && break
done
[ "$SIZE" -lt 1000000000 ] || { note "ERROR: the tile file is over GitHub's 1 GB limit even at one zoom level"; exit 1; }
