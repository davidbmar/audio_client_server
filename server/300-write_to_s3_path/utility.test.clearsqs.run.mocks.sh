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
echo "Simulating a mock Runpod.io text transcriber"
./utility.mock_transcribe.py
echo "DONE: Output should be in SQS Queue."
echo "sqs_queue_runpodio_whisperprocessor_us_east_2_completed_transcription_nonfifo"
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./pull_transcribed_txt_from_sqs_queue.py --run-once"
./pull_transcribed_txt_from_sqs_queue.py --run-once
echo "DONE: Pulled from the SQS Queue. Output should be in output.csv."
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./sort_csv.py"
./sort_csv.py
echo "DONE: Sorted. Output should be in output.csv.sorted"
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./llm_transcription_summary.py."
./llm_transcription_summary.py


