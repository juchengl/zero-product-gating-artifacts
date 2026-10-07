#!/bin/bash
set -x
cd ~
rm -rf libify
git -c http.version=HTTP/1.1 clone --depth 1 https://github.com/efabless/libify.git libify 2>&1 | tail -3
ls libify 2>/dev/null | head -6