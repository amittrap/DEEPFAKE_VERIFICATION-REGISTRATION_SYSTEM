import os
import json
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv

# Load variables from .env (for local dev)
load_dotenv()

# --- Load env variables ---

# Support both names: RPC_URL (new) and WEB3_RPC_URL (old)
RPC_URL = os.getenv("RPC_URL") or os.getenv("WEB3_RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))  # Sepolia default

if not RPC_URL or not CONTRACT_ADDRESS:
    raise RuntimeError("RPC_URL/WEB3_RPC_URL or CONTRACT_ADDRESS not set in environment (.env)")


# --- Connect to Sepolia ---

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise RuntimeError("Web3 not connected. Check RPC_URL/WEB3_RPC_URL and internet connection.")


# --- Load ABI ---

ABI_PATH = Path(__file__).resolve().parent.parent / "abi" / "DeepfakeLogger.json"

if not ABI_PATH.exists():
    raise FileNotFoundError(f"ABI file not found at {ABI_PATH}")

with open(ABI_PATH, "r") as f:
    CONTRACT_ABI = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI,
)


# --- Helper functions ---

from web3.exceptions import TransactionNotFound


def store_result(content_hash_bytes32: bytes, label: str, confidence: float):
    """
    Write result to blockchain.

    content_hash_bytes32: 32-byte hash (e.g. hashlib.sha256(image_bytes).digest())
    label: 'real' or 'fake'
    confidence: float between 0 and 1
    """
    if not PRIVATE_KEY:
        raise RuntimeError("PRIVATE_KEY not set in environment")

    account = w3.eth.account.from_key(PRIVATE_KEY)

    # Use 'pending' so we include in-flight txs and avoid nonce clashes
    nonce = w3.eth.get_transaction_count(account.address, 'pending')

    # Scale confidence to 0–10000 as contract expects
    conf_scaled = int(confidence * 10000)
    if conf_scaled > 10000:
        conf_scaled = 10000

    # Take suggested gas price and bump it a bit to avoid 'underpriced' errors
    base_gas_price = w3.eth.gas_price
    gas_price = int(base_gas_price * 1.2)  # +20%

    tx = contract.functions.storeResult(
        content_hash_bytes32,
        label,
        conf_scaled
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 300000,
        "gasPrice": gas_price,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait until mined
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return receipt


def get_result(content_hash_bytes32: bytes) -> dict | None:
    """
    Read result from blockchain (no gas).

    Solidity getResult(bytes32) returns:
      (contentHash, label, confidence, timestamp, recorder)

    We return:
      {
        "contentHash": bytes32,
        "label": string,
        "confidence": float (0–1),
        "timestamp": int,
        "recorder": address,
      }

    If no record is stored for that hash, we return None.
    """
    result = contract.functions.getResult(content_hash_bytes32).call()
    (content_hash, label, confidence, timestamp, recorder) = result

    # Detect "empty" default struct:
    # when nothing stored, label == "" and other fields are 0 / zero address
    if (
        label == ""
        and confidence == 0
        and timestamp == 0
        and recorder == "0x0000000000000000000000000000000000000000"
    ):
        return None

    return {
        "contentHash": content_hash,
        "label": label,
        "confidence": confidence / 10000.0,  # back to 0–1 range
        "timestamp": timestamp,
        "recorder": recorder,
    }
