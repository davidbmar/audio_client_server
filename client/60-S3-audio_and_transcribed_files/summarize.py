#!/usr/bin/python3
from datetime import datetime
import pprint
import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
from scipy.spatial.distance import cosine
import networkx as nx
from networkx.algorithms import community
#from langchain.llms import OpenAI  # new way of import.
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI  # new way of import.
import json
import re
from s3_txt_and_audio import compare_files,generate_html_page, concatenate_txt_files

## Example usage
#data = {'key1': 'value1', 'key2': [1, 2, 3], 'key3': {'nestedKey': 'nestedValue'}}
#file_pretty_print('output.txt', data, indent=4)
def file_pretty_print(file_path, *args, width=1000, **kwargs):
    """ 
    Writes the given arguments to a file in a pretty-printed format without wrapping lines.

    :param file_path: Path of the file where the output will be written.
    :param args: Arguments to be pretty-printed and written to the file.
    :param width: The maximum width of a line in the output. Defaults to 200.
    :param kwargs: Additional keyword arguments for pprint.pformat().
    """
    with open(file_path, 'a') as file:
        for arg in args:
            formatted = pprint.pformat(arg, width=width, **kwargs)
            file.write(formatted + '\n')

def extract_key(filename):
    """ 
    Extract the last 6 digits from the filename and return as an integer.

    Parameters:
    - filename (str): The filename to extract the key from.

    Returns:
    - int: The extracted key as an integer.
    """
    match = re.search(r'(\d{6})\.\w+$', filename)
    return int(match.group(1)) if match else None

def extract_txt_from_json_object(json_object):
    """
    Extract the 'txt' field from each dictionary in a JSON object,
    sort them based on the last 6 digits in the filename, and return a sorted JSON object.

    Parameters:
    - json_object (list): A list of dictionaries representing the JSON object.

    Returns:
    - list: Only the txt representing the JSON object.
    """
    # Sort the list of dictionaries based on the extracted key
    # sorted_json_object = sorted(json_object, key=lambda x: extract_key(x['filename']))

    # Create a list to hold the sorted 'txt' fields
    txt_list = [entry['txt'] for entry in json_object]

    return txt_list

