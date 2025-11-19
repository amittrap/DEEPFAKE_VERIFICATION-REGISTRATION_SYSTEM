import os
import json
from pathlib import Path
from web3 import Web3

# Load env variables
WEB3_RPC_URL = os.getenv("WEB3_RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))

if not WEB3_RPC_URL or not CONTRACT_ADDRESS:
    raise RuntimeError("Missing WEB3_RPC_URL or CONTRACT_ADDRESS")

# Connect to Sepolia
w3 = Web3(Web3.HTTPProvider(WEB3_RPC_URL))
if not w3.is_connected():
    raise RuntimeError("Failed to connect to Sepolia RPC")

# Load ABI
ABI_PATH = Path(__file__).resolve().parent.parent / "abi" / "DeepfakeLogger.json"
with open(ABI_PATH, "r") as f:
    ABI = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)

def store_result(hash_bytes32, label, confidence):
    """Store hash + result on Sepolia testnet."""
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)

    conf_scaled = int(confidence * 10000)

    tx = contract.functions.storeResult(
        hash_bytes32,
        label,
        conf_scaled
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return receipt


def get_result(hash_bytes32):
    """Fetch stored data, read-only (no gas)."""
    return contract.functions.getResult(hash_bytes32).call()
