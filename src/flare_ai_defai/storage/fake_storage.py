
from pydantic import BaseModel

from flare_ai_defai.models import UserInfo
# Define UserInfo class (same as in your original code)


class WalletStore:
    def __init__(self):
        # Internal dictionary to store wallet data
        # Structure: {user_id: {"address": str, "private_key": str, "email": str}}
        self._wallets: dict[str, dict[str, str]] = {}

    def store_wallet(self, user: UserInfo, address: str, private_key: str) -> bool:
        """
        Store a wallet's address and private key for a given user.

        Args:
            user: UserInfo object containing user_id and email
            address: Wallet address to store
            private_key: Private key to store

        Returns:
            bool: True if stored successfully, False if user already has a wallet
        """
        if user.user_id in self._wallets:
            return False  # Wallet already exists for this user
        
        self._wallets[user.user_id] = {
            "address": address,
            "private_key": private_key,
            "email": user.email
        }
        return True

    def get_address(self, user_id: str) -> str | None:
        """
        Fetch the wallet address for a given user.

        Args:
            user_id: Google ID (sub) of the user

        Returns:
            Optional[str]: Wallet address if found, None if not found
        """
        wallet = self._wallets.get(user_id)
        return wallet["address"] if wallet else None

    def get_private_key(self, user_id: str) -> str | None:
        """
        Fetch the private key for a given user.

        Args:
            user_id: Google ID (sub) of the user

        Returns:
            Optional[str]: Private key if found, None if not found
        """
        wallet = self._wallets.get(user_id)
        return wallet["private_key"] if wallet else None

    def get_wallet_info(self, user_id: str) -> dict[str, str] | None:
        """
        Fetch all wallet information for a given user.

        Args:
            user_id: Google ID (sub) of the user

        Returns:
            Optional[Dict[str, str]]: Dictionary with address, private_key, and email if found, None if not found
        """
        return self._wallets.get(user_id)


# Example usage
if __name__ == "__main__":
    # Create a WalletStore instance
    wallet_store = WalletStore()

    # Create a sample UserInfo object
    user = UserInfo(user_id="google123", email="user@example.com")
    
    # Store wallet information
    address = "0x1234567890abcdef1234567890abcdef12345678"
    private_key = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    
    success = wallet_store.store_wallet(user, address, private_key)
    print(f"Wallet stored: {success}")  # True

    # Try storing again for same user
    success = wallet_store.store_wallet(user, "0xnewaddress", "0xnewkey")
    print(f"Wallet stored again: {success}")  # False

    # Retrieve address
    retrieved_address = wallet_store.get_address("google123")
    print(f"Retrieved address: {retrieved_address}")

    # Retrieve private key
    retrieved_key = wallet_store.get_private_key("google123")
    print(f"Retrieved private key: {retrieved_key}")

    # Retrieve full wallet info
    wallet_info = wallet_store.get_wallet_info("google123")
    print(f"Full wallet info: {wallet_info}")

    # Try to get info for non-existent user
    no_wallet = wallet_store.get_address("nonexistent")
    print(f"Non-existent user address: {no_wallet}")  # None