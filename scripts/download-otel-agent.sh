#!/bin/bash
# Download OpenTelemetry Java Agent JAR
# This script downloads the OTEL Java Agent to be mounted as volume in Docker containers

OTEL_VERSION="2.11.0"
OTEL_JAR="opentelemetry-javaagent.jar"
OTEL_URL="https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v${OTEL_VERSION}/${OTEL_JAR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${DEST_DIR}/${OTEL_JAR}" ]; then
    echo "OTEL Java Agent already exists at ${DEST_DIR}/${OTEL_JAR}"
    echo "Version: $(java -jar "${DEST_DIR}/${OTEL_JAR}" --version 2>/dev/null || echo 'unknown')"
    exit 0
fi

echo "Downloading OpenTelemetry Java Agent v${OTEL_VERSION}..."
curl -L -o "${DEST_DIR}/${OTEL_JAR}" "${OTEL_URL}"

if [ $? -eq 0 ]; then
    echo "Download complete: ${DEST_DIR}/${OTEL_JAR}"
    echo "To use, mount as volume: -javaagent:/otel/opentelemetry-javaagent.jar"
else
    echo "Download failed. Please download manually from:"
    echo "${OTEL_URL}"
    exit 1
fi