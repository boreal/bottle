import os
import json
import socket
import requests
import time
from slackclient import SlackClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

BOT_ID = os.environ.get("SLACK_BOT_ID")
BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
API_TOKEN = os.environ.get("SLACK_API_TOKEN")
DOC_URL = os.environ.get("SLACK_BOT_DOCS")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate slack client
slack_client = SlackClient(BOT_TOKEN)

# declare the users, channels and groups objects for caching
channels = None
groups = None
users = None

def get_channels():
    global channels
    url = 'https://slack.com/api/channels.list?token=' + API_TOKEN
    channels_response = http_request(url, None, None, 10, 2)
    channels = json.loads(channels_response.text)
    channels['cache_timestamp'] = time.time()
    channels_response = None

def get_groups():
    global groups
    url = 'https://slack.com/api/groups.list?token=' + API_TOKEN
    groups_response = http_request(url, None, None, 10, 2)
    groups = json.loads(groups_response.text)
    groups['cache_timestamp'] = time.time()
    groups_response = None

def get_users():
    global users
    url = 'https://slack.com/api/users.list?token=' + API_TOKEN
    users_response = http_request(url, None, None, 10, 2)
    users = json.loads(users_response.text)
    users['cache_timestamp'] = time.time()
    users_response = None

'''
Return the channel object when the channel name or ID is provided. Need to use
the "channels" endpoint for public channels and the "groups" endpoint for
private channels.
'''
def channel_info(channel):
    global channels, groups

    # public channels are in channels
    if (channels is None):
        print "channels object is empty. Fetching from source."
        perf_time_before = time.clock()
        get_channels()
        perf_time_after = time.clock()
        perf_time = perf_time_after - perf_time_before
        print "Fetching channels from source took ", perf_time, "seconds."
    elif ( ( time.time() - channels['cache_timestamp'] ) > 600 ):
        print "channels object contents are older than 10 min. Re-fetching from source."
        get_channels()
    else:
        print "channels object is populated and fresh."

    result = None
    perf_time_before = time.clock()
    for x in range (0, len(channels['channels'])):
        channels['channels'][x]['chan_type'] = 'public'
        if (channels['channels'][x]['name'] == channel):
            result = channels['channels'][x]
            break
        elif (channels['channels'][x]['id'] == channel):
            result = channels['channels'][x]
            break
    perf_time_after = time.clock()
    perf_time = perf_time_after - perf_time_before
    print "Searching channels took ", perf_time, "seconds."

    print "channel result: %s" % (result)
    if result is not None:
        result['chan_type'] = 'public'
        return result

    # private channels are in groups
    if ( groups is None ):
        print "groups object is empty. Fetching from source."
        perf_time_before = time.clock()
        get_groups()
        perf_time_after = time.clock()
        perf_time = perf_time_after - perf_time_before
        print "Fetching groups from source took ", perf_time, "seconds."
    elif ( ( time.time() - groups['cache_timestamp'] ) > 600 ):
        print "groups object contents are older than 10 min. Re-fetching from source."
        get_groups()
    else:
        print "groups object is populated and fresh."

    result = None
    perf_time_before = time.clock()
    for x in range (0, len(groups['groups'])):
        groups['groups'][x]['chan_type'] = 'private'
        if ( groups['groups'][x]['name'] == channel ):
            result = groups['groups'][x]
            break
        elif ( groups['groups'][x]['id'] == channel ):
            result = groups['groups'][x]
            break
    perf_time_after = time.clock()
    perf_time = perf_time_after - perf_time_before
    print "Searching groups took ", perf_time, "seconds."

    print "group result: %s" % (result)
    if result is not None:
        result['chan_type'] = 'private'
    return result

'''
Return the user object when the user name or ID is provided.
'''
def user_info(user):
    global users
    user = user.lower()

    if (users is None):
        print "users object is empty. Fetching from source."
        perf_time_before = time.clock()
        get_users()
        perf_time_after = time.clock()
        perf_time = perf_time_after - perf_time_before
        print "Fetching users from source took ", perf_time, "seconds."
    elif ( ( time.time() - users['cache_timestamp'] ) > 600 ):
        print "users object contents are older than 10 min. Re-fetching from source."
        get_users()
    else:
        print "users object is populated and fresh."

    result = None
    perf_time_before = time.clock()
    for x in range (0, len(users['members'])):
        if ( users['members'][x]['name'] == user ):
            result = users['members'][x]
            break
        elif ( users['members'][x]['id'] == user.upper() ):
            result = users['members'][x]
            break
        elif ( user in users['members'][x]['profile']['real_name'].lower() ):
            result = users['members'][x]
            break
    perf_time_after = time.clock()
    perf_time = perf_time_after - perf_time_before
    print "Searching users took ", perf_time, "seconds."

    print "user result: %s" % (result)
    return result

