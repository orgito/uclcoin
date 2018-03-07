import os
import pickle
import time

import coincurve

from uclcoin import logger
from uclcoin.block import Block
from uclcoin.exceptions import *
from uclcoin.transaction import Transaction


class BlockChain(object):
    COINS_PER_BLOCK = 10
    MAX_TRANSACTIONS_PER_BLOCK = 50
    MINIMUM_HASH_DIFFICULTY = 7

    def __init__(self, blocks=None):
        self.blocks = []
        self.pending_transactions = []

        if not blocks:
            genesis_block = self._get_genesis_block()
            self.add_block(genesis_block)
        else:
            for block in blocks:
                self.add_block(block)

    def load_from_file(self, filename):
        if os.stat(filename).st_size > 0:
            with open(filename, 'rb') as chain_file:
                bc = pickle.load(chain_file)
                self.blocks = []
                self.pending_transactions = []
                for b in bc['chain']:
                    b = Block.from_dict(b)
                    self.add_block(b)
                for t in bc['pending']:
                    t = Transaction.from_dict(t)
                    self.add_transaction(t)

    def save_to_file(self, filename):
        bc = {
            'pending': [dict(t) for t in self.pending_transactions],
            'chain': [dict(b) for b in self.blocks]
        }
        with open(filename, 'wb') as chain_file:
            pickle.dump(bc, chain_file)

    def add_block(self, block):
        self.validate_block(block)
        for t in block.transactions[:-1]:
            self.remove_pending_transaction(t.tx_hash)
        self.blocks.append(block)
        return

    def calculate_hash_difficulty(self, index=None):
        return self.MINIMUM_HASH_DIFFICULTY

    def find_duplicate_transactions(self, transaction_hash):
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.tx_hash == transaction_hash:
                    return block.index
        return False

    def get_balance_pending(self, address):
        balance = self.get_balance(address)
        for transaction in self.pending_transactions:
            if transaction.source == address:
                balance -= transaction.amount + transaction.fee
            if transaction.destination == address:
                balance += transaction.amount
        return balance

    def get_balance(self, address):
        balance = 0
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.source == address:
                    balance -= transaction.amount + transaction.fee
                if transaction.destination == address:
                    balance += transaction.amount
        return balance

    def get_block_by_index(self, index):
        if index > len(self.blocks) - 1:
            return None
        return self.blocks[index]

    def get_latest_block(self):
        return self.blocks[-1]

    def get_minable_block(self, reward_address):
        transactions = []
        latest_block = self.get_latest_block()
        new_block_id = latest_block.index + 1
        previous_hash = latest_block.current_hash
        fees = 0

        for pending_transaction in self.pending_transactions:
            if pending_transaction is None:
                break
            if pending_transaction.tx_hash in [transaction.tx_hash for transaction in transactions]:
                continue
            if self.find_duplicate_transactions(pending_transaction.tx_hash):
                continue
            if not pending_transaction.verify():
                continue
            transactions.append(pending_transaction)
            fees += pending_transaction.fee
            if len(transactions) >= self.MAX_TRANSACTIONS_PER_BLOCK:
                break

        timestamp = int(time.time())

        reward_transaction = Transaction(
            '0',
            reward_address,
            self.get_reward(new_block_id) + fees,
            0,
            timestamp,
            '0'
        )
        transactions.append(reward_transaction)

        return Block(new_block_id, transactions, previous_hash, timestamp)

    def get_reward(self, index):
        return self.COINS_PER_BLOCK

    def remove_pending_transaction(self, transaction_hash):
        for i, t in enumerate(self.pending_transactions):
            if t.tx_hash == transaction_hash:
                self.pending_transactions.pop(i)
                return True
        return False

    def validate_block(self, block):
        # if genesis block, check if block is correct
        if block.index == 0:
            if len(self.blocks) > 0:
                raise GenesisBlockMismatch(block.index, f'Genesis Block Mismatch: {block.index}')
            self._check_genesis_block(block)
            return
        # current hash of data is correct and hash satisfies pattern
        self._check_hash_and_hash_pattern(block)
        # block index is correct and previous hash is correct
        self._check_index_and_previous_hash(block)
        # block reward is correct based on block index and halving formula
        self._check_transactions_and_block_reward(block)
        return

    def validate_transaction(self, transaction):
        index = len(self.blocks)
        if transaction in self.pending_transactions:
            raise InvalidTransactions(index, f'Transaction not valid.  Duplicate transaction detected: {transaction.tx_hash}')
        if self.find_duplicate_transactions(transaction.tx_hash):
            raise InvalidTransactions(index, f'Transaction not valid.  Replay transaction detected: {transaction.tx_hash}')
        if not transaction.verify():
            raise InvalidTransactions(index, f'Transaction not valid.  Invalid transaction signature: {transaction.tx_hash}')
        if not transaction.verify_hash():
            raise InvalidTransactions(index, f'Transaction not valid.  Invalid hash: {transaction.tx_hash}')
        balance = self.get_balance(transaction.source)
        if transaction.amount + transaction.fee > balance:
            raise InvalidTransactions(index, f'Transaction not valid.  Insufficient funds: {transaction.tx_hash}')
        return

    def add_transaction(self, transaction):
        self.validate_transaction(transaction)
        self.pending_transactions.append(transaction)
        return True

    def _check_genesis_block(self, block):
        if block != self._get_genesis_block():
            raise GenesisBlockMismatch(block.index, f'Genesis Block Mismatch: {block.index}')
        return

    def _check_hash_and_hash_pattern(self, block):
        hash_difficulty = self.calculate_hash_difficulty()
        if block.current_hash != block.calc_current_hash():
            raise InvalidHash(block.index, f'Incompatible Block Hash: {block.current_hash}')
        if block.merkle_root != block.calc_merkle_root():
            raise BlockchainException(block.index, f'Incompatible Block merkle root: {block.merkle_root}')
        if block.current_hash[:hash_difficulty].count('0') < hash_difficulty:
            raise InvalidHash(block.index, f'Incompatible Block Hash: {block.current_hash}')
        return

    def _check_index_and_previous_hash(self, block):
        latest_block = self.get_latest_block()
        if latest_block.index != block.index - 1:
            raise ChainContinuityError(block.index, f'Incompatible block index: {block.index}')
        if latest_block.current_hash != block.previous_hash:
            raise ChainContinuityError(block.index, f'Incompatible block hash: {block.index} and hash: {block.previous_hash}')
        return

    def _check_transactions_and_block_reward(self, block):
        reward_amount = self.get_reward(block.index)
        payers = dict()
        for transaction in block.transactions[:-1]:
            if self.find_duplicate_transactions(transaction.tx_hash):
                raise InvalidTransactions(block.index, 'Transactions not valid.  Duplicate transaction detected')
            if not transaction.verify():
                raise InvalidTransactions(block.index, 'Transactions not valid.  Invalid Transaction signature')
            if transaction.source in payers:
                payers[transaction.source] += transaction.amount  + transaction.fee
            else:
                payers[transaction.source] = transaction.amount  + transaction.fee
            reward_amount += transaction.fee
        for key in payers:
            balance = self.get_balance(key)
            if payers[key] > balance:
                raise InvalidTransactions(block.index, 'Transactions not valid.  Insufficient funds')
        # last transaction is block reward
        reward_transaction = block.transactions[-1]
        if reward_transaction.amount != reward_amount or reward_transaction.source != '0':
            raise InvalidCoinbaseTransaction(block.index, 'Transactions not valid.  Incorrect block reward')
        return

    def _get_genesis_block(self):
        genesis_transaction_one = Transaction(
            '0',
            '032b72046d335b5318a672763338b08b9642225189ab3f0cba777622cfee0fc07b',
            10,
            0,
            0,
            ''
        )
        genesis_transaction_two = Transaction(
            '0',
            '02f846677f65911f140a42af8fe7c1e5cbc7d148c44057ce49ee0cd0a72b21df4f',
            10,
            0,
            0,
            ''
        )
        genesis_transactions = [genesis_transaction_one, genesis_transaction_two]
        genesis_block = Block(0, genesis_transactions, '000000000000000000000000000000000000000000000000000000000000000000', 0, 130898395)
        return genesis_block
