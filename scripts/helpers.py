from brownie import network, accounts, config, interface
from web3 import Web3

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def get_account(index=None, id=None):
    print(f"active network: {network.show_active()}")
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if network.show_active() in (
        LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


def get_erc20_balance(erc20_address, account):
    balance = Web3.fromWei(interface.IERC20(erc20_address).balanceOf(account), "ether")
    return balance
