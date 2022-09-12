import video
from db_ops import sql_ops
from selenium.webdriver.common.by import By
import logging, time
logging.basicConfig(filename="video_scraper.log", level=logging.INFO, format="%(name)s:%(levelname)s:%(asctime)s:%(message)s" )

class Channel:

    def __init__(self, url, driver):
        self.driver = driver
        self.url = url
        self.name = ''
        self.subscribers = ''
        self.videos_num = 0
        self.video_objs = []

        # get the webpage
        self.driver.get(url)
        time.sleep(3)

    def get_channel_info(self, driver) :
        logging.info("Getting channel info...")

        content = driver.find_element(By.ID, "inner-header-container")

        name_tag = content.find_element(By.ID, "text-container").find_element(By.TAG_NAME, "yt-formatted-string")
        self.name = name_tag.get_attribute("innerHTML")

        # format the name properly
        self.name = (self.name).replace(' ', '_').replace('-', '_').replace('.', '_').replace("'", '').replace(",", "")

        self.subscribers = content.find_element(By.ID, "subscriber-count").get_attribute("innerHTML")

        # create the databases in Mysql and Mongodb
        self.create_db()

        logging.info("Channel info complete.")

    def create_db(self):
        sql_ops.create_db(self.name)

    def get_video_urls(self, number_of_videos: int, driver) :
        """
        :param channel_link: url of the youtube channel
        :param number_of_videos: number of videos to fetch
        :return: list containing urls of the videos
        """

        logging.info("\nGET_VIDEO_URLS:")
        driver.maximize_window()
        try:
            driver.get(self.url + "/videos")
        except Exception as e:
            logging.exception(e)
        time.sleep(2)

        # select the 'SORT-BY' option to 'Most recent'
        try:
            sort_button = driver.find_element(By.ID, "sort-menu")
            sort_button.click()
            sort_options = sort_button.find_elements(By.TAG_NAME, "a")
            opt1 = sort_options[2].find_elements(By.TAG_NAME, "div")
            logging.info("Selecting option :%s" % opt1[0].get_attribute("innerHTML"))

            # get the webpage for the selected option
            link = sort_options[2].get_attribute("href")
            driver.get(link)
            time.sleep(2)
        except Exception as e:
            logging.exception(e)

        # now we are on the 'Most recent videos' page
        # get the video urls by selecting proper elements
        try:
            videos = driver.find_elements(By.XPATH, "//div[@id='contents']")[1]
            videos = videos.find_element(By.ID, "items")
            logging.info("Reached items tag...")  # 'items' tag contains the info related to all the videos
        except Exception as e:
            logging.exception(e)

        #video_urls = []  # to save urls , format : [ { video_url : thumbnail_url } ]
        finished = 0  # flag to know if the task is complete

        logging.info("Starting extraction ....")
        while len(self.video_objs) < number_of_videos:
            # scroll down
            driver.execute_script(
                "window.scrollBy(0, document.body.scrollHeight || document.documentElement.scrollHeight);")
            time.sleep(3)

            try:
                videos_tag = videos.find_elements(By.ID, "dismissible")
            except Exception as e:
                logging.exception(e)

            # if there are no more videos to load, i.e., if we have reached to the end
            if len(videos_tag) == len(self.video_objs):
                logging.info("Cannot scroll down... Reached to the end...")
                logging.info("Extracted %s videos. Complete." % len(self.video_objs))
                break

            logging.info("Found %s elements ...." % len(videos_tag))

            # extract the links
            for elem in videos_tag[len(self.video_objs):]:
                link = elem.find_element(By.TAG_NAME, "a")
                url = link.get_attribute("href")

                # extract thumbnail url
                try:
                    thumb = elem.find_element(By.ID, "img").get_attribute("src")
                except Exception as e:
                    print(e)


                new_video = video.video(url, driver)
                new_video.thumb_url = thumb

                self.video_objs.append(new_video)

                if len(self.video_objs) == number_of_videos:
                    logging.info("Extracted %s videos. Complete." % len(self.video_objs))
                    finished = 1
                    break

            if finished:
                break
            else:
                logging.info("Scrolling down and looking for more videos... ")

        logging.info("\nGET_VIDEO_URLS FUNCTION COMPLETE.\n")

    def save_data(self, driver):
        logging.info("\nSaving the channel data to the database ....")

        for video_obj in self.video_objs:
            try :
                video_obj.extract_data(driver)
                video_obj.insert_into_sql(self.name)
                video_obj.insert_into_mongodb(self.name)
            except Exception as e:
                logging.exception(e)
                raise e

        logging.info("Videos saved to the databases successfully.")

