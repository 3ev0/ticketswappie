import time
import os
import os.path
import logging
import pprint
import signal
import json
import argparse

import requests
import telegram
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
import selenium.webdriver.chrome.options

import telegram_alert

config ={}
tickets_seen = []


def signal_handler(signum, frame):
    raise OSError(f"Signal received: {signum}")


signal.signal(signal.SIGTERM, signal_handler)


def build_config() -> dict:
    """
    Check the environment variables and copy into a dict
    :return:
    """
    config["RUN_INTERVAL"] = float(os.environ.get("RUN_INTERVAL", 30))
    config["MSG_INTERVAL"] = float(os.environ.get("MSG_INTERVAL", 0.5))
    config["TG_TICKET_CHANNEL"] = os.environ["TG_TICKET_CHANNEL"]
    config["TG_TICKET_BOT_TOKEN"] = os.environ["TG_TICKET_BOT_TOKEN"]
    config["TG_ALERT_CHANNEL"] = os.environ["TG_ALERT_CHANNEL"]
    config["TG_ALERT_BOT_TOKEN"] = os.environ["TG_ALERT_BOT_TOKEN"]
    config["TICKET_SOURCE_URLS_URI"] = os.environ["TICKET_SOURCE_URLS_URI"]
    config["SELENIUM_HOST"] = os.environ["SELENIUM_HOST"]
    return config


def load_ticket_sources(url: str) -> dict:
    logging.info(f"Loading ticket sources from {url}")
    if url.lower().startswith("http://") or url.lower().startswith("https://"):
        resp = requests.get(url)
        resp.raise_for_status()
        ticket_sources = resp.json()
    elif url.lower().startswith("file://"):
        with open(url[7:], "r") as fh:
            ticket_sources = json.load(fh)
    else:
        raise ValueError(f"{url} is not a valid url for reading ticket sources.")
    logging.info(f"Ticket_sources successfully loaded from {url}: {len(ticket_sources)} sources.")
    return ticket_sources


def get_chrome_driver() -> WebDriver:
    """
    Get the remote chrome_driver
    Build Chrome options. This configuration is required for chromedriver to function properly in a docker container.
    :return:
    """
    chrome_options = webdriver.chrome.options.Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    for i in range(10):
        try:
            logging.info(f"Connecting to selenium Chrome instance @{config['SELENIUM_HOST']}...")
            driver = webdriver.Remote(f"http://{config['SELENIUM_HOST']}/wd/hub", options=chrome_options)
        except Exception as err:
            logging.error(f"Error connecting to Selenium driver: {err}")
            logging.error("Retrying in 3 seconds..")
            time.sleep(3)
            continue
        break
    logging.info("Connection established.")
    return driver


class Swappie:

    def __init__(self, tg_token: str) -> None:
        self.driver = get_chrome_driver()
        self.bot = telegram.Bot(tg_token)
        self.tg_token = tg_token
        logging.info(f"Swappie initialized: {self}")

    def __repr__(self):
        return f"Swappie(driver={repr(self.driver)}, token=<secret>"

    def get_ticketswap_available_tickets(self, ticket_source: dict) -> list:
        url = ticket_source["url"]
        ticket_name = ticket_source["ticket"]
        logging.info(f"Analysing web page @ {url}...")
        self.driver.get(url)
        time.sleep(2)
        xpath = '//ul[@data-testid="available-tickets-list"]/li/a/div/div/div/div/h4'
        ticket_titles = self.driver.find_elements(By.XPATH, xpath)
        xpath = '//ul[@data-testid="available-tickets-list"]/li/a/div/div/div/div/span'
        ticket_types = self.driver.find_elements(By.XPATH, xpath)
        xpath = '//ul[@data-testid="available-tickets-list"]/li/a/div/div/div/footer/strong'
        ticket_prices = self.driver.find_elements(By.XPATH, xpath)
        xpath = '//ul[@data-testid="available-tickets-list"]/li/a'
        ticket_links = self.driver.find_elements(By.XPATH, xpath)
        available_tickets = []
        for i in range(len(ticket_titles)):
            valuta, pricestr = ticket_prices[i].text.split()[:2]
            num_tickets = ticket_titles[i].text.split()[0]
            available_tickets.append({"service": "Ticketswap",
                                      "ticket": ticket_name,
                                      "number": num_tickets,
                                      "type": ticket_types[i].text,
                                      "link": ticket_links[i].get_attribute("href"),
                                      "valuta": valuta,
                                      "price": float(pricestr.strip(".").replace(",","."))})
        logging.info(f"{len(available_tickets)} tickets found.")
        return available_tickets

    def notify(self, tickets, chat_id):
        self.bot.sendMessage(chat_id, "Nieuwe tickets te koop!")
        for t in tickets:
            ttext = f"<a href='{t['link']}'>{t['service']} - {t['ticket']} - {t['number']} tickets : {t['valuta']} {t['price']} / ticket</a>"
            self.bot.sendMessage(chat_id, ttext, parse_mode="HTML")
            logging.info("Message sent: %s...", ttext[:20])
            time.sleep(config["MSG_INTERVAL"])
        return True


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="TicketsWappie. Want tickets.")
    argparser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    args = argparser.parse_args()

    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=loglevel)
    build_config()
    logging.info("Program started with config:")
    logging.info(pprint.pformat(config))
    alert_bot = telegram_alert.TelegramAlertBot(config["TG_ALERT_BOT_TOKEN"],
                                                config["TG_ALERT_CHANNEL"], "TicketsWappie")
    alert_bot.info("Program started.")
    swappie = Swappie(config["TG_TICKET_BOT_TOKEN"])
    tickets_seen = []
    try:
        while True:
            tickets = []
            logging.info("Routine start.")
            ticket_sources = load_ticket_sources(config["TICKET_SOURCE_URLS_URI"])
            for ticket_source in [ts for ts in ticket_sources if ts["service"] == "ticketswap"]:
                tickets += swappie.get_ticketswap_available_tickets(ticket_source)
            new_tickets = [t for t in tickets if t not in tickets_seen]
            if new_tickets:
                swappie.notify(new_tickets, config["TG_TICKET_CHANNEL"])
            else:
                logging.info("No new tickets discovered.")
            tickets_seen += new_tickets
            time.sleep(config["RUN_INTERVAL"])
    except Exception as err:
        alert_bot.error(f"A fatal exception occurred: {str(err)}")
        logging.error(f"A fatal exception occurred: {str(err)}")
        swappie.driver.close()
        swappie.driver.quit()
        raise
    finally:
        alert_bot.info("Program ended.")