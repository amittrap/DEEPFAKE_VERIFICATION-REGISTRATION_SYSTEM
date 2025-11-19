import os
import json
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv

# Load variables from .env
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
    nonce = w3.eth.get_transaction_count(account.address)

    # Contract requires _confidence <= 10000
    conf_scaled = int(confidence * 10000)
    if conf_scaled > 10000:
        conf_scaled = 10000

    tx = contract.functions.storeResult(
        content_hash_bytes32,
        label,
        conf_scaled
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # You can also return tx_hash.hex() if you only care about hash
    return receipt


def get_result(content_hash_bytes32: bytes) -> dict | None:
    """
    Read result from blockchain (no gas).

    Returns dict with fields:
      contentHash, label, confidence, timestamp, recorder
    or None if not stored.
    """
    result = contract.functions.getResult(content_hash_bytes32).call()

    (content_hash, label, confidence, timestamp, recorder) = result

    # Detect "empty" default struct
    if content_hash == b"\x00" * 32 and label == "" and confidence == 0 and timestamp == 0:
        return None

    return {
        "contentHash": content_hash,
        "label": label,
        "confidence": confidence / 10000.0,  # back to 0–1 range
        "timestamp": timestamp,
        "recorder": recorder,
    }
