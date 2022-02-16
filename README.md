# TicketsWappie 
Scrape and monitor Ticketswap for available tickets and alert via Telegram.


## Fire up the wappie
### 0. Prerequisites
Install docker and docker-compose



### 1. Get the code from Github
`git clone https://github.com/3ev0/ticketswappie.git`

### 2. Settings.env 
Make sure to set the environment variables.

In the folder ticketswappie, create a file `./settings.env`:

```
# Interval seconds between ticket-check-routines
RUN_INTERVAL=30
# Interval seconds between TG messages
MSG_INTERVAL=0.5
# Channel ID of the Telegram ticket channel
TG_TICKET_CHANNEL=
# Token of the Telegram Ticket bot
TG_TICKET_BOT_TOKEN=
# Channel ID of the Telegram Channel for alerts
TG_ALERT_CHANNEL=
# Token of the Telegram AlertBot
TG_ALERT_BOT_TOKEN=
# The selenium connection-string. Should be fine
SELENIUM_HOST=selenium-chrome:4444

# use this var to point to file:// or http:// containing json 
# with ticket sources
TICKET_SOURCE_URLS_URI= 
```

### 3. Run it
Build and start the containers using docker-compose



