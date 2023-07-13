#!/bin/bash

declare -A sizes=([1]="1" [2]="5" [3]="10" [4]="25" [5]="50" [6]="100")

declare -A n_lines=(
[AGENCY.csv]="2 6 11 26 51 101"
[CALENDAR.csv]="6 26 51 126 251 501"
[CALENDAR_DATES.csv]="15 351 701 1751 3501 7001"
[FEED_INFO.csv]="2 6 11 26 51 101"
[FREQUENCIES.csv]="51 4276 8551 21376 42751 85501"
[ROUTES.csv]="14 66 131 326 651 1301"
[SHAPES.csv]="68 292701 585401 1463501 2927001 5854001"
[STOP_TIMES.csv]="41 11821 23641 59101 118201 236401"
[STOPS.csv]="37 6311 12621 31551 63101 126201"
[TRIPS.csv]="40 651 1301 3251 6501 13001"
)

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

long=$([ "-l" = $1 ]; echo $?)

for i in $(seq 1 ${#sizes[@]}); do
	s=${sizes[$i]}
	echo "Verifying size $s..."
	for f in $(ls data$s/); do
		current_size=$(wc -l data$s/$f | cut -d ' ' -f1)
		right_size=$(echo ${n_lines[$f]} | cut -d ' ' -f$i)
		if [ $current_size -ne $right_size ]; then
			echo -e "\t$f...${RED}ERROR${NC}: $current_size vs $right_size"
		else
			if [ $long = "0" ]; then
				echo -e "\t$f...${GREEN}OK${NC} ($current_size)"
			fi
		fi
	done
done

