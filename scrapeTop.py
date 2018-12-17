from bs4 import BeautifulSoup
from datetime import date
import os
import praw
import requests
import time

# Initializes a connection w/ Reddit
def initReddit():
	# TODO secure this
	clientId = "";
	clientSecret = "";
	userAgent = "";

	reddit = praw.Reddit(client_id=clientId,
			client_secret=clientSecret,
			user_agent=userAgent)
	return reddit

# Downloads top submissions
# returns a string of downloaded / total
#	ex: 7 downloaded, 10 total => 7/10
def getTop(subreddit, time, count, parentPath):
	if not initDirectory(subreddit, time, count, parentPath):
		return "0/0"

	totalNum = 0
	numDownloaded = 0

	for submission in reddit.subreddit(subreddit).top(time, limit=count):
		success = False

		print("{} {}".format(totalNum, submission.title))
		success = downloadSubmission(submission)
		print("\t" + submission.url)
		print("\t" + success.__str__())

		totalNum += 1
		if success:
			numDownloaded += 1

	return str(numDownloaded) + "/" + str(totalNum)

# Returns False if directory already present
def initDirectory(subreddit, time, count, parentPath):
	dirName = "{}_{}_{}_{}".format(
		subreddit, time, count, date.today())
	pwd = parentPath + dirName

	if os.path.exists(pwd):
		return False

	os.makedirs(pwd)
	os.chdir(pwd)
	return True

# returns True if submission downloaded
def downloadSubmission(submission):
	success = False
	if ".jpg" in submission.url or ".png" in submission.url:
		success = getDirect(submission.url, submission.id)
	elif ".gifv" in submission.url:
		cleanedUrl = gifvToMp4(submission.url)
		success = getDirect(cleanedUrl, submission.id)
	elif "v.redd.it" in submission.url:
		vreddit_getDirect(submission.url, submission.id)
	elif "imgur.com/a/" in submission.url:
		originalPath = os.getcwd()
		albumDir = originalPath + "/" + submission.id
		os.makedirs(albumDir)
		os.chdir(albumDir)

		success = imgur_getAlbum(submission.url, submission.id)	

		os.chdir(originalPath)

	elif "imgur" in submission.url:
		success = getDirect(submission.url + ".jpg", submission.id)
	elif "gfycat" in submission.url:
		cleanedUrl = gyfcatToMp4(submission.url)
		success = getDirect(cleanedUrl, submission.id)
	return success

# Downloads content from vreddit urls
# 	TODO properly test this with videos and files
def vreddit_getDirect(submissionUrl, submissionId):
	htmlSource = requests.get(submissionUrl).text
	soup = BeautifulSoup(htmlSource, "html.parser")
	vidId = "video-" + submissionId

	# Retries until id is found
	imageUrl = soup.find(id=vidId)
	while imageUrl.__str__() == "None":
		time.sleep(2)
		htmlSource = requests.get(submissionUrl).text
		soup = BeautifulSoup(htmlSource, "html.parser")
		vidId = "video-" + submissionId;
		imageUrl = soup.find(id=vidId)
	imageUrl = imageUrl['data-seek-preview-url']
	print("\t " + imageUrl)
	time.sleep(2)

# TODO boolean handling
def imgur_getAlbum(submissionUrl, submissionId):
	htmlSource = requests.get(submissionUrl).text
	soup = BeautifulSoup(htmlSource, "html.parser")
	imageUrl = soup.select('[src*="i.imgur.com"]')

	success = True
	numInAlbum = 0
	#print(imageUrl)
	for img in imageUrl:
		fileName = submissionId + "-" + str(numInAlbum).zfill(2)
		success = success and getDirect("http:" + img['src'], fileName)
		numInAlbum += 1
	
	return success

# Returns true if request is valid
def getDirect(imageUrl, submissionId):
	print("getting " + imageUrl)
	response = requests.get(imageUrl)
	if (response.status_code == 200):
		fileName = submissionId + getFileExt(imageUrl)
		download(response, fileName)
		return True
	return False

def download(response, fileName):
	with open(fileName, 'wb') as fo:
		fo.write(response.content)

# Changes ".gifv" ending urls to ".mp4"
def gifvToMp4(url):
	newUrl = url[:url.rfind('.')] + ".mp4"
	return newUrl

# Changes gyfcat urls to direct .mp4 links
def gyfcatToMp4(url):
	left = url[:url.find('g')]
	middle = url[url.find('g'):]
	newUrl = left + "giant." + middle + ".mp4"
	print(newUrl)
	return newUrl

# Returns the file extension of direct urls
def getFileExt(imageUrl):
	return imageUrl[imageUrl.rfind('.'):]

# ---------- Main ----------
reddit = initReddit()
#downloadedFraction = getTop("aww", "week", 10, "./")

print("-" * 40)
print(downloadedFraction + " downloaded\n")

