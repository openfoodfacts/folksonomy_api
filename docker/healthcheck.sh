#!/bin/sh

if curl -f http://localhost:8000/; then
  exit 0
else
  exit 1
fi
