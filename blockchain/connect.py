from web3 import Web3
import json
import os

# Ganache / Local Blockchain URL
GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Check connection
if not w3.is_connected():  # corrected method name here
    raise Exception("⚠️ Web3 not connected. Please check Ganache or RPC URL.")
else:
    print(f"✅ Connected to blockchain at {GANACHE_URL}")

# Load contract ABI
ABI_PATH = os.path.join("contract", "abi.json")
try:
    with open(ABI_PATH) as f:
        abi = json.load(f)
except FileNotFoundError:
    raise Exception(f"⚠️ ABI file not found at {ABI_PATH}")

# Contract address (replace with your deployed contract address)
CONTRACT_ADDRESS = "0x9d7834C376B2b722c5693af588C3e7a03Ea8e44D"

# Create contract instance
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

# Default account - using Ganache account[0]
if len(w3.eth.accounts) == 0:
    raise Exception("⚠️ No accounts found in the node. Please check your Ganache setup.")
ACCOUNT = w3.eth.accounts[0]

# Private key for signing transactions (Keep it secret, avoid hardcoding in production)
PRIVATE_KEY = "0x46054a5484b0ec4b6b296da46e27fdd6bd0d06acc1e3f61bca979dba569c2898"

# Optional: Print default account info
print(f"Using account: {ACCOUNT}")
