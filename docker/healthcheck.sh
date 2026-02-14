#!/bin/sh

if curl -f http://localhost:8000/health; then
  exit 0
else
  exit 1
fi
