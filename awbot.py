#!/usr/bin/env python3
import os
import sys
import json
import time
import random
import pathlib
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from timeit import default_timer as timer
from utils import download_chromedriver, has_chromedriver, Release


# set Chrome options
chrome_options = Options()
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-certificate-errors-spki-list')
chrome_options.add_argument('--ignore-ssl-errors')
# chrome_options.add_argument('--headless')
# save session
pwd = pathlib.Path().absolute()
chrome_options.add_argument(f"--user-data-dir={pwd}\\chrome-data")

# instantiate Chrome driver with given Chrome options
driver = webdriver.Chrome(
    options=chrome_options,
)

# change page load timeout
driver.set_page_load_timeout(10)

# save current window handle
main_window = driver.current_window_handle


class AlienWorlds:
    url = "https://play.alienworlds.io/"

    def __init__(self):
        self.federation_account = "federation"
        self.mining_account = "m.federation"
        self.hyperion_endpoints = ["https://api.waxsweden.org", "https://wax.eosrio.io"]
        # visit url
        driver.get(AlienWorlds.url)


    def login(self):
        """
        Calls javascript code to login user and saves wax account name to instance variable called account
        """
        driver.execute_script("""await server_login();""")
        time.sleep(3)
        # get wax user
        self.account = self.get_wax_user()


    def get_wax_user(self):
        """
        Calls javascript code to retrieve wax account name
        """
        wax = driver.execute_script('return wax;')
        return wax['userAccount']


    def get_bag(self) -> list:
        """
        Returns list containing the item details of player's bag
        """
        bag = driver.execute_script('var bag = await getBag("' + self.mining_account + '" , "' + self.account + '", wax.api.rpc, aa_api); return bag;')
        return bag


    def set_bag(self, bag:list):
        """
        Sets the bag of account with given list of items in bag argument
        """
        raise NotImplementedError
        if 0 <= len(bag) <= 3:
            driver.execute_script(f'await server_setBag("{self.account}", {bag})')


    def get_land(self) -> dict:
        """
        Returns dictionary containing details of current land
        """
        land = driver.execute_script(f'var data = await getLand("{self.federation_account}", "{self.mining_account}", "{self.account}", wax.api.rpc, aa_api); return data;')
        return land


    def get_balance(self) -> str:
        """
        Returns a string indicating the TLM balance of player's account
        """
        balance = driver.execute_script(f'var balance = await getBalance("{self.account}", wax.api.rpc); return balance;')
        return balance


    def get_mine_delay(self) -> int:
        """
        Returns an integer indicating the time in milliseconds before next allowable mine attempt
        """
        mine_delay = driver.execute_script(f'var minedelay = await getMineDelay("{self.account}"); return minedelay;')
        return mine_delay


    def get_bag_difficulty(self) -> int:
        """
        Returns an integer indicating the current bag difficulty
        """
        bag_difficulty = driver.execute_script(f'var difficulty = await getBagDifficulty("{self.account}"); return difficulty')
        return bag_difficulty


    def get_land_difficulty(self) -> int:
        """
        Returns an integer indicating the current land difficulty
        """
        land_difficulty = driver.execute_script(f'var difficulty = await getLandDifficulty("{self.account}"); return difficulty')
        return land_difficulty


    def get_difficulty(self) -> int:
        """
        Returns an integer indicating the current total difficulty
        """
        difficulty = self.get_bag_difficulty() + self.get_land_difficulty()
        return difficulty


    def get_last_mine_tx(self) -> str:
        """
        Returns the last mine transaction as a string
        """
        last_mine_tx = driver.execute_script(f'const last_mine_tx = await lastMineTx("{self.mining_account}", "{self.account}", wax.api.rpc); return last_mine_tx;')
        return last_mine_tx


    def claim(self, mine_work):
        """
        Submits the mine_work data to the wax.api for claiming
        """
        mine_data = {
            'miner': mine_work['account'],
            'nonce': mine_work['rand_str']
        }
        try:
            claimData = driver.execute_script(f'const claimData = await claim("{self.mining_account}","{self.account}", "active", {mine_data}, {self.hyperion_endpoints}, wax.api); return claimData;')
        except:
            pass
        else:
            print(claimData)
        finally:
            print('Finished claiming.')


    def mine(self, max_tries:int=10) -> dict:
        """
        Returns a dictionary containing the mine_work data from current mining transaction
        """
        while max_tries:
            try:
                mine_work = driver.execute_script('var mine = doWorkWorker({ mining_account: "' + self.mining_account + '", account: "'+ self.account + '", difficulty: ' + str(self.get_difficulty()) + ', last_mine_tx: "' + self.get_last_mine_tx() + '" }); return mine;')
            except:
                max_tries -= 1
            else:
                break
        return mine_work


    def get_bounty(self) -> str:
        """
        Returns a string containing the amount in TLM mined from the last mine transaction
        """
        bounty = driver.execute_script(f'const claimBounty = await getBountyFromTx("{self.get_last_mine_tx()}", "{self.account}", {self.hyperion_endpoints}); return claimBounty;')
        return bounty


