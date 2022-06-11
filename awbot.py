#!/usr/bin/env python3
import sys
import os
import time
import random
import pathlib
from itertools import count
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from awapi import Account


def _print_(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def main():
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
            print("\nDeleted.\nRestarting bot.")
            time.sleep(1)
            return

    # create account.txt file if not found
    else:
        nfile = open("account.txt", "w")
        nfile.write(input("\nPlease enter your wax wallet address: "))
        nfile.close()
        print("\nRestarting bot.")
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
    chrome_options.add_argument("--window-size=480,270")
    chrome_options.add_argument("--mute-audio")
    # when there is already a persistent session, you may activate headless mode
    # chrome_options.add_argument("--headless")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # save current browsing session to make it persistent
    pwd = pathlib.Path().absolute()
    chrome_options.add_argument(f"--user-data-dir={pwd}\\chrome-data")

    # instantiate Chrome driver with given Chrome options
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
    except TypeError:
        print("\nPlease update your selenium package.")
        driver.quit()
        sys.exit()

    # change page load timeout
    driver.set_page_load_timeout(60)

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

    # check for sign.file file
    if os.path.exists("sign.file"):
        print("\nStarting bot in 10 seconds.")
        time.sleep(10)

    # create sign.file if not found
    else:
        print("\nPausing bot.")
        input("\nPlease sign-in .Then, press any key to continue.")
        open("sign.file", "a").close()

    print("\nStarting bot, press \"Ctrl + C\" to stop.\n")

    # initialize crash count
    crashes = 0

    # main bot loop
    for loop_count in count(1):
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

            # line width
            width = 80

            print("=" * width)
            print("CPU: [ {:,} / {:,} ms ]\t\tUsed: {} %".format(cpu_used, cpu_max, cpu_pct))
            print("NET: [ {:,} / {:,} B ]\t\tUsed: {} %".format(net_used, net_max, net_pct))
            print("RAM: [ {:,} / {:,} B ]\t\tUsed: {} %".format(ram_used, ram_max, ram_pct))
            print("=" * width)

            # get balances
            wax = aw.wax_balance
            tlm = aw.tlm_balance

            # show balances
            print("\nWAX Balance: ", wax)
            print("\nTLM Balance: ", tlm)

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
                    mine_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Mine')]")

                except KeyboardInterrupt:
                    print("\nStopping bot.")
                    driver.quit()
                    sys.exit()

                # if button is not found
                except NoSuchElementException:
                    time.sleep(5)

                # if button is found
                else:
                    print("\nFound Mine button!")
                    # click
                    mine_btn.click()
                    break

            # wait for claim button
            claim_btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Claim Mine')]")))
            print("\nFound Claim button!")

            # click claim button
            claim_btn.click()

            # pause for 3 seconds
            time.sleep(3)

            # switch control to pop-up window
            for this_window in driver.window_handles:
                if this_window != main_window:
                    print("\n\tSwitching to new window.")
                    driver.switch_to.window(this_window)
                    break

            # wait for approve button to be visible and click button
            btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Approve')]")))

            # if approve button is found
            if btn:
                print("\n\tFound Approve button.")
                btn.click()
                print("\n\tApproving transaction.")

            # if approve button could not be found
            else:
                raise IOError('\n\tUnable to load or find approve button.')

            # go control back to main window
            print("\n\tSwitching back to main window.\n")
            driver.switch_to.window(main_window)

            # show the number of loops done
            print(f"\nTotal runs: {loop_count}")

            # delay the bot before starting next loop
            delay = random.randint(delay_min, delay_max)
            print(f"\nSleeping for {delay} seconds.")
            time.sleep(delay)
            print("\nDone sleeping.\n")

        except KeyboardInterrupt:
            print("\nStopping bot.")
            driver.quit()
            sys.exit()

        # if error occured
        except:
            crashes += 1
            print(f"\nBot encountered an error. {crashes} Total crashes since start.")
            
            # make GET request
            driver.get(url)

    # close the webdriver
    driver.quit()


while True:
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'

    # call main routine
    main()
