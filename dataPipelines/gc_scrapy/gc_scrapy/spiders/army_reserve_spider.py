import scrapy
import re
from datetime import datetime
from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSpider import GCSpider

from urllib.parse import urljoin, urlparse
from datetime import datetime
from dataPipelines.gc_scrapy.gc_scrapy.utils import dict_to_sha256_hex_digest

type_and_num_regex = re.compile(r"([a-zA-Z].*) (\d.*)") # Get 'type' (alphabetic) value and 'num' (numeric) value from 'doc_name' string


class ArmyReserveSpider(GCSpider):
    '''
    Class defines the behavior for crawling and extracting text-based documents from the U.S. Army Reserves "Publications" site.
    This class inherits the 'GCSpider' class from GCSpider.py. The GCSpider class is Gamechanger's implementation of the standard
    parse method used in Scrapy crawlers in order to return a response.

    The "class" and its methods = the army_reserve "spider".
    '''

    name = "Army_Reserve" # Crawler name
    display_org = "Dept. of the Army" # Level 1: GC app 'Source' filter for docs from this crawler
    data_source = "Army Publishing Directorate" # Level 2: GC app 'Source' metadata field for docs from this crawler
    source_title = "Unlisted Source" # Level 3 filter

    allowed_domains = ['usar.army.mil'] # Domains the spider is allowed to crawl
    start_urls = [
        'https://www.usar.army.mil/Publications/'
    ] # URL where the spider begins crawling

    file_type = "pdf" # Define filetype for the spider to download
    cac_login_required = False # Assume document is accessible without CAC

    @staticmethod
    def clean(text):
        '''
        This function forces text into the ASCII characters set, ignoring errors
        '''
        return text.encode('ascii', 'ignore').decode('ascii').strip()

    @staticmethod
    def get_display_doc_type(doc_type):
        """This function returns value for display_doc_type based on doc_type -> display_doc_type mapping"""
        display_type_dict = {
        "usar cir": "Circular",
        "usar pam": "Pamphlet",
        "usar reg": "Regulation"
        }
        if doc_type.lower() in display_type_dict.keys():
            return display_type_dict[doc_type.lower()]
        else:
            return "Document"

    def parse(self, response):
        '''
        This function generates a link and metadata for each document found on the Army Reserves Publishing
        site for use by bash download script.
        '''
        selected_items = response.css(
            "div.DnnModule.DnnModule-ICGModulesExpandableTextHtml div.Normal > div p") # Get expandable section (each exposes doc links on webpage when selected)
        for item in selected_items: # Iterate over each link in the section
            pdf_url = item.css('a::attr(href)').get() # Get link url
            if pdf_url is None: # Fail-safe
                continue
            # Join relative urls to base
            web_url = urljoin(self.start_urls[0], pdf_url) if pdf_url.startswith(
                '/') else pdf_url
            web_url = web_url.replace(" ", "%20") # Add document to base url, encoding spaces (with %20)

            cac_login_required = True if "usar.dod.afpims.mil" in web_url else False # Determine if CAC is required from url

            doc_name_raw = "".join(item.css('strong::text').getall()) # Bolded portion of displayed document name as doc_name_raw
            doc_title_raw = item.css('a::text').get() # Unbolded portion of displayed document name as doc_title_raw
            
            if doc_title_raw is None:
                doc_title_raw = item.css('a span::text').get() # If no unbolded text, some have title nested in span

                if doc_title_raw is None:
                    doc_title_raw = doc_name_raw # Some only have the bolded name, e.g. FY20 USAR IDT TRP Policy Update

            doc_name = self.clean(doc_name_raw) # ASCII fail-safe
            doc_title = self.clean(doc_title_raw) # ASCII fail-safe

            type_and_num_groups = re.search(type_and_num_regex, doc_name) # Get doc_type and doc_num (using naming convention) from 'doc_name'
            if type_and_num_groups is not None:
                doc_type = type_and_num_groups[1] # Assign value to 'doc_type'
                doc_num = type_and_num_groups[2] # Assign value to 'doc_num'
            else: # Apply default values if doc type and num are not decipherable from 'doc_name'
                doc_type = "USAR Doc"
                doc_num = ""

            # This site/crawler does not have pub dates
            fields = {
                'doc_name': doc_name,
                'doc_num': doc_num,
                'doc_title': doc_title,
                'doc_type': doc_type,
                'cac_login_required': cac_login_required,
                'download_url': web_url
            }

            ## Instantiate DocItem class and assign document's metadata values
            doc_item = self.populate_doc_item(fields)
       
            yield doc_item


    def populate_doc_item(self, fields):
        '''
        This functions provides both hardcoded and computed values for the variables
        in the imported DocItem object and returns the populated metadata object
        '''
        display_org = "Dept. of the Army" # Level 1: GC app 'Source' filter for docs from this crawler
        data_source = "Army Publishing Directorate" # Level 2: GC app 'Source' metadata field for docs from this crawler
        source_title = "Unlisted Source" # Level 3 filter
        is_revoked = False

        doc_name = fields['doc_name']
        doc_num = fields['doc_num']
        doc_title = fields['doc_title']
        doc_type = fields['doc_type']
        display_doc_type = self.get_display_doc_type(doc_type)
        cac_login_required = fields['cac_login_required']
        download_url = fields['download_url']
        display_source = data_source + " - " + source_title
        display_title = doc_type + " " + doc_num + ": " + doc_title
        source_page_url = self.start_urls[0]
        source_fqdn = urlparse(source_page_url).netloc
        downloadable_items = [
                {
                    "doc_type": self.file_type,
                    "download_url": download_url,
                    "compression_type": None
                }
            ] # Get document metadata
        version_hash_fields = {
            "doc_name":doc_name,
            "doc_num": doc_num,
            "download_url": download_url.split('/')[-1],
            "display_title": display_title
        } # Assign fields used for versioning
        file_ext = downloadable_items[0]["doc_type"]
        version_hash = dict_to_sha256_hex_digest(version_hash_fields)

        return DocItem(
            doc_name = doc_name,
            doc_title = doc_title,
            doc_num = doc_num,
            doc_type = doc_type,
            display_doc_type = display_doc_type,
            publication_date = None, # Publication dates not available from website, link, or filename
            cac_login_required = cac_login_required,
            crawler_used = self.name,
            downloadable_items = downloadable_items,
            source_page_url = source_page_url,
            source_fqdn = source_fqdn,
            download_url = download_url,
            version_hash_raw_data = version_hash_fields,
            version_hash = version_hash,
            display_org = display_org,
            data_source = data_source,
            source_title = source_title,
            display_source = display_source,
            display_title = display_title,
            file_ext = file_ext,
            is_revoked = is_revoked,
        )
