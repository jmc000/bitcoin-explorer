import requests
import json
import os
import logging

from dotenv import load_dotenv
from contextlib import contextmanager
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import HTTPError

# ------------------------------------------------------------
class GetBlockClient:
    """ Shared GetBlock JSON-RPC setup """
    def __init__(self):
        self._headers = {
            'Content-Type': 'application/json'
        }
        self._payload = {
            "jsonrpc": "2.0",
            "id": "getblock.io"
        }
        self._rpc_url = None
        self._retries = Retry(total=5, backoff_factor=1)
        self._session = self._create_session()
        logging.basicConfig(filename="output.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    
    @property
    def rpc_url(self) -> str:
        if self._rpc_url is None:
            load_dotenv()
            token = os.getenv('GETBLOCK_ACCESS_TOKEN')
            if not token:
                raise RuntimeError("Could not retrieve GetBlock Access Token — check .env file")
            self._rpc_url = f"https://go.getblock.io/{token}"
        return self._rpc_url
    
    @contextmanager
    def _fail_on_error(self):
        try:
            yield
        except (requests.exceptions.RequestException, OSError, RuntimeError, AttributeError) as e:
            logging.error(f"Error: {e}")
    
    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.mount('https://', HTTPAdapter(max_retries=self._retries))
        return s

    def call_rpc(self, verb: str, method: str, params: list = []):
        logging.info(f"Calling RPC:  {verb}  {method}  with params: {params}")
        with self._fail_on_error():
            payload = json.dumps({**self._payload, 'method': method, 'params': params})
            response = self._session.request(
                verb, 
                self.rpc_url, 
                headers=self._headers, 
                data=payload
            )
            response.raise_for_status()
            return response.json()['result']

# ------------------------------------------------------------
class Blocks(GetBlockClient):

    def get_block_hash(self, block_height: int):
        return self.call_rpc("POST", "getblockhash",[block_height])
    
    def get_block(self, hash: str, verbosity: int = 1):
        return self.call_rpc("POST", "getblock",[hash, verbosity])

class Transactions(GetBlockClient):
    def get_transaction(self, txid: str, verbose: bool = True):
        return self.call_rpc("POST", "getrawtransaction",[txid, verbose])

class BlockChainInfo(GetBlockClient):
    
    def get_blockchaininfo(self):
        return self.call_rpc("POST", "getblockchaininfo", [])   
    
    def get_current_difficulty(self):
        return self.get_blockchaininfo()['result']['difficulty']
    
    def get_last_block_height(self):
        return self.get_blockchaininfo()['result']['blocks']
    
    def get_last_header(self):
        return self.get_blockchaininfo()['result']['headers']
    
    def get_last_block_time(self):
        return self.get_blockchaininfo()['result']['time']


if __name__ == "__main__":
    
    ## Block Chain Info
    # bci = BlockChainInfo()
    # print(json.dumps(bci.get_blockchaininfo(), indent=2))
    # print(f"Current Difficulty: {bci.get_current_difficulty()}")
    # print(f"Last Header: {bci.get_last_header()}")
    # print(f"Last Block Height: {bci.get_last_block_height()}")
    # print(f"Last Block Time: {bci.get_last_block_time()}")

    ## Block
    block = Blocks()
    block_number = 957354
    block_hash = block.get_block_hash(block_number)
    print(f"Block Hash: {block_hash}")
    my_block = block.get_block(block_hash)
    print(f"Block: {my_block['confirmations']}")
    first_txid = my_block['tx'][3]
    print(f"First TXID: {first_txid}")

    ## Transaction
    transaction = Transactions()
    my_transaction = transaction.get_transaction(first_txid)
    print(json.dumps(my_transaction, indent=2))