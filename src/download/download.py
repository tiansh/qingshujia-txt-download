import typing
import os
import sys
import re
import random
import json
import code
import time
import traceback
from urllib.parse import urlparse

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

FOLDER = 'download'
TIMEOUT, RETRY_TIMEOUT = 45, 10
MAX_RETRY_BOOK, MAX_RETRY_CHAPTER = 3, 10
CURSOR_FILE = len(sys.argv) > 1 and sys.argv[1] or 'cursor.txt'
PROXY_FILE = len(sys.argv) > 2 and sys.argv[2] or 'proxy.txt'
LOGIN_FILE = len(sys.argv) > 3 and sys.argv[3] or 'login.txt'
SLOW = False if len(sys.argv) > 4 and sys.argv[4] == 'fast' else True
FIREFOX_PATH = r'C:\Program Files\Mozilla Firefox\firefox.exe'
print(CURSOR_FILE, PROXY_FILE, LOGIN_FILE, SLOW)

with open(PROXY_FILE) as proxy_file:
    proxy = (
        proxy_file.readline().strip(),
        int(proxy_file.readline().strip()),
    )
    if not proxy[0] or not proxy[1]:
        sys.exit(-1)
with open(LOGIN_FILE) as login_file:
    username = login_file.readline().strip()
    password = login_file.readline().strip()
    if not username or not password:
        sys.exit(-1)


def setupDriver():
    options = Options()
    options.binary_location = FIREFOX_PATH
    options.set_preference('network.proxy.type', 1)
    options.set_preference('network.proxy.socks', proxy[0])
    options.set_preference('network.proxy.socks_port', proxy[1])
    options.set_preference('network.proxy.socks_remote_dns', True)
    options.set_preference('browser.tabs.closeWindowWithLastTab', False)
    driver = Firefox(options=options)
    driver.set_window_size(1024, 768)
    driver.set_script_timeout(600)
    return driver

def quitDriver(driver: WebDriver):
    print('Quit browser.')
    driver.quit()

def cleanUpPages(driver: WebDriver):
    windows = [*driver.window_handles]
    driver.switch_to.window(windows[0])
    driver.switch_to.new_window('tab')
    for window in windows:
        driver.switch_to.window(window)
        driver.close()
    driver.switch_to.window(driver.window_handles[0])

def isLogin(url: str):
    return urlparse(url).path == '/login'

def doLogin(driver: WebDriver, times = 0):
    print('Login website...')
    old_url = driver.current_url
    username_input, password_input = driver.find_elements(By.CSS_SELECTOR, 'form input')
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button = driver.find_element(By.CSS_SELECTOR, 'form button')
    login_button.click()
    try: WebDriverWait(driver, 60).until(lambda driver: driver.current_url != old_url)
    except:
        time.sleep(min(15 * times, 900))
        driver.refresh();
        doLogin(driver, times + 1)

def openUrl(url: str, newTab: bool = False, retry: int = 12):
    driver.switch_to.window(driver.window_handles[0])
    if newTab: driver.switch_to.new_window('tab')
    try: driver.get(url)
    except Exception as e:
        if not retry: raise e
        time.sleep(RETRY_TIMEOUT)
        openUrl(url, False, retry - 1)
    if isLogin(driver.current_url):
        try: doLogin(driver)
        except: pass
        if driver.current_url != url and not isLogin(url):
            openUrl(url, False, retry - 1)

def runFile(driver: WebDriver, filename: str):
    with open(filename, 'r', encoding='utf-8') as f:
        return driver.execute_async_script(f.read())

REG_INVALID_CHARACTERS = re.compile('[<>:\"/\\|?*\x00-\x1f]', re.IGNORECASE)
REG_INVALID_NAMES = re.compile('^(?=CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]$)', re.IGNORECASE)

def normalizeFilename(filename: str):
    filename = re.sub(REG_INVALID_CHARACTERS, '_', filename)
    if re.match(REG_INVALID_NAMES, filename):
        filename += '_'
    return os.path.join(FOLDER, filename + '.txt')

class DownloadException(Exception): pass

BookInfo = typing.TypedDict('BookInfo', { 'title': str, 'url': str, 'id': str })
def getList(driver: WebDriver, pageNum: int) -> typing.List[BookInfo]:
    lastException = None
    for i in range(MAX_RETRY_BOOK):
        try:
            openUrl(f'https://www.lightnovel.app/book/list/latest/{pageNum}')
            locator = (By.CSS_SELECTOR, 'main a[href^="/book/info/"]')
            WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located(locator))
            books: typing.List[BookInfo] = json.loads(runFile(driver, 'list.js'))
            return books
        except Exception as e:
            print('Exception while getting list: ' + str(e))
            traceback.format_exc()
            time.sleep(RETRY_TIMEOUT)
            if isLogin(driver.current_url): doLogin(driver)
            lastException = e
    else:
        raise lastException

