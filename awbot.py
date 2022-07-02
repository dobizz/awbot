#!/usr/bin/env python3
import sys
import os
import time
import random
import pathlib
import http.client as httplib
from itertools import count
from plyer import notification
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

path = os.path.dirname(__file__)

# variable as condition to exit script
exit_sc = False

def _print_(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()

def main():
    global path, exit_sc

    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # check internet connection
    conn = httplib.HTTPConnection("1.1.1.1", timeout = 10)
    
    try:
        print("Internet check.")
        conn.request("HEAD", "/")
        conn.close()
        print("Internet available.")
    
    except KeyboardInterrupt:
        print("\nStopping bot.")
        exit_sc = True
        return
    
    except:
        conn.close()
        print("No Internet. Re-checking in 30 seconds.")
        for x in range(30):
            time.sleep(1)
            _print_(".")
        return

    # define game url
    url = "https://play.alienworlds.io"

    # wax signin page
    signin = "https://all-access.wax.io/"

    # for account.txt file
    try:
        # check for account.txt file
        if os.path.exists("account.txt"):
            # check for file size & read
            if os.stat("account.txt").st_size != 0:
                afile = open("account.txt", "r")
                wallet = afile.read()
                afile.close()

            # delete the file if found empty account.txt file
            else:
                print("\nDeleting corrupted \"account.txt\".")
                os.remove("account.txt")
                print("File deleted.")
                print("Restarting bot.")
                return

        # create account.txt file if not found
        else:
            anfile = open("account.txt", "w")
            anfile.write(input("\nPlease enter your wax wallet address: "))
            anfile.close()
            print("Restarting bot.")
            return
    
    except KeyboardInterrupt:
        print("\nStopping bot.")
        exit_sc = True
        return 

    except:
        print("\nBot encountered an error. Restarting.")
        return

    # check for sign.file file
    if os.path.exists("sign.file"):
        headless = True
        sign_file = True

    else:
        headless = False
        sign_file = False

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
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")

    # headless mode when signed in
    if headless:
        # to open in hidden browser window
        chrome_options.add_argument("--headless")

    # save current browsing session to make it persistent
    pwd = pathlib.Path().absolute()
    chrome_options.add_argument(f"--user-data-dir={pwd}\\chrome-data")

    # for older ChromeDriver under version 79.0.3945.16
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # for ChromeDriver version 79.0.3945.16 or over
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # instantiate Chrome driver with given Chrome options
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # instantiate stealth
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

        # save current window handle
        main_window = driver.current_window_handle
        
        # change page load timeout
        driver.set_page_load_timeout(60)

        # make GET request
        if headless:
            driver.get(url)

        else:
            driver.get(signin)
            driver.set_window_position(0, 0)

        print("\nSuccessfully loaded \"{}\".".format(driver.title))
    
    except TypeError:
        print("\nPlease update your selenium package.")
        exit_sc = True
        return
    
    except KeyboardInterrupt:
        print("\nStopping bot.")
        exit_sc = True
        return
    
    except:
        print("\nBot encountered an error. Restarting.")
        return

    try:
        # check for sign.file file
        if sign_file:
            print("\nStarting bot in 3 seconds. \n\t- Delete \"sign.file\" in case of re-login. \n\t- Press \"Ctrl + C\" to stop")
            for x in range(3):
                time.sleep(1)
                _print_(".")

        # create sign.file if not found
        else:
            driver.execute_script("""
                var wallet = arguments[0];
                document.title = wallet;
                alert(wallet);
            """, wallet)
            print("\nPausing bot.")
            notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Sign-in required.")
            input("Please sign-in, then press any key to continue.")
            open("sign.file", "a").close()
            print("Restarting bot.")
            return
    
    except KeyboardInterrupt:
        print("\nStopping bot.")
        exit_sc = True
        driver.quit()
        return

    except:
        print("\nBot encountered an error. Restarting.")
        return

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

            print("CPU: [ {:,} / {:,} ms ]\t\tUsed: {} %".format(cpu_used, cpu_max, cpu_pct))
            print("NET: [ {:,} / {:,} B ]\t\tUsed: {} %".format(net_used, net_max, net_pct))
            print("RAM: [ {:,} / {:,} B ]\t\tUsed: {} %".format(ram_used, ram_max, ram_pct))

            tlm_new = aw.tlm_balance

            # show balances
            print(f"\nWAX Balance: {aw.wax_balance:.4f}")

            # show tlm mined per click
            if i and tlm_old < tlm_new:
                try:
                    print(f"TLM Balance: {tlm_new:.4f}")
                    
                    # to find the value of tlm mined
                    tlm_mined = tlm_new - tlm_old
                    print(f"TLM mined in last claim: {tlm_mined:.4f}")
                    tlm_old = tlm_new

                    # to find average rate of tlm mining
                    tlm_sum += tlm_mined
                    avg = tlm_sum/mine_loop_count
                    print(f"Average rate for TLM mining: {avg:.4f}/claim")

                    # to show sum of tlm mined
                    print(f"Total TLM mined in this session: {tlm_sum:.4f}")

                except KeyboardInterrupt:
                    print("\nStopping bot.")
                    exit_sc = True
                    driver.quit()
                    return

                except:
                    print("\nUnable to retrieve the value(s).")

            # check for throttle.txt file
            if os.path.exists("throttle.txt"):

                # check for file size & read
                if os.stat("throttle.txt").st_size != 0:
                    tfile = open("throttle.txt", "r")
                    throttle = tfile.read()
                    tfile.close()

                    if throttle == "Y" or throttle == "y":
                        # resource utilization throttling
                        if (cpu_pct > resource_limit) or (ram_pct > resource_limit) or (net_pct > resource_limit):
                            print("\nResource utilization is above the set threshold of {} %.".format(resource_limit))
                            print("Sleeping for {} seconds.".format(resource_sleep))
                            for x in range(resource_sleep):
                                time.sleep(1)
                                _print_(".")
                            continue
                    
                    elif throttle == "N" or throttle == "n":
                        print("\nResource utilization throttling is OFF. Turn ON by changing value to \"N\" in the \"throttle.txt\" file.")

                    # delete the file if value found other than Y or N
                    else:
                        print("\nAppropriate input not found.")
                        print("Deleting corrupted \"throttle.txt\".")
                        os.remove("throttle.txt")
                        print("File deleted.")
                        print("Restarting bot.")
                        driver.quit()
                        return

                # delete the file if found empty throttle.txt file
                else:
                    print("\nDeleting corrupted \"throttle.txt\".")
                    os.remove("throttle.txt")
                    print("File deleted.")
                    print("Restarting bot.")
                    driver.quit()
                    return

            # create throttle.txt file if not found
            else:
                ntfile = open("throttle.txt", "w")
                ntfile.write(input("\nDo you want to enable the bot resource(s) throttling [Y/N]: "))
                ntfile.close()
                driver.quit()
                return

            # wait for mine button to be found
            print("\nWaiting for \"Mine\" button.")

            while True:
                # try to find mine button
                try:
                    mine_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Mine')]")

                # if button is not found
                except NoSuchElementException:
                    time.sleep(1)
                    _print_(".")

                except KeyboardInterrupt:
                    print("\nStopping bot.")
                    exit_sc = True
                    driver.quit()
                    return

                # if button is found, then click
                else:
                    print("\nFound \"Mine\" button!")

                    # full page screenshot
                    total_width = driver.execute_script("return document.body.offsetWidth")
                    total_height = driver.execute_script("return document.body.scrollHeight")
                    driver.set_window_size(total_width, total_height)
                    driver.save_screenshot("sc_main_mine.png")   # image will be saved as "sc_main_mine.png" in the bot's directory

                    mine_btn.click()
                    break

            # wait for claim button
            print("\nSearching for \"Claim\" button.")
            
            try:
                claim_btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Claim Mine')]")))
                print("Found \"Claim\" button!")

                # full page screenshot
                total_width = driver.execute_script("return document.body.offsetWidth")
                total_height = driver.execute_script("return document.body.scrollHeight")
                driver.set_window_size(total_width, total_height)
                driver.save_screenshot("sc_main_claim.png")   # image will be saved as "sc_main_claim.png" in the bot's directory

                # click claim button
                claim_btn.click()
            
            except KeyboardInterrupt:
                print("\nStopping bot.")
                exit_sc = True
                driver.quit()
                return

            except:
                notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Script restarting. Unable to load or find \"Claim\" button.")
                print('\n\tUnable to load or find \"Claim\" button. Restarting.')
                driver.quit()
                return

            # wait for pop-up window
            print("\n\tSearching for pop-up window.")

            # to continue below while loop
            switch = False

            while True:                
                if switch:
                    break

                else:
                    this_window = None

                    # switch control to pop-up window
                    for this_window in driver.window_handles:
                        if this_window != main_window:
                            try:
                                print("\tSwitching to pop-up window.")
                                driver.switch_to.window(this_window)
                                print("\tSwitched successfully to \"{}\".".format(driver.title))

                            except KeyboardInterrupt:
                                print("\n\tStopping bot.")
                                exit_sc = True
                                driver.quit()
                                return
                            
                            except:
                                print("\n\tBot encountered an error. Restarting.")
                                driver.quit()
                                return                               

                            # to exit while loop
                            switch = True
                            break

            # for pop-up window click(s)
            try:
                # wait for approve button to be visible & click button
                btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Approve')]")))

                # if button found then it'll be clicked
                if btn:
                    print("\n\tFound \"Approve\" button!")

                    # full page screenshot
                    total_width = driver.execute_script("return document.body.offsetWidth")
                    total_height = driver.execute_script("return document.body.scrollHeight")
                    driver.set_window_size(total_width, total_height)
                    driver.save_screenshot("sc_popup_approve.png")   # image will be saved as "sc_popup_approve.png" in the bot's directory

                    btn.click()
                    print("\tApproving transaction.")
                    mine_loop_count += 1

            except KeyboardInterrupt:
                print("\n\tStopping bot.")
                exit_sc = True
                driver.quit()
                return

            except:
                try:
                    # wait for cancel button to be visible & click button
                    btn_can = WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Cancel')]")))

                    # if cancel button found then it'll be clicked
                    if btn_can:
                        print("\n\tFound \"Cancel\" button!")

                        # full page screenshot
                        total_width = driver.execute_script("return document.body.offsetWidth")
                        total_height = driver.execute_script("return document.body.scrollHeight")
                        driver.set_window_size(total_width, total_height)
                        driver.save_screenshot("sc_popup_can.png")   # image will be saved as "sc_popup_can.png" in the bot's directory

                        btn_can.click()
                        print("\tCancelling transaction.")

                except KeyboardInterrupt:
                    print("\n\tStopping bot.")
                    exit_sc = True
                    driver.quit()
                    return
                
                except:
                    try:
                        # wait for login button to be visible
                        btn_login = WebDriverWait(driver, 15).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Login')]")))

                        # if login button found then print message & restart
                        if btn_login:
                            notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Please \"Login\".")
                            
                            # full page screenshot
                            total_width = driver.execute_script("return document.body.offsetWidth")
                            total_height = driver.execute_script("return document.body.scrollHeight")
                            driver.set_window_size(total_width, total_height)
                            driver.save_screenshot("sc_popup_login.png")   # image will be saved as "sc_popup_login.png" in the bot's directory

                            os.remove("sign.file")
                            print("\n\tRestarting bot.")
                            driver.quit()
                            return

                    except KeyboardInterrupt:
                        print("\n\tStopping bot.")
                        exit_sc = True
                        driver.quit()
                        return

                    except:
                        notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Script restarting. Unable to load or find button(s).")
                        print('\n\tUnable to load or find button(s). Restarting.')
                        driver.quit()
                        return

            # go control back to main window
            print("\n\tSwitching back to main window.")
            driver.switch_to.window(main_window)
            print("\tSwitched successfully to \"{}\".".format(driver.title))
            time.sleep(3)

            # full page screenshot
            total_width = driver.execute_script("return document.body.offsetWidth")
            total_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(total_width, total_height)
            driver.save_screenshot("sc_main.png")   # image will be saved as "sc_main.png" in the bot's directory

            # show the number of loops done
            print(f"\nTotal number of execution(s): {loop_count}")

            # show the number of loops done
            print(f"Total number of approval(s): {mine_loop_count}")

            i = True

            # delay the bot before starting next loop
            delay = random.randint(delay_min, delay_max)
            print(f"\nSleeping for {delay} seconds.")
            for x in range(delay):
                time.sleep(1)
                _print_(".")
            print("Done sleeping.")

        except KeyboardInterrupt:
            print("\nStopping bot.")
            exit_sc = True
            driver.quit()
            return

        # if any error occured
        except:
            print("\nBot encountered an error. Restarting.")
            driver.quit()
            return

    # close the webdriver
    driver.quit()

while True:
    assert sys.version_info >= (3, 6), "Python 3.6+ required."

    try:
        if not exit_sc:
            # call main routine
            main()
        
        else:
            # notification for termination
            notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Script terminated.")
            print("\nScript terminated.")
            os._exit(0)

    except KeyboardInterrupt:
        # notification for termination
        notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Script terminated.")
        print("\nScript terminated.")
        os._exit(0)

    except:
        # notification for termination
        notification.notify(title = os.path.basename(path) + "\\" + os.path.basename(__file__), message = "Script unable to restart.")
        print("\nScript cannot be restarted due to an unknown error.")
        os._exit(0)
