#!/bin/bash

if [[ -z $1 ]]; then
	echo "Argument 1 has to be size 1, 5, 10, 25, 50 or 100"
	exit 1
fi

for f in data$1/*; do
	ln -srf $f data/$(basename $f);
done

python3 test_morph.py

