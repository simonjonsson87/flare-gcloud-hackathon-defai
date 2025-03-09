"""
Module for reading and writing in sparkDEX.

It will be able to handle swaps.
"""

from dataclasses import dataclass

import structlog
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams

from flare_ai_defai.blockchain import FlareExplorer


logger = structlog.get_logger(__name__)


class SparkDEX:
    
    def swapFLRforJOULE():
        """
        When you click Swap, you signa transaction request with 15D3 (named Sparkdex V2: Universal Router).
        This interacts with the execute function.
        https://flarescan.com/tx/0x97fe7283ececc166d8244884bff45b9a9e5b6ca52f7792f36c0a789be60dfcb1
        
        
        """
        
    def swapFLRforflrETH():
        """
        When you click Swap, you signa transaction request with 15D3 (named Sparkdex V2: Universal Router).
        This interacts with the execute function. This actually swaps FLR for WFLR, then WFLR for sFLR and finally 
        sFLR for flrETH.
        https://flarescan.com/tx/0x42fac59b66b9725f70850ea1ab08c7d57762bec067b20ce72b587cf0b1fb1a84
        
        
        """        