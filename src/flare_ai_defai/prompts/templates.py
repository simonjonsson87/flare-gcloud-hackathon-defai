from typing import Final

SEMANTIC_ROUTER: Final = """
Classify the following user input into EXACTLY ONE category. Analyze carefully and choose the most specific matching category.

Categories (in order of precedence):
1. GENERATE_ACCOUNT
   • Keywords: create wallet, new account, generate address, make wallet
   • Must express intent to create/generate new account/wallet
   • Ignore if just asking about existing accounts

2. SEND_TOKEN
   • Keywords: send, transfer, pay, give tokens
   • Must include intent to transfer tokens to another address
   • Should involve one-way token movement

3. SWAP_TOKEN
   • Keywords: swap, exchange, trade, convert tokens
   • Must involve exchanging one token type for another
   • Should mention both source and target tokens

4. REQUEST_ATTESTATION
   • Keywords: attestation, verify, prove, check enclave
   • Must specifically request verification or attestation
   • Related to security or trust verification

5. CONVERSATIONAL (default)
   • Use when input doesn't clearly match above categories
   • General questions, greetings, or unclear requests
   • Any ambiguous or multi-category inputs
   
6. STAKE_STAKE
   - Keywords: stake, staking, lock, earn rewards, deposit for staking
   - Must express intent to stake or lock tokens to earn rewards or participate in a staking mechanism.
   - Typically involves committing tokens to a protocol or smart contract for a period.
   - Ignore if the user is just asking about staking without intent to perform the action.
   Examples:
   "I want to stake 10 FLR."
   "Can you help me lock my tokens for staking?"
   "Stake my tokens to earn rewards."
   
7. SUPPLY_TOKEN
   - Keywords: supply, lend, provide, deposit for lending
   - Must indicate intent to supply or lend tokens to a protocol (e.g., a lending pool or liquidity pool).
   - Involves depositing tokens to enable others to borrow or use them, often for interest.
   - Ignore if the user is just inquiring about supplying without intent to act.
   Examples:
   "Supply 5 FLR to the lending pool."
   "I want to lend my tokens."
   "Deposit 20 tokens for others to borrow."   
   
8. BORROW_TOKEN
   - Keywords: borrow, loan, take out, get a loan
   - Must express intent to borrow tokens from a protocol or pool, typically requiring collateral or a repayment plan.
   - Involves requesting tokens with an obligation to return them later (possibly with interest).
   - Ignore if the user is just asking about borrowing without intent to proceed.
   Examples:
   "Borrow 3 FLR from the pool."
   "Can I take out a loan of 10 tokens?"
   "Get me a loan in FLR."   

Input: ${user_input}

Instructions:
- Choose ONE category only
- Select most specific matching category
- Default to CONVERSATIONAL if unclear
- Ignore politeness phrases or extra context
- Focus on core intent of request
"""

GENERATE_ACCOUNT: Final = """
Generate a welcoming message that includes ALL of these elements in order:

1. Welcome message that conveys enthusiasm for the user joining
2. Security explanation:
   - Account is secured in a Trusted Execution Environment (TEE)
   - Private keys never leave the secure enclave
   - Hardware-level protection against tampering
3. Account address display:
   - EXACTLY as provided, make no changes: ${address}
   - Format with clear visual separation
4. Funding account instructions:
   - Tell the user to fund the new account: [Add funds to account](https://faucet.flare.network/coston2)

Important rules:
- DO NOT modify the address in any way
- Explain that addresses are public information
- Use markdown for formatting
- Keep the message concise (max 4 sentences)
- Avoid technical jargon unless explaining TEE

Example tone:
"Welcome to Flare! 🎉 Your new account is secured by secure hardware (TEE),
keeping your private keys safe and secure, you freely share your
public address: 0x123...
[Add funds to account](https://faucet.flare.network/coston2)
Ready to start exploring the Flare network?"
"""

TOKEN_SEND: Final = """
Extract EXACTLY two pieces of information from the input text for a token send operation:

1. DESTINATION ADDRESS
   Required format:
   • Must start with "0x"
   • Exactly 42 characters long
   • Hexadecimal characters only (0-9, a-f, A-F)
   • Extract COMPLETE address only
   • DO NOT modify or truncate
   • FAIL if no valid address found
   - Ensure that your extracted address is an address only, without any more characters at the end. It cannot be longer than a EVM address normally is.

2. TOKEN AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5)
   • Handle decimals and integers
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Recognize common amount formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With words: "5 tokens", "10 FLR"
   • Extract first valid number only
   • FAIL if no valid amount found

Input: ${user_input}

Rules:
- Both fields MUST be present
- Amount MUST be positive
- Amount MUST be float type
- DO NOT infer missing values
- DO NOT modify the address
- FAIL if either value is missing or invalid

Output format should be valid json.
"""

