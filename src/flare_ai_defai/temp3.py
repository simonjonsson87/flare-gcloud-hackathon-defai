from web3 import Web3
from eth_account import Account
from web3.middleware import ExtraDataToPOAMiddleware, SignAndSendRawMiddlewareBuilder
import sys, json

import requests
from requests.exceptions import RequestException, Timeout

import structlog
logger = structlog.get_logger(__name__)  

class SparkDEX:
    SIMON_ADDRESS = "0x1812C40b5785AeD831EC4a0d675f30c5461Fd42E"
    SPARKDEX_ROUTER = "0x0f3D8a38D4c74afBebc2c42695642f0e3acb15D3"
    WFLR_ADDRESS = "0x1D80c49BbBCD1C0911346656B529DF9E5c2F783d"
    SPARKDEX_ABI = [
        {
            "inputs": [
                {"internalType": "bytes", "name": "commands", "type": "bytes"},
                {"internalType": "bytes[]", "name": "inputs", "type": "bytes[]"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "execute",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ]

    def __init__(self, web3_provider_url: str, flare_explorer: object, flare_provider: object) -> None:
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        # Add PoA middleware for Flare's extraData
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.flare_explorer = flare_explorer
        self.flare_provider = flare_provider
        self.logger = logger.bind(blockchain="explorer")
        self.address = self.flare_provider.address
        self.private_key = self.flare_provider.private_key
        

    def get_token_decimals(self, token_address):
        checksum_address = self.w3.to_checksum_address(token_address)
        token_contract = self.w3.eth.contract(address=checksum_address, abi=[
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
        ])
        return token_contract.functions.decimals().call()

    def swapFLRtoToken(self, amount: float, token_out: str, min_amount_out: float = 0, deadline_minutes: int = 20):
        if not self.w3.is_connected():
            raise Exception("Not connected to Flare blockchain")

        router = self.w3.eth.contract(address=self.SPARKDEX_ROUTER, abi=self.SPARKDEX_ABI)
        amount_wei = int(pow(10,18)*amount)

        # Fetch decimals for min_amount_out using checksummed address
        token_out_checksum = self.w3.to_checksum_address(token_out)
        token_decimals = self.get_token_decimals(token_out_checksum)
        min_amount_out_wei = int(min_amount_out * (10 ** token_decimals))

        # Check balance
        balance = self.w3.eth.get_balance(self.SIMON_ADDRESS)
        gas_cost = 250000 * self.w3.eth.gas_price
        if balance < amount_wei + gas_cost:
            raise ValueError(f"Insufficient balance: {self.w3.from_wei(balance, 'ether')} FLR")

        # Use checksummed addresses in the path
        #path = [self.w3.to_checksum_address(self.WFLR_ADDRESS), token_out_checksum]
        deadline = int(self.w3.eth.get_block('latest')['timestamp']) + (deadline_minutes * 60)

        # Define commands
        commands = bytes.fromhex("0b00") # 0x0b=WRAP_ETH and 0x00=V3_SWAP_EXACT_IN

        #path = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002b1d80c49bbbcd1c0911346656b529df9e5c2f783d00006412e605bc104e93b45e1ad99f9e555f659051c2bb000000000000000000000000000000000000000000")
        path = bytes.fromhex("1d80c49bbbcd1c0911346656b529df9e5c2f783d00006412e605bc104e93b45e1ad99f9e555f659051c2bb")
        
        # address recipient; uint256 amountMin;
        wrap_eth_input = self.w3.eth.codec.encode(['uint256', 'uint256'], [2, int(amount_wei)])
        # address recipient; uint256 amountIn; uint256 amountOutMin; bool payerIsUser; bytes path
        swap_input = self.w3.eth.codec.encode(['address', 'uint256', 'uint256', 'bool', 'bytes'], [
            self.SIMON_ADDRESS,
            int(amount_wei),
            int(min_amount_out_wei),
            False,
            path
        ])

        inputs = [wrap_eth_input, swap_input]

        # Build transaction
        tx = self.flare_provider.create_contract_function_tx(
            router,
            "execute",
            0,
            commands,
            inputs,
            deadline,
            value=amount_wei
        )

        # Queue and send
        self.flare_provider.add_tx_to_queue(f"Swapping {amount} FLR to {token_out}", [tx])
        return self.flare_provider.send_tx_in_queue()
    
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



class FlareExplorer:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.logger = logger
        self.logger = logger.bind(blockchain="explorer")

    def _get(self, params: dict) -> dict:
        """Get data from the Chain Explorer API.

        :param params: Query parameters
        :return: JSON response
        """
        headers = {"accept": "application/json"}
        try:
            response = requests.get(
                self.base_url, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()
            try:
                json_response = response.json()
                self.logger.debug("Response JSON:", extra={"json_response": json_response})
            except ValueError:
                # If the response is not JSON, log the raw content
                #self.logger.error("Response is not in JSON format, raw content:", extra={"response_text": response.text})
                #with open('invalid_response.json', 'w') as f:
                #    f.write(response.text)
                
                # Raise an exception to stop the program
                raise ValueError("Response content is not valid JSON.")


            if "result" not in json_response:
                msg = (f"Malformed response from API: {json_response}",)
                raise ValueError(msg)

        except (RequestException, Timeout):
            logger.exception("Network error during API request")
            raise
        else:
            return json_response

    def get_contract_abi(self, contract_address: str) -> dict:
        """Get the ABI for a contract from the Chain Explorer API.

        :param contract_address: Address of the contract
        :return: Contract ABI
        """
        self.logger.debug("Fetching ABI for `%s` from `%s`", contract_address, self.base_url)
        #self.logger.debug("Fetching ABI for `%s` from `%s`", contract_address, self.base_url)
        response = self._get(
            params={
                "module": "contract",
                "action": "getabi",
                "address": contract_address,
            }
        )
        #self.logger.debug("After self._get() call", response=response)
        #return json.loads(response["result"])

        abi_list = json.loads(response["result"])  # Convert string to list
        #return {"abi": abi_list}    # Convert list to dict

        return abi_list  
    
    
class FlareProvider:
    def __init__(self, web3_provider_url: str) -> None:
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        # Add PoA middleware for Flare's extraData
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.address = "0x1812C40b5785AeD831EC4a0d675f30c5461Fd42E"
        self.private_key = "3294ca045aacbd40c717fe064ef5e39932d635b90335e881aae8d2c27dccccde"
        # Add signing middleware
        account = Account.from_key(self.private_key)
        self.w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(account), layer=0)
        self.w3.eth.default_account = account.address  # Set default account for transactions
        self.tx_queue = []

    def create_contract_function_tx(self, contract, function_name, add_to_nonce, *args, **kwargs):
        if not self.address:
            raise ValueError("Account not initialized")
        function = getattr(contract.functions, function_name, None)
        if not function:
            raise AttributeError(f"Function '{function_name}' not found in contract ABI")
        nonce = self.w3.eth.get_transaction_count(self.address) + add_to_nonce
        tx = function(*args).build_transaction({
            "from": self.address,
            "nonce": nonce,
            "gas": kwargs.get("gas", 200000),
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            "chainId": self.w3.eth.chain_id,
            "value": kwargs.get("value", 0),
        })
        print(tx)
        self.print_formatted_data(tx["data"])
        #sys.exit()
        #tx["data"] = "0x3593564c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000009184e72a00000000000000000000000000000000000000000000000000000000000000000020b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000de0b6b3a76400000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000e016eeb29af76c379a4f2bb3d71a05d70efbc8a30000000000000000000000000000000000000000000000000de0b6b3a76400000000000000000000000000000000000000000000000000000a68026c877d5b5300000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002b1d80c49bbbcd1c0911346656b529df9e5c2f783d00006412e605bc104e93b45e1ad99f9e555f659051c2bb000000000000000000000000000000000000000000"
        return tx

    def print_formatted_data(self, data_str):
        # Remove '0x' prefix
        clean_data = data_str[2:] if data_str.startswith("0x") else data_str
        clean_data = clean_data[8:]
        
        # Print data in 64-character rows with index
        for i in range(0, len(clean_data), 64):
            print(f"{i//64:03}: {clean_data[i:i+64]}")

    def add_tx_to_queue(self, msg: str, txs: list):
        self.tx_queue.append({"msg": msg, "txs": txs})

    def send_tx_in_queue(self):
        if self.tx_queue:
            tx_hashes = []
            for tx in self.tx_queue[-1]["txs"]:
                # The signing middleware handles signing and sending
                try:
                    tx_hash = self.w3.eth.send_transaction(tx)
                    self.w3.eth.wait_for_transaction_receipt(tx_hash)
                except Exception as e:
                    print(f"Revert reason: {str(e)}")    
                
                tx_hashes.append(tx_hash.hex())
            self.tx_queue.pop()
            return tx_hashes
        raise ValueError("No transactions in queue")

# Example usage
if __name__ == "__main__":
    web3_provider_url = "https://flare-api.flare.network/ext/C/rpc"
    flare_provider = FlareProvider(web3_provider_url)
    flare_explorer = FlareExplorer("https://flare-explorer.flare.network/api")
    sparkdex = SparkDEX(web3_provider_url, flare_explorer, flare_provider)
    #tx_hashes = sparkdex.swapFLRtoToken(1.0, "0x12e605bc104e93B45e1aD99F9e555f659051c2BB", min_amount_out=0.5)
    #sparkdex.wrap_flr_to_wflr(1)
    sparkdex.handle_swap_token("flr", "usdc", 1)
    #print("Transaction hashes:", tx_hashes)

    
 #   self.address = "0x1812C40b5785AeD831EC4a0d675f30c5461Fd42E"  # Replace with actual address
 #       self.private_key = "3294ca045aacbd40c717fe064ef5e39932d635b90335e881aae8d2c27dccccde"
 
 
 
 
# https://flarescan.com/tx/0x51b5e93a162050486d64c22ddd9d3c5f42d7a2cfb68a832a5ac16f4fae70035e
# Function: execute(bytes commands, bytes[] inputs, uint256 deadline) payable
#MethodID: 0x3593564c
#[0]:
#0000000000000000000000000000000000000000000000000000000000000060 Offset to start of commands (96)
#[1]:
#00000000000000000000000000000000000000000000000000000000000000a0 Offset to start of inputs (160)
#[2]:
#000000000000000000000000000000000000000000000000000009184e72a000 Deadline
#[3]:
#0000000000000000000000000000000000000000000000000000000000000002 Length of commands
#[4]:
#0b00000000000000000000000000000000000000000000000000000000000000 Both commands WRAP_ETH = 0x0b, V3_SWAP_EXACT_IN = 0x00;
#[5]:
#0000000000000000000000000000000000000000000000000000000000000002 Length of bytes[] inputs
#[6]:
#0000000000000000000000000000000000000000000000000000000000000040 Offset to input[0]
#[7]:
#00000000000000000000000000000000000000000000000000000000000000a0 Offset to input[1]

#[8]:
#0000000000000000000000000000000000000000000000000000000000000040 Length of input[0]
#[9]:
#0000000000000000000000000000000000000000000000000000000000000002 Two jumps?
#[10]:
#0000000000000000000000000000000000000000000000008ac7230489e80000 10 FLR - First parameter in the first inputs element

#[11]:
#0000000000000000000000000000000000000000000000000000000000000100 Length of input[1]
#[12]:
#000000000000000000000000e016eeb29af76c379a4f2bb3d71a05d70efbc8a3 Recipient (my account) - Start of the second inputs element (recipient of tokens)
#[13]:
#0000000000000000000000000000000000000000000000008ac7230489e80000 10 * 10^18. amountIn?
#[14]:
#00000000000000000000000000000000000000000000000067e2cd1b9f84733e 7.56 * 10^18 Amount of sFLR. amountOutMin
#[15]:
#00000000000000000000000000000000000000000000000000000000000000a0 payerIsUser (bool)
#[16]:
#0000000000000000000000000000000000000000000000000000000000000000
#[17]:
#000000000000000000000000000000000000000000000000000000000000002b Length of remaining data 32+11=43
#[18]:
#1d80c49bbbcd1c0911346656b529df9e5c2f783d 000064 12e605bc104e93b45e First bit is WFLR, middle is 100 in decimal (gas price?). last bit is sFLR. 
#[19]:
#1ad99f9e555f659051c2bb000000000000000000000000000000000000000000 

#0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002b1d80c49bbbcd1c0911346656b529df9e5c2f783d00006412e605bc104e93b45e1ad99f9e555f659051c2bb000000000000000000000000000000000000000000

















[
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_factory",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "_WETH9",
        "type": "address"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "inputs": [],
    "name": "WETH9",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "components": [
          {
            "internalType": "bytes",
            "name": "path",
            "type": "bytes"
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
          }
        ],
        "internalType": "struct ISwapRouter.ExactInputParams",
        "name": "params",
        "type": "tuple"
      }
    ],
    "name": "exactInput",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "amountOut",
        "type": "uint256"
      }
    ],
    "stateMutability": "payable",
    "type": "function"
  },
  {
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
  },
  {
    "inputs": [
      {
        "components": [
          {
            "internalType": "bytes",
            "name": "path",
            "type": "bytes"
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
            "name": "amountOut",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "amountInMaximum",
            "type": "uint256"
          }
        ],
        "internalType": "struct ISwapRouter.ExactOutputParams",
        "name": "params",
        "type": "tuple"
      }
    ],
    "name": "exactOutput",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      }
    ],
    "stateMutability": "payable",
    "type": "function"
  },
  {
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
            "name": "amountOut",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "amountInMaximum",
            "type": "uint256"
          },
          {
            "internalType": "uint160",
            "name": "sqrtPriceLimitX96",
            "type": "uint160"
          }
        ],
        "internalType": "struct ISwapRouter.ExactOutputSingleParams",
        "name": "params",
        "type": "tuple"
      }
    ],
    "name": "exactOutputSingle",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      }
    ],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "factory",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "bytes[]",
        "name": "data",
        "type": "bytes[]"
      }
    ],
    "name": "multicall",
    "outputs": [
      {
        "internalType": "bytes[]",
        "name": "results",
        "type": "bytes[]"
      }
    ],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "refundETH",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "value",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "deadline",
        "type": "uint256"
      },
      {
        "internalType": "uint8",
        "name": "v",
        "type": "uint8"
      },
      {
        "internalType": "bytes32",
        "name": "r",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "s",
        "type": "bytes32"
      }
    ],
    "name": "selfPermit",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "nonce",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "expiry",
        "type": "uint256"
      },
      {
        "internalType": "uint8",
        "name": "v",
        "type": "uint8"
      },
      {
        "internalType": "bytes32",
        "name": "r",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "s",
        "type": "bytes32"
      }
    ],
    "name": "selfPermitAllowed",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "nonce",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "expiry",
        "type": "uint256"
      },
      {
        "internalType": "uint8",
        "name": "v",
        "type": "uint8"
      },
      {
        "internalType": "bytes32",
        "name": "r",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "s",
        "type": "bytes32"
      }
    ],
    "name": "selfPermitAllowedIfNecessary",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "value",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "deadline",
        "type": "uint256"
      },
      {
        "internalType": "uint8",
        "name": "v",
        "type": "uint8"
      },
      {
        "internalType": "bytes32",
        "name": "r",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "s",
        "type": "bytes32"
      }
    ],
    "name": "selfPermitIfNecessary",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "amountMinimum",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "recipient",
        "type": "address"
      }
    ],
    "name": "sweepToken",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "token",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "amountMinimum",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "recipient",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "feeBips",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "feeRecipient",
        "type": "address"
      }
    ],
    "name": "sweepTokenWithFee",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "int256",
        "name": "amount0Delta",
        "type": "int256"
      },
      {
        "internalType": "int256",
        "name": "amount1Delta",
        "type": "int256"
      },
      {
        "internalType": "bytes",
        "name": "_data",
        "type": "bytes"
      }
    ],
    "name": "uniswapV3SwapCallback",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "amountMinimum",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "recipient",
        "type": "address"
      }
    ],
    "name": "unwrapWETH9",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "amountMinimum",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "recipient",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "feeBips",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "feeRecipient",
        "type": "address"
      }
    ],
    "name": "unwrapWETH9WithFee",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "stateMutability": "payable",
    "type": "receive"
  }
]