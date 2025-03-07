import json
import logging
import structlog

import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)
logger2 = structlog.get_logger(__name__)

params={
    "module": "contract",
    "action": "getabi",
    "address": "0x12e605bc104e93B45e1aD99F9e555f659051c2BB",
}

headers = {"accept": "application/json"}
try:
    response = requests.get(
        "https://flare-explorer.flare.network/api", params=params, headers=headers, timeout=10
    )
    response.raise_for_status()
    try:
        json_response = response.json()
    except ValueError:
        # If the response is not JSON, log the raw content
        logger2.error("Response is not in JSON format, raw content:", extra={"response_text": response.text})
        with open('invalid_response.json', 'w') as f:
            f.write(response.text)
        
        # Raise an exception to stop the program
        raise ValueError("Response content is not valid JSON.")


    if "result" not in json_response:
        msg = (f"Malformed response from API: {json_response}",)
        raise ValueError(msg)

except (RequestException, Timeout):
    logger.exception("Network error during API request")
    raise

print(response.json())



