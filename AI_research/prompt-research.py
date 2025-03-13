from swap_templates import templates

#from typing import TypedDict
from typing_extensions import TypedDict

from dataclasses import dataclass
from enum import Enum
from string import Template
from typing import Final
from typing import Any

import json, sys

import structlog
logger = structlog.get_logger(__name__)

import google.generativeai as genai
import structlog
#from google.generativeai.types import ContentDict

class Response(TypedDict):
    from_token: str
    to_token: str
    amount: float

class PromptInputs(TypedDict, total=False):
    user_input: str
    text: str
    content: str
    code: str


@dataclass
class Prompt:
    name: str
    description: str
    template: str
    required_inputs: list[str] | None
    response_schema: type | None
    response_mime_type: str | None
    examples: list[dict[str, str]] | None = None
    category: str | None = None
    version: str = "1.0"

    def format(self, **kwargs: str | PromptInputs) -> str:
        if not self.required_inputs:
            return self.template

        try:
            return Template(self.template).safe_substitute(**kwargs)
        except KeyError as e:
            missing_keys = set(self.required_inputs) - set(kwargs.keys())
            if missing_keys:
                msg = f"Missing required inputs: {missing_keys}"
                raise ValueError(msg) from e
            raise
               
        
def get_formatted_prompt(template, **kwargs: Any
) -> tuple[str, str | None, type | None]:
    try:
        prompt = Prompt(
            name="semantic_router",
            description="Some desc.",
            template=template,
            required_inputs=["user_input"],
            response_mime_type="application/json",
            response_schema=Response,
            category="generic"
        )
        formatted = prompt.format(**kwargs)
    except Exception as e:
        logger.exception(
            "prompt_formatting_failed", error=str(e)
        )
        raise
    else:
        return (formatted, prompt.response_mime_type, prompt.response_schema)     
   
@dataclass
class ModelResponse:
    text: str
    raw_response: Any  # Original provider response
    metadata: dict[str, Any]    
       
genai.configure(api_key="AIzaSyCka9NwqsnJT4w6dNUF-rYznO5U4p3WgP0")
model = genai.GenerativeModel(model_name="gemini-2.0-flash")  
    
def generate(
    prompt: str,
    response_mime_type: str | None = None,
    response_schema: Any | None = None,
) -> ModelResponse:

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig( 
            response_mime_type=response_mime_type
            #, response_schema=response_schema
            , max_output_tokens=100
        ),
    )
    #logger.debug("generate", prompt=prompt, response_text=response.text)
    return ModelResponse(
        text=response.text,
        raw_response=response,
        metadata={
            "candidate_count": len(response.candidates),
            "prompt_feedback": response.prompt_feedback,
        },
    )  
    
         
#####################################################################
# Test cases
#####################################################################
class InputOutput:
    def __init__(self, user_input: str, expected_output: str):
        self.user_input = user_input
        self.expected_output = expected_output
    
