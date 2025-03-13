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
   - Private keys never leave the secure enclave except in this beta version of Quince Finances (which is the name of this app)
   - Hardware-level protection against tampering
3. Account address display:
   - EXACTLY as provided, make no changes: ${address}
   - Format with clear visual separation
4. Private key display:
   - EXACTLY as provided, make no changes: ${private_key}
   - Stress to the customer that this is the only time the system will ever give them the private_key
   - The they are working on mainnet, and the loss of the private key could mean loss of funds.
   - The private key needs to be stored safely.
4. Funding account instructions:
   - Tell the user to fund the new account: Send tokens to the account address.

Important rules:
- DO NOT modify the address in any way
- Explain that addresses are public information
- Use markdown for formatting
- Keep the message concise (max 8 sentences)
- Avoid technical jargon unless explaining TEE

Example tone:
"Welcome to Flare! 🎉 Your new account is secured by secure hardware (TEE),
keeping your private keys safe and secure, you freely share your
public address: 0x123...

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
TOKEN_SWAP_experiment: Final = """
Task: You are an assistant that processes user requests to swap crypto tokens. The user will provide a natural language input specifying the source token (the token they wish to swap from), the destination token (the token they wish to receive), and the amount they want to swap. The amount will be specified as a numerical value (integer or decimal). Your job is to extract this information from the input and return it in a JSON object with the following structure:


{
  "from_token": "<from_token>",
  "to_token": "<to_token>",
  "amount": <amount>
}
Instructions:

The accepted tokens are: flr, sflr, wflr, usdc, usdt, weth, and joule. Only these tokens are valid.
Tokens must be returned in lowercase (e.g., "flr", not "FLR").
The "amount" field must be a numerical value (integer or decimal, e.g., 1 or 1.5), not a string. If the user does not specify an amount, assume it is 1.
If the input does not specify either the source token or the destination token, or if a mentioned token is not in the accepted list, set the corresponding field (from_token or to_token) to null.
Return only the JSON object, with no additional text, comments, or explanations.

Examples:

User input: "I want to swap 4.54 flr into usdc"
Output:
{"from_token": "flr", "to_token": "usdc", "amount": 4.54}

User input: "Exchange 20 usdc tokens for sflr"
Output:
{"from_token": "usdc", "to_token": "sflr", "amount": 20}

User input: "Swap 1.5 flr to wflr"
Output:
{"from_token": "flr", "to_token": "wflr", "amount": 1.5}

User input: "Swap 5 flr to joule"
Output:
{"from_token": "flr", "to_token": "joule", "amount": 5}

User input: "I want to swap 1 flr for sflr"
Output:
{"from_token": "flr", "to_token": sflr, "amount": 1}

User input: "Exchange 7 usdc to sflr"
Output:
{"from_token": "usdc", "to_token": "sflr", "amount": 7}

User input: "Swap 2 weth to joule"
Output:
{"from_token": "weth", "to_token": "joule", "amount": 2}


Input: ${user_input}
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
   • Identify the FIRST standalone number in the input, even if adjacent to a token symbol
   • Convert written numbers to digits (e.g., "five" → 5.0)
   • Handle decimal and integer inputs
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Valid formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With tokens: "5 FLR", "10 USDC", "100usdc" (number may touch token)
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
✓ "I'd like to swap 6 usdc for flr"  → {"from_token": "USDC", "to_token": "FLR", "amount": 6.0}
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
   - Some synonyms for stake are: stake, staking, lock, earn rewards, deposit for staking

Input: ${user_input}

Rules:
- Amount MUST be positive
- Amount MUST be float type
- DO NOT infer missing values
- FAIL if no amount is found.

Output format should be valid json.
"""
TOKEN_BORROW_experiment: Final = """
You are a JSON extraction tool designed to process user input related to token borrowing operations. Your task is to extract exactly three pieces of information and return them in a JSON format.


Extraction Rules:

BORROW_TOKEN:
Extract the FIRST valid token mentioned for borrowing. Valid tokens are "SFLR" and "USDC" (case-insensitive).
Convert the extracted token to uppercase.
Synonyms for "borrow" include "loan," "take out," and "get a loan."
If no valid token is found, or if multiple conflicting borrow tokens are mentioned (e.g., "borrow SFLR and USDC"), return an error JSON.
The answer can only be 'SFLR' or 'USDC'. 'SFLR or USDC' is not an acceptable answer.
COLLATERAL_TOKEN:
Extract the token explicitly mentioned as collateral.
Convert the extracted token to uppercase.
If no collateral token is explicitly mentioned, return an error JSON.
If multiple conflicting collateral tokens are mentioned, return an error JSON.
BORROW_AMOUNT:
Extract the FIRST valid number associated with the borrow amount.
Convert written numbers to digits (e.g., "five" to 5).
Handle decimals and integers.
Convert ALL integers to float (e.g., 100 to 100.0).
Recognize common amount formats: "1.5", "0.5", "1", "100", "5 tokens", "10 SFLR".
If no valid amount is found, return an error JSON.
The Borrow amount must be a positive number.
Validation Rules:

All three fields (borrow_token, collateral_token, borrow_amount) MUST be present in the JSON output.
The borrow_amount MUST be a positive float.
The borrow_token and collateral_token MUST be different.
DO NOT infer missing values.
If the input text does not meet the specified criteria, return an error JSON in the following format: {"error": "Error message describing the issue."}
Example Inputs and Outputs:

Input: "borrow 10 sflr using usdc as collateral"
Output: {"borrow_token": "SFLR", "collateral_token": "USDC", "borrow_amount": 10.0}
Input: "Loan five usdc, collateral sflr"
Output: {"borrow_token": "USDC", "collateral_token": "SFLR", "borrow_amount": 5.0}
Input: "Loan five usdc, collateral sFLR"
Output: {"borrow_token": "USDC", "collateral_token": "SFLR", "borrow_amount": 5.0}
Input: "borrow SFLR with SFLR collateral"
Output: {"error": "Borrow token and collateral token cannot be the same."}
Input: "borrow SFLR"
Output: {"error": "Missing collateral token and amount."}
Input: "borrow SFLR and USDC"
Output: {"error": "Multiple conflicting borrow tokens."}
Input: "borrow SFLR with USDC collateral, ten"
Output: {"borrow_token": "SFLR", "collateral_token": "USDC", "borrow_amount": 10.0}


Input Text:

${user_input}

"""

