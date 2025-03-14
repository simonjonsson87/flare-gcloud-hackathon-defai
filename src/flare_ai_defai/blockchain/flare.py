"""
Flare Network Provider Module

This module provides a FlareProvider class for interacting with the Flare Network.
It handles account management, transaction queuing, and blockchain interactions.
"""

from dataclasses import dataclass

import structlog
import logging
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import TxParams
from web3.contract import Contract

from flare_ai_defai.models import UserInfo
from flare_ai_defai.storage.fake_storage import WalletStore

logging.basicConfig(level=logging.DEBUG)

@dataclass
class TxQueueElement:
    """
    Represents a transaction in the queue with its associated message.

    Attributes:
        msg (str): Description or context of the transaction
        tx (TxParams): Transaction parameters
    """

    msg: str
    confirm_msg: str
    txs: list[TxParams]


logger = structlog.get_logger(__name__)


class FlareProvider:
    """
    Manages interactions with the Flare Network including account
    operations and transactions.

    Attributes:
        address (ChecksumAddress | None): The account's checksum address
        private_key (str | None): The account's private key
        tx_queue (list[TxQueueElement]): Queue of pending transactions
        w3 (Web3): Web3 instance for blockchain interactions
        logger (BoundLogger): Structured logger for the provider
    """

    def __init__(self, web3_provider_url: str, wallet_store: WalletStore) -> None:
        """
        Initialize the Flare Provider.

        Args:
            web3_provider_url (str): URL of the Web3 provider endpoint
        """
        self.address: ChecksumAddress | None = None
        self.private_key: str | None = None
        self.tx_queue: list[TxQueueElement] = []
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        self.logger = logger.bind(router="flare_provider")
        self.wallet_store = wallet_store
        
        # Just for testing!
        #self.address = "0x1812C40b5785AeD831EC4a0d675f30c5461Fd42E"
        #self.private_key = "3294ca045aacbd40c717fe064ef5e39932d635b90335e881aae8d2c27dccccde"

    def reset(self) -> None:
        """
        Reset the provider state by clearing account details and transaction queue.
        """
        self.address = None
        self.private_key = None
        self.tx_queue = []
        self.logger.debug("reset", address=self.address, tx_queue=self.tx_queue)

    def add_tx_to_queue(self, msg: str, txs: list[TxParams]) -> None:
        """
        Add a transaction to the queue with an associated message.

        Args:
            msg (str): Description of the transaction
            tx (TxParams): Transaction parameters
        """
        tx_queue_element = TxQueueElement(msg=msg, confirm_msg="CONFIRM", txs=txs)
        self.tx_queue.append(tx_queue_element)
        self.logger.debug("add_tx_to_queue", tx_queue=self.tx_queue)

    def send_tx_in_queue(self, user: UserInfo) -> list[str]:
        """
        Send the most recent transaction in the queue.

        Returns:
            str: Transaction hash of the sent transaction

        Raises:
            ValueError: If no transaction is found in the queue
        """
        self.logger.debug("In send_tx_in_queue.", tx_queue=self.tx_queue)
        if self.tx_queue:
            tx_hashes = []
            for tx in self.tx_queue[-1].txs:
                tx_hash = self.sign_and_send_transaction(user, tx)
                self.logger.debug("sent_tx_hash", tx_hash=tx_hash)
                tx_hashes.append(tx_hash)
            self.tx_queue.pop()
            return tx_hashes
        msg = "Unable to find confirmed tx"
        raise ValueError(msg)

    def generate_account(self, user: UserInfo) -> ChecksumAddress:
        """
        Generate a new Flare account.

        Returns:
            ChecksumAddress: The checksum address of the generated account
        """
        account = Account.create()
        self.private_key = account.key.hex()
        self.address = self.w3.to_checksum_address(account.address)
        self.logger.debug(
            "generate_account", address=self.wallet_store.get_address(user), private_key=self.wallet_store.get_private_key(user)
        )
        self.wallet_store.store_wallet(user, str(self.address), str(self.private_key))
        return self.address, self.private_key

    def sign_and_send_transaction(self, user:UserInfo, tx: TxParams) -> str:
        """
        Sign and send a transaction to the network.

        Args:
            tx (TxParams): Transaction parameters to be sent

        Returns:
            str: Transaction hash of the sent transaction

        Raises:
            ValueError: If account is not initialized
        """
        if not self.wallet_store.get_private_key(user) or not self.wallet_store.get_address(user):
            msg = "Account not initialized"
            raise ValueError(msg)
        signed_tx = self.w3.eth.account.sign_transaction(
            tx, private_key=self.wallet_store.get_private_key(user)
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.logger.debug("sign_and_send_transaction", tx=tx)
        return "0x" + tx_hash.hex()   

    def check_balance(self, user: UserInfo) -> float:
        """
        Check the balance of the current account.

        Returns:
            float: Account balance in FLR

        Raises:
            ValueError: If account does not exist
        """
        if not self.wallet_store.get_address(user):
            msg = "Account does not exist"
            raise ValueError(msg)
        balance_wei = self.w3.eth.get_balance(self.wallet_store.get_address(user))
        self.logger.debug("check_balance", balance_wei=balance_wei)
        return float(self.w3.from_wei(balance_wei, "ether"))

    def create_send_flr_tx(self, to_address: str, amount: float, user: UserInfo) -> TxParams:
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
            "from": self.wallet_store.get_address(user),
            "nonce": self.w3.eth.get_transaction_count(self.wallet_store.get_address(user)),
            "to": self.w3.to_checksum_address(to_address),
            "value": self.w3.to_wei(amount, unit="ether"),
            "gas": 500000,
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            "chainId": self.w3.eth.chain_id,
            "type": 2,
        }
        return tx

    def create_contract_function_tx(self, user:UserInfo, contract: Contract, function_name: str, add_to_nonce: int = 0, *args, **kwargs) -> TxParams:
        if not self.wallet_store.get_address(user):
            raise ValueError("Account not initialized")
        if not contract:
            raise ValueError("Contract not initialized")

        function = getattr(contract.functions, function_name, None)
        if not function:
            raise AttributeError(f"Function '{function_name}' not found in contract ABI")

        nonce = self.w3.eth.get_transaction_count(self.wallet_store.get_address(user))
        nonce = nonce + add_to_nonce
        
        #base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
        gas_price = self.w3.eth.gas_price
        priority_fee = self.w3.eth.max_priority_fee
        
        print("kwargs.get('value', 0):", kwargs.get("value", 0))
        tx = function(*args).build_transaction({
            "from": self.wallet_store.get_address(user),
            "nonce": nonce,
            "gas": kwargs.get("gas", 500000),
            "maxFeePerGas": 2*(gas_price + priority_fee),
            "maxPriorityFeePerGas": 2*(priority_fee),
            "chainId": self.w3.eth.chain_id,
            "value": kwargs.get("value", 0),
        })
        self.logger.debug("Created contract function tx", function=function_name, tx=tx)
        return tx
   



    def queue_contract_function(self, contract: Contract, msg: str, function_name: str, *args, **kwargs) -> None:
        tx = self.create_contract_function_tx(contract, function_name, *args, **kwargs)
        self.add_tx_to_queue(msg, [tx])