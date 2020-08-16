from scraper import scraper
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import requests
import twitter
import os
import shutil

PHANTOMJS_PATH = os.environ['PHANTOMJS_PATH']
OUTPUT_DIR = os.path.join(".", "output")
CACHE_NAME = os.path.join(OUTPUT_DIR, 'cache.html')
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')
MAX_TWEET_LENGTH = 280
MAX_TWEET_IMAGES = 4
MAX_SCREENSHOT_HEIGHT = 450
MAX_CACHE_AGE_DAYS = 5
HEADING = "Controversies"
WIKIPEDIA_URL = "https://en.wikipedia.org"
SEARCH_URL = "https://en.wikipedia.org/w/index.php?title=Special:Search&limit=5000&offset=0&ns0=1&sort=random&search" \
             "=insource%3A%3D%3DControversies%3D%3D+insource%3A%2F%3D%3DControversies%3D%3D%2F&advancedSearch-current" \
             "={}"
HTML_TEMPLATE = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="../css/styles.css">
      </head>
      <body>
      </body>
    </html>
"""


def screenshot_article(header_tags, body_tags):
    def build_and_visit_page(tags):
        html = BeautifulSoup(HTML_TEMPLATE, 'html.parser')
        html.find("body").extend(tags)
        tmp_file = os.path.join(OUTPUT_DIR, 'tmp.html')
        with open(tmp_file, 'w') as f:
            f.write(html.prettify())
        driver = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
        driver.get(tmp_file)
        return driver

    def get_window_height(driver):
        return driver.execute_script("return document.body.scrollHeight")

    # Add as many tags as will fit before reaching max_image_height
    def fit_tags_to_screenshot(tags, image_name, max_image_height):
        image_height = 0
        tags_index = 0
        driver = None
        while image_height <= max_image_height and tags_index <= len(tags):
            tags_index += 1
            old_driver = driver
            driver = build_and_visit_page(tags[0:tags_index])
            image_height = get_window_height(driver)
            # Revert to last state if paragraph pushes image height over max
            if image_height >= max_image_height and old_driver is not None:
                driver = old_driver
                tags_index -= 1
                break
        driver.save_screenshot(image_name)
        driver.quit()
        return tags[tags_index:]

    images = []
    driver = build_and_visit_page(header_tags + body_tags[0:2])
    first_image_path = os.path.join(IMAGES_DIR, 'tmp0.png')
    driver.save_screenshot(first_image_path)
    images.append(first_image_path)

    img_num = 1
    remaining_tags = body_tags[2:]
    while remaining_tags:
        image_path = os.path.join(IMAGES_DIR, 'tmp{}.png'.format(img_num))
        remaining_tags = fit_tags_to_screenshot(remaining_tags, image_path, MAX_SCREENSHOT_HEIGHT)
        images.append(image_path)
        img_num += 1
    return images


def get_website_or_cache(url):
    def invalidate_cache(invalidation_age, file_path):
        if not os.path.exists(file_path):
            return True

        age_delta = datetime.now() - timedelta(days=invalidation_age)
        file_age = datetime.fromtimestamp(os.path.getctime(file_path))
        if file_age < age_delta:
            return True
        return False

    if invalidate_cache(MAX_CACHE_AGE_DAYS, CACHE_NAME):
        print('not cached')
        response = requests.get(url)
        with open(CACHE_NAME, 'wb') as f:
            f.write(response.content)
        return response.text
    else:
        with open(CACHE_NAME, 'rb') as f:
            return f.read().decode("utf-8")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    if os.path.exists(IMAGES_DIR):
        shutil.rmtree(IMAGES_DIR)
    os.mkdir(IMAGES_DIR)

    html = get_website_or_cache(SEARCH_URL)
    page_links = scraper.scrape_search_results(html)
    rand_link = random.choice(page_links)
    page_url = WIKIPEDIA_URL + rand_link
    print(page_url)

    html = requests.get(page_url)
    scraped_html_dict = scraper.scrape_html_under_heading(html.text, HEADING)
    rand_section = random.choice(list(scraped_html_dict.keys()))
    rand_section_tags = scraped_html_dict[rand_section]
    print(rand_section)

    article_title_tag = scraper.scrape_article_title(html.text)
    intro_tags = scraper.scrape_introduction_text(html.text)

    images = screenshot_article([article_title_tag]+intro_tags, rand_section_tags)

    # Can't have more than 4 images in a tweet
    if len(images) > MAX_TWEET_IMAGES:
        print("Controversies section was too long")
        exit(1)

    # Build tweet
    article_title_text = article_title_tag.text
    headline_text = article_title_text + ' - ' + scraper.process_text(rand_section)
    controversy_text = scraper.process_text(scraper.get_text(rand_section_tags[1:]))
    short_controversy_text = scraper.truncate_to_length('\n\n'+controversy_text, MAX_TWEET_LENGTH-len(headline_text))
    tweet_text = headline_text + short_controversy_text
    print(tweet_text)

    api = twitter.Api(consumer_key=os.getenv("CONTROVERSY_CONSUMER_KEY"),
                      consumer_secret=os.getenv("CONTROVERSY_CONSUMER_SECRET"),
                      access_token_key=os.getenv("CONTROVERSY_ACCESS_TOKEN_KEY"),
                      access_token_secret=os.getenv("CONTROVERSY_ACCESS_TOKEN_SECRET"))
    status = api.PostUpdate(tweet_text, media=images)
    api.PostUpdate(page_url, in_reply_to_status_id=status.id)


if __name__ == "__main__":
    main()
