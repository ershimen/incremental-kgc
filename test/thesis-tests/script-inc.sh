#!/bin/bash

sizes=("1" "5" "10" "25" "50")
tests=("test-morph-disk-no-opt.py" "test-morph-memory-no-opt.py" "test-rdfizer-no-opt.py" "test-morph-disk-opt.py" "test-morph-memory-opt.py" "test-rdfizer-opt.py")
n_times=5

rm results/inc/* &> /dev/null

for s in "${sizes[@]}"; do
    # Create links of datasources
    for f in "data$s"/*; do
        ln -srf $f data/$(basename $f)
    done
    echo "Running tests on size $s..."
    for test in "${tests[@]}"; do
        echo -ne "\tRunning $test $n_times times"
        for x in $(seq 1 $n_times); do
			echo -n "."
			printf '#%.0s' {1..25} >> results/inc/$test-$s.out
			echo -n " $x " >> results/inc/$test-$s.out
			printf '#%.0s' {1..25} >> results/inc/$test-$s.out
			echo "" >> results/inc/$test-$s.out
			python3 $test &>> results/inc/$test-$s.out || exit 1
		done
		echo ""
    done
done

rm data/*
rm -rf .aux
rm error.log

echo "Finished running tests."
