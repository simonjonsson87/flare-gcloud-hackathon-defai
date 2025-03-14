import logging
from web3 import Web3
from web3.exceptions import ContractLogicError

from web3.middleware import ExtraDataToPOAMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
FACTORY_ADDRESSES = [
    "0x8A2578d23d4C532cC9A98FaD91C0523f5efDE652",  
]
UNIVERSAL_ROUTER_ADDRESS = "0x8a1E35F5c98C4E85B36B7B253222eE17773b2781"
WFLR_ADDRESS = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
USDC_ADDRESS = "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6"  # USDC.e
FEE_TIER = 500
USER_ADDRESS = "0x1812C40b5785AeD831EC4a0d675f30c5461Fd42E"  # Replace with your address
RPC_URL = "https://flare-api.flare.network/ext/C/rpc"
FALLBACK_POOL_ADDRESS = None  # Replace with "0x..." if known, else None

# ABIs
FACTORY_ABI = [{"inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}], "name": "getPool", "outputs": [{"internalType": "address", "name": "pool", "type": "address"}], "stateMutability": "view", "type": "function"}]
POOL_ABI = [{"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
ERC20_ABI = [{"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
UNIVERSAL_ROUTER_ABI = [{"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}], "internalType": "struct ISwapRouter.ExactInputSingleParams", "name": "params", "type": "tuple"}], "name": "exactInputSingle", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "payable", "type": "function"}]

# Connect to Flare
logger.info("=== STEP 1: CONNECTING TO FLARE NETWORK ===")
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    logger.error("Failed to connect to Flare RPC")
    exit(1)
logger.info("Successfully connected to Flare network")
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Check factory code
logger.info("=== STEP 2: FINDING VALID FACTORY ADDRESS ===")
for factory_addr in FACTORY_ADDRESSES:
    code = w3.eth.get_code(factory_addr)
    logger.debug(f"Factory {factory_addr} bytecode length: {len(code)}")
    if len(code) > 0:
        logger.info(f"Found factory with code at {factory_addr}")
        FACTORY_ADDRESS = factory_addr
        break
else:
    logger.error("No factory with bytecode found. Please provide SparkDEX factory address.")
    if FALLBACK_POOL_ADDRESS:
        logger.info(f"Using fallback pool address: {FALLBACK_POOL_ADDRESS}")
        pool_address = FALLBACK_POOL_ADDRESS
    else:
        logger.error("No fallback pool address provided. Exiting.")
        exit(1)

# Contracts
factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)
wflr_contract = w3.eth.contract(address=WFLR_ADDRESS, abi=ERC20_ABI)
usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
universal_router = w3.eth.contract(address=UNIVERSAL_ROUTER_ADDRESS, abi=UNIVERSAL_ROUTER_ABI)

# Step 3: Get pool address
logger.info("=== STEP 3: FETCHING POOL ADDRESS ===")
if not FALLBACK_POOL_ADDRESS:
    try:
        pool_address = factory.functions.getPool(WFLR_ADDRESS, USDC_ADDRESS, FEE_TIER).call()
        logger.debug(f"WFLR/USDC.e pool address at fee {FEE_TIER}: {pool_address}")
        if pool_address == "0x0000000000000000000000000000000000000000":
            logger.error("No pool found for WFLR/USDC.e at fee tier 500")
            exit(1)
    except Exception as e:
        logger.error(f"Failed to get pool: {str(e)}")
        exit(1)
else:
    pool_address = FALLBACK_POOL_ADDRESS
    logger.info(f"Using provided fallback pool address: {pool_address}")

# Step 4: Verify pool details
logger.info("=== STEP 4: VERIFYING POOL DETAILS ===")
pool = w3.eth.contract(address=pool_address, abi=POOL_ABI)
token0 = pool.functions.token0().call()
token1 = pool.functions.token1().call()
fee = pool.functions.fee().call()
logger.debug(f"Pool tokens: token0={token0}, token1={token1}, fee={fee}")
if {token0, token1} != {WFLR_ADDRESS, USDC_ADDRESS} or fee != FEE_TIER:
    logger.error("Pool mismatch: tokens or fee incorrect")
    exit(1)
logger.info("Pool verified successfully")

# Step 5: Check pool state
logger.info("=== STEP 5: CHECKING POOL STATE ===")
slot0 = pool.functions.slot0().call()
liquidity = pool.functions.liquidity().call()
logger.debug(f"Slot0: {slot0}")
logger.debug(f"Liquidity: {liquidity}")

# Step 6: Get decimals and balance
logger.info("=== STEP 6: FETCHING TOKEN DETAILS AND BALANCE ===")
decimals_wflr = wflr_contract.functions.decimals().call()
decimals_usdc = usdc_contract.functions.decimals().call()
balance_wflr = wflr_contract.functions.balanceOf(USER_ADDRESS).call()
logger.debug(f"WFLR decimals: {decimals_wflr}, USDC.e decimals: {decimals_usdc}")
logger.debug(f"User WFLR balance: {balance_wflr} wei ({balance_wflr / 10**decimals_wflr} WFLR)")

# Step 7: Test swap (1 WFLR -> USDC.e)
logger.info("=== STEP 7: TESTING SWAP (1 WFLR -> USDC.e) ===")
amount_in = 1 * 10**decimals_wflr
if balance_wflr < amount_in:
    logger.error(f"Insufficient balance: {balance_wflr} < {amount_in}")
    exit(1)

deadline = w3.eth.get_block("latest")["timestamp"] + 300
params = (WFLR_ADDRESS, USDC_ADDRESS, FEE_TIER, USER_ADDRESS, deadline, amount_in, 1, 0)
logger.debug(f"Swap params: {params}")

try:
    amount_out = universal_router.functions.exactInputSingle(params).call()
    logger.info(f"Swap successful! Expected USDC.e output: {amount_out} wei ({amount_out / 10**decimals_usdc} USDC.e)")
except ContractLogicError as e:
    logger.error(f"Swap failed: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")

logger.info("=== CHECK COMPLETE ===")


    
    
swap_tx = universal_router.functions.exactInputSingle(params).build_transaction({
    'from': USER_ADDRESS,
    'nonce': 76,
    "maxFeePerGas": w3.eth.gas_price * w3.eth.max_priority_fee,
    "maxPriorityFeePerGas": w3.eth.max_priority_fee,
    'chainId': 14,
    "type": 2,
})










