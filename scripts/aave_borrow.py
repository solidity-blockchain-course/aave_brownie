"""
1. Swap ETH for ERC20 equivalent WETH 
https://github.com/aave/protocol-v2/blob/master/contracts/misc/WETHGateway.sol

WETHGateway wraps WETH and ILendingPool, combining the operations. 
I am going to use IWETH token contract and do the operations separately
"""

from brownie import network, interface, config
from scripts.get_weth import get_weth
from scripts.helpers import (
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
)
from web3 import Web3

AMOUNT = Web3.toWei(0.01, "ether")


def main():

    # swapping ETH -> WETH
    erc20_weth_address = config["networks"][network.show_active()]["weth_token"]
    account = get_account()
    if network.show_active() in (
        LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        get_weth(erc20_weth_address, account, AMOUNT)

    lending_pool = get_lending_pool()
    approve_erc20(erc20_weth_address, lending_pool.address, AMOUNT, account)

    """
    ========== Deposit ===========
    """
    # deposit
    deposit_tx = lending_pool.deposit(
        erc20_weth_address,
        AMOUNT,
        account.address,
        0,
        {"from": account},
    )
    deposit_tx.wait(1)
    print(f"Deposited: {Web3.fromWei(AMOUNT, 'ether')} WETH")

    """
    ======== Borrow ===========
    """

    # get user's borrowable amount
    (_, _, borrowable_eth) = get_user_borrowable_data(lending_pool, account.address)
    print(f"borrowable eth: {borrowable_eth}")

    # get DAI / ETH ratio
    dai_eth_price = get_token_eth_rate(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )

    # borrow 95% DAI from the ETH
    dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"dai to borrow {dai_to_borrow}")

    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print_info(lending_pool, account)

    """
    Repay
    """
    repay_all(dai_address, lending_pool, account)
    print_info(lending_pool, account)


def get_token_eth_rate(dai_eth_price_feed_address):
    token_eth_price_feed = interface.AggregatorV3Interface(dai_eth_price_feed_address)
    token_eth_price = float(
        Web3.fromWei(token_eth_price_feed.latestRoundData()[1], "ether")
    )
    return token_eth_price


def approve_erc20(erc20_address, spender_address, amount, initiator):
    approve_tx = interface.IERC20(erc20_address).approve(
        spender_address, amount, {"from": initiator}
    )
    approve_tx.wait(1)
    print("Approved !")


def get_lending_pool():
    # init lending_pool
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )

    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def get_user_borrowable_data(lending_pool, account_address):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrows_eth,
        _,
        _,
        _,
    ) = lending_pool.getUserAccountData(account_address)
    return (
        float(Web3.fromWei(total_collateral_eth, "ether")),
        float(Web3.fromWei(total_debt_eth, "ether")),
        float(Web3.fromWei(available_borrows_eth, "ether")),
    )


def repay_all(token_address, lending_pool, account):
    approve_erc20(token_address, lending_pool.address, AMOUNT, account)
    repay_tx = lending_pool.repay(
        token_address, AMOUNT, 1, account.address, {"from": account}
    )
    repay_tx.wait(1)


def print_info(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
    ) = get_user_borrowable_data(lending_pool, account)
    print(f"Total Collateral: {total_collateral_eth}")
    print(f"Worth of ETH borrowed: {total_debt_eth}")
    print(f"Borrowable eth: {available_borrow_eth}")
