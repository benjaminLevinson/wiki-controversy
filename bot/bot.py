from scraper import scraper
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import requests
import twitter
import os


def tweet(text):
    api = twitter.Api(consumer_key=os.getenv("CONTROVERSY_CONSUMER_KEY"),
                      consumer_secret=os.getenv("CONTROVERSY_CONSUMER_SECRET"),
                      access_token_key=os.getenv("CONTROVERSY_ACCESS_TOKEN_KEY"),
                      access_token_secret=os.getenv("CONTROVERSY_ACCESS_TOKEN_SECRET"))
    api.PostUpdate(text)


def invalidate_cache(invalidation_age, file_path):
    if not os.path.exists(file_path):
        return True

    age_delta = datetime.now() - timedelta(days=invalidation_age)
    file_age = datetime.fromtimestamp(os.path.getctime(file_path))
    if file_age < age_delta:
        return True
    return False


def get_website(url):
    file_name = 'cache.html'
    if invalidate_cache(5, file_name):
        print('not cached')
        response = requests.get(url)
        with open('cache.html', 'wb') as f:
            f.write(response.content)
        return response.text
    else:
        with open('cache.html', 'rb') as f:
            return f.read().decode("utf-8")


def main():
    url = "https://en.wikipedia.org/w/index.php?title=Special:Search&limit=5000&offset=0&ns0=1&search=insource%3A%2F%3D" \
          "%3DControversies%3D%3D%2F"

    html = get_website(url)
    page_links = scraper.scrape_search_results(html)
    rand_link = random.choice(page_links)
    print(rand_link)
    page_url = "https://en.wikipedia.org" + rand_link
    # page_url = "https://en.wikipedia.org/wiki/Baxter_International"
    print(page_url)

    html = requests.get(page_url)
    article_title = scraper.scrape_article_title(html.text)
    controversies_dict = scraper.scrape_under_heading(html.text, "Controversies")
    random_key = random.choice(list(controversies_dict.keys()))
    print(article_title)
    print(random_key)
    print(controversies_dict)
    random_par = random.choice(controversies_dict[random_key])
    shortened_controversy = scraper.truncate_to_length(random_par, 280-len(article_title + '\n\n'))
    tweet_text = article_title + '\n\n' + shortened_controversy
    print(tweet_text)
    tweet(tweet_text)


if __name__ == "__main__":
    main()
