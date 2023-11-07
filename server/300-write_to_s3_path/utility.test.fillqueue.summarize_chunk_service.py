#!/usr/bin/python3
import boto3
import json
import hashlib
import time

# Your AWS region
region_name = 'us-east-2'

# The URL of the FIFO SQS queue (make sure it ends with '.fifo')
queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/sqs_summarize_chunk.fifo'

# Creating an SQS client
sqs = boto3.client('sqs', region_name=region_name)

def generate_deduplication_id(message_body):
    """
    Generates a deduplication ID based on the message content.

    Parameters:
    - message_body (str): The JSON serialized message content.

    Returns:
    - The deduplication ID (str).
    """
    return hashlib.sha256(message_body.encode('utf-8')).hexdigest()

def send_message_to_fifo_sqs(message_body, message_group_id):
    """
    Sends a message to the FIFO SQS queue with exception handling.

    Parameters:
    - message_body (dict): The message content to send.
    - message_group_id (str): The group ID for the message, messages with the same group ID are delivered in order.

    Returns:
    - The response from the SQS service or None if an exception occurred.
    """

    try:
        # Serialize the message body to JSON
        json_message_body = json.dumps(message_body)

        # Generate a deduplication ID
        message_deduplication_id = generate_deduplication_id(json_message_body)

        # Send the message to the FIFO SQS queue
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json_message_body,
            MessageGroupId=message_group_id,
            MessageDeduplicationId=message_deduplication_id
        )
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

#data_chunks = [
   #{  'end_sentence_num': 4,
      #'num_words': 149,
      #'start_sentence_num': 0,
      #'text': "A"},
   #{  'end_sentence_num': 4,
      #'num_words': 149,
      #'start_sentence_num': 0,
      #'text': "B"},
   #{  'end_sentence_num': 4,
      #'num_words': 149,
      #'start_sentence_num': 0,
      #'text': "C"}]