def invite_new_hire( params ):
    response = []
    #default_channels = ['back-end-team', 'front-end-team', 'product-support', 'product-team', 'production-deployment', 'release_qa', 'tech', 'leaguelife', 'market-news', 'dose-of-wellness', 'api-announcements', 'backend-pull-requests', 'mobile-apps-team', 'product-member-ux', 'beer-o_clock']
    default_channels = ['onboard-test', 'onboard-test-1', 'onboard-test-2', 'onboard-test-3']
    user = user_info(params[1])
    # No matching user found.
    if user is None:
        return "User not found"
    # No channels specified therefore add the user to the default channels.
    if ( len(params) < 3 ):
        for channel in default_channels:
            chaninfo = channel_info(channel)
            print "CHANNEL INFO: %s" % chaninfo
            print "USER INFO: %s" % user
            if ( chaninfo['chan_type'] == 'private' ):
                url = "https://slack.com/api/groups.invite?token=%s&user=%s&channel=%s" % (API_TOKEN, user['id'], chaninfo['id'])
            elif ( chaninfo['chan_type'] == 'public' ):
                url = "https://slack.com/api/channels.invite?token=%s&user=%s&channel=%s" % (API_TOKEN, user['id'], chaninfo['id'])
            response_json = http_request(url, None, None, 10, 2)
            print "invitation response: %s" % (response_json.text)
            try:
                re = json.loads( response_json.text )
            except (ValueError, KeyError, TypeError):
                print "JSON format error: %s" % (response_json.text)
                return "Something went wrong loading up the JSON response"
            re['failchan'] = chaninfo['name']
            response.append(re)

    return response

def share_docs( params ):
    user = user_info(params[1])
    # No matching user found.
    if user is None:
        return "User not found"
    im_open = slack_client.api_call( "im.open", user=user['id'] )
    print "IM.OPEN response: %s" % (im_open)
    msg_return = slack_client.api_call("chat.postMessage", channel=im_open['channel']['id'], text="Welcome Document: " + DOC_URL, as_user=True)
    print "MSG RETURN: %s" % msg_return
    return "\nOnboarding document shared with %s" % ( params[1] )


'''
Make HTTP requests.
'''
def http_request(url, data=None, headers=None, timeout=20, tries=1):
    if headers is None:
        headers = {}
    headers['user_agent'] = "Mozilla/5.0 (Bottle 1.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

    while tries > 0:
        tries -= 1
        try:
            if data is None:
                response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            else:
                response = requests.post(url, data=data, headers=headers, timeout=timeout, verify=False)

        except requests.exceptions.RequestException as error:
            response = "HTTP Request Exception trying to get %s - Error: %s" % (url, error)
            time.sleep(1)
            continue

        if response.status_code == 503:
            time.sleep(1)
        else:
            tries = 0

    return response

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        print output_list
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                #return output['text'].split(AT_BOT)[1].strip().lower(), \
                return output['text'].split(AT_BOT)[1].strip(), output['channel']
    return None, None

def print_help():
    send_response = "Oh hai! Bottle is happy to serve. Please try a command like one of these::\n" + \
                    '```@bottle onboard aristotle\n@bottle channel general\n@bottle user aristotle```'
    slack_client.api_call("chat.postMessage", channel=channel, text=send_response, as_user=True)

def handle_command(command, channel):
    # Commands bottle understands
    do = ['onboard', 'user', 'channel']
    commands = command.split()
    if commands[0] in do:
        #slack_client.api_call("chat.postMessage", channel=channel, text="Processing your request...", as_user=True)
        if (commands[0] == "onboard" ):
            success = ''
            fail = ''
            response = invite_new_hire(commands)
            if isinstance(response, list):
                for invite in response:
                    if ( invite['ok'] ):
                        print "invite ok: %s" % invite
                        if 'channel' in invite:
                            success += invite['channel']['name'] + " "
                        else:
                            success += invite['group']['name'] + " "
                    else:
                        print "invite bad: %s" % invite
                        if 'channel' in invite:
                            fail += invite['failchan'] + " "
                        else:
                            fail += invite['failchan'] + " "
                if success:
                    send_response = "%s was added to %s." % (commands[1], success)
                if fail:
                    send_response += " Failed to add %s to %s." % (commands[1], fail)
            else:
                send_response = response
            response = share_docs( commands )
            send_response += response

        # Get channel info
        elif (commands[0] == "channel"):
            response = channel_info(commands[1])
            if response is not None:
                send_response = '```Channel Name: ' + response['name'] + '\n'
                send_response += 'Channel ID: ' + response['id'] + '\n'
                if ( response['chan_type'] == 'public' ):
                    send_response += 'Member Count: %d\n' % (response['num_members'])
                send_response += 'Channel type: ' + response['chan_type'] + '```'
            else:
                send_response = "Invalid %s parameter: %s" % (commands[0], commands[1])
        # Get user info
        elif (commands[0] == "user"):
            response = user_info(commands[1])
            if response is not None:
                send_response = '```User Name: ' + response['name'] + '\n'
                send_response += 'User ID: ' + response['id'] + '\n'
                send_response += 'Real Name: ' + response['profile']['first_name'] + " " + response['profile']['last_name'] + '```'
            elif ( commands[1] == "aristotle"):
                send_response = "No silly! Aristotle is just an example. Specify a real slack user."
            else:
                send_response = "Invalid %s parameter: %s" % (commands[0], commands[1])
        # No command given. Send snarky reply.
        else:
            send_response = "Sure...write some more code then I can do that!"
        slack_client.api_call("chat.postMessage", channel=channel, text=send_response, as_user=True)
    else:
        print_help()

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("bottle connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            else:
                send_response = print_help()
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
