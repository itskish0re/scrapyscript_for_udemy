import scrapy
from scrapy.crawler import CrawlerProcess as Cp
from urllib.parse import urlencode
import json
import sys

CATEGORY = {
    'category_Development': 288,
    'category_Business': 268,
    'category_Finance_Accounting': 328,
    'category_IT_Software': 294,
    'category_Office_Productivity': 292,
    'category_Personal_Development': 296,
    'category_Design': 269,
    'category_Marketing': 290,
    'category_Lifestyle': 274,
    'category_Photography_Video': 273,
    'category_Health_Fitness': 276,
    'category_Music': 278,
    'category_Teaching_Academics': 300
}

# limit of for no. of pages to scrape. set 0 for scraping all pages.
LIMIT = 2


class Udemy_Scraper(scrapy.Spider):
    # scraper name
    name = 'udemy_scraper'

    # limit
    limit = LIMIT

    # spider settings
    custom_settings = {
        # 'DOWNLOAD_DELAY': 1,
        'COOKIES_DISABLED': True,
        # 'LOG_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            "Host": "www.udemy.com",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,ta;q=0.8,hi;q=0.7",
            "Connection": "keep-alive",
            "user-agent": "PostmanRuntime/7.28.4",
            "x-udemy-cache-price-country": "IN"
        }
    }

    # URLS
    SITEURL = "https://www.udemy.com"
    BASEURL = "https://www.udemy.com/api-2.0/discovery-units/all_courses/?"
    PRICEURL = 'https://www.udemy.com/api-2.0/pricing/?'

    # string query parameters
    params_for_categories = {
        'category_id': CATEGORY[sys.argv[1]],
        'closed_captions': '',
        'currency': 'inr',
        'duration': '',
        'fl': 'cat',
        'instructional_level': '',
        'lang': '',
        'locale': 'en_US',
        'navigation_locale': 'en_US',
        'page_size': 50,
        'price': '',
        'skip_price': 'true',
        'sos': 'pc',
        'source_page': 'category_page',
        'subcategory': '',
        'subs_filter_type': '',
        'p': 1
    }

    # crawler's entry point
    def start_requests(self):
        yield scrapy.Request(
            url=self.BASEURL + urlencode(self.params_for_categories),
            headers={"reffer": "https://www.udemy.com"},
            callback=self.parse_courses
        )

    # courses API call response callback function
    def parse_courses(self, response, **kwargs):
        # parse JSON response
        courses = json.loads(response.text)['unit']

        # extract courses' ids
        ids = [str(course['id']) for course in courses['items']]

        # price API string query parameters
        price_params = {
            'course_ids': ','.join(ids),
            'fields[pricing_result]': 'price,list_price',
            'currency': 'inr'
        }

        yield scrapy.Request(
            url=self.PRICEURL + urlencode(price_params),
            callback=self.parse,
            meta={'courses': courses},
            headers={"reffer": "https://www.udemy.com"}
        )

    def parse(self, response, **kwargs):
        # get courses from meta container
        courses = response.meta['courses']
        # parse courses
        course_prices = json.loads(response.text)

        for course in courses['items']:
            yield {
                'course_title': course['title'].strip(),
                'course_id': course['id'],
                'course_avg_ratings': round(course['avg_rating'], 2),
                'num_course_subscribers': course['num_subscribers'],
                'num_course_reviews': course['num_reviews'],
                'course_length': course['content_info_short'],
                'course_language': course['locale']['simple_english_title'],
                'course_type': "Paid" if course['is_paid'] else "Free",
                'course_instructor': " and ".join([ins['display_name'] for ins in course['visible_instructors']]),
                'course_instructor_id': ", ".join([str(ins['id']) for ins in course['visible_instructors']]),
                'num_course_instructor': len(course['visible_instructors']),
                'num_course_lectures': course['num_published_lectures'],
                'course_publsihed_date': course['published_time'].split("T")[0],
                'course_updated_date': course['last_update_date'],
                'course_list_price_inr': course_prices['courses'][str(course['id'])]['list_price']['amount'],
                'course_current_price_inr': course_prices['courses'][str(course['id'])]['price']['amount'],
                'course_instructional_level': course['instructional_level'],
                'course_category': course['context_info']['category']['title'],
                'course_label': "N/A" if course['context_info']['label'] is None else course['context_info']['label'][
                    'title'],
                'is_course_bestseller': "No" if course['bestseller_badge_content'] is None else "Yes",
                'course_headline': course['headline'],
                'course_url': self.SITEURL + course['url'],
                'course_image_url': course['image_750x422']
            }

        if self.limit == 0:
            self.limit = courses['pagination']['total_page']

        if self.limit > courses['pagination']['current_page'] and 'next' in courses['pagination']:
            next_req = 'https://www.udemy.com' + courses['pagination']['next']['url']
            yield scrapy.Request(
                url=next_req,
                callback=self.parse_courses
            )


# naming output file with time as suffix
name = f"{sys.argv[1]}.csv"

# starting spider by process
process = Cp(settings={
    "FEED_URI": name,
    "FEED_FORMAT": "csv",
})

process.crawl(Udemy_Scraper)
process.start()
process.stop()