all_data_chunks = [
   {  'end_sentence_num': 24,
      'num_words': 550,
      'start_sentence_num': 20,
      'text': "I think right cuz you like don't do you don't schedule or something like that?  like I mean Like it "
              "looks like being an ass  right?  But I Like you guys I would get so many DMS and they're all like I "
              "mean generally very low-quality DMS  right?  Like I want to collaborate but I don't want to invest I "
              "don't want to like you want something from you I think it's like being a hot girl in the club like "
              "people want something for you But they don't want to invest the time to actually get to know you or you "
              "know you feel like an object and I don't like to feel like that and I want to spend more time with  you "
              'know  like with my friends in real life  with my girlfriend or something. I want to spend time in the '
              'gym  you know  on my health and cooking food and. that kind of stuff  go for walks and. I think because '
              "I because I've been doing this for 10 years like started like eight years and now I get the money's "
              "going well so I don't really need to do any calls anymore any dms so I'm just trying to create a more "
              "chill life and I'm not an asshole it just means like I don't have time to met to reply to everybody so "
              "I close my dms and and then people got really angry on twitter like why don't you why do you close your "
              'jams are you arrogant and stuff so I wrote a blog post like kind of explaining my day and my routine '
              "and what I do in a day and that I don't really have time if I do all the things I do now to also dm "
              "everybody and reply everybody and do calls and stuff um and that's pretty much the argument argument "
              "let's give the context so let's explain who you who the heck you are so uh your name is peter levels "
              "you're known on um twitter as levels io right yeah that's the uh that's the right way to say it I saw "
              "you a while back I'm just going to say some interesting things about you I believe that you can correct "
              "me if I have any of these wrong I believe you publish how much you make every year and in fact it's in "
              "your twitter bio in your location there's like a meter that's like your road to three million a year "
              'yeah and it says 2. 7 million so your your meter is almost all the way full filled up um you build a '
              'bunch of random small projects usually around some things you like or believe or your lifestyle which '
              "is kind of a nomadic lifestyle so I believe uh  I think you hop around or you don't have a home base  "
              'so you live  you know  you could be like in Bali and then you could be in the Netherlands  you could be '
              'a different place all the time. And you make these small websites or apps  and it says in your bio that '
              'you have 13 million monthly active users.'},
   {  'end_sentence_num': 8,
      'num_words': 140,
      'start_sentence_num': 4,
      'text': "No  but that's the thing. I was thinking like Sam is like  he's not a regular interviewer. You know  he "
              "asks some crazy shit  so. Wait  me?  First of all  I don't know if that's true. I don't know if we  "
              "first of all  it's not just me. It's you too  Sean  that asks weird stuff. But also  I don't think we "
              "ask that weird questions. I think we ask the questions that everyone's thinking. That's true. But I "
              "mean  you're not Yes Man. Like  you know  there's Yes Man podcast where like they just  it's kind of "
              "like a fan thing. Obviously that's not you guys. You have real shit  real questions. And that's  I "
              "think it's more interesting as well."},
   {  'end_sentence_num': 12,
     'num_words': 135,
      'start_sentence_num': 8,
      'text': "Obviously that's not you guys. You have real shit  real questions. And that's  I think it's more "
              'interesting as well. Can we  Sam  can we share the thing you were just telling us in Slack?  Can I '
              "share that on here on the pod?  Yeah  which one?  This is Sam Parr's strategy for networking. This is  "
              "you know  you can go to Harvard. You can go to Stanford. You're not gonna learn this one. Sam has this "
              "habit where if  like  you know  it's a very small little tweak  but it's just so Sam that it just is "
             "awesome. So if you're  if Sam wants to hang out with you  he'll text you just like a normal person "
              'would.'},
   {  'end_sentence_num': 16,
      'num_words': 195,
     'start_sentence_num': 12,
      'text': "So if you're  if Sam wants to hang out with you  he'll text you just like a normal person would. But  "
              "and he doesn't need to even know you. He's just like interested in you. Maybe it's a cold DM. Maybe "
              "it's a text message. Maybe he got your number from somebody else. Like  hey  it's Sam. You know  I'm in "
             "San Francisco  but instead of saying  wanna hang?   Same we'll just go. I'm in San Francisco. Let's You "
              "send me some shit that I want What what is this and why does it work so well It's like a phrase like  "
              'you know  like people will be like  you know  I fuck with that guy like I fuck with Drake I like Drake '
              "it Extends from that and I just say it and people They reply I don't know I just yeah this particular "
              "one I it was a CEO of a multi-billion dollar company who I'm friendly with. I just said what's up?  I'm "
             "in your hood Let's and he goes down when?  Like it worked out."},
   {  'end_sentence_num': 20,
      'num_words': 274,
      'start_sentence_num': 16,
      'text': "I just said what's up?  I'm in your hood Let's and he goes down when?  Like it worked out. It's "
              "amazing. And now so normally we try to play it cool  but we've actually been chasing you Peter We've "
              "been we've been talking about your projects. We've been being like  hey  we got to get this guy in the "
              "pod Sam is a fan of you for sure I would say I am less of a fan than Sam  but I am a and that doesn't "
              "mean I like you It's just I'm more in the closet about it. Whereas Sam is very Sam's like this guy's "
              "amazing. This guy's like an artist. This guy's got great hair and you do have great hair So it's all "
              "true Finally got you here and it was hard. I think right cuz you like don't do you don't schedule or "
              'something like that?  like I mean Like it looks like being an ass  right?  But I Like you guys I would '
              "get so many DMS and they're all like I mean generally very low-quality DMS  right?  Like I want to "
              "collaborate but I don't want to invest I don't want to like you want something from you I think it's "
              "like being a hot girl in the club like people want something for you But they don't want to invest the "
              "time to actually get to know you or you know you feel like an object and I don't like to feel like that "
              'and I want to spend more time with  you know'},
   {  'end_sentence_num': 24,
      'num_words': 550,
      'start_sentence_num': 20,
      'text': "I think right cuz you like don't do you don't schedule or something like that?  like I mean Like it "
              "looks like being an ass  right?  But I Like you guys I would get so many DMS and they're all like I "
              "mean generally very low-quality DMS  right?  Like I want to collaborate but I don't want to invest I "
              "don't want to like you want something from you I think it's like being a hot girl in the club like "
              "people want something for you But they don't want to invest the time to actually get to know you or you "
              "know you feel like an object and I don't like to feel like that and I want to spend more time with  you "
              'know  like with my friends in real life  with my girlfriend or something. I want to spend time in the '
              'gym  you know  on my health and cooking food and. that kind of stuff  go for walks and. I think because '
              "I because I've been doing this for 10 years like started like eight years and now I get the money's "
              "going well so I don't really need to do any calls anymore any dms so I'm just trying to create a more "
              "chill life and I'm not an asshole it just means like I don't have time to met to reply to everybody so "
              "I close my dms and and then people got really angry on twitter like why don't you why do you close your "
              'jams are you arrogant and stuff so I wrote a blog post like kind of explaining my day and my routine '
              "and what I do in a day and that I don't really have time if I do all the things I do now to also dm "
              "everybody and reply everybody and do calls and stuff um and that's pretty much the argument argument "
              "let's give the context so let's explain who you who the heck you are so uh your name is peter levels "
              "you're known on um twitter as levels io right yeah that's the uh that's the right way to say it I saw "
              "you a while back I'm just going to say some interesting things about you I believe that you can correct "
              "me if I have any of these wrong I believe you publish how much you make every year and in fact it's in "
              "your twitter bio in your location there's like a meter that's like your road to three million a year "
              'yeah and it says 2. 7 million so your your meter is almost all the way full filled up um you build a '
              'bunch of random small projects usually around some things you like or believe or your lifestyle which '
              "is kind of a nomadic lifestyle so I believe uh  I think you hop around or you don't have a home base  "
              'so you live  you know  you could be like in Bali and then you could be in the Netherlands  you could be '
              'a different place all the time. And you make these small websites or apps  and it says in your bio that '
              'you have 13 million monthly active users.'},
   {  'end_sentence_num': 28,
      'num_words': 160,
      'start_sentence_num': 24,
      'text': ' you could be a different place all the time. And you make these small websites or apps  and it says in '
              'your bio that you have 13 million monthly active users. And I remember seeing you because you did a '
              'community  like a nomad community  a Slack community really early on  like Slack had just come out. And '
              "I was like  this guy's like charging 10 bucks  I think it was 10 bucks a month or something to get into "
              "this thing. I was like  he's got like a thousand people in here. Wow  this is actually  this guy's "
              'making good money doing this  like just by making a Slack group. You just do a bunch of small '
              "experiments like that. That's what I know. Sam  what did I miss?  I'll give  Peter  let me give like "
              "the outsider's perspective that's a little more holistic."},
   {  'end_sentence_num': 32,
      'num_words': 136,
      'start_sentence_num': 28,
      'text': "You just do a bunch of small experiments like that. That's what I know. Sam  what did I miss?  I'll "
              "give  Peter  let me give like the outsider's perspective that's a little more holistic. So basically "
              "there's two things that are interesting to you. The first one is your businesses  which actually are "
              'the least  the lesser of the two interesting things. So you have roughly five or  yeah  you have seven '
              "different businesses ranging from Nomad List  which makes $2. 1 million in the last 12 months. That's a "
              "job board. You have another job board called Remote OK  that's making $115 000 a month. You have "
              "ReadMate  which looks like it's like an ebook  something like that. Yeah  60K a month."},
   {  'end_sentence_num': 36,
      'num_words': 133,
      'start_sentence_num': 32,
      'text': "You have ReadMate  which looks like it's like an ebook  something like that. Yeah  60K a month. Then "
              "you have got like a bunch of really- Sam  you're seeing these numbers because he publishes them. Where "
              "do you publish these?  He publishes all of them on like the URL. Go to his Twitter profile and we'll "
              'let you talk  sorry  Peter  in a second  but go to his Twitter profile. Go to his Twitter profile and '
              "then like click off and it's like open revenue at the very bottom. But I'm reading off of our notes. "
              "And then you have like a QR menu creator. Then you have like an inflation chart  which doesn't seem "
              'like it makes money  but tracks inflation.'},
   {  'end_sentence_num': 40,
      'num_words': 144,
      'start_sentence_num': 36,
      'text': "And then you have like a QR menu creator. Then you have like an inflation chart  which doesn't seem "
              'like it makes money  but tracks inflation. And then you have Rebase  which is a platform to help people '
              'become a citizen of Portugal  help them relocate to Portugal. So the first part is those businesses. '
              'Like I said  you have those that are interesting. I would narrow it down to say you have a series of '
              "job boards for nomadic or remote work that are pretty profitable. But the second thing that's even more "
              'interesting is the way that you do these things. So you do a few things that are interesting. So for '
              "the past 10 years  I've been keeping this little notebook with a scratch pad that I call  You see "
              'that?  Money wisdom.'},
   {  'end_sentence_num': 44,
      'num_words': 144,
      'start_sentence_num': 40,
      'text': "So for the past 10 years  I've been keeping this little notebook with a scratch pad that I call  You "
              'see that?  Money wisdom. Reminders to self. And these are basically just anytime I heard something  I '
              'read something  or I learned something that was wise about wealth  I would write it down. And I put all '
              "the notes here  and today I'm going to read you a bunch of the things that are in this notebook. And I "
              "feel like I could do that because in most places  you can't really talk about money. Money is sort of "
              "this tacky  taboo thing. Everybody has to pretend they don't care about money  but we all do  which is "
              'weird. But you just have to treat it like this silent fart in the room.'}]

data_chunks = all_data_chunks[0:15]
message_group_id = str(int(time.time()))


for chunk in data_chunks:
    response = send_message_to_fifo_sqs(chunk, message_group_id)
    if response:
        print(f"Message sent with ID: {response['MessageId']}")
    # Removed time.sleep(2) - uncomment if needed for throttling
    # time.sleep(2)


