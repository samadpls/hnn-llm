# Authors: Abdul Samad Siddiqui <abdulsamadsid1@gmail.com>
#          Maira Usman <maira.usman5703@gmail.com>
import os
import requests
from bs4 import BeautifulSoup


class HNNDataScraper:
    def __init__(self, output_dir='./data'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def scrape_website(self, url, selectors, data_extractors):
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        data = []
        for selector, extractor in zip(selectors, data_extractors):
            elements = soup.select(selector)
            for element in elements:
                result = extractor(element)
                if result:
                    data.append(result)

        return data

    def save_to_txt(self, data, filename):
        with open(os.path.join(self.output_dir, filename), 'w',
                  encoding='utf-8') as f:
            for entry in data:
                f.write(entry + '\n\n')
        print(f"Data has been saved to '{filename}'")

    def scrape_hnn_website(self):
        url = "https://hnn.brown.edu/getting-started/"
        selectors = ['ul.sub-menu li a']

        def extract_item(item):
            link = item.get('href')
            if link == '#' or link.startswith('#'):
                return None
            title = item.get_text(strip=True)
            return f"Title: {title}\nLink: {link}"

        menu_items = self.scrape_website(url, selectors, [extract_item])

        descriptions = []
        for item in menu_items:
            _, link = item.split('\nLink: ')
            link = link.strip()
            page_response = requests.get(link)
            page_response.raise_for_status()
            page_soup = BeautifulSoup(page_response.text, 'html.parser')
            content_div = page_soup.select_one(
                'div.srj.m-width.srj-spacious') or page_soup.select_one(
                    'div.srj.srj-spacious')
            description = content_div.get_text(
                strip=True) if content_div else "No content found"
            descriptions.append(f"{item}\nDescription: {description}")

        self.save_to_txt(descriptions, 'hnn_website_data.txt')

    def scrape_hnn_core(self):
        url = "https://jonescompneurolab.github.io/hnn-core/stable/index.html"
        selectors = ['section#about', 'section#dependencies',
                     'section#optional-dependencies', 'section#installation']

        def extract_section(section):
            title = section.h2.text.strip() \
                if section.h2 else section.h1.text.strip()
            paragraphs = [p.get_text(separator=" ").strip()
                          for p in section.find_all('p')]
            list_items = [li.get_text(strip=True)
                          for li in section.find_all('li')]
            content = ' '.join(paragraphs + list_items)
            return f"{title} Section\n{content}"

        sections_data = []
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')

        for selector in selectors:
            section = soup.find('section', id=selector.split('#')[-1])
            if section:
                section_data = extract_section(section)
                sections_data.append(section_data)

        self.save_to_txt(sections_data, 'hnn_core_data.txt')

    def scrape_hnn_tutorials(self):
        url = 'https://jonescompneurolab.github.io/hnn-core/stable/auto_examples/index.html'
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        titles = []
        urls = []
        descriptions = []

        for thumb_container in soup.find_all('div',
                                             class_='sphx-glr-thumbcontainer'):
            title_tag = thumb_container.find('span', class_='std std-ref')
            title = title_tag.get_text(strip=True) if title_tag else 'No title'
            link_tag = thumb_container.find('a', class_='reference internal')
            relative_url = link_tag.get('href') if link_tag else ''
            full_url = requests.compat.urljoin(url, relative_url)

            example_response = requests.get(full_url)
            example_response.raise_for_status()
            example_soup = BeautifulSoup(example_response.text, 'html.parser')

            for unwanted_class in ['sphx-glr-script-out',
                                   'highlight-none', 'notranslate']:
                for element in example_soup.find_all(class_=unwanted_class):
                    element.decompose()

            section_content = example_soup.find(
                'section', class_='sphx-glr-example-title')
            description = ' '.join(
                section_content.stripped_strings) \
                if section_content else 'No content found'

            titles.append(
                f"Title: {title}\nURL: {full_url}\nDescription: {description}")

        self.save_to_txt(titles, 'hnn_example_tutorials.txt')


def main():
    scraper = HNNDataScraper()
    scraper.scrape_hnn_website()
    scraper.scrape_hnn_core()
    scraper.scrape_hnn_tutorials()


if __name__ == "__main__":
    main()
