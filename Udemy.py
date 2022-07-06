# importing required libraries
import scrapy
from scrapy.crawler import CrawlerProcess as Cp
from urllib.parse import urlencode
import json
import time


# Defining spider class
class Udemy_Scraper(scrapy.Spider):
    # scraper name
    name = 'udemy_scraper'

    # spider settings
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'COOKIES_DISABLED': True,
        'DEFAULT_REQUEST_HEADERS': {
            "Host": "www.udemy.com",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,ta;q=0.8,hi;q=0.7",
            "Connection": "keep-alive",
            "user-agent": "PostmanRuntime/7.28.4",
        }
    }

    # base URL
    course_url = 'https://www.udemy.com/api-2.0/discovery-units/all_courses/?'

    # string query parameters
    params = {
        'p': 1,
        'page_size': 50,
        'category_id': 288,                 # To change course category change category_id
        'source_page': 'category_page',
        'currency': 'inr',
        'skip_price': 'false',
        'sos': 'pc',
        'fl': 'cat'
    }

    # crawler's entry point
    def start_requests(self):
        yield scrapy.Request(
            url=self.course_url + urlencode(self.params),
            callback=self.parse_courses
        )

    # courses API call response callback function
    def parse_courses(self, response, **kwargs):
        # parse JSON response
        courses = json.loads(response.text)['unit']

        # extract courses' ids
        ids = [str(course['id']) for course in courses['items']]

        # generate price API URL
        price_url = 'https://www.udemy.com/api-2.0/pricing/?'

        # price API string query parameters
        price_params = {
            'course_ids': ','.join(ids),
            'fields[pricing_result]': 'price',
            'currency': 'inr'
        }

        yield scrapy.Request(
            url=price_url + urlencode(price_params),
            callback=self.parse,
            meta={
                'courses': courses
            }
        )

    def parse(self, response, **kwargs):
        # get courses from meta container
        courses = response.meta['courses']
        # parse courses
        course_prices = json.loads(response.text)['courses']

        for course in courses['items']:
            yield {
                'id': course['id'],
                'title': course['title'],
                'url': "https://www.udemy.com" + course['url'],
                'instructor': ' and '.join([ins['display_name'] for ins in course['visible_instructors']]),
                'image_url': course['image_125_H'],
                'price': f"{round(course_prices[str(course['id'])]['price']['amount'])} INR",
                'rating': round(course['rating'], 1)
            }

        if 'next' in courses['pagination']:
            next_req = 'https://www.udemy.com' + courses['pagination']['next']['url']
            yield scrapy.Request(
                url=next_req,
                callback=self.parse_courses
            )


# naming output file with time as suffix
name = f'udemy_{str(round(time.time()))}.csv'

# starting spider by process
process = Cp(settings={
    "FEED_URI": name,
    "FEED_FORMAT": "csv",
})
process.crawl(Udemy_Scraper)
process.start()
process.stop()
