from scrapy.http import Request, FormRequest
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule

from scrapy.contrib.spiders import CrawlSpider
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

from scrapy.contrib.linkextractors import LinkExtractor

from mit.items import MitItem

import sys
sys.path.append("../name_parser")
sys.path.append("../usaddress")

import usaddress
from nameparser import HumanName

from dateutil.parser import parse

import logging

class MitSpider(CrawlSpider):
    name = 'mit'
    login_url = "https://alum.mit.edu/user/directory/home.dyn"
    start_urls = ["https://alum.mit.edu/user/directory/home.dyn"]
    input_file = "input.txt"

    logger = logging.getLogger("mit")

    def start_requests(self): 
        # This method is called first, by default.
        return [Request(url=self.login_url,
                       callback=self.login,
                       dont_filter=True)]

    def login(self, response):
        # Generate a login request.
        return FormRequest.from_response(response, formname='mainform',
                    formdata={'username': 'bfinkel', 'password': 'Greta99'},
                    callback=self.check_login_response)

    def check_login_response(self, response):
        # Check the response returned by a login request to see if we are successfully logged in.
        if "Logout" in response.body and "Start your search by using the search box" in response.body:
            # Go to search page
            return self.search(response)

        else:
            logger.error("Login was unsuccessful. Did not reach search page.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def get_input_data(self, input_file):
        data_form = {}
        data = ["name", "city", "state", "zipcode", "company", "title"] # just for clarity, the actual data fields
        fields = ["Name", "Location", "Location", "Location", "Company", "Job Title"] # category of data fields
        f = open(input_file,"r");
        lines = f.readlines()
        for field in fields:
            line = "".join(lines.pop(0).split(":")[1:]).strip()
            if line is not "":
                data_form[field] = line
        return data_form


    def search(self, response):
        # Fill in form (search field) with default term "data scientist" and search.

        data_form = None
        if 'data_form' in response.meta.keys():
            data_form = response.meta['data_form']
        else:
            data_form = self.get_input_data(self.input_file)

        if not data_form:
            return
        elif len(data_form) == 1:
            key, value = data_form.popitem()
            return FormRequest.from_response(response,
                        formdata={"newNtk": key,
                                  "newNtt": value},
                        callback=self.parse_results)
        else:
            key, value = data_form.popitem()
            form_request = FormRequest.from_response(response,
                    formdata={"newNtk": key,
                              "newNtt": value},
                    callback=self.search)
            form_request.meta['data_form'] = data_form
            return form_request

    def parse_results(self, response):
        count = 1
        for result in response.xpath('//div[@class="result"]'):
            if count <= 20:
                item = MitItem()
                # Step in one page (click on result name) and parse result page
                links = result.xpath('h4/a/@href').extract()
                if links:
                    result_page = "https://alum.mit.edu" + links[0]
                    request = Request(url=result_page,
                                  callback=self.parse_result_page)
                    request.meta['item'] = item
                    yield request
                # Yield completed item
                else:
                    yield item
                count += 1

        # Recursively crawl the "next page" - currenty commented out to minimize records accessed       
        # links = response.xpath('//div[@class="clearfix"]/div/ul/li[@id="next-page"]/a/@href').extract()
        # if links:
        #     next_page = "https://alum.mit.edu" + links[0]
        #     yield Request(url=next_page,
        #                   callback=self.parse_results)

    def parse_result_page(self, response):
        item = response.meta['item']
        # Get name fields
        unparsed_name = response.xpath('normalize-space(//div[@id="content"]/h2/text())').extract()[0]
        name = HumanName(unparsed_name)
        item['PREFIX'] = name.title
        item['FIRST_NAME'] = name.first
        item['LAST_NAME'] = name.last
        item['SUFFIX'] = name.suffix
        # Get home address field using usaddress module
        home_selector = response.xpath('//ul/li[@class="homeAddress"]')
        if home_selector.extract():
            unparsed_home_address = " ".join(response.xpath('//ul/li[@class="homeAddress"]/strong/following-sibling::text()').extract()).split()
            try: # Use usaddress module
                home_address = usaddress.tag(" ".join(unparsed_home_address))[0] # an ordered dict
                # Get home city, state, zip fields and remove from ordered dict
                if 'PlaceName' in home_address.keys():
                    item['HOME_CITY'] = home_address.pop('PlaceName')
                if 'StateName' in home_address.keys():
                    item['HOME_STATE'] = home_address.pop('StateName')
                if 'ZipCode' in home_address.keys():
                    item['HOME_ZIPCODE'] = home_address.pop('ZipCode')
                # Get street name field
                item['HOME_STREET'] = " ".join(home_address.values())

            except usaddress.RepeatedLabelError:
                logger.warning("The address: " + home_address + " may have been parsed incorectly." +
                                    "\n Check entry for " + name.first + " " + name.last + ".")
                pass

        # Get last updated home date
        for line in home_selector.xpath('../li'):
            if "Last Update:" in " ".join(line.xpath('strong/text()').extract()):
                home_date = " ".join(line.xpath('normalize-space(strong/following-sibling::text())').extract())
                parsed_home_date = parse(home_date)
                item['HOME_LAST_UPDATED'] =   parsed_home_date.strftime('%m/%d/%Y') 


        work_selector = response.xpath('//ul/li[@class="workAddress"]')
        if work_selector.extract():
            unparsed_work_address = " ".join(response.xpath('//ul/li[@class="workAddress"]/strong/following-sibling::text()').extract()).split()
            try: # Use usaddress module
                work_address = usaddress.tag(" ".join(unparsed_work_address))[0]
                 # Get work city, state, zip fields and remove from ordered dict
                if 'PlaceName' in work_address.keys():
                    item['WORK_CITY'] = work_address.pop('PlaceName')
                if 'StateName' in work_address.keys():
                    item['WORK_STATE'] = work_address.pop('StateName')
                if 'ZipCode' in work_address.keys():
                    item['WORK_ZIPCODE'] = work_address.pop('ZipCode')

                # Getting street name -- a little more complicated. see usaddress.tag() documentation.
                item['WORK_STREET'] = " ".join(work_address.values())
                
            except usaddress.RepeatedLabelError:
                logger.warning("The address: " + work_address + " may have been parsed incorectly." +
                                    "\n Check entry for " + name.first + " " + name.last + ".")
                pass

        # Get last updated work date
        for line in work_selector.xpath('../li'):
            if "Last Update:" in " ".join(line.xpath('strong/text()').extract()):
                work_date = " ".join(line.xpath('normalize-space(strong/following-sibling::text())').extract())
                parsed_work_date = parse(work_date)
                item['WORK_LAST_UPDATED'] =   parsed_work_date.strftime('%m/%d/%Y')             

        # Get email, industry, company, job title, spouse, and phone fields
        for line in response.xpath('//ul/li'):
            if "Email:" in " ".join(line.xpath('strong/text()').extract()):
                item['EMAILS'] = line.xpath('normalize-space(a/text())').extract()
            elif "Industry:" in " ".join(line.xpath('strong/text()').extract()):
                item['INDUSTRY'] = " ".join(line.xpath('normalize-space(strong/following-sibling::text())').extract())
            elif "Company:" in " ".join(line.xpath('strong/text()').extract()):
                item['COMPANY'] = " ".join(line.xpath('normalize-space(strong/following-sibling::text())').extract())
            elif "Job Title:" in " ".join(line.xpath('strong/text()').extract()):
                item['JOB_TITLE'] = " ".join(line.xpath('normalize-space(strong/following-sibling::text())').extract())
            elif "Spouse" in " ".join(line.xpath('strong/text()').extract()):
                item['SPOUSE'] = " ".join(line.xpath('normalize-space(strong/following-sibling::text())').extract())

        # Get phone fields -- Phone numbers don't have home vs. work identifiers, so must take from home and work selectors 
        for line in home_selector.xpath('../li/strong'):
            if "Mobile Phone:" in " ".join(line.xpath('text()').extract()):
                item['MOBILE_PHONE'] = " ".join(line.xpath('normalize-space(following-sibling::text())').extract())
        for line in home_selector.xpath('../li/strong'):
            if "Phone:" in " ".join(line.xpath('text()').extract()):
                item['HOME_PHONE'] = " ".join(line.xpath('normalize-space(following-sibling::text())').extract())
        for line in work_selector.xpath('../li/strong'):
            if "Phone:" in " ".join(line.xpath('text()').extract()):
                item['WORK_PHONE'] = " ".join(line.xpath('normalize-space(following-sibling::text())').extract())
        return item