TOKEN_SWAP: Final = """
Extract EXACTLY three pieces of information from the input for a token swap operation:

1. SOURCE TOKEN (from_token)
   Valid formats:
   • Native token: "FLR" or "flr"
   • Listed pairs only: "USDC", "WFLR", "USDT", "sFLR", "WETH"
   • Case-insensitive match
   • Strip spaces and normalize to uppercase
   • FAIL if token not recognized

2. DESTINATION TOKEN (to_token)
   Valid formats:
   • Same rules as source token
   • Must be different from source token
   • FAIL if same as source token
   • FAIL if token not recognized

3. SWAP AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5.0)
   • Handle decimal and integer inputs
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Valid formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With tokens: "5 FLR", "10 USDC"
   • Extract first valid number only
   • Amount MUST be positive
   • FAIL if no valid amount found

Input: ${user_input}

Response format:
{
  "from_token": "<UPPERCASE_TOKEN_SYMBOL>",
  "to_token": "<UPPERCASE_TOKEN_SYMBOL>",
  "amount": <float_value>
}

Processing rules:
- All three fields MUST be present
- DO NOT infer missing values
- DO NOT allow same token pairs
- Normalize token symbols to uppercase
- Amount MUST be float type
- Amount MUST be positive
- FAIL if any value missing or invalid

Examples:
✓ "swap 100 FLR to USDC" → {"from_token": "FLR", "to_token": "USDC", "amount": 100.0}
✓ "exchange 50.5 flr for usdc" → {"from_token": "FLR", "to_token": "USDC", "amount": 50.5}
✗ "swap flr to flr" → FAIL (same token)
✗ "swap tokens" → FAIL (missing amount)
"""

CONVERSATIONAL: Final = """
I am Artemis, an AI assistant representing Flare, the blockchain network specialized in cross-chain data oracle services.

Key aspects I embody:
- Deep knowledge of Flare's technical capabilities in providing decentralized data to smart contracts
- Understanding of Flare's enshrined data protocols like Flare Time Series Oracle (FTSO) and  Flare Data Connector (FDC)
- Friendly and engaging personality while maintaining technical accuracy
- Creative yet precise responses grounded in Flare's actual capabilities

When responding to queries, I will:
1. Address the specific question or topic raised
2. Provide technically accurate information about Flare when relevant
3. Maintain conversational engagement while ensuring factual correctness
4. Acknowledge any limitations in my knowledge when appropriate

<input>
${user_input}
</input>
"""

REMOTE_ATTESTATION: Final = """
A user wants to perform a remote attestation with the TEE, make the following process clear to the user:

1. Requirements for the users attestation request:
   - The user must provide a single random message
   - Message length must be between 10-74 characters
   - Message can include letters and numbers
   - No additional text or instructions should be included

2. Format requirements:
   - The user must send ONLY the random message in their next response

3. Verification process:
   - After receiving the attestation response, the user should https://jwt.io
   - They should paste the complete attestation response into the JWT decoder
   - They should verify that the decoded payload contains your exact random message
   - They should confirm the TEE signature is valid
   - They should check that all claims in the attestation response are present and valid
"""


TX_CONFIRMATION: Final = """
Respond with a confirmation message for the successful transaction that:

1. Required elements:
   - Express positive acknowledgement of the successful transaction
   - Include the EXACT transaction hash link with NO modifications:
     [See transaction on Explorer](${block_explorer}/tx/${tx_hash})
   - Place the link on its own line for visibility

2. Message structure:
   - Start with a clear success confirmation
   - Include transaction link in unmodified format
   - End with a brief positive closing statement

3. Link requirements:
   - Preserve all variables: ${block_explorer} and ${tx_hash}
   - Maintain exact markdown link syntax
   - Keep URL structure intact
   - No additional formatting or modification of the link

Sample format:
Great news! Your transaction has been successfully confirmed. 🎉

[See transaction on Explorer](${block_explorer}/tx/${tx_hash})

Your transaction is now securely recorded on the blockchain.
"""

TX_FAILED: Final = """
Just apologise and say that the transaction could not be completed, either because we didn't understand the user.
Ask for clarify.
"""

TX_NO_CONFIRMATION: Final = """
Tell the user that we didn't get the confirmation we expected and therefore we have cancelled the transaction. Tell the user that they can initiate another one if they wish. If the user has asked a question in the message (${msg}), answer it.
"""

TOKEN_STAKE: Final = """
Extract EXACTLY one piece of information from the input text for a token send operation:
   
1. TOKEN AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5)
   • Handle decimals and integers
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Recognize common amount formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With words: "5 tokens", "10 FLR"
   • Extract first valid number only
   • FAIL if no valid amount found

Input: ${user_input}

Rules:
- Both fields MUST be present
- Amount MUST be positive
- Amount MUST be float type
- DO NOT infer missing values
- DO NOT modify the address
- FAIL if either value is missing or invalid

Output format should be valid json.
"""