def read_and_convert_to_json(input_filename, output_filename):
    """
    Read a text file line by line and convert it to a JSON structure.

    Parameters:
    - input_filename (str): The name of the input text file.
    - output_filename (str): The name of the output JSON file.
    """
    # Initialize an empty list to store the dictionaries
    json_list = []

    try:
        # Open the input text file and read line by line
        with open(input_filename, 'r') as infile:
            for line in infile:
                # Split the line into filename and text
                filename, txt = line.split(',', 1)
                # Remove leading and trailing whitespaces and quotes from text
                txt = txt.strip().strip('"')
                # Append the data as a dictionary to the list
                json_list.append({"filename": filename, "txt": txt})

        # Write the list of dictionaries to a JSON file
        with open(output_filename, 'w') as outfile:
            json.dump(json_list, outfile, indent=4)

        return json_list

    except FileNotFoundError:
        print(f"File {input_filename} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def create_sentences(segments, MIN_WORDS, MAX_WORDS):

  # Combine the non-sentences together
  sentences = []

  is_new_sentence = True
  sentence_length = 0 
  sentence_num = 0 
  sentence_segments = []

  for i in range(len(segments)):
    if is_new_sentence == True:
      is_new_sentence = False
    # Append the segment
    sentence_segments.append(segments[i])
    segment_words = segments[i].split(' ')
    sentence_length += len(segment_words)

    # Check Conditions: If the sentence length is at least MIN_WORDS and the segment ends with a period, 
    # or if the sentence length exceeds MAX_WORDS, the sentence is considered complete.
    # If exceed MAX_WORDS, then stop at the end of the segment. Only consider it a sentence if the length is at least MIN_WORDS.
    if (sentence_length >= MIN_WORDS and segments[i][-1] == '.') or sentence_length >= MAX_WORDS:
      sentence = ' '.join(sentence_segments)
      sentences.append({
        'sentence_num': sentence_num,
        'text': sentence,
        'sentence_length': sentence_length
      })  
      # Reset
      is_new_sentence = True
      sentence_length = 0 
      sentence_segments = []
      sentence_num += 1

  return sentences

# The function create_chunks takes a list of sentences, a CHUNK_LENGTH, and a OVERLAP as arguments. 
# It aims to create chunks of sentences based on the given chunk length and stride. The function uses the Pandas library for data manipulation.
# OVERLAP refers to the number of sentences to skip when creating the next chunk of sentences. It's a way to control the overlap between consecutive c
# How Stride Works: 
#    Let's say you have a CHUNK_LENGTH of 5 and a OVERLAP of 2. If your first chunk starts at sentence 0 and ends at sentence 4, then:
#    With a OVERLAP of 2, the next chunk will start at sentence 3 (i.e., 5 - 2 = 3) and end at sentence 7.
#    The third chunk will then start at sentence 6 (i.e., 8 - 2 = 6) and so on.
def create_chunks(sentences, CHUNK_LENGTH, OVERLAP):

  sentences_df = pd.DataFrame(sentences)

  chunks = []
  for i in range(0, len(sentences_df), (CHUNK_LENGTH - OVERLAP)):
    chunk = sentences_df.iloc[i:i+CHUNK_LENGTH]
    chunk_text = ' '.join(chunk['text'].tolist())

    chunks.append({
      'start_sentence_num': chunk['sentence_num'].iloc[0],
      'end_sentence_num': chunk['sentence_num'].iloc[-1],
      'text': chunk_text,
      'num_words': len(chunk_text.split(' '))
    })

  chunks_df = pd.DataFrame(chunks)
  return chunks_df.to_dict('records')

def parse_title_summary_results(results):
  out = []
  for e in results:
    e = e.replace('\n', '')
    if '|' in e:
      processed = {'title': e.split('|')[0],
                    'summary': e.split('|')[1][1:]
                    }
    elif ':' in e:
      processed = {'title': e.split(':')[0],
                    'summary': e.split(':')[1][1:]
                    }
    elif '-' in e:
      processed = {'title': e.split('-')[0],
                    'summary': e.split('-')[1][1:]
                    }
    else:
      processed = {'title': '',
                    'summary': e
                    }
    out.append(processed)
  return out

def summarize_stage_1(chunks_text):

  print(f'Start time: {datetime.now()}')

  # Prompt to get title and summary for each chunk
  map_prompt_template = """Firstly, give the following text an informative title. Then, on a new line, write a 75-100 word summary of the following te
  {text}

  Return your answer in the following format:
  Title | Summary...
  e.g.
  Why Artificial Intelligence is Good | AI can make humans more productive by automating many repetitive processes.

  TITLE AND CONCISE SUMMARY:"""

  map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

  # Define the LLMs
  map_llm = ChatOpenAI(temperature=0, model_name = 'gpt-3.5-turbo')
  map_llm_chain = LLMChain(llm = map_llm, prompt = map_prompt)

  # Initialize an empty list to store the outputs
  stage_1_outputs = []

  # Loop through each chunk and process it
  for chunk in chunks_text:
    single_prompt_input = {'text': chunk}
    single_prompt_result = map_llm_chain.apply([single_prompt_input])
    parsed_result = parse_title_summary_results([e['text'] for e in single_prompt_result])
    stage_1_outputs.extend(parsed_result)

  print(f'Stage 1 done time {datetime.now()}')
  return {
    'stage_1_outputs': stage_1_outputs
  }


def summarize_objects(bucket_text_name, start_time, end_time):

   # Load the API key from an environment variable
   api_key = os.environ.get("OPENAI_API_KEY")
   # Check if the API key is available
   if api_key is None:
       raise ValueError("OPENAI_API_KEY environment variable not set.")
   
   pp=pprint.PrettyPrinter(indent=3,width=120)

   concatenated_text = concatenate_txt_files(bucket_text_name, start_time, end_time)

   # Join the list into a single string
   segments = [sentence.strip() for sentence in concatenated_text.split('.') if sentence.strip()]
   
   # Put the . back in
   segments = [segment + '.' for segment in segments]
   
   # Further split by ? 
   #segments = [segment.split('?') for segment in segments]
   segments = [sub_segment for segment in segments for sub_segment in re.split(r'(?<=\?)', segment) if sub_segment.strip()]
   
   # Further split by comma
   segments = [segment.split(',') for segment in segments]
   
   segments = [item for sublist in segments for item in sublist]
   
   sentences = create_sentences(segments, MIN_WORDS=20, MAX_WORDS=80)
   chunks = create_chunks(sentences, CHUNK_LENGTH=5, OVERLAP=1)
   chunks_text = [chunk['text'] for chunk in chunks]
   
   # Run Stage 1 Summarizing
   stage_1_outputs = summarize_stage_1(chunks_text)['stage_1_outputs']
   # Split the titles and summaries
   stage_1_summaries = [e['summary'] for e in stage_1_outputs]
   stage_1_titles = [e['title'] for e in stage_1_outputs]
   num_1_chunks = len(stage_1_summaries)
   
   # Combine titles and summaries into a list of dictionaries
   combined_output = [{"title": title, "summary": summary} for title, summary in zip(stage_1_titles, stage_1_summaries)]
   
   # Convert the list of dictionaries to a JSON string
   json_output = json.dumps(combined_output, indent=3)
   
   # Optionally, save the JSON string to a file
   with open('temp/summary_output.json', 'w') as file:
       file.write(json_output)
   
   # Return the JSON string
   return json_output

def generate_summary_html(json_data):
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Summary Display</title>
        <style>
            .summary {
                margin-left: 20px;
                display: block; /* Default to showing */
            }
            .title {
                font-weight: bold;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div id="content">
    '''

    for item in json_data:
        html_content += f'''
            <div class="title" onclick="toggleSummary(this)">{item['title']}</div>
            <div class="summary">{item['summary']}</div>
        '''

    html_content += '''
        </div>
        <script>
            function toggleSummary(element) {
                var summary = element.nextElementSibling;
                summary.style.display = summary.style.display === 'none' ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    '''

    return html_content


if __name__ == "__main__":
   # Define your time filter, bucket names, and the full URL for the audio bucket
   start_time = '2023-12-13-14-01-47-206-016414'
   end_time = '2023-12-13-14-24-49-953-016437'

   bucket_text_name = 'audioclientserver-transcribedobjects-public'

   print (summarize_objects(bucket_text_name, start_time, end_time))

   json_output = summarize_objects(bucket_text_name, start_time, end_time)
   json_data = json.loads(json_output)
   html_content = generate_summary_html(json_data)

   # Save the HTML content to a file
   with open('summary_output.html', 'w') as file:
      file.write(html_content)



