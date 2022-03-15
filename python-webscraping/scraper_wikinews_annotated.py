# Module for making requests
import requests

# Module for parsing HTML
from bs4 import BeautifulSoup

# Module for sleep timers
from time import sleep

# Helper module for pretty printing output
from pprint import pprint


website = "https://en.wikinews.org"


# making a GET request
r = requests.get(website)

# Check if it was successful
pprint(r.status_code)


# Now we pass the content of the response into BeautifulSoup
# The first argument is the HTML we want to parse
# The second argument is the parsing engine 'lxml'
soup = BeautifulSoup(r.content, 'lxml')

# Select the element with the id "MainPage_latest_news_text"
# We use the "find()" method: it finds the first tag meeting the criteria we specify
# Remeber that ids are unique, therefore, the first hit is always the correct one
latest_news = soup.find(id="MainPage_latest_news_text")

# Now we want to get all links inside the element
# Remember that links are inside <a> tags
# We use the "find_all()" method, it returns all elements that meet our specified criteria
# This means we get a list of <a> tags

a_tags = latest_news.find_all('a')

# to look at the first element we can simply access it like this

pprint(a_tags[0])

# Now we want to extract the URL to the full article
# and also the headline of the article
# Beautiful Soup allows us to access HTML attributes like a python dictionary
# Links are inside the "href" attribute

pprint(a_tags[0]['href'])

# In this particular example, the "href" contains a *relative* link
# As you can see, the URL starts with "/wiki/"
# In order to get the complete URL, we have to add the main website:

pprint(website + a_tags[0]['href'])
# It is a good idea to manually test, if the link really works

# The headline is the bare text, we can access it with the 'get_text()' method

pprint(a_tags[0].get_text()) 

# Now we want to do that for all <a> and store them inside a list
# So we create an empty list first, where each element is a news article

articles = []

# There are different ways of approaching this. 
# I prefer using dictionaries to represent news articles
# So an article would look like this:

article = {'url': 'https://en.wikinews.org/wiki/Court_finds_UK_allowed_undervalued_Chinese_imports_into_EU?',
           'headline': 'Court finds UK allowed undervalued Chinese imports into EU',
           'publication_date': "2022-03-11",
           'text': 'blablablabla'}


# Now we iterate through a_tags and each time we extract the url and the title
# And then we append the article dictionary to the articles list

for a in a_tags:
    url = a['href']
    headline = a.get_text()
    article = {'url': website + url,
               'headline': headline}
    articles.append(article)

# Let's check the output:

pprint(articles)

# Next we want to get the full text and publication date for each article
# Therefore, we have to request each link and parse the output again
# Unlike the first time, we have to iterate over a list and make a request each time
# We do with a single article first, to see how it works:

article = articles[0]


# Make a GET request:

r = requests.get(article['url'])

# Check the status code
pprint(r.status_code)

# pass the content into Beautiful Soup

soup = BeautifulSoup(r.content, 'lxml')

# First, we try to get the publish date at the top of the article
# It is inside the <strong> with the class "published"
# Note that we need an underscore here, because "class" is a reserved keyword in Python

published_date = soup.find(class_="published")

# We can now get the text using the 'get_text()' method:

published_date_string = published_date.get_text()

# However, this is not a very nice format, because it is not machine-readable
# We can improve this by using the python dateutil, which is a non-standard module

from dateutil import parser as dateparser

parsed_date = dateparser.parse(published_date_string)
# this way, we get a nice python datetime object
# However, this kind of parsing is not very robust and prone to error
# It is recommended to only use it if there is no other way of retrieving the date

# Another way is to look closer at the HTML attributes
# The <span> tag inside the <strong> tag has a "title" attribute, which contains the date as machine readable string
# We can access children tags as a property and then get the attribute like a dictionary

published_date_title = published_date.span['title']

# Next we get the text of the article
# First, we identify the parent element of the article text
# All text content is inside the <div> with the class "mw-parser-output"

content = soup.find(class_="mw-parser-output") 

# We want to get the text of every <p> tag inside the content box
# So first we select all <p> tags

p_tags = content.find_all('p')

# Then we iterate over all of them

for p in p_tags:
    pprint(p.get_text())

# Almost perfect, but we do not want to get the last <p>
# And also not the first one (we have the date already)
# It is always the same text in every article
# We can simply skip it like this:

for p in p_tags[1:-2]:
    pprint(p.get_text())

# Now we just have to turn the single strings into a long one

text = []

for p in p_tags[1:-2]:
    text.append(p.get_text())

# And then join it:

text = "\n\n".join(text)

# For the experts: here is the one liner solution

text = "\n\n".join([p.get_text() for p in p_tags[1:-2]])

# Now we add our parsed results to the article dictionary

article['published_date'] = published_date_title
article['text'] = text


# Now we do in a large loop, for every article
# The code is almost the same, 
# but we will add some more extras


for article in articles:
    r = requests.get(article['url'])
    # we also want to keep track on the status code of each request
    article['status_code'] = r.status_code
    # if the request was unsuccessful, we skip it and continue
    if r.status_code != 200:
        continue
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

    # but we have to add a short sleep timer at the end
    # to prevent overloading the server
    # 0.2 seconds is enough
    sleep(0.2)


# Finally, we are going to store the output in a separate file
# There are many ways to achieve this, and here we look at two of them
# First we use the JSON module to export the list of dictionaries

import json

# We define a file name that also has a timestamp in it
# So we prevent overwriting previous scraper output

from datetime import datetime

output_file_name = "wikinews_scraper_output_" + datetime.now().strftime('%Y%m%d_%H.%M.%S')

# Side note: the expression "%Y%m%d_%H.%M.%S" tells how to format the current date time.
# You can look up the syntax here: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

# To store to a JSON file, we use a context manager
# the open() function takes two arguments: filename and mode
# we pass 'w' as mode for 'write'

with open(output_file_name + '.json', 'w') as f:
    json.dump(articles, f)


# Another method is to use pandas

import pandas as pd

df = pd.DataFrame(articles)

# Now we can save the output in any format that pandas supports
# I strongly advice against using csv files, as these are not suitable for text data
# Instead we are using the feather format, 
# which is designed to exchange data between python, R and other programming languages 

df.to_feather(output_file_name + '.feather')