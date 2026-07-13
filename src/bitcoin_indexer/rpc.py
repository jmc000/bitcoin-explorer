import requests
import json
import os

from dotenv import load_dotenv
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import HTTPError

import logger
import context_manager

logger = logger.setup_logging(__name__)

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


    @property
    def rpc_url(self) -> str:
        if self._rpc_url is None:
            load_dotenv()
            token = os.getenv('GETBLOCK_ACCESS_TOKEN')
            if not token:
                raise RuntimeError("Could not retrieve GetBlock Access Token — check .env file")
            self._rpc_url = f"https://go.getblock.io/{token}"
        return self._rpc_url

    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.mount('https://', HTTPAdapter(max_retries=self._retries))
        return s

    def call_rpc(self, verb: str, method: str, params: list = []):
        logger.info(f"Calling RPC:  {verb}  {method}  with params: {params}")
        with context_manager.fail_on_error():
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