ChapterInfo = typing.TypedDict('ChapterInfo', {
    'url': str,
    'title': str,
    'content': str,
})
BookInfoDetail = typing.TypedDict('BookInfoDetail', {
    'title': str, 'url': str, 'id': str, 'remark': str,
    'author': str, 'last_update': str, 'description': str,
    'chapters': typing.List[ChapterInfo],
})
def getBook(driver: WebDriver, book: BookInfoDetail) -> BookInfoDetail:
    print('>', book['id'], book['title'])
    locator = (By.CSS_SELECTOR, '.q-skeleton')
    next_chapter_locator = (By.CSS_SELECTOR, '.read-page + * > button:last-child')
    cleanUpPages(driver)
    openUrl(book['url'], True)
    lastException = None
    for retry in range(MAX_RETRY_BOOK):
        try:
            WebDriverWait(driver, TIMEOUT).until(EC.all_of(
                EC.invisibility_of_element(locator),
                EC.presence_of_element_located((By.CSS_SELECTOR, 'main .introduction'))
            ))
            if 'chapters' not in book:
                book.update(json.loads(runFile(driver, 'info.js')))
            break
        except Exception as e:
            print('Exception while getting book info: ' + str(e))
            traceback.format_exc()
            if isLogin(driver.current_url):
                doLogin(driver)
            driver.refresh()
            lastException = e
    else:
        driver.close()
        raise lastException
    empty_chapters = [chapter for chapter in book['chapters'] if chapter.get('content', None) is None]
    if not empty_chapters: return
    chapter_url = driver.current_url
    chapters = driver.find_elements(By.CSS_SELECTOR, 'main a[href^="/read/"]')
    next_chapter = next(chapter for chapter in chapters if chapter.get_attribute('href') == empty_chapters[0]['url'])
    done = False
    while not done:
        lastException = None
        for retry in range(MAX_RETRY_CHAPTER):
            try:
                if retry:
                    openUrl(chapter_url, True)
                else:
                    driver.execute_script(f'window.scrollTo(0, {next_chapter.get_attribute("offsetTop")})')
                    next_chapter.click()
                    WebDriverWait(driver, TIMEOUT).until(lambda driver: driver.current_url != chapter_url)
                    chapter_url = driver.current_url
                WebDriverWait(driver, TIMEOUT).until(EC.all_of(
                    EC.invisibility_of_element(locator),
                    EC.presence_of_element_located(next_chapter_locator)
                ))
                chapter = next(chapter for chapter in book['chapters'] if chapter['url'] == driver.current_url)
                print('    ' + str(retry or '.'), chapter['title'], end='\r')
                parse = json.loads(runFile(driver, 'parse.js'))
                if 'error' in parse: raise DownloadException(parse['error'])
                chapter['content'] = parse['result']
                print('    #', chapter['title'])
                if chapter is book['chapters'][-1]: done = True; break
                next_chapter = driver.find_element(*next_chapter_locator)
                break
            except Exception as e:
                print('Exception while getting book chapter: ' + str(e))
                traceback.format_exc()
                driver.close()
                time.sleep(RETRY_TIMEOUT)
                if isLogin(driver.current_url):
                    doLogin(driver)
                lastException = e
        else:
            raise lastException
    driver.close()
    return book

def toTxt(book: BookInfoDetail) -> str:
    return f"""{book['title']}
{book['url']}

作者：{book['author']}
更新日期：{book['last_update']}

简介

{book['description']}

""" + "".join(f"""
§ {chapter['title']}

{chapter['content']}
""" for chapter in book['chapters'])

def writeTxt(book: BookInfoDetail):
    txt = toTxt(book)
    filename = normalizeFilename(book['title'])
    with open(filename, 'w', encoding='utf-8-sig', newline='\r\n') as f:
        outbytes = f.write(txt)
    print('<', book['id'], book['title'], ':', outbytes, 'bytes')

def writeEmptyTxt(book: BookInfoDetail):
    filename = normalizeFilename(book['title'])
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f.write()
    print('E', book['title'])


def hasTxt(book: BookInfo):
    filename = normalizeFilename(book['title'])
    return os.path.isfile(filename)

def downloadBook(driver: WebDriver, book: BookInfoDetail):
    for retry in range(20):
        try:
            getBook(driver, book)
            writeTxt(book)
        except Exception as e:
            print('Exception while getting book: ' + str(e))
            traceback.format_exc()
            continue
        break
    if SLOW:
        time.sleep(10)

def downloadPage(driver: WebDriver, pageNum: int):
    print('PAGE', pageNum)
    cleanUpPages(driver)
    books = getList(driver, pageNum)
    for index, book in enumerate(books):
        if 'Level' in book['remark']: continue
        if hasTxt(book): continue
        print(':', 'PAGE', pageNum, 'BOOK', index + 1)
        try: downloadBook(driver, book)
        except Exception as e:
            print(e)
            pass

def lastFinished(page: int = None):
    if page:
        with open(CURSOR_FILE, 'w') as f: f.write(str(page))
    else:
        try:
            with open(CURSOR_FILE, 'r') as f:
                return int(f.readline())
        except:
            return 0

# driver = setupDriver()
# openUrl('https://www.lightnovel.app/login')
# for index, page in enumerate(range(70, 115)):
#     try: downloadPage(driver, page)
#     except Exception as e:
#         print(e)
#         time.sleep(120)
# quitDriver(driver)

# driver = setupDriver()
# openUrl('https://www.lightnovel.app/login')
for index, page in enumerate(range(1, 187)):
    if index % 10 == 0:
        if index: quitDriver(driver)
        driver = setupDriver()
        openUrl('https://www.lightnovel.app/login')
    for retry in range(10):
        try: downloadPage(driver, page)
        except Exception as e:
            print(e)
            time.sleep(120)
            continue
        break
    else: print(f'PAGE {page} FAIL')
    lastFinished(page)

quitDriver(driver)

# while True:
#     try: code.InteractiveConsole(locals=globals()).interact()
#     except: pass
