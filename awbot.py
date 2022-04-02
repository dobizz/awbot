#!/usr/bin/env python3
import os
import sys
import json
import time
import random
import pathlib
import platform
from itertools import count
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
from selenium_stealth import stealth
from utils import download_chromedriver, has_chromedriver


def _print_(text:str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def get_wax_balance(driver, account:str):
    script = """
    const val = await fetch(
        'https://chain.wax.io/v1/chain/get_table_rows', 
        {
            method: 'POST',
            body: JSON.stringify({
                'json': true,
                'code': 'eosio.token',
                'table': 'accounts',
                'scope': '""" + account + """',
                'limit': 1000
            }),  
            headers: {
                'Content-type': 'application/json; charset=UTF-8',
                'accept': 'application/json, text/plain, */*',
                'origin': 'https://wallet.wax.io',
                'referer': 'https://wallet.wax.io'  
            }
        }
    ).then(res => res.json());return val;
    """
    # execute JavaScript in chrome driver
    resp = driver.execute_script(script)
    assert "rows" in resp
    return resp["rows"][0]["balance"]


def get_tlm_balance(driver, account:str):
    script = """
    const val = await fetch(
        'https://chain.wax.io/v1/chain/get_table_rows', 
        {
            method: 'POST',
            body: JSON.stringify({
                'json': true,
                'code': 'alien.worlds',
                'table': 'accounts',
                'scope': '""" + account + """',
                'limit': 1000
            }),  
            headers: {
                'Content-type': 'application/json; charset=UTF-8',
                'accept': 'application/json, text/plain, */*',
                'origin': 'https://wallet.wax.io',
                'referer': 'https://wallet.wax.io'  
            }
        }
    ).then(res => res.json());return val;
    """
    # execute JavaScript in chrome driver
    resp = driver.execute_script(script)
    assert "rows" in resp
    return resp["rows"][0]["balance"]


def get_account_stats(driver, account:str) -> dict:
    script = """
    const val = await fetch(
        'https://chain.wax.io/v1/chain/get_account', 
        {
            method: 'POST',
            body: JSON.stringify({account_name: '""" + account + """'}),  
            headers: {
                'Content-type': 'application/json; charset=UTF-8',
                'origin': 'https://wallet.wax.io',
                'referer': 'https://wallet.wax.io'  
            }
        }
    ).then(res => res.json());return val;
    """
    # execute JavaScript in chrome driver
    return driver.execute_script(script)


def main():
    # define game url
    url = "https://play.alienworlds.io"

    # define range for loop delay
    delay_min = 60          # min delay before next loop
    delay_max = 300         # max delay before next loop

    # define resource threshold
    resource_limit = 95     # skip mining if resources are above the set limit
    resource_sleep = 300    # sleep for given time if there is not enough resources

    # set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-ssl-errors")
    # when there is already a persistent session, you may activate headless mode
    # chrome_options.add_argument('--headless')

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # save current browsing session to make it persistent
    pwd = pathlib.Path().absolute()
    chrome_options.add_argument(f"--user-data-dir={pwd}\\chrome-data")

    # instantiate Chrome driver with given Chrome options
    driver = webdriver.Chrome(
    	service=Service(os.path.join(os.getcwd(), "chromedriver.exe" if platform.system() == "Windows" else "chromedriver")),
        options=chrome_options,
    )

    # change page load timeout
    driver.set_page_load_timeout(10)

    # instatiate stealth        
    stealth(
        driver,                
        languages=["en-US", "en"],                
        vendor="Google Inc.",                
        platform="Win32",                
        webgl_vendor="Intel Inc.",                
        renderer="Intel Iris OpenGL Engine",                
        fix_hairline=True,        
    )

    # save current window handle
    main_window = driver.current_window_handle

    # make GET request
    driver.get(url)

    account = input("Please enter account name (e.g abcde.wam): ")
    
    input("\nPlease login and press <ENTER> when ready to Mine")

    print("\nStarting bot.\n")

    # main bot loop
    for loop_count in count(1):
        # fetch account stats
        stats = get_account_stats(driver, account)

        # cpu details
        cpu_max = stats["cpu_limit"]["max"]
        cpu_used = stats["cpu_limit"]["used"]
        cpu_pct = int(cpu_used / cpu_max * 100)

        # ram details
        ram_max = stats["ram_quota"]
        ram_used = stats["ram_usage"]
        ram_pct = int(ram_used / ram_max * 100)

        # net details
        net_max = stats["net_limit"]["max"]
        net_used = stats["net_limit"]["used"]
        net_pct = int(net_used / net_max * 100)

        # line width
        width = 80

        print("=" * width)
        print("CPU: [ {:,} / {:,} ms ]\t\t\tUsed: {} %".format(cpu_used, cpu_max, cpu_pct))
        print("NET: [ {:,} / {:,} B ]\t\t\tUsed: {} %".format(net_used, net_max, net_pct))
        print("RAM: [ {:,} / {:,} B ]\t\t\tUsed: {} %".format(ram_used, ram_max, ram_pct))
        print("=" * width)

        # get balances
        wax = get_wax_balance(driver, account)
        tlm = get_tlm_balance(driver, account)
        
        # show balances
        print("WAX Balance:", wax)
        print("TLM Balance:", tlm)

        if (cpu_pct > resource_limit) or (ram_pct > resource_limit) or (net_pct > resource_limit):
            print("\nResource utilization is above the set threshold of {} %".format(resource_limit))
            print("\nSleeping for {} seconds\n".format(resource_sleep))
            time.sleep(resource_sleep)
            continue        

        # wait for mine button to be found
        print("\nWaiting for Mine button")

        while True:
            _print_(".")
            # try to find mine button
            try:
                mine_btn = driver.find_element(By.XPATH, '//*[text()="Mine"]')

            # if button is not found
            except NoSuchElementException:
                time.sleep(1)

            # if button is found
            else:
                _print_(":")
                print("\nFound Mine button!")
                # click
                mine_btn.click()
                break

        # wait for claim button
        claim_btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, '//*[text()="Claim Mine"]')))
        print("Found Claim button!")

        # click claim button
        claim_btn.click()

        # pause for 3 seconds
        time.sleep(3)

        # switch control to pop-up window
        for this_window in driver.window_handles:
            if this_window != main_window:
                print('\n\tSwitching to new window.')
                driver.switch_to.window(this_window)
                break

        # wait for approve button to be visible and click button
        btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Approve')]")))

        # if approve button is found
        if btn:
            print('\tFound Approve button.')
            btn.click()
            print('\tApproving transaction.')

        # if approve button could not be found
        else:
            raise IOError('\tUnable to load or find approve button.')

        # go control back to main window
        print('\tSwitching back to main window.\n')
        driver.switch_to.window(main_window)

        # show the number of loops done
        print(f"Total runs: {loop_count}")

        # delay the bot before starting next loop
        delay = random.randint(delay_min, delay_max)
        print(f"\nSleeping for {delay} seconds.")
        time.sleep(delay)
        print("\nDone sleeping.\n")


if __name__ == '__main__':
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'

    # check if chromedriver is present and download if needed
    if not has_chromedriver():
        # change to Release.BETA to use beta releases
        # change to Release.STABLE to use stable releases
        download_chromedriver()

    # call main routine
    main()

