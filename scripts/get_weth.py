from brownie import interface, config, network
from scripts.helpers import get_erc20_balance


def get_weth(erc20_weth_address, account, amount):

    weth_tx = interface.IWETH(erc20_weth_address).deposit(
        {"from": account, "value": amount}
    )
    weth_tx.wait(1)
    print(
        f"deposited {get_erc20_balance(erc20_weth_address, account)} WETH to {account.address}"
    )
