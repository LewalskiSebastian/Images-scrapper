from selenium import webdriver
import time
import io
from PIL import Image
import requests
import os
import hashlib


class Scraper:
    def __init__(self, driver_path, sleep_time=0.1, quiet_mode=False):
        """

        :param driver_path: str
            Path to chrome driver compatible with installed Chrome version

        :param sleep_time: float
            Time to sleep between actions (prevent bot detection)
        """
        self.wd = webdriver.Chrome(executable_path=driver_path)
        self.sleep_time = sleep_time
        self.quiet_mode = quiet_mode

    def search_and_download(self, query: str, color='', nation='', save_path='', prefix=None, number_images=5):
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        if not prefix:
            prefix = '_'.join(query.lower().split(' '))

        urls = self.get_image_urls(query, color, nation, number_images)

        for url in urls:
            image = self.get_image_from_url(url)
            self.save_image(image, save_path, prefix)

    def __del__(self):
        try:
            self.exit()
        except ImportError:
            pass

    def exit(self):
        self.wd.quit()

    def scroll_end(self):
        self.wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(self.sleep_time)

    def get_image_urls(self, query, color='', nation='', max_links_to_fetch=5):
        query = '%20'.join(query.split(' '))
        search_url = "https://www.google.com/search?q={q}&tbm=isch&tbs=ic:specific%2Cisc:{c}&hl={n}".format(q=query,
                                                                                                            c=color,
                                                                                                            n=nation)

        self.wd.get(search_url)

        image_urls = set()
        urls_count = 0
        results_start = 0
        while urls_count < max_links_to_fetch:
            self.scroll_end()

            web_elements_results = self.wd.find_elements_by_css_selector("img.Q4LuWd")
            number_of_results = len(web_elements_results)

            if not self.quiet_mode:
                print(f"Found {number_of_results} links.")

            for img in web_elements_results[results_start:number_of_results]:
                try:
                    img.click()
                    time.sleep(self.sleep_time)
                except Exception:
                    continue

                query_images = self.wd.find_elements_by_css_selector('img.n3VNCb')
                for query_image in query_images:
                    if query_image.get_attribute('src') and 'http' in query_image.get_attribute('src'):
                        image_urls.add(query_image.get_attribute('src'))

                urls_count = len(image_urls)

                if urls_count >= max_links_to_fetch:
                    break

            if urls_count >= max_links_to_fetch:
                if not self.quiet_mode:
                    print(f"Got {urls_count} links")
                break
            else:
                if not self.quiet_mode:
                    print("Found only", urls_count, "links, looking for more...")
                time.sleep(self.sleep_time)
                load_more_button = self.wd.find_element_by_css_selector(".mye4qd")
                if load_more_button:
                    self.wd.execute_script("document.querySelector('.mye4qd').click();")

            results_start = len(web_elements_results)

        return image_urls

    def get_image_from_url(self, url: str):
        try:
            image_content = requests.get(url).content
            image_file = io.BytesIO(image_content)
            image = Image.open(image_file).convert('RGB')
            return image
        except Exception as e:
            if not self.quiet_mode:
                print(f"Could not download {url} - {e}")

    def save_image(self, image, save_path, prefix):
        buf = io.BytesIO()
        image.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        file_path = os.path.join(save_path, prefix + '-' + hashlib.sha1(byte_im).hexdigest()[:10] + '.jpg')
        try:
            with open(file_path, 'wb') as f:
                image.save(f, "JPEG", quality=85)
            if not self.quiet_mode:
                print(f"Saved {file_path}")
        except Exception as e:
            if not self.quiet_mode:
                print(f" Could not save {file_path} - {e}")
