# Wikipedia Controversies Twitter Bot
This Twitter bot tweets picks random Wikipedia pages and tweets
screenshots of their controversy sections. The bot works by
scraping the HTML from the controversy section, opening a page
with the scraped tags locally using Selenium, and taking
screenshots of that page. 

The bot can be found at https://twitter.com/WikiControversy.

## Installation
Run:
```
make init
source venv/bin/activate
make install
```

Add a file to the root directory called keys.env with the following
contents to export the Twitter keys corresponding to your app:
```
export CONTROVERSY_CONSUMER_KEY=[key here]
export CONTROVERSY_CONSUMER_SECRET=[key here]
export CONTROVERSY_ACCESS_TOKEN_KEY=[key here]
export CONTROVERSY_ACCESS_TOKEN_SECRET=[key here]
```
Now, if you run `tweet.sh` your bot should send out its first
Tweet! To truly automate your bot, setup a cron job to execute
`tweet.sh` on a regular schedule.
