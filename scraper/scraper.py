from bs4 import BeautifulSoup, NavigableString, Tag
import collections
import re


# Returns a list of search results in a Wikipedia section
def scrape_search_results(search_page):
    soup = BeautifulSoup(search_page, 'html.parser')
    result_heading_divs = soup.findAll(class_="mw-search-result-heading")
    links = map(lambda x: x.find('a').get("href"), result_heading_divs)
    return list(links)


def scrape_article_title(article):
    soup = BeautifulSoup(article, 'html.parser')
    return soup.find(id="firstHeading").text


def scrape_under_heading(html, heading):
    def get_heading_tag_size(tag):
        return int(tag.name[-1])

    soup = BeautifulSoup(html, 'html.parser')
    heading_tag = soup.find(id=heading).parent
    tag_size = get_heading_tag_size(heading_tag)
    paragraphs = collections.defaultdict(list)
    header = "Controversies"
    for tag in heading_tag.next_siblings:
        if type(tag) is NavigableString and tag == '\n':
            continue
        elif type(tag) is Tag and tag.name[0] == 'h' and get_heading_tag_size(tag) <= tag_size:
            break
        elif type(tag) is Tag and tag.name[0] == 'h' and get_heading_tag_size(tag) > tag_size:
            header = process_text(tag.text)
        elif type(tag) is Tag and tag.name == 'p':
            paragraphs[header].append(process_text(tag.text))
    return paragraphs


def process_text(text):
    # Remove references example: [1]
    text_stripped = text.strip()
    text_no_references = re.sub(r'\[.*?\]', "", text_stripped)
    # Remove parentheticals example: (1994-2014)
    text_no_parentheticals = re.sub(r'\s\(.*?\)', "", text_no_references)
    list_no_newlines = text_no_parentheticals.split('\n')
    text_no_newlines = '. '.join(list_no_newlines)
    return text_no_newlines


# Drops sentences in a paragraph until paragraph is tweet length
def truncate_to_length(p, length):
    if length < 0:
        raise Exception("Negative truncation length")

    if len(p) <= length:
        return p

    sentence = p.split('.')
    while len('.'.join(sentence)) > length:
        sentence = sentence[:-1]
    sentence = '.'.join(sentence)

    # First sentence was larger than LENGTH characters
    if len(sentence) == 0:
        raise Exception("Too short")

    return sentence
