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
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./pull_transcribed_txt_from_sqs_queue.py --run-once"
./pull_transcribed_txt_from_sqs_queue.py --run-once
sleep 2

echo "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n"
echo "./sort_csv.py"
./sort_csv.py