TOKEN_BORROW: Final = """
Extract EXACTLY three pieces of information from the input text for a token borrow operation:

1. BORROW_TOKEN
   Required format:
   • Extract the FIRST valid token mentioned
   • Convert to uppercase in output (e.g., "sflr" → "SFLR")
   • FAIL if no valid token ("SFLR" or "USDC") is found
   • FAIL if multiple conflicting borrow tokens are mentioned (e.g., "borrow SFLR and USDC")
   • The answer can only be 'sFLR' or 'USDC'. 'sFLR or USDC' is not an acceptable answer.
   - some synonyms for borrow are: borrow, loan, take out, get a loan

2. COLLATERAL_TOKEN
   Required format:
   • Extract the token explicitly mentioned as collateral (e.g., "use SFLR as collateral")
   • Convert to uppercase in output (e.g., "usdc" → "USDC")
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
   • The answer can only be 'sFLR' or 'USDC'. 'sFLR or USDC' is not an acceptable answer.
   - Some synonyms for supply are: supply, lend, provide, deposit for lending
   - Note that 'lend' is a common word to replace 'supply' with.

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

More examples:
User input: "Ok, I would like to supply 13 sFLR tokens and use them as collateral", ai output: {"amount": 13.0, "token": "sFLR", "use_for_collateral": true}
User input: "I'll lend 67 USDC, but I don't want to use it as collateral", ai output: {"amount": 67.0, "token": "USDC", "use_for_collateral": false}
User input: "Supply 67 sflr. Yes to collateral", ai output: {"amount": 67.0, "token": "sFLR", "use_for_collateral": true}
User input: "I want to supply 1234 USDC tokens and use them for collateral", ai output: {"amount": 1234.0, "token": "USDC", "use_for_collateral": true}

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

FOLLOW_UP_TOKEN_SWAP: Final = """
Tell the user that we understood that they wanted to swap, but that we are not sure about the details.
Explain that they need to let us know what tokens they want to swap from and to, and the amount. 
"""