TOKEN_BORROW: Final = """
Extract EXACTLY three pieces of information from the input text for a token borrow operation:

1. BORROW_TOKEN
   Required format:
   • Must be exactly one of: "SFLR" or "USDC" (case-insensitive)
   • Extract the FIRST valid token mentioned
   • Convert to uppercase in output (e.g., "sflr" → "SFLR")
   • FAIL if no valid token ("SFLR" or "USDC") is found
   • FAIL if multiple conflicting borrow tokens are mentioned (e.g., "borrow SFLR and USDC")

2. COLLATERAL_TOKEN
   Required format:
   • Must be exactly one of: "SFLR" or "USDC" (case-insensitive)
   • Extract the token explicitly mentioned as collateral (e.g., "use SFLR as collateral")
   • Convert to uppercase in output (e.g., "usdc" → "USDC")
   • FAIL if no valid collateral token ("SFLR" or "USDC") is found
   • FAIL if borrow and collateral tokens are the same (e.g., "borrow SFLR with SFLR collateral")
   • FAIL if multiple conflicting collateral tokens are mentioned

3. BORROW_AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5)
   • Handle decimals and integers
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Recognize common amount formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With words: "5 tokens", "10 SFLR"
   • Extract the FIRST valid number associated with the borrow amount
   • FAIL if no valid amount found

Input: ${user_input}

Rules:
- All three fields (BORROW_TOKEN, COLLATERAL_TOKEN, BORROW_AMOUNT) MUST be present
- BORROW_AMOUNT MUST be positive
- BORROW_AMOUNT MUST be float type
- BORROW_TOKEN and COLLATERAL_TOKEN MUST be different
- Only "SFLR" and "USDC" are acceptable as tokens
- DO NOT infer missing values
- FAIL if any value is missing or invalid

Output format should be valid JSON. Examples:
- Success: {"borrow_token": "SFLR", "collateral_token": "USDC", "borrow_amount": 10.0}
- Failure: {"error": "Missing or invalid borrow token. Please specify SFLR or USDC."}
"""

TOKEN_SUPPLY: Final = """
Extract EXACTLY three pieces of information from the input text for a token supply operation:

1. SUPPLY_TOKEN
   Required format:
   • Must be exactly one of: "SFLR" or "USDC" (case-insensitive)
   • Extract the FIRST valid token mentioned
   • Convert to uppercase in output (e.g., "sflr" → "SFLR")
   • FAIL if no valid token ("SFLR" or "USDC") is found
   • FAIL if multiple conflicting supply tokens are mentioned (e.g., "supply SFLR and USDC")

2. SUPPLY_AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5)
   • Handle decimals and integers
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Recognize common amount formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With words: "5 tokens", "10 SFLR"
   • Extract the FIRST valid number associated with the supply amount
   • FAIL if no valid amount found

3. USE_AS_COLLATERAL
   Boolean extraction rules:
   • Look for explicit indicators of collateral intent:
     - Positive: "use as collateral", "for collateral", "as collateral", "enable collateral", "with collateral option"
     - Negative: "don’t use as collateral", "no collateral", "not as collateral"
   • Default to FALSE if no explicit collateral intent is mentioned
   • Output as a boolean (true/false)
   • FAIL only if conflicting intents are present (e.g., "use as collateral and not as collateral")

Input: ${user_input}

Rules:
- SUPPLY_TOKEN and SUPPLY_AMOUNT MUST be present
- SUPPLY_AMOUNT MUST be positive
- SUPPLY_AMOUNT MUST be float type
- Only "SFLR" and "USDC" are acceptable as tokens
- USE_AS_COLLATERAL defaults to FALSE if not specified
- DO NOT infer missing SUPPLY_TOKEN or SUPPLY_AMOUNT values
- FAIL if SUPPLY_TOKEN or SUPPLY_AMOUNT is missing or invalid

Output format should be valid JSON. Examples:
- Success: {"supply_token": "SFLR", "supply_amount": 10.0, "use_as_collateral": false}
- Success: {"supply_token": "USDC", "supply_amount": 5.5, "use_as_collateral": true}
- Failure: {"error": "Missing or invalid supply token. Please specify SFLR or USDC."}
"""

FOLLOW_UP_TOKEN_STAKE: Final = """
Tell the user that we understood that they wanted to stake, but that we are not sure about the details. 
Inform the user that we only support staking JOULE for the moment. Also tell them that if they don't 
have any joule to stake, they can ask use to swap some for them. Clarify that they either need to tell us how much 
JOULE they want to stake, or swap some tokens first.
"""

FOLLOW_UP_TOKEN_BORROW: Final = """
Tell the user that we understood that they wanted to borrow, but that we are not sure about the details.
Explain that they need to tell use what token to borrow, which one to use as collateral, and the amount. 
Also inform them that only sFLR and USDC are valid. Both as collateral and the borrowed token.
"""

FOLLOW_UP_TOKEN_SUPPLY: Final = """
Tell the user that we understood that they wanted to supply, but that we are not sure about the details.
Explain that they need to let us know what token they want to supply, and the amount. We also need to 
know if they want to be able to use the token as collateral.
Also let them know that they can only supply sFLR and USDC. Point out that they can swap if they don't have
either of those tokens.
"""