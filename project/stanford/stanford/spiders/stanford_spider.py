from scrapy.http import Request, FormRequest
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule

from scrapy.contrib.spiders import CrawlSpider
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

from scrapy.contrib.linkextractors import LinkExtractor

from stanford.items import StanfordItem

import sys
sys.path.append("../name_parser")
sys.path.append("../usaddress")

import usaddress
from nameparser import HumanName

import logging

class StanfordSpider(CrawlSpider):
    name = 'stanford'
    login_url = "https://alumni.stanford.edu/get/page/directory/advanced/"
    start_urls = ["https://alumni.stanford.edu/get/page/directory/advanced/"]
    input_file = "input.txt"

    logger = logging.getLogger('stanford')

    def start_requests(self): 
        """

        This method is called first, by default. It starts the crawl by requesting the login page.

        """
        return [Request(url=self.login_url,
                       callback=self.login,
                       dont_filter=True)]

    def login(self, response):
        """

        Generate a login request.

        """
        return FormRequest.from_response(response, formname='mainform',
                    formdata={'username': 'bryanfinkel', 'password': 'GretaStan99'},
                    callback=self.check_login_response)

    def check_login_response(self, response):
        """

        Check the response returned by a login request to see if we are successfully logged in.

        """
        if "Log Out" in response.body:
            # Go to search page
            return self.search(response)

        else:
            logger.error("Login was unsuccessful. Did not reach search page.")
            # Something went wrong, we couldn't log in, so nothing happens.

    def get_input_data(self, input_file):
        data_form = {}
        data = ["first_name", "city", "state", "employment_company", "employment_title"]
        f = open(input_file,"r");
        lines = f.readlines()
        for field in data:
            line = "".join(lines.pop(0).split(":")[1:]).strip()
            if line is not "":
                data_form[field] = line
        return data_form

    def search(self, response):
        """

        Fill in form (search field) with default term "data scientist" and search.

        """
        if "Alumni Directory Search: Advanced" in response.body:
            self.log("\n\n\n Made it to the search! \n\n\n")
            return FormRequest.from_response(response,
                    formxpath='//form[@id="dirsrchform"]',
                    formdata=self.get_input_data(self.input_file),
                    callback=self.check_search)
        else:
            self.log("\n\n\n Didn't make it to the search. \n\n\n")

    def check_search(self, response):
        if "Your search will return more than 500 results." in response.body:
            my_url = ""
            links = response.xpath('//fieldset/ul/li/a')
            for link in links:
                link_text = "".join(link.xpath('text()').extract())
                if "View 500 results only." in link_text:
                    my_url = "https://alumni.stanford.edu" + "".join(link.xpath("@href").extract())
            return Request(url=my_url,
                           callback=self.crawl_results)
        elif "Alumni Directory Profile" in response.body:
            return self.parse_result_page(response)
        else:
            return self.crawl_results(response)

    def crawl_results(self, response):
        """

        Crawls the linked results of individuals' personal profiles on search page.
        (Results are essentially a list of alumni names with links to their personal pages.)
        
        """
        try:    
            count = 1
            links = response.xpath('//div[@class="results"]/table/tr/td/h5/a/@href').extract()
            for link in links:
                if count <= 5:
                    item = StanfordItem()
                    # Step in one page (click on result name) and parse result page
                    result_page = "https://alumni.stanford.edu" + link
                    request = Request(url=result_page,
                                  callback=self.parse_result_page)
                    request.meta['item'] = item
                    yield request
                    # Yield completed item
                    count += 1

            # Recursively crawl the "personal profile" - currently commented out to minimize records acccessed     
            # links = response.xpath('//div[@class="clearfix paginationContainer"]/div[@class="floatright"]/a')
            # for link in links:
            #     if "next" in " ".join(link.xpath('text()').extract()):
            #         next_page = "https://alumni.stanford.edu/" + " ".join(link.xpath('@href').extract())
            #         yield Request(url=next_page,
            #                       callback=self.crawl_results)
        except Exception, error:
            logger.error("Results were not crawled.\n" + str(error))

    def parse_result_page(self, response):
        """

        Parses the result pages of each individual. 
        Collects data fields defined in StanfordItem class, stores data within a StanfordItem instance.
        Returns data-filled StanfordItem instance. 

        """
        try:

            item = response.meta['item']
            # Get name fields
            unparsed_name = response.xpath('normalize-space(//div[@id="profileSummaryTop"]/p/strong/text())').extract()[0]
            name = HumanName(unparsed_name)
            item['PREFIX'] = name.title
            item['FIRST_NAME'] = name.first
            item['LAST_NAME'] = name.last
            item['SUFFIX'] = name.suffix
            # Scrape through "personal" webpage section, focus on "personal profile"
            personal_selector = response.xpath('//div[@id="profilePersonal"]')
            if personal_selector.extract():
                personal_sections = personal_selector.xpath('div/div/div/h2')
                personal_profile = None
                for section in personal_sections:
                    if "Personal Profile" in section.extract():
                        personal_profile = section.xpath('../..') # Find "personal profile" xpath
                if personal_profile:
                    labels = personal_profile.xpath('dl/dt/text()').extract()
                    index = 1
                    for label in labels:
                        # Get home address field using usaddress module
                        if "Address:" in label:
                            unparsed_home_address = " ".join(personal_profile.xpath('dl/dd[' + str(index) + ']/text()').extract()).split()
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
                   
                        # Get email field
                        elif "Email:" in label:
                            emails = personal_profile.xpath('dl/dd[' + str(index) + ']/a/text()').extract()
                            email_list = []
                            if len(emails) >= 1:
                                email_list.append(emails[0])
                            if len(emails) >= 2:
                                email_list.append(emails[1])
                            if len(emails) >= 3:
                                email_list.append(emails[2])
                            item['EMAILS'] = email_list
                        elif "Phone:" in label:
                            item['HOME_PHONE'] = personal_profile.xpath('normalize-space(dl/dd[' + str(index) + ']/text())').extract() 
                        index += 1

            # Scrape through "work/professional" webpage section, focus on "primary position"
            professional_selector = response.xpath('//div[@id="profileProfessional"]')
            if professional_selector.extract():
                professional_sections = professional_selector.xpath('div/div/h4')
                primary_position = None
                for section in professional_sections:
                    if "Primary Position" in section.extract():
                        primary_position = section.xpath('..') # Find "primary position" xpath
                if primary_position:
                    labels = primary_position.xpath('div/div[@class="content"]/dl/dt/text()').extract()
                    # Get job title and company
                    job_line = " ".join(primary_position.xpath('normalize-space(div/h5/text())').extract()).split(" at ")
                    if len(job_line) == 2:
                        item['JOB_TITLE'] = job_line[0]
                        item['COMPANY'] = job_line[1]

                    index = 1
                    for label in labels:
                        # Get work address field using usaddress module
                        if "Address:" in label:
                            unparsed_work_address = " ".join(primary_position.xpath('div/div[@class="content"]/dl/dd[' + str(index) + ']/text()').extract()).split()
                            try: # Use usaddress module
                                work_address = usaddress.tag(" ".join(unparsed_work_address))[0] # an ordered dict
                                # Get work city, state, zip fields and remove from ordered dict
                                if 'PlaceName' in work_address.keys():
                                    item['WORK_CITY'] = work_address.pop('PlaceName')
                                if 'StateName' in work_address.keys():
                                    item['WORK_STATE'] = work_address.pop('StateName')
                                if 'ZipCode' in work_address.keys():
                                    item['WORK_ZIPCODE'] = work_address.pop('ZipCode')

                                # Get street name field
                                item['WORK_STREET'] = " ".join(work_address.values())
                            
                            except usaddress.RepeatedLabelError:
                                logger.warning("The address: " + work_address + " may have been parsed incorectly." +
                                        "\n Check entry for " + name.first + " " + name.last + ".")
                                pass
                        # Get industry field
                        elif "Industry" in label:
                            item['INDUSTRY'] = " ".join(primary_position.xpath('normalize-space(div/div[@class="content"]/dl/dd[' + str(index) + ']/text())').extract())
                        # Get work phone field
                        elif "Phone" in label:
                            item['WORK_PHONE'] = " ".join(primary_position.xpath('normalize-space(div/div[@class="content"]/dl/dd[' + str(index) + ']/text())').extract())
                        index += 1
                    # Get date of last update
                    unparsed_last_update = " ".join(primary_position.xpath('div/div[@class="content"]/p[@class="lastupdated"]/text()').extract())
                    split_last_update = unparsed_last_update.split()
                    if len(split_last_update) == 3:
                        item['WORK_LAST_UPDATED'] = split_last_update[2]
            return item
        except Exception, erorr:
            logger.error("Results of and individual were not crawled.\n" + str(error))

