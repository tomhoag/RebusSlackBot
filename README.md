# RebusSlackBot
Post a random rebus puzzle to a Slack channel.

## Usage
The slack bot will respond to the following commands:

`/rebus` Returns and easy rebus puzzle
`/rebus [easy|medium|hard]` Returns a rebus puzzle of the requested difficulty
`/rebus info` Returns a simple getting started message.

Any other `/rebus <foo>` command returns an "I don't understand" message

## Setup

### Slack App

Create a slack app @ api.slack.com.

On the 'Basic Information' page, select 'Add features and functionality' and configure for a 'Slash Command'.  Set up your command as /rebus (or whatever you'd like to use to call the bot)

Under 'Features', select 'OAuth & Permissions' and get a Bot User OAuth Token.  Keep this handy, you will need it when setting up the second lambda function.


### AWS SQS & Lambda

This bot makes use of two AWS lambda functions and an AWS queue (SQS).

Create a queue using AWS SQS.  Give the queue a name -- this repo code uses the name 'rebus'.  If you use something else, update the code appropriately.

#### The lambda functions

When a slack bot calls your function, it expects a response within 3 seconds.  Unfortunately, this bot requires a bit longer than 3s to respond.  The first lambda function accepts the rebus request and forwards it to the SQS queue and then responds to the user that a rebus is on the way.

The second lambda function processes requests on the queue and sends a second response to the user with the rebus and a DM with the answer.

For each lambda function, you will need to package up all each function separately with its requirements in a zip file.  The contents of the zip file should be organized like this:

```
Archive.zip
|
+- lambda_function.py
|
+- package
   |
   +- <requirement dir>
   +- <requirement2 dir>
   +
   +
```
If you did not name your SQS queue 'rebus' be sure to update the code with your queue name before you package up and upload the zip file!

Note that the two python files have different requirements.  Use the 'Upload from' dropdown to upload the zip file.

#### The first lambda function

The first lambda function accepts the slack bot request and processes it.  Package up the code in lambda_function.py as described above and upload the code to a lambda function.

Add an API Gateway trigger for the function.  Make note of the API endpoint -- and add this to Request URL of the slash command configuration.

#### The second lambda function

The second lambda function monitors the SQS and returns a rebus puzzle and a DM to the requestor with the answer.

Package up rebus2.py as described above (rename the file to lambda_function.py) and create a second AWS lambda function and upload the second zip file to that function.

Create an SQS trigger for this lambda function so that it will run when a new message is added to the 'rebus' queue.

Using the 'Configuration' tab, set up an 'Environment variable' with the key 'SLACK_TOKEN' and the value set to the Bot User OAuth Token you created when you set up your app.





 
    

