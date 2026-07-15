import json
import os

from web3 import Web3

from service.shared.configuration import Configuration

CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "contracts", "Proposal.json")

with open(CONTRACT_PATH, "r") as file:
    contract_interface = json.load(file)

CONTRACT_ABI = contract_interface["abi"]
CONTRACT_BYTECODE = contract_interface["bytecode"]

web3 = Web3(Web3.HTTPProvider(Configuration.GANACHE_URI))

admin_account = web3.eth.accounts[0]


def deploy_proposal_contract(voters):
    factory = web3.eth.contract(abi = CONTRACT_ABI, bytecode = CONTRACT_BYTECODE)
    transaction_hash = factory.constructor(voters).transact({ "from": admin_account })
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    return web3.eth.contract(address = receipt.contractAddress, abi = CONTRACT_ABI)
