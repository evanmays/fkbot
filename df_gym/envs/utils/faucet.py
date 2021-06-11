from web3 import Web3
import random
import string

def createNewUser():
    # connect to hardhat
    w3 = Web3()

    # create account
    entropy = ''.join(random.choice(string.ascii_lowercase) for i in range(32))
    myAccount = w3.eth.account.create(entropy)
    newAddress = myAccount.address
    newPrivateKey = myAccount.privateKey.hex()

    # transfer from root account to new account
    w3.eth.send_transaction({'to': newAddress, 'value': int(1e18)}) # Idk where the money's coming from but I think this function breaks after about 1000 calls
    assert w3.eth.get_balance(newAddress) > 0

    return newAddress, newPrivateKey
