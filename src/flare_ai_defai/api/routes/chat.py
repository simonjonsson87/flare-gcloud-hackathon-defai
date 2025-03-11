"""
Chat Router Module

This module implements the main chat routing system for the AI Agent API with Google Sign-In authentication.
"""

import json
import secrets
import datetime
import structlog
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import Web3RPCError
from google.oauth2 import id_token
from google.auth.transport import requests

from flare_ai_defai.ai import GeminiProvider
from flare_ai_defai.attestation import Vtpm, VtpmAttestationError
from flare_ai_defai.blockchain import FlareProvider
from flare_ai_defai.blockchain import FlareExplorer
from flare_ai_defai.prompts import PromptService, SemanticRouterResponse
from flare_ai_defai.settings import settings
from flare_ai_defai.blockchain import KineticMarket
from flare_ai_defai.blockchain import SparkDEX

from flare_ai_defai.storage.fake_storage import WalletStore

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,  # Add log level to event dict
        structlog.stdlib.add_logger_name, #add logger name
        structlog.processors.TimeStamper(fmt="iso"),  # Add timestamp
        structlog.processors.StackInfoRenderer(),  # Add stack info
        structlog.processors.format_exc_info,  # Format exceptions
        structlog.processors.JSONRenderer(sort_keys=True),  # Render as JSON
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)
logging.basicConfig(level=logging.DEBUG)
logger = structlog.get_logger(__name__)



# Session storage (use Redis or database in production)
sessions: dict[str, dict] = {}

# Google Client ID
GOOGLE_CLIENT_ID = "289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com"

# Models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)

class TokenRequest(BaseModel):
    token: str

