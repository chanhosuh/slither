#!/usr/bin/env bash

### Test slither-prop

python scripts/ast_parsing_test.py
if [ $? -ne 0 ]; then
  exit "test failed"
fi
