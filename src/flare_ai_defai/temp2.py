from web3 import Web3

# Flare Mainnet RPC URL
FLARE_RPC_URL = "https://flare-api.flare.network/ext/C/rpc"

# Connect to Flare network
web3 = Web3(Web3.HTTPProvider(FLARE_RPC_URL))

if not web3.is_connected():
    raise Exception("Failed to connect to Flare blockchain")

print("Connected to Flare Blockchain!")

# Contract address (replace with actual contract)
CONTRACT_ADDRESS = "0x12e605bc104e93B45e1aD99F9e555f659051c2BB"


CONTRACT_ABI = [
  {
    "inputs": [],
    "name": "buyInStakingFee",
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
]  

# Load contract
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

print("Available Functions:")
for func in contract.functions:
    print("-", func)
    
# Call a function on the contract
result = contract.functions.buyInStakingFee().call()
print("Contract function result:", result)