class UserInfo(BaseModel):
    user_id: str
    email: str

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/verify")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    """Dependency to verify Google token and get user info"""
    try:
        # Verify Google ID token
        id_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Check if session exists
        if token not in sessions:
            raise HTTPException(status_code=401, detail="Invalid session")
            
        return UserInfo(user_id=id_info["sub"], email=id_info["email"])
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

class ChatRouter:
    def __init__(
        self,
        ai: GeminiProvider,
        blockchain: FlareProvider,
        flareExplorer: FlareExplorer,
        attestation: Vtpm,
        prompts: PromptService,
        kinetic_market: KineticMarket,
        sparkdex: SparkDEX,
        wallet_store: WalletStore
    ) -> None:
        self._router = APIRouter()
        self.ai = ai
        self.blockchain = blockchain
        self.flareExplorer = flareExplorer
        self.attestation = attestation
        self.prompts = prompts
        self.logger = logger.bind(router="chat")
        self._setup_routes()
        self.google_auth_client_id = "289493342717-rqktph7q97vsgegclf28ngfhuhcni1d8.apps.googleusercontent.com"
        self.kinetic_market = kinetic_market
        self.sparkdex = sparkdex
        self.wallet_store = wallet_store

    def _setup_routes(self) -> None:
        @self._router.post("/verify")
        async def verify(token_request: TokenRequest):
            self.logger.debug("Entered verify function.")
            """Verify Google ID token and create session"""
            try:
                # Verify Google token
                id_info = id_token.verify_oauth2_token(
                    token_request.token,
                    requests.Request(),
                    GOOGLE_CLIENT_ID
                )
                
                # Store session with Google token
                sessions[token_request.token] = {
                    "user_id": id_info["sub"],
                    "email": id_info["email"],
                    "created_at": datetime.datetime.utcnow().isoformat()
                }
                
                self.logger.info(
                    "User authenticated",
                    user_id=id_info["sub"],
                    email=id_info["email"]
                )
                return {
                    "message": "User verified",
                    "user_id": id_info["sub"],
                    "email": id_info["email"]
                }
            except ValueError as e:
                self.logger.error(f"Token verification failed: {e}")
                raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        @self._router.post("/")
        async def chat(
            message: ChatMessage,
            user: UserInfo = Depends(get_current_user)
        ) -> dict[str, str]:
            """Handle chat messages with authenticated user"""
            try:
                self.logger.debug(
                    "In chat function - Received message",
                    message=message.message,
                    user_id=user.user_id
                )

                if message.message.startswith("/"):
                    return await self.handle_command(message.message)
                self.logger.debug(tx_queue=self.blockchain.tx_queue, tx_queue_len=len(self.blockchain.tx_queue))
                if (self.blockchain.tx_queue):
                    if (message.message == self.blockchain.tx_queue[-1].confirm_msg):
                        try:
                            self.logger.debug("About to send_tx_in_queue")
                            tx_hash = self.blockchain.send_tx_in_queue(user)
                            prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                                "tx_confirmation",
                                tx_hash=tx_hash[-1],
                                block_explorer=settings.web3_explorer_url,
                            )
                            response = self.ai.generate(
                                prompt=prompt,
                                response_mime_type=mime_type,
                                response_schema=schema,
                            )
                            return {"response": response.text}
                        except Web3RPCError as e:
                            self.logger.exception("send_tx_failed", error=str(e))
                            return {"response": f"Transaction failed: {str(e)}"}
                    else:
                        self.blockchain.tx_queue = []
                        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                            "tx_no_confirmation",
                            msg=message
                        )
                        response = self.ai.generate(
                            prompt=prompt,
                            response_mime_type=mime_type,
                            response_schema=schema,
                        )  
                        return {"response": response.text}      

                if self.attestation.attestation_requested:
                    try:
                        resp = self.attestation.get_token([message.message])
                        self.attestation.attestation_requested = False
                        return {"response": resp}
                    except VtpmAttestationError as e:
                        return {"response": f"Attestation failed: {str(e)}"}

                route = await self.get_semantic_route(message.message)
                return await self.route_message(route, message.message, user)

            except Exception as e:
                self.logger.exception("message_handling_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self._router.post("/logout")
        async def logout(token: str = Depends(oauth2_scheme)):
            """Remove user session"""
            if token in sessions:
                del sessions[token]
                self.logger.info("User logged out", token=token)
                return {"message": "Logged out successfully"}
            return {"message": "No active session"}
        
    async def verify_google_token(self, token: str) -> dict[str, str]:
        try:
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.google_auth_client_id
            )
            return {
                "user_id": id_info["sub"],
                "email": id_info["email"],
                "message": "User verified"
            }
        except ValueError as e:
            self.logger.error(f"Token verification failed: {e}")
            return {"error": f"Invalid token: {e}"}
   

    @property
    def router(self) -> APIRouter:
        """Get the FastAPI router with registered routes."""
        return self._router    
    
    async def handle_command(self, command: str) -> dict[str, str]:
        """
        Handle special command messages starting with '/'.

        Args:
            command: Command string to process

        Returns:
            dict[str, str]: Response containing command result
        """
        self.logger.debug("received command: ", command=command)
        if command == "/reset":
            self.blockchain.reset()
            self.ai.reset()
            return {"response": "Reset complete"}
        
        if command == "/queryDefi":
            self.logger.debug("In /queryDefi just before calling flare explorer")
            response = self.flareExplorer.get_contract_abi("0x12e605bc104e93B45e1aD99F9e555f659051c2BB")
            return {"response": json.dumps(response)}
        
        return {"response": "Unknown command"}

    async def get_semantic_route(self, message: str) -> SemanticRouterResponse:
        """
        Determine the semantic route for a message using AI provider.

        Args:
            message: Message to route

        Returns:
            SemanticRouterResponse: Determined route for the message
        """
        try:
            prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                "semantic_router", user_input=message
            )
            route_response = self.ai.generate(
                prompt=prompt, response_mime_type=mime_type, response_schema=schema
            )
            return SemanticRouterResponse(route_response.text)
        except Exception as e:
            self.logger.exception("routing_failed", error=str(e))
            return SemanticRouterResponse.CONVERSATIONAL

    async def route_message(
        self, route: SemanticRouterResponse, message: str, user: UserInfo
    ) -> dict[str, str]:
        """
        Route a message to the appropriate handler based on semantic route.

        Args:
            route: Determined semantic route
            message: Original message to handle

        Returns:
            dict[str, str]: Response from the appropriate handler
        """
        handlers = {
            SemanticRouterResponse.GENERATE_ACCOUNT: self.handle_generate_account,
            SemanticRouterResponse.SEND_TOKEN: self.handle_send_token,
            SemanticRouterResponse.SWAP_TOKEN: self.handle_swap_token,
            SemanticRouterResponse.REQUEST_ATTESTATION: self.handle_attestation,
            SemanticRouterResponse.CONVERSATIONAL: self.handle_conversation,
            SemanticRouterResponse.STAKE_TOKEN: self.handle_stake,
            SemanticRouterResponse.BORROW_TOKEN: self.handle_borrow,
            SemanticRouterResponse.SUPPLY_TOKEN: self.handle_supply,
        }

        handler = handlers.get(route)
        if not handler:
            return {"response": "Unsupported route"}

        return await handler(message, user)

    async def handle_generate_account(self, _: str, user: UserInfo) -> dict[str, str]:
        if self.blockchain.address:
            return {"response": f"Account exists - {self.blockchain.address}"}
        address = self.blockchain.generate_account(user)
        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "generate_account", address=address, user_id=user.user_id
        )
        gen_address_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        return {"response": gen_address_response.text}


    async def handle_attestation(self, _: str, user: UserInfo) -> dict[str, str]:
        """
        Handle attestation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing attestation request
        """
        prompt = self.prompts.get_formatted_prompt("request_attestation")[0]
        request_attestation_response = self.ai.generate(prompt=prompt)
        self.attestation.attestation_requested = True
        return {"response": request_attestation_response.text}
    
    
    async def handle_conversation(self, message: str, user: UserInfo) -> dict[str, str]:
        """
        Handle general conversation messages.

        Args:
            message: Message to process

        Returns:
            dict[str, str]: Response from AI provider
        """
        response = self.ai.send_message(message)
        return {"response": response.text}


    async def handle_send_token(self, message: str, user: UserInfo) -> dict[str, str]:
        """
        Handle token sending requests.

        Args:
            message: Message containing token sending details

        Returns:
            dict[str, str]: Response containing transaction preview or follow-up prompt
        """
        if not self.blockchain.address:
            await self.handle_generate_account(message, user)

        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "token_send", user_input=message
        )
        send_token_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        
        send_token_json = json.loads("{}")
        try:
            send_token_json = json.loads(send_token_response.text)
        except:
            self.logger.debug("We probably did not get valid json back from Gemini. See below.")
                
        self.logger.debug(message=message)
        self.logger.debug(prompt=prompt)
        self.logger.debug(mime_type=mime_type)
        self.logger.debug(schema=schema)
        self.logger.debug(send_token_response=send_token_response)
        self.logger.debug(send_token_json=send_token_json)
        self.logger.debug(len_send_token_json=len(send_token_json))        
                
        self.logger.debug(message=message, prompt=prompt, json_len=len(send_token_json), json=send_token_json)
        expected_json_len = 2
        if (
            len(send_token_json) != expected_json_len
            or send_token_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_send")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text}

        tx = self.blockchain.create_send_flr_tx(
            to_address=send_token_json.get("to_address"),
            amount=send_token_json.get("amount"),
            user=user
        )
        self.logger.debug("send_token_tx", tx=tx)
        txs = [tx]
        self.blockchain.add_tx_to_queue(msg=message, txs=txs)
        formatted_preview = (
            "Transaction Preview: "
            + f"Sending {Web3.from_wei(tx.get('value', 0), 'ether')} "
            + f"FLR to {tx.get('to')}\nType CONFIRM to proceed."
        )
        return {"response": formatted_preview}


    async def getDeFiJson(self, message: str, prompt_str: str) -> dict:
        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            prompt_str, user_input=message
        )
        send_token_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        
        send_token_json = json.loads("{}")
        try:
            send_token_json = json.loads(send_token_response.text)
        except:
            self.logger.debug("We probably did not get valid json back from Gemini. See below.")
                
        self.logger.debug("In getDeFiJson. ",message=message, prompt=prompt, json_len=len(send_token_json), json=send_token_json)
        
        return send_token_json
        

    async def handle_swap_token(self, message: str, user: UserInfo) -> dict[str, str]:
        """
        Handle token swap requests (currently unsupported).

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response indicating unsupported operation
        """
        self.logger.debug("In handle_swap_token()")
        response_json = await self.getDeFiJson(message, "token_swap")
        
        expected_json_len = 3
        if (
            len(response_json) != expected_json_len
            or response_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_swap")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text + " \n " + json.dumps(response_json)}
        
       
        # Return stringified JSON
        return {"response": json.dumps(response_json)}

    
    
    
    async def handle_stake(self, message: str, user: UserInfo) -> dict[str, str]:
        """
        Handle token staking requests.

        Args:
            message: The user's input message
            user: User information from authentication

        Returns:
            dict[str, str]: Response with stringified JSON or a follow-up prompt
        """
        self.logger.debug("In handle_stake()")
        response_json = await self.getDeFiJson(message, "token_stake")
        
        expected_json_len = 1
        if (
            len(response_json) != expected_json_len
            or response_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_stake")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text + " \n " + json.dumps(response_json)}
        
        
        
        # Return stringified JSON
        return {"response": json.dumps(response_json)}
    
    
    async def handle_borrow(self, message: str, user: UserInfo) -> dict[str, str]:
        self.logger.debug("In handle_borrow()")
        
        prompt, mime_type, schema = self.prompts.get_formatted_prompt("token_borrow", user_input=message)
        ai_response = self.ai.generate(prompt=prompt, response_mime_type=mime_type, response_schema=schema)
                
        
        
        
        expected_json_len = 3
        ai_response_json = json.loads("{}")
        for i in range(1,5):
            
            try:
                ai_response_json = json.loads(ai_response.text)
            except:
                self.logger.debug("We probably did not get valid json back from Gemini. See below.")
        
            self.logger.debug(message=message)
            self.logger.debug(prompt=prompt)
            self.logger.debug(mime_type=mime_type)
            self.logger.debug(schema=schema)
            self.logger.debug(ai_response=ai_response)
            self.logger.debug(ai_response_json=ai_response_json)
            self.logger.debug(len_ai_response_json=len(ai_response_json))

            len_ai_response_json = len(ai_response_json)
            if (len_ai_response_json != expected_json_len):
                prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_borrow")
                ai_response = self.ai.generate(f"The response you gave me ({ai_response}) what incorrect, because it had {len_ai_response_json} and I was expecting {expected_json_len}")
              
            print ("Round ", i)    
        if (ai_response_json.get("amount") == 0.0):
            return {"response": "Sorry, amount must be more than 0.0 \n " + json.dumps(ai_response_json)}
        
        
        # Return stringified JSON
        return {"response": json.dumps(ai_response_json)}
    
    
    async def handle_supply(self, message: str, user: UserInfo) -> dict[str, str]:
        self.logger.debug("In handle_supply()")        
        response_json = await self.getDeFiJson(message, "token_supply") 
        
        expected_json_len = 3
        if (
            len(response_json) != expected_json_len
            or response_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_supply")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text + " \n " + json.dumps(response_json)}
        
        # Return stringified JSON
        return {"response": json.dumps(response_json)}
    

    
