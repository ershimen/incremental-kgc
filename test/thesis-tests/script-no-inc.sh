#!/bin/bash

sizes=("1" "5" "10" "25" "50")
tests=("test-morph-disk-no-inc.py" "test-morph-memory-no-inc.py" "test-rdfizer-no-inc.py")
n_times=5

rm results/no-inc/* &> /dev/null

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
			printf '#%.0s' {1..25} >> results/no-inc/$test-$s.out
			echo -n " $x " >> results/no-inc/$test-$s.out
			printf '#%.0s' {1..25} >> results/no-inc/$test-$s.out
			echo "" >> results/no-inc/$test-$s.out
			python3 $test &>> results/no-inc/$test-$s.out || exit 1
		done
		echo ""
    done
done

rm data/*
rm rdfizer_out/*
rm error.log
rm -rf .aux

echo "Finished running tests."
