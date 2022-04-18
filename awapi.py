import logging
import requests
from requests.exceptions import ReadTimeout


class Account:

    HTTP_TIMEOUT = 10

    def __init__(self, account_name) -> None:
        self.account = account_name
        self._session = requests.Session()
        self._session.headers.update(
            {
                'origin': 'https://wax.bloks.io',
                'referer': 'https://wax.bloks.io',
            }
        )

    def get_actions(self, pos:int=-1, offset:int=-100) -> dict:
        """
        Get list of actions related to the account in the wax blockchain.

        Returns dictionary with the list of actions, the current head block, and the last permanent block.
        """
        try:
            url = 'https://wax.greymass.com/v1/history/get_actions'
            json_payload = {
                'account_name': self.account,
                'pos': pos,
                'offset': offset,
            }
            reply = self._session.post(url, json=json_payload, timeout=Account.HTTP_TIMEOUT)
        except ReadTimeout:
            url= f'https://wax.eosrio.io/v2/history/get_actions?account={self.account}&skip=0&limit={abs(offset)}&sort=desc'
            reply = self._session.get(url, timeout=Account.HTTP_TIMEOUT)
        assert reply.status_code == 200
        return reply.json()

    def get_balance(self, contract:str, currency:str) -> float:
        """
        Gets the account balance for the given contract and currency.

        Returns the current balance as a float.
        """
        json_payload = {
            'code': contract,
            'account': self.account,
            'symbol': currency,
        }
        try:
            url = 'https://wax.greymass.com/v1/chain/get_currency_balance'
            reply = self._session.post(url, json=json_payload, timeout=Account.HTTP_TIMEOUT)
        except ReadTimeout:
            url = 'https://chain.wax.io/v1/chain/get_currency_balance'
            reply = self._session.post(url, json=json_payload, timeout=Account.HTTP_TIMEOUT)
        assert reply.status_code == 200
        balance = float(reply.json()[0].split()[0])
        return balance

    def get_account(self) -> dict:
        """
        Gets the instance account details and returns the data as a dictionary.
        """
        json_payload = {
            'account_name': self.account,
        }
        try:
            url = 'https://wax.greymass.com/v1/chain/get_account'
            reply = self._session.post(url, json=json_payload, timeout=Account.HTTP_TIMEOUT)
        except ReadTimeout:
            url = 'https://wax.eosrio.io/v1/chain/get_account'
            reply = self._session.post(url, json=json_payload, timeout=Account.HTTP_TIMEOUT)
        assert reply.status_code == 200
        return reply.json()

    def get_tokens(self) -> list:
        """
        Gets and returns the list of tokens held by the instance account.
        """
        url = f'https://wax.eosrio.io/v2/state/get_tokens?account={self.account}'
        reply = self._session.get(url, timeout=Account.HTTP_TIMEOUT)
        assert reply.status_code == 200
        data = reply.json()
        assert data['account'] == self.account
        return data['tokens']

    def get_chain_info(self) -> dict:
        """
        Gets the current block info and returns it as a dictionary.
        """
        try:
            url = 'https://chain.wax.io/v1/chain/get_info'
            reply = self._session.get(url, timeout=Account.HTTP_TIMEOUT)
            assert reply.status_code == 200
        except AssertionError:
            url = 'https://wax.eosrio.io/v1/chain/get_info'
            reply = self._session.get(url, timeout=Account.HTTP_TIMEOUT)
        assert reply.status_code == 200
        return reply.json()

    @property
    def last_action(self) -> dict:
        return self.get_actions(-1, -1)

    @property
    def wax_balance(self) -> float:
        return self.get_balance(contract='eosio.token', currency='wax')

    @property
    def tlm_balance(self) -> float:
        return self.get_balance(contract='alien.worlds', currency='tlm')

    @property
    def cpu_usage(self) -> dict:
        return self.get_account()['cpu_limit']

    @property
    def net_usage(self) -> dict:
        return self.get_account()['net_limit']

    @property
    def ram_usage(self) -> dict:
        account = self.get_account()
        max_ram = account['ram_quota']
        use_ram = account['ram_usage']
        free_ram = max_ram - use_ram
        return {
            'used': use_ram,
            'available': free_ram,
            'max': max_ram,
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    aw = Account(input("Enter wax account name: "))
    
    print("ACCOUNT:", aw.account)
    print("WAX:", aw.wax_balance)
    print("TLM:", aw.tlm_balance)
    print("CPU:", aw.cpu_usage)
    print("NET:", aw.net_usage)
    print("RAM:", aw.ram_usage)
    print("\nAccount Data:", aw.get_account())
    print("\nLast action:", aw.last_action)
    print("\nTokens:", aw.get_tokens())
    print("\nChain Info:", aw.get_chain_info())
