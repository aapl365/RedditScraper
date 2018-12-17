from bs4 import BeautifulSoup
from datetime import date
import os
import praw
import requests
import time


def init_reddit():
    """
    Initializes a connection w/ Reddit
    """
    # ---------- TODO secure this ----------
    client_id = ''
    client_secret = ''
    user_agent = ''
    # ---------- TODO secure this ----------

    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent)
    return reddit


def get_top(subreddit, time, count, parent_path):
    """
    Downloads top submissions

    returns a string of downloaded / total
    ex: 7 downloaded, 10 total => 7/10
    """
    if not init_directory(subreddit, time, count, parent_path):
        return '0/0'

    total_num = 0
    num_downloaded = 0

    for submission in reddit.subreddit(subreddit).top(time, limit=count):
        success = False

        print('{} {}'.format(total_num, submission.title))
        success = download_submission(submission)
        print('\t' + submission.url)
        print('\t' + success.__str__())

        total_num += 1
        if success:
            num_downloaded += 1

    return str(num_downloaded) + '/' + str(total_num)


def init_directory(subreddit, time, count, parent_path):
    """
    Returns False if directory already present
    """
    dir_name = '{}_{}_{}_{}'.format(subreddit, time, count, date.today())
    pwd = parent_path + dir_name

    if os.path.exists(pwd):
        return False

    os.makedirs(pwd)
    os.chdir(pwd)
    return True


def download_submission(submission):
    """
    Returns True if submission downloaded
    """
    success = False
    if '.jpg' in submission.url or '.png' in submission.url:
        success = get_direct(submission.url, submission.id)
    elif '.gifv' in submission.url:
        cleaned_url = gifv_to_mp4(submission.url)
        success = get_direct(cleaned_url, submission.id)
    elif 'v.redd.it' in submission.url:
        vreddit_get_direct(submission.url, submission.id)
    elif 'imgur.com/a/' in submission.url:
        original_path = os.getcwd()
        album_dir = original_path + '/' + submission.id
        os.makedirs(album_dir)
        os.chdir(album_dir)

        success = imgur_get_album(submission.url, submission.id)

        os.chdir(original_path)

    elif 'imgur' in submission.url:
        success = get_direct(submission.url + '.jpg', submission.id)
    elif 'gfycat' in submission.url:
        cleaned_url = gyfcat_to_mp4(submission.url)
        success = get_direct(cleaned_url, submission.id)
    return success


def vreddit_get_direct(submission_url, submission_id):
    """
    Downloads content from vreddit urls

    TODO properly test this with videos and files
    """
    html_source = requests.get(submission_url).text
    soup = BeautifulSoup(html_source, 'html.parser')
    vid_id = 'video-' + submission_id

    # Retries until id is found
    image_url = soup.find(id=vid_id)
    while image_url.__str__() == 'None':
        time.sleep(2)
        html_source = requests.get(submission_url).text
        soup = BeautifulSoup(html_source, 'html.parser')
        vid_id = 'video-' + submission_id;
        image_url = soup.find(id=vid_id)
    image_url = image_url['data-seek-preview-url']
    print('\t ' + image_url)
    time.sleep(2)


def imgur_get_album(submission_url, submission_id):
    # TODO boolean handling
    html_source = requests.get(submission_url).text
    soup = BeautifulSoup(html_source, 'html.parser')
    image_url = soup.select('[src*="i.imgur.com"]')

    success = True
    num_in_album = 0
    # print(image_url)
    for img in image_url:
        file_name = submission_id + '-' + str(num_in_album).zfill(2)
        success = success and get_direct('http:' + img['src'], file_name)
        num_in_album += 1

    return success


def get_direct(image_url, submission_id):
    """
    Returns true if request is valid
    """
    print('getting ' + image_url)
    response = requests.get(image_url)
    if response.status_code == 200:
        file_name = submission_id + get_file_ext(image_url)
        download(response, file_name)
        return True
    return False


def download(response, file_name):
    with open(file_name, 'wb') as fo:
        fo.write(response.content)


def gifv_to_mp4(url):
    """
    Changes ".gifv" ending urls to ".mp4"
    """
    newUrl = url[:url.rfind('.')] + '.mp4'
    return newUrl


def gyfcat_to_mp4(url):
    """
    Changes gyfcat urls to direct .mp4 links
    """
    left = url[:url.find('g')]
    middle = url[url.find('g'):]
    new_url = left + 'giant.' + middle + '.mp4'
    print(new_url)
    return new_url


def get_file_ext(image_url):
    """
    Returns the file extension of direct urls
    """
    return image_url[image_url.rfind('.'):]


# ---------- Main ----------
if __name__ == '__main__':
    reddit = init_reddit()
    downloadedFraction = get_top('aww', 'week', 10, './')

    print('-' * 40)
    print(downloadedFraction + ' downloaded\n')
