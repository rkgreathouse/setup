#!/bin/sh
set -e
cd "$(dirname "$0")"

mkdir -p build
rm -f build/forest-night-intellij.jar
jar cf build/forest-night-intellij.jar -C src/main/resources .

echo "Built build/forest-night-intellij.jar"
