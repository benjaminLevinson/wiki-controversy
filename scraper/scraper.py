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
    return soup.find(id="firstHeading")


# Scrape first sentence of bio
def scrape_introduction_text(html_doc):
    def p_no_class(tag):
        return tag.name == 'p' and not tag.has_attr('class')

    soup = BeautifulSoup(html_doc, 'html.parser')
    infobox = soup.find(class_="infobox")
    if infobox:
        par = infobox.find_next_sibling(p_no_class)
    else:
        # No infobox
        print("No infobox found!")
        par = soup.find(id="mw-content-text").find(p_no_class)

    # Find first navigable string containing a period to get first sentence
    # (if a period is in a non-navigable string, it may be part of an abbreviated title like 'Dr.' and not actually the
    # end of the sentence)
    par_tags = []
    for child in par:
        if type(child) is NavigableString and '.' in child:
            remaining_sentence = child.partition('.')[0]
            par_tags.append(remaining_sentence+'.')
            return par_tags
        par_tags.append(child)
    return par_tags


def scrape_html_under_heading(html, heading):
    def get_heading_tag_size(tag):
        return int(tag.name[-1])

    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find(id=heading)
    if not heading:
        return {}
    heading_tag = heading.parent
    tag_size = get_heading_tag_size(heading_tag)

    headings_to_subtags = collections.defaultdict(BeautifulSoup("", 'html.parser'))
    header = heading_tag.text
    headings_to_subtags[header].append(heading_tag)
    for tag in heading_tag.next_siblings:
        if type(tag) is NavigableString and tag == '\n':
            continue
        elif type(tag) is Tag and "thumb" in tag.get("class", "") or "hatnote" in tag.get("class", ""):
            continue
        elif type(tag) is Tag and tag.name[0] == 'h' and get_heading_tag_size(tag) <= tag_size:
            break
        elif type(tag) is Tag and tag.name[0] == 'h' and get_heading_tag_size(tag) > tag_size:
            header = tag.text
        elif type(tag) is Tag and tag.name == 'div':
            tag['style'] = ""
        headings_to_subtags[header].append(tag)

    # Remove empty heading sections
    # (ie subheadings start immediately under main heading, no body text under main section)
    for heading in headings_to_subtags:
        if heading == get_text(headings_to_subtags[heading]):
            del headings_to_subtags[heading]

    return headings_to_subtags


def get_text(ls_tags):
    text_section = list(map(lambda x: x.text, ls_tags))
    return ''.join(text_section).strip()


def process_text(text):
    # Remove references example: [1]
    text_stripped = text.strip()
    text_no_references = re.sub(r'\[.*?\]', "", text_stripped)
    list_no_newlines = text_no_references.split('\n')
    text_no_newlines = '. '.join(list_no_newlines)
    return text_no_newlines


# Drops sentences in a paragraph until paragraph is tweet length
# If returned sentence is empty, first sentence was larger than LENGTH characters
def truncate_to_length(p, length, delimiter='.'):
    if length < 0:
        raise Exception("Negative truncation length")

    if len(p) <= length:
        return p

    sentence = p.split(delimiter)
    while len(delimiter.join(sentence)) > length:
        sentence = sentence[:-1]
    sentence = delimiter.join(sentence)

    return sentence
