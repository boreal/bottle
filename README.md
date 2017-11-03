# bottle - A Slack bot.

All the hard stuff is made easy because of https://github.com/slackapi/python-slackclient

## Installing and running

Add a bot to the org: https://your_org_name.slack.com/apps/manage/custom-integrations
Take note of the token. It will be required as an environment variable
SLACK_BOT_TOKEN


```
mkdir botle
cd bottle
virtualenv venv
source venv/bin/activate
git clone https://github.com/boreal/bottle.git
pip install -r requirements.txt
export SLACK_BOT_ID=xxxx export SLACK_API_TOKEN=xxxx export SLACK_BOT_TOKEN=xxxx; python bottle.py
```
