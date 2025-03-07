import json
import logging
import structlog

import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)
logger2 = structlog.get_logger(__name__)

class FlareExplorer:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.logger = logger
        self.logger2 = logger2.bind(blockchain="explorer")

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
                #self.logger2.debug("Response JSON:", extra={"json_response": json_response})
            except ValueError:
                # If the response is not JSON, log the raw content
                #self.logger2.error("Response is not in JSON format, raw content:", extra={"response_text": response.text})
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
        self.logger2.debug("Fetching ABI for `%s` from `%s`", contract_address, self.base_url)
        #self.logger.debug("Fetching ABI for `%s` from `%s`", contract_address, self.base_url)
        response = self._get(
            params={
                "module": "contract",
                "action": "getabi",
                "address": contract_address,
            }
        )
        #self.logger2.debug("After self._get() call", response=response)
        #return json.loads(response["result"])

        abi_list = json.loads(response["result"])  # Convert string to list
        #return {"abi": abi_list}    # Convert list to dict

        return abi_list