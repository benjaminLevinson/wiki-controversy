from scraper import scraper
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import requests
import twitter
import os

PHANTOMJS_PATH = os.environ['PHANTOMJS_PATH']
OUTPUT_DIR = "./output"
CACHE_NAME = OUTPUT_DIR + '/cache.html'
IMAGE_NAME = OUTPUT_DIR + "/controversy_screenshot.png"


def tweet(text, media=""):
    api = twitter.Api(consumer_key=os.getenv("CONTROVERSY_CONSUMER_KEY"),
                      consumer_secret=os.getenv("CONTROVERSY_CONSUMER_SECRET"),
                      access_token_key=os.getenv("CONTROVERSY_ACCESS_TOKEN_KEY"),
                      access_token_secret=os.getenv("CONTROVERSY_ACCESS_TOKEN_SECRET"))
    api.PostUpdate(text, media=media)


def build_image(html):
    tmp_file = OUTPUT_DIR + '/tmp.html'
    with open(tmp_file, 'w') as f:
        f.write(html)

    driver = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
    driver.get(tmp_file)
    driver.save_screenshot(IMAGE_NAME)
    return True


def invalidate_cache(invalidation_age, file_path):
    if not os.path.exists(file_path):
        return True

    age_delta = datetime.now() - timedelta(days=invalidation_age)
    file_age = datetime.fromtimestamp(os.path.getctime(file_path))
    if file_age < age_delta:
        return True
    return False


def get_website(url):
    if invalidate_cache(5, CACHE_NAME):
        print('not cached')
        response = requests.get(url)
        with open(CACHE_NAME, 'wb') as f:
            f.write(response.content)
        return response.text
    else:
        with open(CACHE_NAME, 'rb') as f:
            return f.read().decode("utf-8")


def get_text(ls_tags):
    text_section = list(map(lambda x: x.text, ls_tags))
    return ''.join(text_section).strip()


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    url = "https://en.wikipedia.org/w/index.php?title=Special:Search&limit=5000&offset=0&ns0=1&search=insource%3A%2F%3D" \
          "%3DControversies%3D%3D%2F"

    html = get_website(url)
    page_links = scraper.scrape_search_results(html)
    rand_link = random.choice(page_links)
    page_url = "https://en.wikipedia.org" + rand_link
    print(page_url)

    html = requests.get(page_url)
    article_title = scraper.scrape_article_title(html.text)
    article_title_text = article_title.text
    controversies_html = BeautifulSoup("""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="../css/styles.css">
      </head>
      <body>
      </body>
    </html>
    """, 'html.parser')
    scraped_html_dict = scraper.scrape_html_under_heading(html.text, "Controversies")

    # Remove empty Controversies sections
    # (ie controversy subheadings that start immediately, no body text under main section)
    controversies_heading = "Controversies[edit]"
    if controversies_heading in scraped_html_dict and \
            get_text(scraped_html_dict[controversies_heading]) == "Controversies[edit]":
        del scraped_html_dict[controversies_heading]

    rand_section = random.choice(list(scraped_html_dict.keys()))
    controversies_html.find("body").insert_after(article_title)
    controversies_html.find("h1").extend(scraped_html_dict[rand_section])

    build_image(controversies_html.prettify())

    # Build tweet
    headline_text = article_title_text + ' - ' + scraper.process_text(rand_section)
    controversy_text = scraper.process_text(get_text(scraped_html_dict[rand_section][1:]))
    short_controversy_text = scraper.truncate_to_length('\n\n'+controversy_text, 280-len(headline_text))
    tweet_text = headline_text + short_controversy_text
    tweet(tweet_text, media=IMAGE_NAME)
    print(tweet_text)


if __name__ == "__main__":
    main()
