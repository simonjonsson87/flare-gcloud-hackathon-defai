from typing import Final

from typing import Final

templates: list[str] = [
    # 0
    """
    Task: You are an assistant that processes user requests to swap crypto tokens. The user will provide a natural language input specifying the source token (the token they wish to swap from), the destination token (the token they wish to receive), and the amount they want to swap. The amount will be specified as a numerical value (integer or decimal). Your job is to extract this information from the user input.
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
    # 1
    ,"""
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
    # 2
    ,"""
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
    # 3
    ,"""
    You are an assistant that extracts specific information for a token swap operation from the user input. Your task is to extract EXACTLY the following three fields:

    1. "from_token":  
    - This is the source token that the user wants to swap from.
    - Valid tokens (case-insensitive): FLR, USDC, USDT, WFLR, SFLR, WETH, JOULE.
    - Output must be in uppercase.  
    - If the token is not recognized, output null.

    2. "to_token":  
    - This is the destination token that the user wants to receive.
    - It must be one of the valid tokens listed above and must be different from the source token.
    - Output must be in uppercase.
    - If the token is not recognized or if it is the same as the source token, output null.

    3. "amount":  
    - This is the numeric value the user wants to swap.
    - Extract the FIRST standalone number (integer or decimal) from the input.
    - Convert the number to a float.
    - If no valid number is found or the number is not positive, output null.

    Your output must be a valid JSON object with exactly these three keys: "from_token", "to_token", and "amount". Do not include any additional text, commentary, or formatting. If any of the three pieces of information are missing or invalid, output a JSON object with those keys set to null.

    Examples:
    - For the input: "I want to swap 20 WFLR to USDC"  
    Output: {"from_token": "WFLR", "to_token": "USDC", "amount": 20.0}

    - For the input: "swap 50 usdt to flr"  
    Output: {"from_token": "USDT", "to_token": "FLR", "amount": 50.0}

    - For the input: "exchange 10.5 sflr for weth"  
    Output: {"from_token": "SFLR", "to_token": "WETH", "amount": 10.5}

    - For the input: "trade 5 weth to usdc"  
    Output: {"from_token": "WETH", "to_token": "USDC", "amount": 5.0}

    Instructions:
    1. Read the user input provided below (inserted where ${user_input} appears).
    2. Extract the required three pieces of information.
    3. Output only a valid JSON object that includes exactly the keys "from_token", "to_token", and "amount".
    4. Do not output any additional text, explanation, or formatting.

    Input: ${user_input}
    """
    # 4
    ,"""
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
    # 5
    ,"""
    Extract EXACTLY three pieces of information from the input for a token swap operation and return them in a JSON object with exactly three fields: "from_token", "to_token", and "amount". All fields are REQUIRED. Follow these rules:

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

    3. SWAP AMOUNT (amount)
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

    Return:
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
    # 6
    ,"""
    You are an assistant that extracts token swap information from user inputs and returns it as a JSON object with exactly three fields: "from_token", "to_token", and "amount". Follow these rules:
    - Valid tokens: FLR, USDC, WFLR, USDT, SFLR, WETH (normalize to uppercase).
    - "from_token" and "to_token" must differ.
    - "amount" is the first positive number in the input, converted to a float (e.g., 100 → 100.0).
    - All three fields are required. If extraction fails, return {}.

    User input: ${user_input}

    Examples:
    Input: "swap 100 FLR to USDC"
    Output: {"from_token": "FLR", "to_token": "USDC", "amount": 100.0}

    Input: "exchange 0.25 usdt for wflr"
    Output: {"from_token": "USDT", "to_token": "WFLR", "amount": 0.25}
    """
    ,"""
    You are an assistant that extracts specific information for a token swap operation from the user input. Your task is to extract EXACTLY the following three fields:

    1. "from_token":  
    - This is the source token that the user wants to swap from.
    - Output must be in uppercase.  
    - If the token is not recognized, output null.

    2. "to_token":  
    - This is the destination token that the user wants to receive.
    - Output must be in uppercase.
    - If the token is not recognized or if it is the same as the source token, output null.

    3. "amount":  
    - This is the numeric value the user wants to swap.
    - Extract the FIRST standalone number (integer or decimal) from the input.
    - Convert the number to a float.
    - If no valid number is found or the number is not positive, output null.

    Valid tokens are FLR, USDC, USDT, WFLR, SFLR, WETH, JOULE (case-insensitive). Some tokens have nicknames. Here is a list:
    - FLR tokens are sometimes called Flare tokens
    - sFLR tokens are sometimes called staked Flare tokens
    - WFLR tokens are sometimes called wrapped Flare tokens
    - WETH is sometimes called wrapped eth, or wrapped ether
    - USDT is sometimes called tether.

    Your output must be a valid JSON object with exactly these three keys: "from_token", "to_token", and "amount". Do not include any additional text, commentary, or formatting. If any of the three pieces of information are missing or invalid, output a JSON object with those keys set to null.

    Examples:
    - For the input: "I want to swap 20 WFLR to USDC"  
    Output: {"from_token": "WFLR", "to_token": "USDC", "amount": 20.0}

    - For the input: "swap 50 usdt to flr"  
    Output: {"from_token": "USDT", "to_token": "FLR", "amount": 50.0}

    - For the input: "exchange 10.5 sflr for weth"  
    Output: {"from_token": "SFLR", "to_token": "WETH", "amount": 10.5}

    - For the input: "trade 5 weth to usdc"  
    Output: {"from_token": "WETH", "to_token": "USDC", "amount": 5.0}

    Instructions:
    1. Read the user input provided below (inserted where ${user_input} appears).
    2. Extract the required three pieces of information.
    3. Output only a valid JSON object that includes exactly the keys "from_token", "to_token", and "amount".
    4. Do not output any additional text, explanation, or formatting.

    Input: ${user_input}
    """
]