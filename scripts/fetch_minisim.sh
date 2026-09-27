#!/usr/bin/env bash
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
upstream=https://github.com/Shimuuar/cryptopool-simulator.git
revision=b8046e8a840a498ff2f14f673524adf0534b20dd
destination="$project_dir/.deps/cryptopool-simulator"
sample_data=reference-check/data/binance-short-btcusdt-1m.json.xz

mkdir -p "$project_dir/.deps"

git clone \
    --filter=blob:none \
    --no-checkout \
    --single-branch \
    --branch minisim \
    "$upstream" \
    "$destination"

git -C "$destination" sparse-checkout set --no-cone \
    '/minisim/' \
    '/json.hpp' \
    "/$sample_data"
git -C "$destination" checkout "$revision"

make -C "$destination/minisim"
xz --decompress --keep "$destination/$sample_data"
