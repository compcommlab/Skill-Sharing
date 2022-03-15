# Module for making requests
import requests

# Module for parsing HTML
from bs4 import BeautifulSoup

# Module for sleep timers
from time import sleep

import json
import pandas as pd
from datetime import datetime

website = "https://en.wikinews.org"

print(f'Requesting: {website} ...')

# making a GET request
r = requests.get(website)

if r.status_code != 200:
    # Adding a failsafe
    print(f'Request unsucessful! Status code: {r.status_code}')
    import sys
    sys.exit(1)

print('Success!', f'Parsing content ...')
soup = BeautifulSoup(r.content, 'lxml')

latest_news = soup.find(id="MainPage_latest_news_text")
a_tags = latest_news.find_all('a')

articles = []

# Now we iterate through a_tags and each time we extract the url and the title
# And then we append the article dictionary to the articles list

for a in a_tags:
    url = a['href']
    headline = a.get_text()
    article = {'url': website + url,
               'headline': headline}
    articles.append(article)

print(f'got {len(articles)} articles to scrape...')

for article in articles:
    print(f"Requesting: {article['url']} ...")
    r = requests.get(article['url'])

    # we also want to keep track on the status code of each request
    article['status_code'] = r.status_code
    # if the request was unsuccessful, we skip it and continue

    if r.status_code != 200:
        print(f'Request unsucessful! Status code: {r.status_code}')
        continue

    print('Success!', f'Parsing content ...')

    soup = BeautifulSoup(r.content, 'lxml')
    
    published_date = soup.find(class_="published")
    published_date_title = published_date.span['title']
    
    content = soup.find(class_="mw-parser-output") 
    p_tags = content.find_all('p')
    text = []
    
    for p in p_tags[1:-2]:
        text.append(p.get_text())
    
    text = "\n\n".join(text)
    
    article['published_date'] = published_date_title
    article['text'] = text

    print('\n')

    sleep(0.2)


output_file_name = "wikinews_scraper_output_" + datetime.now().strftime('%Y%m%d_%H.%M.%S')

print(f'saving output to {output_file_name}')

with open(output_file_name + '.json', 'w') as f:
    json.dump(articles, f)

df = pd.DataFrame(articles)
df.to_feather(output_file_name + '.feather')