test_cases = [
    InputOutput("I want to swap 20 WFLR to USDC", '{"from_token": "WFLR", "to_token": "USDC", "amount": 20.0}'),
    InputOutput("swap 50 usdt to flr", '{"from_token": "USDT", "to_token": "FLR", "amount": 50.0}'),
    InputOutput("exchange 10.5 sflr for weth", '{"from_token": "SFLR", "to_token": "WETH", "amount": 10.5}'),
    InputOutput("convert 100 FLR to USDT", '{"from_token": "FLR", "to_token": "USDT", "amount": 100.0}'),
    InputOutput("trade 5 WETH to USDC", '{"from_token": "WETH", "to_token": "USDC", "amount": 5.0}'),
    InputOutput("I need to swap 200 flr to wflr", '{"from_token": "FLR", "to_token": "WFLR", "amount": 200.0}'),
    InputOutput("transfer 75.3 USDC to FLR", '{"from_token": "USDC", "to_token": "FLR", "amount": 75.3}'),
    InputOutput("I would like to swap 1.5 WETH to SFLR", '{"from_token": "WETH", "to_token": "SFLR", "amount": 1.5}'),
    InputOutput("Change 0.25 USDT to WFLR", '{"from_token": "USDT", "to_token": "WFLR", "amount": 0.25}'),
    InputOutput("Please exchange 99 FLR to WETH", '{"from_token": "FLR", "to_token": "WETH", "amount": 99.0}'),
    InputOutput("Turn 300 USDT into WFLR", '{"from_token": "USDT", "to_token": "WFLR", "amount": 300.0}'),
    InputOutput("Make 42 WFLR into USDT", '{"from_token": "WFLR", "to_token": "USDT", "amount": 42.0}'),
    InputOutput("Swap 88 SFLR for FLR", '{"from_token": "SFLR", "to_token": "FLR", "amount": 88.0}'),
    InputOutput("I need 5.55 FLR in exchange for WETH", '{"from_token": "WETH", "to_token": "FLR", "amount": 5.55}'),
    InputOutput("Send 0.75 WETH to USDT", '{"from_token": "WETH", "to_token": "USDT", "amount": 0.75}'),
    InputOutput("Trade 1200 FLR to WFLR", '{"from_token": "FLR", "to_token": "WFLR", "amount": 1200.0}'),
    InputOutput("I want to convert 2.89 USDC into SFLR", '{"from_token": "USDC", "to_token": "SFLR", "amount": 2.89}'),
    InputOutput("Get 67.8 WFLR in exchange for FLR", '{"from_token": "FLR", "to_token": "WFLR", "amount": 67.8}'),
    InputOutput("Move 500 SFLR to WETH", '{"from_token": "SFLR", "to_token": "WETH", "amount": 500.0}'),
    InputOutput("Swap 15 USDT with USDC", '{"from_token": "USDT", "to_token": "USDC", "amount": 15.0}'),
     InputOutput("Swap 10 Flare to USDC", '{"from_token": "FLR", "to_token": "USDC", "amount": 10.0}'),
    InputOutput("Exchange 20 staked Flare to WETH", '{"from_token": "SFLR", "to_token": "WETH", "amount": 20.0}'),
    InputOutput("Convert 30 wrapped Flare to USDT", '{"from_token": "WFLR", "to_token": "USDT", "amount": 30.0}'),
    InputOutput("Trade 40 tether to FLR", '{"from_token": "USDT", "to_token": "FLR", "amount": 40.0}'),
    InputOutput("I want to swap 50 wrapped eth to USDC", '{"from_token": "WETH", "to_token": "USDC", "amount": 50.0}'),
    InputOutput("Swap 5 Flare tokens to USDC", '{"from_token": "FLR", "to_token": "USDC", "amount": 5.0}'),
    InputOutput("exchange 10 staked flare tokens to weth", '{"from_token": "SFLR", "to_token": "WETH", "amount": 10.0}'),
    InputOutput("convert 15 wrapped flare tokens to usdt", '{"from_token": "WFLR", "to_token": "USDT", "amount": 15.0}'),
    InputOutput("trade 20 tether tokens to flr", '{"from_token": "USDT", "to_token": "FLR", "amount": 20.0}'),
    InputOutput("I want to swap 25 wrapped ether to usdc", '{"from_token": "WETH", "to_token": "USDC", "amount": 25.0}'),
    InputOutput("Swap 60 flare for usdc", '{"from_token": "FLR", "to_token": "USDC", "amount": 60.0}'),
    InputOutput("exchange 70 staked flare for weth", '{"from_token": "SFLR", "to_token": "WETH", "amount": 70.0}'),
    InputOutput("convert 80 wrapped flare for usdt", '{"from_token": "WFLR", "to_token": "USDT", "amount": 80.0}'),
    InputOutput("trade 90 tether for flr", '{"from_token": "USDT", "to_token": "FLR", "amount": 90.0}'),
    InputOutput("I want to swap 100 wrapped ether for usdc", '{"from_token": "WETH", "to_token": "USDC", "amount": 100.0}'),
    InputOutput("Swap 11 flare token for usdc", '{"from_token": "FLR", "to_token": "USDC", "amount": 11.0}'),
    InputOutput("exchange 12 staked flare token for weth", '{"from_token": "SFLR", "to_token": "WETH", "amount": 12.0}'),
    InputOutput("convert 13 wrapped flare token for usdt", '{"from_token": "WFLR", "to_token": "USDT", "amount": 13.0}'),
    InputOutput("trade 14 tether token for flr", '{"from_token": "USDT", "to_token": "FLR", "amount": 14.0}'),
    InputOutput("I want to swap 15 wrapped eth token for usdc", '{"from_token": "WETH", "to_token": "USDC", "amount": 15.0}')
]
#

#####################################################################
# Execution and Statistics per Template
#####################################################################

overall_total = 0
overall_passed = 0
overall_failed = 0
print(len(templates))
print(len(templates[0]))
print(len(test_cases))
#sys.exit()
templates = [templates[-1]]
for template_idx, template in enumerate(templates):
    template_total = 0
    template_passed = 0
    template_failed = 0

    test_case_idx = 0
    for test_case in test_cases:
        overall_total += 1
        template_total += 1

        # Get the prompt using the current test case's input
        prompt, mime_type, schema = get_formatted_prompt(template, user_input=test_case.user_input)
        # Generate a response from the model
        response = generate(prompt=prompt, response_mime_type=mime_type, response_schema=schema)
        #print("==========================================")
        #print(prompt)
        #print(response)
        try:
            actual = json.loads(response.text)
        except Exception as e:
            print(f"Template {template_idx} Test Case: Error parsing response JSON: {e}")
            overall_failed += 1
            template_failed += 1
            continue

        try:
            expected = json.loads(test_case.expected_output)
        except Exception as e:
            print(f"Template {template_idx} Test Case: Error parsing expected JSON: {e}")
            overall_failed += 1
            template_failed += 1
            continue

        if actual == expected:
            #print(f"Template {template_idx} Test Case {test_case_idx} PASSED")
            overall_passed += 1
            template_passed += 1
        else:
            #print(f"Template {template_idx} Test Case {test_case_idx} FAILED")
            #print("Expected:", json.dumps(expected))
            #print("Actual  :", json.dumps(actual))
            overall_failed += 1
            template_failed += 1
            
        test_case_idx += 1    

    print(f"\nStatistics for Template {template_idx}:")
    print(f"  Total: {template_total}")
    print(f"  Passed: {template_passed}")
    print(f"  Failed: {template_failed}")
    print("---------------------------------------------------")

print(f"\nOverall Statistics:")
print(f"  Total test cases: {overall_total}")
print(f"  Passed: {overall_passed}")
print(f"  Failed: {overall_failed}")