def main():
    # create new AlienWorlds instance
    aw = AlienWorlds()

    time.sleep(5)

    # login to game
    print("Logging in to game...")
    aw.login()

    input("\n[Press ENTER to start]\n")
    # get bag details
    bag = aw.get_bag()

    # print bag details
    print(f"Bag:")
    for item in bag:
        asset_id = item['asset_id']
        name = item['data']['name']
        print(f'[{asset_id}]: {name}')

    # get land details
    land = aw.get_land()

    print(f'\nNow mining at {land["name"]} [{land["immutable_data"]["x"]}, {land["immutable_data"]["y"]}] owned by {land["owner"]}')
    print(f'Commission rate: {land["data"]["commission"] / 100:0.2f}%')

    # initialize total mined this session
    mined = 0.0

    delay = aw.get_mine_delay()

    input("\n[Press ENTER to continue]\n")

    # mining loop
    for _ in range(100):
        # get TLM balance
        tlm = aw.get_balance()
        print(f"Balance: {tlm}")

        if delay:
            wait_time = (delay / 1000)
            wait_time += random.randint(1, wait_time // 10)
            print(f'\n[Waiting for {wait_time} seconds]\n')
            time.sleep(wait_time)

        # start mining
        print('Mining...')
        t0 = timer()
        mine_work = aw.mine()
        t1 = timer()
        nonce = mine_work['rand_str']
        print(f"Nonce: {nonce} found after {t1 - t0:0.3f} seconds")

        # create new thread for claiming
        claim = Thread(target=aw.claim, args=(mine_work,))
        print('Claiming thread started.')
        claim.start()

        time.sleep(1)

        print('Trying to find new window.')
        # find window of pop-up and switch to that window
        for this_window in driver.window_handles:
            if this_window != main_window:
                print('Switching to new window.')
                driver.switch_to.window(this_window)
                break

        # wait for approve button to be visible and click button
        btn = WebDriverWait(driver, 60).until(ec.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Approve')]")))
        if btn:
            print('Found Approve button.')
            btn.click()
            print('Approving transaction.')
        else:
            raise IOError('Unable to load or find approve button.')

        # go back to main window
        print('Switching back to main window.')
        driver.switch_to.window(main_window)

        print('Claiming done.')

        bounty = aw.get_bounty()
        delay = aw.get_mine_delay()
        print(f'Mined: {bounty}\nTime to next mine: {delay / 1000} seconds')
        amount, unit = bounty.split()
        amount = float(amount)
        mined += amount
        print(f'Total mined this session: {mined} TLM')


if __name__ == '__main__':
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'

    # check if chromedriver is present and download if needed
    if not has_chromedriver():
        # change to Release.BETA to use beta releases
        # change to Release.STABLE to use stable releases
        download_chromedriver(Release.AUTO_DETECT)

    # call main routine
    main()
