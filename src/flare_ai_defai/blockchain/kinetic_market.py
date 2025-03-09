"""
Module for reading and writing in Kinetic Market.

It will be able to handle supplying, borrowing, and staking.
"""

from dataclasses import dataclass

import structlog
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams

from flare_ai_defai.blockchain import FlareExplorer


logger = structlog.get_logger(__name__)


class KineticMarket:
    """
    """
    CONTRACT_ADDRESS = "0x12e605bc104e93B45e1aD99F9e555f659051c2BB"

    def __init__(self, web3_provider_url: str, flare_explorer: FlareExplorer) -> None:
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
        self.contract = self.getContract(self.CONTRACT_ADDRESS)
        

    def getContract(self, address: msg) -> void:
        abi = self.flare_explorer.get_contract_abi(self.CONTRACT_ADDRESS)
        self.contract = Web3.eth.contract(address=self.CONTRACT_ADDRESS, abi=abi)

    def getBuyInFee(self) -> int:
        # Connect to Flare network
        web3 = Web3(Web3.HTTPProvider(self.web3_provider_url))

        if not web3.is_connected():
            raise Exception("Failed to connect to Flare blockchain")

        print("Connected to Flare Blockchain!")

        

        print("Available Functions:")
        for func in self.contract.functions:
            print("-", func)
            
        # Call a function on the contract
        result = self.contract.functions.buyInStakingFee().call()
        print("Contract function result:", result)
        
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
        
        def borrowUSDC():
            """
            When you click to borrow you sign a transaction request with 29B8.
            This interacts with a borrow() function
            https://flarescan.com//tx/0x91b3d1e4c4178d05914f05c13d47ee3c2869087b0a7ef7a9b636f8e8ad759f19
            
            
            """

        def borrowUSDT():
            """
            When you click to borrow you sign a transaction request with 93bb.
            This interacts with a borrow() function
            https://flarescan.com//tx/0xfaff5427e53996a324e81357b1eb9eef430ba5e210f0973f46719f2066510d6d
            
            """

        def stakeJoule():
            













    def reset(self) -> None:
        """
        Reset the provider state by clearing account details and transaction queue.
        """
        self.address = None
        self.private_key = None
        self.tx_queue = []
        self.logger.debug("reset", address=self.address, tx_queue=self.tx_queue)

    def add_tx_to_queue(self, msg: str, tx: TxParams) -> None:
        """
        Add a transaction to the queue with an associated message.

        Args:
            msg (str): Description of the transaction
            tx (TxParams): Transaction parameters
        """
        tx_queue_element = TxQueueElement(msg=msg, tx=tx)
        self.tx_queue.append(tx_queue_element)
        self.logger.debug("add_tx_to_queue", tx_queue=self.tx_queue)

    def send_tx_in_queue(self) -> str:
        """
        Send the most recent transaction in the queue.

        Returns:
            str: Transaction hash of the sent transaction

        Raises:
            ValueError: If no transaction is found in the queue
        """
        if self.tx_queue:
            tx_hash = self.sign_and_send_transaction(self.tx_queue[-1].tx)
            self.logger.debug("sent_tx_hash", tx_hash=tx_hash)
            self.tx_queue.pop()
            return tx_hash
        msg = "Unable to find confirmed tx"
        raise ValueError(msg)

    def generate_account(self) -> ChecksumAddress:
        """
        Generate a new Flare account.

        Returns:
            ChecksumAddress: The checksum address of the generated account
        """
        account = Account.create()
        self.private_key = account.key.hex()
        self.address = self.w3.to_checksum_address(account.address)
        self.logger.debug(
            "generate_account", address=self.address, private_key=self.private_key
        )
        return self.address

    def sign_and_send_transaction(self, tx: TxParams) -> str:
        """
        Sign and send a transaction to the network.

        Args:
            tx (TxParams): Transaction parameters to be sent

        Returns:
            str: Transaction hash of the sent transaction

        Raises:
            ValueError: If account is not initialized
        """
        if not self.private_key or not self.address:
            msg = "Account not initialized"
            raise ValueError(msg)
        signed_tx = self.w3.eth.account.sign_transaction(
            tx, private_key=self.private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.logger.debug("sign_and_send_transaction", tx=tx)
        return "0x" + tx_hash.hex()

    def check_balance(self) -> float:
        """
        Check the balance of the current account.

        Returns:
            float: Account balance in FLR

        Raises:
            ValueError: If account does not exist
        """
        if not self.address:
            msg = "Account does not exist"
            raise ValueError(msg)
        balance_wei = self.w3.eth.get_balance(self.address)
        self.logger.debug("check_balance", balance_wei=balance_wei)
        return float(self.w3.from_wei(balance_wei, "ether"))

    def create_send_flr_tx(self, to_address: str, amount: float) -> TxParams:
        """
        Create a transaction to send FLR tokens.

        Args:
            to_address (str): Recipient address
            amount (float): Amount of FLR to send

        Returns:
            TxParams: Transaction parameters for sending FLR

        Raises:
            ValueError: If account does not exist
        """
        if not self.address:
            msg = "Account does not exist"
            raise ValueError(msg)
        tx: TxParams = {
            "from": self.address,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "to": self.w3.to_checksum_address(to_address),
            "value": self.w3.to_wei(amount, unit="ether"),
            "gas": 21000,
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            "chainId": self.w3.eth.chain_id,
            "type": 2,
        }
        return tx
