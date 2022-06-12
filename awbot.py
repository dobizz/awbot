#!/usr/bin/env python3
import re
import sys
import os
import time
import random
import pathlib
import http.client as httplib
from itertools import count
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import *
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from awapi import Account


def _print_(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def main():
    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # check internet connection
    conn = httplib.HTTPConnection("1.1.1.1", timeout = 5)
    try:
        print("Internet check.")
        conn.request("HEAD", "/")
        conn.close()
        print("Internet available.")
    except:
        conn.close()
        print("No Internet. Re-checking in 30 seconds.")
        for x in range(30):
            time.sleep(1)
            _print_(".")
        return

    # define game url
    url = "https://play.alienworlds.io"

    # check for account.txt file
    if os.path.exists("account.txt"):

        # check for file size
        if os.stat("account.txt").st_size != 0:
            file = open("account.txt", "r")
            wallet = file.read()
            file.close()

        # delete the file if found empty account.txt file
        else:
            print("\nDeleting corrupted \"account.txt\" file in the directory.")
            time.sleep(1)
            os.remove("account.txt")
            print("File deleted.")
            print("Restarting bot.")
            time.sleep(1)
            return

    # create account.txt file if not found
    else:
        nfile = open("account.txt", "w")
        nfile.write(input("\nPlease enter your wax wallet address: "))
        nfile.close()
        print("Restarting bot.")
        time.sleep(1)
        return

    # create AW Account instance
    aw = Account(wallet)

    # define range for loop delay
    delay_min = 60          # min delay before next loop
    delay_max = 300         # max delay before next loop

    # define resource threshold
    resource_limit = 100   # skip mining if resources are above the set limit
    resource_sleep = 30    # sleep for given time if there is not enough resources

    # set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--window-size=0,180")
    chrome_options.add_argument("--mute-audio")

    # when there is already a persistent session, you may activate headless mode
    # chrome_options.add_argument("--headless")

    # save current browsing session to make it persistent
    pwd = pathlib.Path().absolute()
    chrome_options.add_argument(f"--user-data-dir={pwd}\\chrome-data")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # instantiate Chrome driver with given Chrome options
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
    except TypeError:
        print("\nPlease update your selenium package.")
        driver.quit()
        sys.exit(0)

    # change page load timeout
    driver.set_page_load_timeout(60)

    # instantiate stealth
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

    # check for sign.file file
    if os.path.exists("sign.file"):
        print("\nStarting bot in 10 seconds.")
        for x in range(10):
            time.sleep(1)
            _print_(".")

    # create sign.file if not found
    else:
        print("\nPausing bot.")
        input("Please sign-in .Then, press any key to continue.")
        open("sign.file", "a").close()

    print("\nStarting bot, press \"Ctrl + C\" to stop.")

    # initialize mine loop count
    mine_loop_count = 0

    # load tlm balance
    tlm_old = aw.tlm_balance

    # initialize tlm_sum
    tlm_sum = 0

    # activation switch for checking tlm mined per click
    i = False

    # main bot loop
    for loop_count in count(1):
        # clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            # fetch cpu usage details
            cpu_usage = aw.cpu_usage
            cpu_max = cpu_usage['max']
            cpu_used = cpu_usage['used']
            cpu_pct = int(cpu_used / cpu_max * 100)

            # fetch ram usage details
            ram_usage = aw.ram_usage
            ram_max = ram_usage['max']
            ram_used = ram_usage['used']
            ram_pct = int(ram_used / ram_max * 100)

            # fetch net usage details
            net_usage = aw.net_usage
            net_max = net_usage['max']
            net_used = net_usage['used']
            net_pct = int(net_used / net_max * 100)

            print("CPU: [ {:,} / {:,} ms ]\tUsed: {} %".format(cpu_used, cpu_max, cpu_pct))
            print("NET: [ {:,} / {:,} B ]\tUsed: {} %".format(net_used, net_max, net_pct))
            print("RAM: [ {:,} / {:,} B ]\tUsed: {} %".format(ram_used, ram_max, ram_pct))

            # show balances
            print(f"\nWAX Balance: {aw.wax_balance}")
            print(f"TLM Balance: {aw.tlm_balance}")

            # show tlm mined per click
            if i:
                try:

                    # to find the value of tlm mined
                    tlm_new = aw.tlm_balance
                    tlm_mined = tlm_new - tlm_old
                    print(f"TLM mined on last claim: {tlm_mined:.4f}")
                    tlm_old = tlm_new

                    # to find average rate of tlm mining
                    tlm_sum += tlm_mined
                    average = tlm_sum/mine_loop_count
                    print(f"Average rate for TLM mining: {average:.4f}/claim")
                except:
                    print("\nUnable to show the average rate & the difference between the claims.")

            if (cpu_pct > resource_limit) or (ram_pct > resource_limit) or (net_pct > resource_limit):
                print("\nResource utilization is above the set threshold of {} %.".format(resource_limit))
                print("Sleeping for {} seconds.".format(resource_sleep))
                for x in range(resource_sleep):
                    time.sleep(1)
                    _print_(".")
                continue

            # wait for mine button to be found
            print("\nWaiting for \"Mine\" button.")

            while True:
                # try to find mine button
                try:
                    mine_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Mine')]")

                except KeyboardInterrupt:
                    print("\nStopping bot.")
                    driver.quit()
                    sys.exit(0)

                # if button is not found
                except NoSuchElementException:
                    time.sleep(1)
                    _print_(".")

                # if button is found
                else:
                    print("\nFound \"Mine\" button!")

                    # click
                    mine_btn.click()
                    break

            # wait for claim button
            print("\nSearching for \"Claim\" button.")
            claim_btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Claim Mine')]")))
            print("Found \"Claim\" button!")

            # click claim button
            claim_btn.click()

            # wait for pop-up window
            print("\n\tSearching for pop-up window.")
            time.sleep(3)

            # switch control to pop-up window
            for this_window in driver.window_handles:
                if this_window != main_window:
                    print("\tSwitching to pop-up window.")
                    driver.switch_to.window(this_window)
                    break

            # wait for approve button to be visible & click button
            btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Approve')]")))

            # if approve button is found
            if btn:
                print("\n\tFound \"Approve\" button!")
                btn.click()
                print("\tApproving transaction.")
                mine_loop_count += 1

            # if approve button could not be found
            else:
                raise IOError('\n\tUnable to load or find approve button.')

            # go control back to main window
            print("\n\tSwitching back to main window.")
            driver.switch_to.window(main_window)

            # show the number of loops done
            print(f"\nTotal number of execution(s): {loop_count}")

            # show the number of loops done
            print(f"Total number of approval(s): {mine_loop_count}")

            # delay the bot before starting next loop
            delay = random.randint(delay_min, delay_max)
            print(f"\nSleeping for {delay} seconds.")
            for x in range(delay):
                time.sleep(1)
                _print_(".")
            print("Done sleeping.")
            i = True

        except KeyboardInterrupt:
            print("\nStopping bot.")
            driver.quit()
            sys.exit(0)

        # if any error occured
        except:
            print("\nBot encountered an error. Restarting.")
            return

    # close the webdriver & exit
    driver.quit()


while True:
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'

    # call main routine
    main()
