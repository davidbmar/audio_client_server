#!/usr/bin/bash
# clear the sqs queues
echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "Clearing all the SQS Queues.\n\n"
rm /home/ubuntu/audio_client_server/utilities/temp.output.txt
/home/ubuntu/audio_client_server/utilities/clear_sqs_queues.py > temp.output.txt
cat temp.output.txt; rm temp.output.txt

sleep 4

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "Clearing the outputfile, otherwise it will concatenate it."
rm output.csv
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "Simulating a mock Runpod.io text transcriber --slowly-trickle-data 5 "
./utility.mock_transcribe.py -slowly-trickle-data 5 &
echo "DONE: Output should be in SQS Queue."
echo "sqs_queue_runpodio_whisperprocessor_us_east_2_completed_transcription_nonfifo"
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
#echo "./pull_transcribed_txt_from_sqs_queue.py --run-once"
echo "./pull_transcribed_txt_from_sqs_queue.py --loop-every-x-seconds 2"
#./pull_transcribed_txt_from_sqs_queue.py --run-once
./pull_transcribed_txt_from_sqs_queue.py -loop-every-x-seconds 2 &
echo "DONE: Pulled from the SQS Queue. Output should be in output.csv."
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./sort_csv.py -loop-every-x-seconds"
./sort_csv.py -loop-every-x-seconds 1 &
echo "DONE: Sorted. Output should be in output.csv.sorted"
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "rm csv_to_html_last_line.dat"
echo "Be sure to remove the dat file which tracks the last line read of the transcribed lines."
rm /var/www/html/transcribed_lines.html
rm transcribed_lines.html
rm csv_to_html_last_line.dat

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./csv_to_html.py -loop-every-x-seconds 1 &"
./csv_to_html.py -loop-every-x-seconds 1 &

#echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
#echo "./llm_transcription_summary.py."
#./llm_transcription_summary.py


