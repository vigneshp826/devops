#!/usr/bin/python#
# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, unicode_literals
import re
import requests
import itertools
import paramiko
import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from flask import Flask, request, make_response, Response
import os
import json
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
nltk.download('stopwords', '/home/vcap/app/nltk_data/')
nltk.data.path.append('./nltk_data/')
nltk.download('punkt', '/home/vcap/app/nltk_data/')
nltk.data.path.append('./nltk_data/')

proxies = \
    dict(https='<encode>'
         ,
         http='<encode>'
         )
port = os.getenv('VCAP_APP_PORT', '5000')

# Your app's Slack bot user token

var = os.environ.get('VCAP_SERVICES')
inventory = json.loads(var)
SLACK_BOT_TOKEN = inventory['user-provided'][0]['credentials'
        ]['SLACK_BOT_TOKEN']
SLACK_VERIFICATION_TOKEN = inventory['user-provided'][0]['credentials'
        ]['SLACK_VERIFICATION_TOKEN']
print ('SLACK_BOT_TOKEN', SLACK_BOT_TOKEN)
print ('SLACK_VERIFICATION_TOKEN', SLACK_VERIFICATION_TOKEN)

slack_client = SlackClient(SLACK_BOT_TOKEN, proxies=proxies)


# Flask web server for incoming traffic from Slack

app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN,
        '/slack/events', app)

print slack_events_adapter

# To enable EVENT API initial check from SLACK
@app.route('/challenge', methods=['POST'])
def request_challenge():
    return json.dumps(request.json)

#Handle what user types	and sends
def handle_command(command,   channel, user, mailid):
    channel = channel
    command = command
    
    GREETING_KEYWORDS = (
        'hello',
        'hi',
        'hii',
        'greetings',
        'sup',
        "what's up",
        'hey',
        'morning',
        )
    healthoption = ['health', 'healthcheck', 'check', 'health check']
    mailid1 = mailid.replace('_', ' ')

    # mailid2 = ''.join(mailid1.split("@")[:1])

    GREETING_RESPONSES = 'Hi ' + mailid + ', How can i help you?'

# ********************************************************************************#

    stop_words = set(stopwords.words('english'))
    print stopwords

    filtered_sentence = []

    tokenizedcommand = nltk.word_tokenize(command)

    for w in tokenizedcommand:
        print w
        if w.lower() not in stop_words:
            filtered_sentence.append(w)

    print 'tc: %s' % tokenizedcommand
    print 'fs:%s' % filtered_sentence

# Main for loop with all conditions to check

    for word in filtered_sentence:
        print word

# """If any of the words in the user's input was a greeting, return a greeting response"""

        if word.lower() in GREETING_KEYWORDS:
            slack_client.api_call('chat.postMessage', channel=channel, text=GREETING_RESPONSES, as_user=True)
     	
        elif word.lower() in healthoption:

# """if any of the words in the user's input is for health check, do health check of the app"""
# **********************************************************************************************

            appacronym = \
                open(r'/home/oracle/nltk_data/corpora/gutenberg/appacronymlist.txt'
                     ).read()  # a list contains some application names


            for i in filtered_sentence:
                if i.lower() not in healthoption and i.lower() \
                    in appacronym.lower():
                    argument = '%' + i.lower() + '%'
                    slack_client.api_call('chat.postMessage', channel=channel, text='health check in progress', as_user=True)
                else:
                    pass
                    slack_client.api_call('chat.postMessage',
                            channel=channel,
                            text='I heard health check, but app name is not recognizable'
                            ,
                            icon_url='#https://pbs.twimg.com/profile_images/1232518700/Endhiran-Movie-Wallpapers-6_1__400x400.jpg'
                            , as_user=True)
            break
        else:
            global order_dm
            order_dm = slack_client.api_call('chat.postMessage', as_user=True,
                                  channel=user,
                                  text="I am Coffeebot ::robot_face::, and I\'m here to help bring you fresh coffee :coffee:"
                                  , attachments=[{
                'text': '',
                'callback_id': channel + 'coffee_order_form',
                'color': '#3AA3E3',
                'attachment_type': 'default',
                'actions': [{
                    'name': 'coffee_order',
                    'text': ':coffee: Order Coffee',
                    'type': 'button',
                    'value': 'coffee_order',
                    }],
                }])
    return None

# Slack client for Web API requests

# Dictionary to store coffee orders. In the real world, you'd want an actual key-value store

COFFEE_ORDERS = {}


@app.route('/slack/message_actions', methods=['POST'])
def message_actions():

    # Parse the request payload

    message_action = json.loads(request.form['payload'])
    user_id = message_action['user']['id']
    print("message_action",message_action)

    channel = request.form.get('channel_name')

    # verify_slack_token(message_action["token"], channel)

    username = request.form.get('user_name')
    text = request.form.get('text')
    inbound_message = message_action
	
    COFFEE_ORDERS[user_id] = {
         "order_channel": order_dm["channel"],
         "message_ts": "",
         "order": {}
	}
    slack_client.api_call('chat.postMessage', channel=user_id, text=COFFEE_ORDERS[user_id])
    slack_client.api_call('chat.postMessage', channel=user_id, text=inbound_message)
    if message_action['type'] == 'interactive_message':

        # Add the message_ts to the user's order info

        COFFEE_ORDERS[user_id]['message_ts'] = message_action['message_ts']

        # Show the ordering dialog to the user

        open_dialog = slack_client.api_call('dialog.open',
                trigger_id=message_action['trigger_id'], dialog={
            'title': 'Request a coffee',
            'submit_label': 'Submit',
            'callback_id': user_id + 'coffee_order_form',
            'elements': [{
                'label': 'Coffee Type',
                'type': 'select',
                'name': 'meal_preferences',
                'placeholder': 'Select a drink',
                'options': [{'label': 'Cappuccino',
                            'value': 'cappuccino'}, {'label': 'Latte',
                            'value': 'latte'}, {'label': 'Pour Over',
                            'value': 'pour_over'}, {'label': 'Cold Brew'
                            , 'value': 'cold_brew'}],
                }],
            })

        print(open_dialog)

        # Update the message to show that we're in the process of taking their order

        slack_client.api_call('chat.update',
                              channel=COFFEE_ORDERS[user_id]['order_channel'
                              ], ts=message_action['message_ts'],
                              text=':pencil: Taking your order...',
                              attachments=[])
    elif message_action['type'] == 'dialog_submission':

        coffee_order = COFFEE_ORDERS[user_id]

        # Update the message to show that we're in the process of taking their order

        slack_client.api_call('chat.update', channel=COFFEE_ORDERS[user_id]['order_channel'], ts=coffee_order['message_ts'], text=':white_check_mark: Order received!', attachments=[])

    return make_response('', 200)


	
	
# Example responder to greetings

@slack_events_adapter.on('message')
def handle_message(event_data):

    message = event_data['event']
    print(message)
    
	
    #if message.get('user') == 'W833PC90S':
        #print("dummy")
    if message.get('type') == "dialog_submission":
        message_actions()
    #elif message.get('type') == "message" and message.get('user') != 'W833PC90S':
    elif message.get('type') == "message":
        (text, channel, user) = message.get('text'), message.get('channel'), message.get('user')
        print ('command:channel: user::', text, channel, user)
        handle_command(message.get('text'), message.get('channel'), message.get('user'), message['user_profile']['real_name'])
    else:
        print("dummy2")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port), debug=True)
