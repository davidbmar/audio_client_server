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
echo "rm csv_to_html_last_line.dat"
echo "Be sure to remove the dat file which tracks the last line read of the transcribed lines."
rm /var/www/html/transcribed_lines.html
rm transcribed_lines.html
rm csv_to_html_last_line.dat


