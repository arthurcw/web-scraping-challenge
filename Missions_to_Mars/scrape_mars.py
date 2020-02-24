# Setup dependencies
import pandas as pd
from bs4 import BeautifulSoup
import requests
from splinter import Browser
import time

# wiki Mars image if web scrap cannot return intended image url
image_link_404 = 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/OSIRIS_Mars_true_color.jpg/600px-OSIRIS_Mars_true_color.jpg'

def init_browser():
    executable_path = {"executable_path": "chromedriver.exe"}
    return Browser("chrome", **executable_path, headless=False)

def splinter_soup(browser, url):
    """
    Retrieve page with splinter using provided url
    and return beautiful soup object
    """
    browser.visit(url)
    time.sleep(2)
    return BeautifulSoup(browser.html, 'html.parser')

def mars_news(browser):
    """
    Scrap Mars News
    Return dictionary of `news_title`: title and `news_p`: paragraph
    """

    # Mars News website
    url = 'https://mars.nasa.gov/news/'

    try:
        # Retrieve page with splinter, create BeautifulSoup object
        soup = splinter_soup(browser, url)

        # Extract data
        result = soup.body.find("li", class_="slide")
        news_title = result.find("div", class_="content_title").a.text.strip()
        news_p = result.find("div", class_="article_teaser_body").text.strip()

        return {'news_title': news_title, 'news_p': news_p}

    except:
        return {'news_title': 'no result', 'news_p': 'no result'}

def mars_featured_image(browser):
    """
    Scrap JPL Mars featured image
    Returns dictionary of url of featured image
    """

    # url
    base_url = 'https://www.jpl.nasa.gov'
    url = f'{base_url}/spaceimages/?search=&category=Mars'

    try:
        # 1) Extract url to the featured image page
        soup = splinter_soup(browser, url)
        result = soup.body.find('div', class_='carousel_container')\
            .find('a', class_='button fancybox')
        url_desc = f"{base_url}{result['data-link']}"

        # 2) Extract url of featured image
        soup_desc = splinter_soup(browser, url_desc)
        result = soup_desc.body.find("figure", class_="lede")
        return {'featured_image_url': f"{base_url}{result.a['href']}"}

    except:
        # if not found, default to wiki Mars image
        return {'featured_image_url': image_link_404}

def mars_weather():
    """
    Scrap Mars weather off Twitter
    Returns dictionary with latest weather tweet as text
    """

    #url
    url = 'https://twitter.com/marswxreport?lang=en'

    try:
        # Retrieve page with request module
        response = requests.get(url)

        # Create BeautifulSoup object; parse with 'html.parser'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract weather data from latest tweet message
        result = soup.body.find('div', class_='js-tweet-text-container')
        return {'mars_weather':\
            result.p.text.replace('\n',' ').rstrip(result.p.a.text)}
    
    except:
        return {'mars_weather': 'Data not found!'}

def mars_facts():
    """
    Scrap Space Facts website
    Use Pandas to scrap Mars Fact and return html table string
    """
    
    #url
    url = 'https://space-facts.com/mars/'

    try:
        # Mars facts is in the first table
        mars_facts = pd.read_html(url)[0]
        mars_facts.columns = ['description', 'value']
    except:
        mars_facts = pd.DataFrame({'description': ['none'], 'value': ['none']})

    # format table    
    mars_facts.set_index('description', inplace=True)

    # return as html table string
    return {'facts_table': mars_facts.to_html(justify='left', classes='table table-sm table-striped')}

def mars_hemispheres(browser):
    """
    Scrap USGS Astrogeology site
    Retrieve title and image url to each hemisphere
    Return as a list of dictionary 
    """

    # List to store the hemisphere title and image url.
    hemisphere_image_urls = []

    #url
    url = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'

    # Create BeautifulSoup object
    soup = splinter_soup(browser, url)

    try:

        # Data stored in division tag item class
        results = soup.body.find_all('div', class_='item')

        # Loop through each item
        for result in results:
            # title
            title = result.find('div', class_='description').a.text

            # image
            ## click title link to another page to find full image url
            browser.links.find_by_partial_text(title).click()
            soup_img = BeautifulSoup(browser.html, 'html.parser')

            ## full image link in a tag with 'Sample' text under div tag with 'download' class
            image_url = soup_img.body\
                .find('div', class_='downloads')\
                .find('a', text='Sample')['href']

            # append title and image url to list
            hemisphere_image_urls.append({
                'title': title,
                'image_url': image_url
            })

            # back to previous page for next result
            time.sleep(2)
            browser.back()

        # return list
        return {'hemisphere_image_urls': hemisphere_image_urls}

    except:
        return {'hemisphere_image_urls': [
            {'title': 'Not Found', 'image_url': image_link_404}
        ] * 4
        }

def scrape():
    """
    Main function called by Flask in `/scrape` route
    Return a dictionary of data pulled from multiple websites
    """
    mars_data = {}

    # Initialize browser for splinter
    browser = init_browser()

    # Scrap Mars news
    mars_data.update(mars_news(browser))

    # Get feautured image url on JPL Mars Space Image
    mars_data.update(mars_featured_image(browser))

    # Scrap latest Mars weather
    mars_data.update(mars_weather())

    # Scrap Mars facts and export to a html table string
    mars_data.update(mars_facts())

    # Scrap Mars hemisphere image url and title
    mars_data.update(mars_hemispheres(browser))

    # Close browser
    browser.quit()

    # Return all data as dictionary
    return mars_data