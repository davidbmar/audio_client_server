#!/usr/bin/bash
echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "removing output.csv"
rm output.csv
touch output.csv
sleep 5

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./audio2script.py --env staging &"
./audio2script.py --env staging &
sleep 2

# Nov10 2023 - I believe this should be deprecated.
#echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
#echo "./sort_csv.py -loop-every-x-seconds 1"
#./sort_csv.py -loop-every-x-seconds 1 &
#echo "DONE: Sorted. Output should be in output.csv.sorted"
#sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "rm csv_to_html_last_line.dat"
echo "Be sure to remove the dat file which tracks the last line read of the transcribed lines."
rm /var/www/html/transcribed_lines.html
rm transcribed_lines.html
rm csv_to_html_last_line.dat

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./csv_to_html.py -loop-every-x-seconds 1 &"
./csv_to_html.py --loop-every-x-seconds 1 --last-line-processed 0 &

#echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
#echo "./llm_transcription_summary.py."
#./llm_transcription_summary.py


