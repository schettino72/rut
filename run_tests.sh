#!/bin/bash
export PYTHONPATH=src

if [ "$1" == "--cov" ]; then
  uv run python -m coverage run --source=src -m unittest discover -s tests -p "test_*.py" -v
  uv run python -m coverage report -m
else
  uv run python -m unittest discover -s tests -p "test_*.py" -v
fi
