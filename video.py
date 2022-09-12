from selenium import webdriver
from selenium.webdriver.common.by import By
import time, requests
import base64
from db_ops import sql_ops, mongodb_ops
import logging
logging.basicConfig(filename="video_scraper.log", level=logging.INFO, format="%(name)s:%(levelname)s:%(asctime)s:%(message)s" )


class video:
    def __init__(self, link:str, driver:webdriver):
        self.video_url = link
        self.driver = driver
        self.title = ''
        self.likes = ''
        self.date = ''
        self.views = ''
        self.comments_num = 0
        self.comments = []          # format : { commenter_name : { "Time" : comment_time, "Text" : text } }
        self.thumb_url = ''
        self.thumb_data = ''
        self.video_path = None
        logging.info("\nVideo instance created successfully.")

    def get_title(self) :
        """
        Fetch the title of the youtube video \n
        :param driver: selenium webdriver
        :return: title string
        """

        content = self.driver.find_element(By.ID, "below")

        try:
            title_info = content.find_element(By.ID, "info-contents").find_element(By.TAG_NAME, "h1")
            title = title_info.find_element(By.TAG_NAME, "yt-formatted-string").get_attribute("innerHTML")
            self.title = title
            logging.info("Title extracted.")
        except Exception as e:
            logging.exception(e)

    def get_views_date_likes(self) :
        """
        Fetch views and date from the YouTube video page. \n
        :param driver:
        :return: dictionary containing 'views' and 'date' as keys
        """

        content = self.driver.find_element(By.ID, "below")
        try:
            info = content.find_element(By.ID, "info-contents").find_element(By.ID, "info")

            views_tag = info.find_element(By.ID, "count").find_elements(By.TAG_NAME, "span")[0]
            self.views = views_tag.get_attribute("innerHTML")

            date_tag = info.find_element(By.ID, "info-strings").find_element(By.TAG_NAME, "yt-formatted-string")
            self.date = date_tag.get_attribute("innerHTML")

            likes_tag = info.find_element(By.ID, "menu").find_element(By.TAG_NAME,
                                                                      "ytd-toggle-button-renderer").find_element(
                By.TAG_NAME, "yt-formatted-string")
            self.likes = likes_tag.get_attribute("innerHTML")

            logging.info("Views, likes, date extracted.")
        except Exception as e:
            logging.exception(e)

    def get_comments_info(self):
        # load the comments section first by scrolling down
        js_query = "window.scrollBy(0, " \
                   "document.getElementById('player').scrollHeight  + " \
                   "document.getElementById('info').scrollHeight +" \
                   "document.getElementById('meta').scrollHeight);"
        self.driver.execute_script(js_query)
        time.sleep(4)

        try :
            content = self.driver.find_element(By.ID, "below")
            comment_section = self.driver.find_element(By.ID, "comments")

            # extract the number of comments
            comment_number_tag = comment_section.find_element(By.ID, "header").find_element(By.ID, "title")
            comment_number_tag = comment_number_tag.find_elements(By.TAG_NAME, "span")[0]
            comments_num = comment_number_tag.get_attribute("innerHTML")
            comments_num = int(comments_num.replace(',', ''))
            self.comments_num = comments_num
        except Exception as e:
            logging.exception(e)

        while True:
            self.driver.execute_script(
                "window.scrollBy(0, document.body.scrollHeight || document.documentElement.scrollHeight);")
            try :
                # load the comment tags
                comments_tags = comment_section.find_element(By.ID, "contents").find_elements(By.TAG_NAME,
                                                                                          "ytd-comment-thread-renderer")
            except Exception as e:
                logging.exception(e)

            # if there are no more comments to load, then break
            if len(self.comments) == len(comments_tags):
                break

            for comment_tag in comments_tags[len(self.comments):]:
                header_info = comment_tag.find_element(By.ID, "header")

                # get the commenter's name
                commenter_name = header_info.find_element(By.TAG_NAME, "h3").find_element(
                                                          By.TAG_NAME,"span").get_attribute("innerHTML")
                commenter_name = commenter_name.strip()

                # get the time when the comment was made
                comment_time = header_info.find_element(By.TAG_NAME, "yt-formatted-string").find_element(
                                                        By.TAG_NAME,"a").get_attribute("innerHTML")
                comment_time = comment_time.strip()

                # get the comment text
                comment_info = comment_tag.find_element(By.ID, "comment-content").find_element(By.ID, "content")
                comment_text_tag = comment_info.find_element(By.TAG_NAME, "yt-formatted-string")
                comment_text = ''

                if len(comment_text_tag.find_elements(By.TAG_NAME, "span")) > 0:
                    for tag in comment_text_tag.find_elements(By.TAG_NAME, "span"):
                        comment_text += tag.get_attribute("innerHTML")
                else:
                    if len(comment_text_tag.find_elements(By.TAG_NAME, "a")) > 0:
                        comment_text_tag = comment_text_tag.find_element(By.TAG_NAME  , "a")
                    comment_text += comment_text_tag.get_attribute("innerHTML")

                self.comments.append({commenter_name: {"Time" : comment_time, "Text" :  comment_text} })
                logging.info("Comments extracted.")

    def get_thumbnail(self):
        try :
            img = requests.get(url=self.thumb_url)
            # convert the thumbnail into base64 format
            self.thumb_data = base64.b64encode(img.content)
            logging.info("Thumbnail extracted.")
        except Exception as e:
            logging.exception(e)

    def download_video(video_link):
        pass

    def extract_data(self, driver):
        try :
            driver.get(self.video_url)
            driver.maximize_window()
            time.sleep(3)
            logging.info("Extracting video data...")
        except Exception as e:
            logging.exception(e)
            raise e
        try :
            self.get_title()
            self.get_views_date_likes()
            self.get_comments_info()
            self.get_thumbnail()
        except Exception as e:
            logging.exception(e)
            raise e

    def insert_into_sql(self, db_name):
        # following columns are present in the Mysql database
        columns = ('video_url', 'title', 'likes', 'date', 'views', 'comments_num')
        data = (self.video_url, self.title, self.likes, self.date, self.views, self.comments_num)
        sql_ops.insert_data(db_name, data)

    def insert_into_mongodb(self, db_name):
        # following must be the keys while inserting data to Mongodb
        attributes =  ('title', 'thumb_data', 'comments')
        data = {
            'Title' : self.title,
            'Thumbnail' : self.thumb_data,
            'Comments' : self.comments
        }
        mongodb_ops.insert_data(db_name, data)



"""vid = video("https://www.youtube.com/watch?v=K5fSWsALU-0", webdriver.Chrome())
vid.thumb_url= "https://i.ytimg.com/vi/3FipKTzkTD4/hqdefault.jpg?sqp=-oaymwEcCNACELwBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLBpT-vmwZTcaCjkBQUOKu8SwEBKoQ"
vid.extract_data()
#vid.insert_into_sql("varad")
vid.insert_into_mongodb("varad")"""