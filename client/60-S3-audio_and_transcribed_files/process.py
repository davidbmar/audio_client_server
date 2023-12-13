#!/usr/bin/python3
from find_audiofile_groupings import get_grouped_files
from s3_txt_and_audio import compare_files,generate_html_page


if __name__ == "__main__":

   bucket_audio_name = 'presigned-url-audio-uploads'
   bucket_text_name = 'audioclientserver-transcribedobjects-public'

   # to use in the webpage generation.
   bucket_audio_url = 'https://presigned-url-audio-uploads.s3.us-east-2.amazonaws.com'

   gap_threshold_minutes = 5 

   grouped_files = get_grouped_files(bucket_audio_name, bucket_text_name, gap_threshold_minutes)
   for i, (first_file, last_file) in enumerate(grouped_files, start=1):
       print(f"Group {i}: First file: {first_file}, Last file: {last_file}")
       start_time = first_file
       end_time = last_file

       # Generate the table and HTML page
       table = compare_files(bucket_audio_name, bucket_text_name, start_time, end_time)
       filename = f"group_{i}.html"
       generate_html_page(table, bucket_audio_url, filename)
       






