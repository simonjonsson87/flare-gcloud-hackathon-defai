"""
Module for reading and writing in sparkDEX.

It will be able to handle swaps.



"""

from dataclasses import dataclass

import structlog
from eth_account import Account
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.types import TxParams

from flare_ai_defai.blockchain import FlareExplorer, FlareProvider
from flare_ai_defai.models.user import UserInfo
from flare_ai_defai.storage.fake_storage import WalletStore

logger = structlog.get_logger(__name__)


class SparkDEX:
    #SPARKDEX_ROUTER = "0x67041209cD0A8437A1fcEBf069eC15DB924c4dA6"
    SPARKDEX_ROUTER = "0x0f3D8a38D4c74afBebc2c42695642f0e3acb15D3"
    WFLR_ADDRESS = "0x1D80c49BbBCD1C0911346656B529DF9E5c2F783d"
    SFLR_ADDRESS = "0x12e605bc104e93B45e1aD99F9e555f659051c2BB"
    SPARKDEX_ABI = [
        {
            "inputs": [
            {
                "internalType": "bytes",
                "name": "commands",
                "type": "bytes"
            },
            {
                "internalType": "bytes[]",
                "name": "inputs",
                "type": "bytes[]"
            },
            {
                "internalType": "uint256",
                "name": "deadline",
                "type": "uint256"
            }
            ],
            "name": "execute",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    
    def __init__(self, web3_provider_url: str, flare_explorer: FlareExplorer, flare_provider: FlareProvider, wallet_store: WalletStore) -> None:
        """
        Args:
            web3_provider_url (str): URL of the Web3 provider endpoint
        """
        self.address: ChecksumAddress | None = None
        self.private_key: str | None = None
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)  # Added to deal with the PoA extraData issue.
        self.logger = logger.bind(router="SparkDEX")
        self.web3_provider_url = web3_provider_url
        self.flare_explorer = flare_explorer
        self.flare_provider = flare_provider
        self.wallet_store = wallet_store
        
        self.add_to_nonce = 0  
        
        #tx_hashes = self.swapFLRtoToken(
        #amount=1.0,
        #token_out="0xE3e3bC6Dc69FacbA691832AF7754fC5e8D0e09Ee",  # USDT.e
        #min_amount_out=0.0001,  # Adjust based on expected rate
        #deadline_minutes=20
        #)
    
    
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
        
    def swapFLRforSFLR():
        """
        https://flarescan.com/tx/0x51b5e93a162050486d64c22ddd9d3c5f42d7a2cfb68a832a5ac16f4fae70035e
        """     
        
    def swapFLRtoToken(self, user:UserInfo, amount: float, token_out: str, min_amount_out: float = 0, deadline_minutes: int = 20):
        """
        Swap FLR to a token via SparkDEX.
        
        https://flarescan.com/address/0x0f3D8a38D4c74afBebc2c42695642f0e3acb15D3/contract
        Function: execute(bytes commands, bytes[] inputs, uint256 deadline) payable
        Commands:
        - V3_SWAP_EXACT_IN = 0x00;
        - WRAP_ETH = 0x0b;
        
        V3_SWAP_EXACT_IN
            recipient := calldataload(inputs.offset)
            amountIn := calldataload(add(inputs.offset, 0x20))
            amountOutMin := calldataload(add(inputs.offset, 0x40))
            // 0x60 offset is the path, decoded below
            payerIsUser := calldataload(add(inputs.offset, 0x80))
            The rest is path.
        
        WRAP_ETH
            recipient := calldataload(inputs.offset)
            amountMin := calldataload(add(inputs.offset, 0x20))
        
        Args:
            amount (float): FLR amount to swap
            token_out (str): Address of token to receive (e.g., USDT.e)
            min_amount_out (float): Minimum token amount to accept (slippage protection)
            deadline_minutes (int): Transaction deadline in minutes from now
        """
        if not self.w3.is_connected():
            raise Exception("Not connected to Flare blockchain")

        # Initialize SparkDEX router contract
        #abi = self.flare_explorer.get_contract_abi(self.SPARKDEX_ROUTER)
        router = self.w3.eth.contract(address=self.SPARKDEX_ROUTER, abi=self.SPARKDEX_ABI)

        # Convert amounts to wei
        amount_wei = self.w3.to_wei(amount, "ether")
        min_amount_out_wei = self.w3.to_wei(min_amount_out, "ether")  # Adjust for token decimals if needed

        # Check balance
        balance = self.w3.eth.get_balance(self.flare_provider.address)
        gas_cost = 250000 * self.w3.eth.gas_price
        if balance < amount_wei + gas_cost:
            raise ValueError(f"Insufficient balance: {self.w3.from_wei(balance, 'ether')} FLR")
        self.logger.debug(balance=balance, gas_cost=gas_cost, amount_wei=amount_wei)

        # Set path: FLR -> WFLR -> Token
        path = [self.WFLR_ADDRESS, self.w3.to_checksum_address(token_out)]

        # Set deadline (Unix timestamp)
        from time import time
        deadline = int(time()) + (deadline_minutes * 60)
        
        commands = b'\x0b'  # Example from previous analysis

        # Define `inputs`
        #inputs = [
        #    [
        #        self.w3.to_bytes(amount_wei),
        #        self.w3.to_bytes(min_amount_out_wei),  # Min amount out
        #        self.w3.to_bytes(int(time()))  # Timestamp
        #    ]
        #]
        #inputs = [self.w3.codec.encode(['uint256', 'uint256', 'address[]'], [amount_wei, min_amount_out_wei, path])]
        
        inputs = [
            # First input: Encode amount and a secondary parameter (e.g., min_amount_out)
            self.w3.codec.encode(['uint256', 'uint256'], [amount_wei, min_amount_out_wei]),
            # Second input: Encode swap details (amount, min amount out, path)
            self.w3.codec.encode(
                ['uint256', 'uint256', 'address[]'],
                [amount_wei, min_amount_out_wei, path]
            )
        ]
        
        tx = self.flare_provider.create_contract_function_tx(
            router,
            "execute",
            0,  # First tx in sequence
            commands,
            inputs,
            deadline,
            value=amount_wei
        )

        # Queue and send
        self.flare_provider.add_tx_to_queue(f"Swapping {amount} FLR to {token_out}", [tx])
        tx_hashes = self.flare_provider.send_tx_in_queue(user)
        return tx_hashes    
    
    
    def swap_erc20_tokens(self, token_in: str, token_out: str, amount_in: float):
        """
        Swap ERC20 tokens on Uniswap V3 using the Universal Router.
        
        Args:
            token_in (str): Token to swap from
            token_out (str): Token to swap to
            amount_in (float): Amount of tokens to swap
            
        Returns:
            str: Transaction hash
        """

        amount_in = self.w3.to_wei(amount_in, unit="ether")
        universal_router_address = "0x8a1E35F5c98C4E85B36B7B253222eE17773b2781"  # Replace with Flare's Universal Router if different
        
        token_address = {
            "wflr": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
            "joule": "0xE6505f92583103AF7ed9974DEC451A7Af4e3A3bE",
            "usdc": "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6",
            "usdt": "0x0B38e83B86d491735fEaa0a791F65c2B99535396",
            "weth": "0x1502FA4be69d526124D453619276FacCab275d3D"

        }

        token_address_abi = {
            "wflr": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
            "joule": "0xEE15da0edB70FC6D98D03651F949FcCc2C4e1E80",
            "usdc": "0x3AdAE7Ad0449e26ad2e95059e08CC29ECB93E194",
            "usdt": "0x0B38e83B86d491735fEaa0a791F65c2B99535396",
            "weth": "0x1502FA4be69d526124D453619276FacCab275d3D"
        }
        
        SWAP_ROUTER_ABI =   [{
            "inputs": [
            {
                "components": [
                {
                    "internalType": "address",
                    "name": "tokenIn",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "tokenOut",
                    "type": "address"
                },
                {
                    "internalType": "uint24",
                    "name": "fee",
                    "type": "uint24"
                },
                {
                    "internalType": "address",
                    "name": "recipient",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "deadline",
                    "type": "uint256"
                },
                {
                    "internalType": "uint256",
                    "name": "amountIn",
                    "type": "uint256"
                },
                {
                    "internalType": "uint256",
                    "name": "amountOutMinimum",
                    "type": "uint256"
                },
                {
                    "internalType": "uint160",
                    "name": "sqrtPriceLimitX96",
                    "type": "uint160"
                }
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
            ],
            "name": "exactInputSingle",
            "outputs": [
            {
                "internalType": "uint256",
                "name": "amountOut",
                "type": "uint256"
            }
            ],
            "stateMutability": "payable",
            "type": "function"
        }]

        # token_abi = {
        #     "wflr": WFLR_ABI,
        #     "joule": JOULE_ABI,
        #     "usdc": USDC_ABI
        # }

        token_in_address = token_address[token_in.lower()]
        token_out_address = token_address[token_out.lower()]

        # token_in_abi = token_abi[token_in.lower()]
        # token_out_abi = token_abi[token_out.lower()]

        token_in_abi = self.flare_explorer.get_contract_abi(contract_address=token_address_abi[token_in.lower()])
        token_out_abi = self.flare_explorer.get_contract_abi(contract_address=token_address_abi[token_out.lower()])
        
        
        universal_router = self.w3.eth.contract(address=universal_router_address, abi=SWAP_ROUTER_ABI)
        contract_in = self.w3.eth.contract(address=token_in_address, abi=token_in_abi)
        contract_out = self.w3.eth.contract(address=token_out_address, abi=token_out_abi)

        fee_tier = 500  # Assuming 0.05% pool fee
        amount_out_min = 0  # Fetch dynamically for slippage protection
        deadline = self.w3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        # --- Step 1: Approve Universal Router to Spend wFLR ---
        approval_tx = contract_in.functions.approve(universal_router_address, amount_in).build_transaction({
            'from': self.address,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            'chainId': self.w3.eth.chain_id,
            "type": 2,
        })

        self.logger.debug(f"Approval transaction: {approval_tx}")

        signed_approval_tx = self.w3.eth.account.sign_transaction(approval_tx, self.private_key)
        approval_tx_hash = self.w3.eth.send_raw_transaction(signed_approval_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(approval_tx_hash)
        self.logger.debug(f"Approval transaction hash: {Web3.to_hex(approval_tx_hash)}")

        params = (
        token_in_address,  # Token In
        token_out_address,  # Token Out
        fee_tier,  # Pool Fee Tier (0.05%)
        self.address,  # Recipient
        deadline,  # Deadline (5 min)
        amount_in,  # Amount In (exact wFLR amount)
        amount_out_min,  # Minimum amount of JOULE expected
        0  # sqrtPriceLimitX96 (0 = no limit)
        )

        base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
        priority_fee = self.w3.eth.max_priority_fee

        # --- Step 3: Execute the swap ---
        swap_tx = universal_router.functions.exactInputSingle(params).build_transaction({
            'from': self.address,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            "maxFeePerGas": base_fee + priority_fee, #self.w3.eth.gas_price,
            "maxPriorityFeePerGas": priority_fee, #self.w3.eth.max_priority_fee,
            'chainId': self.w3.eth.chain_id,
            "type": 2,
        })

        signed_swap_tx = self.w3.eth.account.sign_transaction(swap_tx, self.private_key)
        swap_tx_hash = self.w3.eth.send_raw_transaction(signed_swap_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(swap_tx_hash)

        print(f"Swap transaction hash: {Web3.to_hex(swap_tx_hash)}")

        # --- Step 4: Check JOULE Balance ---
        # joule_balance = joule_contract.functions.balanceOf(self.address).call()
        # print(f"New JOULE balance: {joule_balance / 10**6}")

        return Web3.to_hex(swap_tx_hash)


    def swap_erc20_tokens_tx(self, user: UserInfo, token_in: str, token_out: str, amount_in: float):

        amount_in = self.w3.to_wei(amount_in, unit="ether")
        universal_router_address = "0x8a1E35F5c98C4E85B36B7B253222eE17773b2781"  # Replace with Flare's Universal Router if different
        
        token_address = {
            "wflr": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
            "joule": "0xE6505f92583103AF7ed9974DEC451A7Af4e3A3bE",
            "usdc": "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6",
            "usdt": "0x0B38e83B86d491735fEaa0a791F65c2B99535396",
            "weth": "0x1502FA4be69d526124D453619276FacCab275d3D"
        }

        token_address_abi = {
            "wflr": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
            "joule": "0xEE15da0edB70FC6D98D03651F949FcCc2C4e1E80",
            "usdc": "0x3AdAE7Ad0449e26ad2e95059e08CC29ECB93E194",
            "usdt": "0x0B38e83B86d491735fEaa0a791F65c2B99535396",
            "weth": "0x1502FA4be69d526124D453619276FacCab275d3D"
        }
        
        ERC20_ABI = {
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
            },{
                "inputs": [
                {
                    "internalType": "address",
                    "name": "account",
                    "type": "address"
                }
                ],
                "name": "balanceOf",
                "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
                ],
                "stateMutability": "view",
                "type": "function"
            }
    
        
        SWAP_ROUTER_ABI =   [{
            "inputs": [
            {
                "components": [
                {
                    "internalType": "address",
                    "name": "tokenIn",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "tokenOut",
                    "type": "address"
                },
                {
                    "internalType": "uint24",
                    "name": "fee",
                    "type": "uint24"
                },
                {
                    "internalType": "address",
                    "name": "recipient",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "deadline",
                    "type": "uint256"
                },
                {
                    "internalType": "uint256",
                    "name": "amountIn",
                    "type": "uint256"
                },
                {
                    "internalType": "uint256",
                    "name": "amountOutMinimum",
                    "type": "uint256"
                },
                {
                    "internalType": "uint160",
                    "name": "sqrtPriceLimitX96",
                    "type": "uint160"
                }
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
            ],
            "name": "exactInputSingle",
            "outputs": [
            {
                "internalType": "uint256",
                "name": "amountOut",
                "type": "uint256"
            }
            ],
            "stateMutability": "payable",
            "type": "function"
        }]

        # token_abi = {
        #     "wflr": WFLR_ABI,
        #     "joule": JOULE_ABI,
        #     "usdc": USDC_ABI
        # }

        token_in_address = token_address[token_in.lower()]
        token_out_address = token_address[token_out.lower()]

        # token_in_abi = token_abi[token_in.lower()]
        # token_out_abi = token_abi[token_out.lower()]

        #token_in_abi = self.flare_explorer.get_contract_abi(contract_address=token_address_abi[token_in.lower()])
        #token_out_abi = self.flare_explorer.get_contract_abi(contract_address=token_address_abi[token_out.lower()])
        
        token_in_abi = ERC20_ABI
        token_out_abi = ERC20_ABI
        
        
        universal_router = self.w3.eth.contract(address=universal_router_address, abi=SWAP_ROUTER_ABI)
        contract_in = self.w3.eth.contract(address=token_in_address, abi=token_in_abi)
        contract_out = self.w3.eth.contract(address=token_out_address, abi=token_out_abi)

        fee_tier = 500  # Assuming 0.05% pool fee
        amount_out_min = 0  # Fetch dynamically for slippage protection
        deadline = self.w3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        # --- Step 1: Approve Universal Router to Spend wFLR ---
        approval_tx = contract_in.functions.approve(universal_router_address, amount_in).build_transaction({
            'from': self.wallet_store.get_address(user),
            'nonce': self.get_nonce(),
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            'chainId': self.w3.eth.chain_id,
            "type": 2,
        })

        self.logger.debug(f"Approval transaction: {approval_tx}")

        params = (
        token_in_address,  # Token In
        token_out_address,  # Token Out
        fee_tier,  # Pool Fee Tier (0.05%)
        self.wallet_store.get_address(user),  # Recipient
        deadline,  # Deadline (5 min)
        amount_in,  # Amount In (exact wFLR amount)
        amount_out_min,  # Minimum amount of JOULE expected
        0  # sqrtPriceLimitX96 (0 = no limit)
        )

        base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
        priority_fee = self.w3.eth.max_priority_fee

        # --- Step 3: Execute the swap ---
        swap_tx = universal_router.functions.exactInputSingle(params).build_transaction({
            'from': self.wallet_store.get_address(user),
            'nonce': self.get_nonce(),
            "maxFeePerGas": base_fee + priority_fee, #self.w3.eth.gas_price,
            "maxPriorityFeePerGas": priority_fee, #self.w3.eth.max_priority_fee,
            'chainId': self.w3.eth.chain_id,
            "type": 2,
        })

        # --- Step 4: Check JOULE Balance ---
        # joule_balance = joule_contract.functions.balanceOf(self.wallet_store.get_address(user)).call()
        # print(f"New JOULE balance: {joule_balance / 10**6}")

        return approval_tx, swap_tx


    def wrap_flr_to_wflr(self, amount_in: float):
        """
        Wrap native FLR into WFLR (Wrapped FLR).
        
        Args:
            amount_in (float): Amount of FLR to wrap (in wei)

        Returns:
            str: Transaction hash
        """
        
        WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d" 
        
        WFLR_ABI = [{
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }]
        
        # Initialize WFLR contract
        wflr_contract = self.w3.eth.contract(address=WFLR_ADDRESS, abi=WFLR_ABI)

        base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
        priority_fee = self.w3.eth.max_priority_fee

        # Build wrap transaction (calling `deposit()` on WFLR contract)
        wrap_tx = wflr_contract.functions.deposit().build_transaction({
            "from": self.address,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "value": self.w3.to_wei(amount_in, unit="ether"),  # Sending FLR directly
            "maxFeePerGas": base_fee + priority_fee,  
            "maxPriorityFeePerGas": priority_fee,
            "chainId": self.w3.eth.chain_id,
            "type": 2,
        })

        self.logger.debug("Wrap FLR to WFLR", tx=wrap_tx)

        # Sign and send the transaction
        signed_wrap_tx = self.w3.eth.account.sign_transaction(wrap_tx, self.private_key)
        wrap_tx_hash = self.w3.eth.send_raw_transaction(signed_wrap_tx.raw_transaction)

        # Wait for confirmation
        self.w3.eth.wait_for_transaction_receipt(wrap_tx_hash)

        

        self.logger.debug("Wrap FLR to WFLR 2", tx=wrap_tx_hash.hex())

    
        return f"0x{wrap_tx_hash.hex()}"
    
    def wrap_flr_to_wflr_tx(self, user: UserInfo, amount_in: float):
        """
        Make the transaction to wrap native FLR into WFLR (Wrapped FLR).
        
        Args:
            amount_in (float): Amount of FLR to wrap (in wei)

        Returns:
            str: Transaction hash
        """
        
        WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d" 
        
        WFLR_ABI = [{
            "inputs": [],
            "name": "deposit",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }]
        
        # Initialize WFLR contract
        wflr_contract = self.w3.eth.contract(address=WFLR_ADDRESS, abi=WFLR_ABI)

        base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
        priority_fee = self.w3.eth.max_priority_fee

        # Build wrap transaction (calling `deposit()` on WFLR contract)
        wrap_tx = wflr_contract.functions.deposit().build_transaction({
            "from": self.wallet_store.get_address(user),
            "nonce": self.get_nonce(),
            "value": self.w3.to_wei(amount_in, unit="ether"),  # Sending FLR directly
            "maxFeePerGas": base_fee + priority_fee,  
            "maxPriorityFeePerGas": priority_fee,
            "chainId": self.w3.eth.chain_id,
            "type": 2,
        })
        
        return wrap_tx

    def add_swap_txs_to_queue(self, user: UserInfo, from_token: str, to_token: str, amount: float) -> str:
        self.reset_nonce(user)
        
        if from_token.lower() == "flr":
            wrap_tx = self.wrap_flr_to_wflr_tx(user, amount)
            approval_tx, swap_tx = self.swap_erc20_tokens_tx(user, "wflr", to_token, amount)
            if (to_token.lower() == "wflr"):
                self.flare_provider.add_tx_to_queue(
                    f"Swap {amount} {from_token} to {to_token}", 
                    [wrap_tx])
            else:
                self.flare_provider.add_tx_to_queue(
                    f"Swap {amount} {from_token} to {to_token}", 
                    [wrap_tx, approval_tx, swap_tx])
        else:    
            approval_tx, swap_tx = self.swap_erc20_tokens_tx(user, from_token, to_token, amount)
            self.flare_provider.add_tx_to_queue(
                f"Swap {amount} {from_token} to {to_token}", 
                [approval_tx, swap_tx])
        
        
        formatted_preview = (
            "Transaction Preview: "
            + f"Swapping {amount} "
            + f"{from_token} to {to_token}\nType CONFIRM to proceed."
        )
        return formatted_preview

    def handle_swap_token(self, from_token: str, to_token: str, amount: float) -> str:
        """
        Handle token swap by calling swap_flr_for_native_token.
        
        Args:
            from_token (str): Token to swap from
            to_token (str): Token to swap to
            amount (float): Amount of tokens to swap
        
        Returns:
            str: Transaction hash
        """
        # return self.swap_flr_for_native_token2(to_token, from_token, amount)
        if from_token.lower() == "flr":
            self.wrap_flr_to_wflr(amount)
            return self.swap_erc20_tokens("wflr", to_token, amount)
        self.logger.debug("FLR first done")

        return self.swap_erc20_tokens(from_token, to_token, amount)  
    
      
    def reset_nonce(self, user: UserInfo):    
        self.add_to_nonce = self.w3.eth.get_transaction_count(self.wallet_store.get_address(user))

    def get_nonce(self):
        current_add_to_nonce = self.add_to_nonce
        self.add_to_nonce += 1
        return current_add_to_nonce
        
  
    