#!/bin/bash
set -e

echo "Installing Pydantic..."

# Check if uv is installed
if command -v uv &> /dev/null; then
    # Use uv to install pydantic
    uv pip install pydantic>=2.0.0
else
    # Fall back to pip
    pip install pydantic>=2.0.0
fi

echo "Pydantic installed successfully!" 