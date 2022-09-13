from selenium.webdriver.chrome.service import Service

from db_ops import sql_ops
from flask import request, render_template, Flask
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from channel import Channel
import os
import sys
sys.path.insert(0, "/usr/bin/chromedriver")
import threading
import logging
logging.basicConfig(filename="video_scraper.log", level=logging.INFO, format="%(name)s:%(levelname)s:%(asctime)s:%(message)s" )




application = Flask(__name__)

# global variables
channel2 = None
url = ''
num = 0
driver = None
counter = 0

def get_driver():
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    #driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),
        #                     chrome_options=chrome_options)
    #driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=chrome_options)
    #driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    #service = Service(executable_path=ChromeDriverManager().install())
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service)

    return driver


@application.route('/')
def home_page():
    logging.info("\napplication running....rendering index.html...")
    return render_template("index.html")


@application.route('/results', methods=['POST'])
def get_results():
    if request.method == 'POST' :
        logging.info("Getting input for channel name and number of videos...")

        url = request.form['url']
        num = int(request.form['num'])
        try :
            # set up selenium webdriver
            """chrome_options = webdriver.ChromeOptions()
            chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),
                                      chrome_options=chrome_options)"""
            driver = get_driver()

            channel2 = Channel(url, driver)          # create a channel object instance
            channel2.get_channel_info(driver)        # get the channel details
            with open("channel_details.txt", 'w') as f:
                f.write(str(num)+"\n"+url+"\n"+channel2.name+"\n"+"0")
        except Exception as e:
            logging.exception(e)
            return "<p>%s</p>" %e

        logging.info("Input for channel name and videos number received. Rendering results.html...")
        return render_template("results.html", name=channel2.name, subs= channel2.subscribers)

@application.route('/get_urls', methods=['POST'])
def get_urls():
    #global driver, channel2, url , num

    try :
        with open("channel_details.txt", 'r') as f:
            num = int(f.readline())
            url = f.readline()

        driver = get_driver()
        channel2 = Channel(url, driver)
        channel2.get_channel_info(driver)
        channel2.get_video_urls(num, driver)         # retrieve the urls of the videos

        data = []
        for video in channel2.video_objs:
            data.append(str(video.video_url))
    except Exception as e:
        return "<p>%s</p>" %e

    logging.info("Rendering get_urls.html....")
    return render_template("get_urls.html", urls = data)

@application.route('/save_data', methods=['POST', 'GET'])
def save_func():
    new_thread = threading.Thread(target=save_videos)
    new_thread.start()

def save_videos():
    #global driver, channel2
    try :
        with open("channel_details.txt", 'r') as f:
            f.seek(0)
            num = int(f.readline())
            url = f.readline()

        driver = get_driver()
        channel2 = Channel(url, driver)
        channel2.get_channel_info(driver)
        channel2.get_video_urls(num, driver)  # retrieve the urls of the videos
        channel2.save_data(driver)
    except Exception as e:
        logging.exception(e)


    logging.info("All data saved.")
    return "<h2>All data have been saved successfully !!</h2>"


@application.route('/get_updates', methods=['POST'])
def updates():
    #global counter,channel2
    logging.info("Getting updates...")
    try :
        with open("channel_details.txt", 'r') as f:
            f.seek(0)
            num = int(f.readline())
            url = f.readline()
            name = f.readline()
            counter = int(f.readline())
        data = sql_ops.fetch_data(name, "videodata")
    except Exception as e:
        logging.exception(e)
        return "<p>Fetching data failed.%s</p>" %e

    if counter < len(data):
        titles = []
        i = counter
        for v in data[counter:]:
            title = v[1]
            titles.append(title)
        counter = len(data)
        with open("channel_details.txt", 'w') as f:
            f.write(str(num) + "\n" + url + "\n" + name + "\n" + str(counter))

        logging.info("Updates received. Rendering video.html..")
        return render_template("video.html", video_names = titles, idx=i+1)

    msg = "<p>No new data updated to the database yet... please make sure you have clicked 'Save data' button; " \
           "if done already,please try again after about 4-5 seconds.</p><hr>"
    return msg




if __name__ == '__main__':
    application.run(port=5000)