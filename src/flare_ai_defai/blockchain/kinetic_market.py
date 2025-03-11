"""
Module for reading and writing in Kinetic Market.

It will be able to handle supplying, borrowing, and staking.
"""

from dataclasses import dataclass

import structlog
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from flare_ai_defai.blockchain import FlareExplorer, FlareProvider


logger = structlog.get_logger(__name__)


class KineticMarket:
    """
    """
    
    BORROW_ADDRESS = "0xDEeBaBe05BDA7e8C1740873abF715f16164C29B8"
    BORROW_ABI_ADDRESS = "0x10D5D2e68c347bF3aB1784CC6A41c664Ff7AEe56"
    
    SFLR_ADDRESS = "0x12e605bc104e93B45e1aD99F9e555f659051c2BB"
    SFLR_ABI_ADDRESS = "0x21c8F8DEf0A82000558EB5ceB5d5887AdFFb6256"
    
    SFLR_ABI = [{
        "inputs": [],
        "name": "submit",
        "outputs": [
        {
            "internalType": "uint256",
            "name": "",
            "type": "uint256"
        }
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [
        {
            "internalType": "uint8",
            "name": "",
            "type": "uint8"
        }
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [
        {
            "internalType": "address",
            "name": "spender",
            "type": "address"
        },
        {
            "internalType": "uint256",
            "name": "amount",
            "type": "uint256"
        }
        ],
        "name": "approve",
        "outputs": [
        {
            "internalType": "bool",
            "name": "",
            "type": "bool"
        }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }]

    def __init__(self, web3_provider_url: str, flare_explorer: FlareExplorer, flare_provider: FlareProvider) -> None:
        """
        Args:
            web3_provider_url (str): URL of the Web3 provider endpoint
        """
        self.address: ChecksumAddress | None = None
        self.private_key: str | None = None
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url)) 
        self.logger = logger.bind(router="kinetic_market")
        self.web3_provider_url = web3_provider_url
        self.flare_explorer = flare_explorer
        self.flare_provider = flare_provider
        
        #self.swapFLRtoSFLR(2, "0xe016EEb29Af76c379a4F2Bb3D71A05D70Efbc8A3")
        
        #d = {"token": "FLR", "collateral": "USDC", "amount": 0.01}
        #self.borrowUSDC(d)
        

    def getContract(self, address: str, abi_address: str) -> Contract:
        abi = self.flare_explorer.get_contract_abi(abi_address)
        return self.w3.eth.contract(address=address, abi=abi)

    def getBuyInFee(self) -> int:
        # Use the existing Web3 instance
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Flare blockchain")

        self.logger.debug("Connected to Flare Blockchain!")

        self.logger.debug("Available Functions:", functions=[func.fn_name for func in self.contract.functions])
        
        # Call a function on the contract
        contract = self.getContract(self.BORROW_ADDRESS, self.BORROW_ABI_ADDRESS)
        result = contract.functions.buyInStakingFee().call()
        self.logger.debug("Contract function result:", result=result)
        
        return result

    def supplySFLR():
        """
        To supply FLR or WFLR you need to be staked and converted to sFLR via Sceptre Protocol. 
        By supplying sFLR you can receive FlareDrops and Delegation.
        
        This interaction first makes sFLR from FLR, then supply it. 
        
        With supply to collateral disabled:
        
        When you click that you want to convert using Sceptre, you are asked to confirm an interaction with c2BB. Using 1.6 FLR
        https://flarescan.com/tx/0xb76cdb2c6aaed2afebd7df357fb4fb86c1bc5d5d1b41b80a31006a253bc53b4b
        
        Then you click 'Supply sFLR' you sign a spending cap transaction with c2BB
        https://flarescan.com//tx/0xaa331c2537dadb5ddeb5f46c2f5b7303ac28f2a223efee5a3f3ae627a7d0328a
        
        Then immediately you sign a transaction request with 5656. This mints ksFLR.
        https://flarescan.com//tx/0x2a4d05c71a193034194a298efe1ead7a54771101895614b0fd2bc91672c3cd04
        
        With supply to collateral enabled:
        
        When you click to enable collateral, you a prompted with a transaction request with D7c8
        https://flare-explorer.flare.network/tx/0x932afc8d9b25be90854d8a22e00e930f6ba2bd430515df8108a555b6684dee9b
        
        You then click to convert you FLR to sFLR
        https://flarescan.com//tx/0x4c1a149336ea3e581d99520d54aab6e69ff600ec1c6be9d929fa42cd0744dba9
        
        Then you confirm spending cap request with c2BB
        https://flarescan.com//tx/0xfccab2077c361a1a0759bc41456c66b645d13c371529767e64d6ae683049536f
        
        Then transaction request
        https://flare-explorer.flare.network/tx/0x87345aaabd6d2ca19730c2dad62e617272200a1a0fdf2ebc31d2fb413d1ae4ae
        
        """
        pass
    
    def swapFLRtoSFLR(self, amount: float, spender: str = None):
        if not self.w3.is_connected():
            raise Exception("Not connected to Flare blockchain")
        
        contract = self.w3.eth.contract(address=self.SFLR_ADDRESS, abi=self.SFLR_ABI)

        # Get decimals (typically 18 for FLR/sFLR)
        decimals = contract.functions.decimals().call()
        self.logger.debug("Fetched decimals", decimals=decimals)
        
        # Convert amount to wei
        amount_wei = int(amount * pow(10,decimals))
        self.logger.debug("Converted amount to wei", amount=amount, amount_wei=amount_wei)
        
        # Check balance
        balance = self.w3.eth.get_balance(self.flare_provider.address)
        if balance < amount_wei:
            raise ValueError(f"Insufficient balance: {self.w3.from_wei(balance, 'ether')} FLR, required: {amount} FLR")
        
        # Fetch current nonce
        current_nonce = self.w3.eth.get_transaction_count(self.flare_provider.address)
        
        # Create submit transaction with value
        tx1 = self.flare_provider.create_contract_function_tx(
            contract, "submit", 0, value=amount_wei
        )
        tx2 = self.flare_provider.create_contract_function_tx(
            contract, "approve", 1, spender, amount_wei
        )
        
        # Add to queue and send
        self.flare_provider.add_tx_to_queue("Swapping FLR to sFLR", [tx1, tx2])
        tx_hashes = self.flare_provider.send_tx_in_queue()
        
        return tx_hashes
        
        
    def borrowUSDC(self,user_order: dict):
        """
        When you click to borrow you sign a transaction request with 29B8.
        This interacts with a borrow() function
        https://flarescan.com//tx/0x91b3d1e4c4178d05914f05c13d47ee3c2869087b0a7ef7a9b636f8e8ad759f19
        """
        token = user_order["token"]
        collateral = user_order["collateral"]
        amount = user_order["amount"]
        
        contract = self.getContract(self.BORROW_ADDRESS, self.BORROW_ABI_ADDRESS)
        #for function in contract.functions:
        #    print(function)
        decimals = contract.functions.decimals().call()
        result = contract.functions.borrow(int(pow(10,decimals)*amount)).call()
        print(result)

    def borrowUSDT():
        """
        When you click to borrow you sign a transaction request with 93bb.
        This interacts with a borrow() function
        https://flarescan.com//tx/0xfaff5427e53996a324e81357b1eb9eef430ba5e210f0973f46719f2066510d6d
        
        """
        pass

    def stakeJoule():
        pass


