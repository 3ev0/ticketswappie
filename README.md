# Installation
Build the docker image using the dockerfile and run it

Or 

1. Install Chrome browser
2. Install Chrome driver to PATH, e.g. /usr/local/bin/
3. Setup python virtual env
4. Install python deps: `pip install -r requirements.txt`

# Run it
Make sure to set the environment variables:

```
RUN_INTERVAL=30
MSG_INTERVAL=0.5
TG_TICKET_CHANNEL=
TG_TICKET_BOT_TOKEN=
TG_ALERT_CHANNEL=
TG_ALERT_BOT_TOKEN=

# use this var to point to file:// or http:// containing json 
# with ticket sources
TICKET_SOURCE_URLS_URI= 
```
Start the docker container

or 

1. Active virtualenv
2. Run `python main.py`