#!/usr/bin/env bash
# Start the translation server with the Python of the active environment.
cd "$(dirname "$0")" && exec python server.py
