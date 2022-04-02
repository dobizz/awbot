#!/usr/bin/env python3
import os
import re
import time
import stat
import logging
import subprocess
import platform
import urllib.parse
import requests
from lxml import html
from zipfile import ZipFile 

logging.basicConfig(
    format="[%(asctime)s] %(levelname)8s | %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)

def has_chromedriver() -> bool:
    '''Check if chromedriver is present in current directory'''
    executable = 'chromedriver.exe' if platform.system() == 'Windows' else 'chromedriver'
    return os.path.exists(executable)


def download_chromedriver() -> None:
    '''Download released chromedriver'''
    url = 'https://chromedriver.chromium.org/downloads/'
    logging.debug(url)

    # get link to releases
    logging.info('Checking available versions.')
    page = requests.get(url)
    tree = html.fromstring(page.content)

    # select html element of release
    installed_version = check_system_chrome_version()

    # if chrome is not installed exit
    if installed_version is None:
        logging.error("Chrome is not installed")
        return

    search_str = '.'.join(installed_version.split('.')[:-1])
    version = re.search(rf'{search_str}.\d+', page.text).group()

    logging.debug(f'Version: {version}')

    sys_platform = platform.system()
    
    # Set chromedriver download filename based on system platform
    # Linux
    if sys_platform == 'Linux':
        filename = 'chromedriver_linux64.zip'
    # Windows
    elif sys_platform == 'Windows':
        filename = 'chromedriver_win32.zip'
    # Mac
    else:
        filename = 'chromedriver_mac64.zip'

    # build download url
    url = urllib.parse.urljoin(f'https://chromedriver.storage.googleapis.com/{version}/', filename)

    # select executable based on system platform
    executable = 'chromedriver.exe' if sys_platform == 'Windows' else 'chromedriver'

    # check if executable exists and rename old files
    if has_chromedriver():
        src = executable
        dst = f'backup_{int(time.time())}_{executable}'
        os.rename(src, dst)

    # download zip file
    logging.info(f'Downloading: {url}')
    reply = requests.get(url)
    with open(filename, 'wb') as chunk:
        chunk.write(reply.content)
    logging.info('Download complete.')

    # unzip downloaded file
    with ZipFile(filename, 'r') as zip:
        logging.info(f'Extracting: {filename}\n')
        zip.printdir()
        zip.extractall()
        print()

    # set file permissions for Linux/Mac
    if sys_platform != 'Windows':
        # chmod 774 chromedriver
        os.chmod(executable, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)

    # delete zip file
    logging.info('Cleaning up')
    os.remove(filename)

    logging.info('Done!')


def check_system_chrome_version() -> str:
    sys_platform = platform.system()

    # Windows
    if sys_platform == 'Windows':
        try:
            if os.path.exists("C:\Program Files (x86)\Google\Chrome"):
                path = "C:\Program Files (x86)\Google\Chrome"
            elif os.path.exists("C:\Program Files\Google\Chrome"):
                path = "C:\Program Files\Google\Chrome"
            else:
                logging.warning("Unable to find Chrome")
                path = input("Please input absolute path to Chrome installation (eg. C:\Program Files (x86)\Google\Chrome): ")
            cmd = f'dir /B/AD "{path}\Application"|findstr /R /C:"^[0-9].*\..*[0-9]$"'
            logging.debug(cmd)
            version = subprocess.check_output(cmd, shell=True).decode().strip()
        except subprocess.CalledProcessError:
            version = None
    # Linux/Mac
    else:
        cmd = 'google-chrome --version'
        try:
            version = os.popen(cmd).read().strip().split()[-1]
        except IndexError:
            version = None
    return version


if __name__ == '__main__':
    logging.info(f'Installed Chrome version: {check_system_chrome_version()}')
    download_chromedriver()
