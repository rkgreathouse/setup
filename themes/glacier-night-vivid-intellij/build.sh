#!/bin/sh
set -e
cd "$(dirname "$0")"

mkdir -p build
rm -f build/GlacierNightVivid.jar
jar cf build/GlacierNightVivid.jar -C src .

echo "Built build/GlacierNightVivid.jar"
