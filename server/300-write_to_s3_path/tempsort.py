#!/usr/bin/python3

data = """
2023-11-19-22-42-52750-009000.flac, Here we go. It's starting now. Let's play a YouTube video here.
2023-11-19-22-50-23340-002011.flac, W.
2023-11-19-22-43-20750-009000.flac, And so I wanted to make another quick video. I'm not going to do a whole bunch of po
2023-11-19-22-44-21332-002000.flac," We only made one change. We probably made everything we know. But before we get int
2023-11-19-22-45-49330-002001.flac," tweets, not really giving any insights into what's going on. Later that night, thre
2023-11-19-22-48-41334-002002.flac," the board no longer has confidence in his ability to continue leading OpenAI. We al
2023-11-19-22-49-51334-002003.flac," Now, if you're not familiar, Sam Altman doesn't own equity in OpenAI. In fact, I do
2023-11-19-22-50-05342-002007.flac, H-I-J-E-R-I-N-G.
2023-11-19-22-49-57346-002005.flac, C. D.
2023-11-19-22-49-55330-002004.flac," A, B, C, D, E, F." 
2023-11-19-22-50-01330-002006.flac," E, F, G." 
2023-11-19-22-50-17348-002009.flac, Q. R. S.
2023-11-19-22-50-13334-002008.flac, K-L-M-N-O-P.
2023-11-19-22-50-21344-002010.flac, T-U-V
"""

# Split the data into lines and filter out any empty lines
lines = [line for line in data.strip().split('\n') if line]

# Extract the sequence number and sort the lines based on it
sorted_lines = sorted(lines, key=lambda x: int(x.split('.')[0].split('-')[-1]))

# Join the sorted lines back into a single string
sorted_data = '\n'.join(sorted_lines)

print(sorted_data)

