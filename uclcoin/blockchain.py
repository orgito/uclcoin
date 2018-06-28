# pylint: disable=C0103,C0111
import time
from typing import Iterator

from uclcoin.block import Block
from uclcoin.exceptions import *  # pylint: disable=W0401
from uclcoin.transaction import Transaction

try:
    from pymongo.database import Database
    pymongo_not_installed = False
except ModuleNotFoundError:
    pymongo_not_installed = True


def genesis_block():
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
    return Block(0, genesis_transactions, '000000000000000000000000000000000000000000000000000000000000000000', 0, 130898395)


def check_genesis_block(block):
    if block != genesis_block():
        raise GenesisBlockMismatch(block.index, f'Genesis Block Mismatch: {block.index}')


class BlockChain(object):
    COINS_PER_BLOCK = 10
    MAX_TRANSACTIONS_PER_BLOCK = 200
    MINIMUM_HASH_DIFFICULTY = 7

    def __init__(self, mongodb: Database = None):
        if pymongo_not_installed and mongodb is not None:
            raise RuntimeError('Cannot use Mongodb for persistnece without pymongo')

        if isinstance(mongodb, Database):
            self.mongo = True
            self._blocks = mongodb.blocks
            self._pending_transactions = mongodb.pending_transactions
        else:
            self.mongo = False
            self._blocks = []
            self._pending_transactions = []

        if self._count_blocks() == 0:
            self.add_block(genesis_block())

    def add_block(self, block):
        self.validate_block(block)
        for t in block.transactions[:-1]:
            self.remove_pending_transaction(t.tx_hash)
        if self.mongo:
            self._blocks.insert_one(dict(block))
        else:
            self._blocks.append(block)

    def calculate_hash_difficulty(self, index=None):
        if index is None:
            index = self._count_blocks()
        if index > 3892:
            return self.MINIMUM_HASH_DIFFICULTY
        if index > 3330 and index <= 3400:
            return self.MINIMUM_HASH_DIFFICULTY
        if index >= 2000:
            return self.MINIMUM_HASH_DIFFICULTY + 1
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
        if index >= self._count_blocks():
            return None
        if self.mongo:
            if index < 0:
                index = self._count_blocks() + index
            block = self._blocks.find_one({'index': index}, {'_id': 0})
            if block is not None:
                block = Block.from_dict(block)
        else:
            block = self._blocks[index]
        return block

    def get_latest_block(self):
        return self.get_block_by_index(-1)

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
        if index > 3892:
            return self.COINS_PER_BLOCK * 0.2
        if index > 3330 and index <= 3400:
            return self.COINS_PER_BLOCK * 0.3
        return self.COINS_PER_BLOCK

    def remove_pending_transaction(self, transaction_hash):
        if self.mongo:
            self._pending_transactions.find_one_and_delete({'tx_hash': transaction_hash})
            return
        for i, t in enumerate(self._pending_transactions):
            if t.tx_hash == transaction_hash:
                self._pending_transactions.pop(i)

    def validate_block(self, block):
        # if genesis block, check if block is correct
        if block.index == 0:
            if self._count_blocks() > 0:
                raise GenesisBlockMismatch(f'Genesis Block Mismatch: {block.index}')
            check_genesis_block(block)
            return
        # current hash of data is correct and hash satisfies pattern
        self._check_hash_and_hash_pattern(block)
        # block index is correct and previous hash is correct
        self._check_index_and_previous_hash(block)
        # block reward is correct based on block index and halving formula
        self._check_transactions_and_block_reward(block)
        return

    def validate_transaction(self, transaction):
        if transaction in self.pending_transactions:
            raise InvalidTransactions(f'Transaction not valid.  Duplicate transaction detected: {transaction.tx_hash}')
        if not transaction.verify():
            raise InvalidTransactions(f'Transaction not valid.  Invalid transaction signature: {transaction.tx_hash}')
        if transaction.amount <= 0 or transaction.fee < 0:
            raise InvalidTransactions(f'Transaction not valid.  Invalid transaction values: {transaction.tx_hash}')
        if not transaction.verify_hash():
            raise InvalidTransactions(f'Transaction not valid.  Invalid hash: {transaction.tx_hash}')
        if self.find_duplicate_transactions(transaction.tx_hash):
            raise InvalidTransactions(f'Transaction not valid.  Replay transaction detected: {transaction.tx_hash}')
        balance = self.get_balance(transaction.source)
        if transaction.amount + transaction.fee > balance:
            raise InvalidTransactions(f'Transaction not valid.  Insufficient funds: {transaction.tx_hash}')
        balance_pending = self.get_balance_pending(transaction.source)
        if transaction.amount + transaction.fee > balance_pending:
            raise InvalidTransactions(f'Transaction not valid.  Insufficient funds: {transaction.tx_hash}')

    def add_transaction(self, transaction):
        self.validate_transaction(transaction)
        if self.mongo:
            self._pending_transactions.insert_one(dict(transaction))
        else:
            self._pending_transactions.append(transaction)

    def _check_hash_and_hash_pattern(self, block):
        hash_difficulty = self.calculate_hash_difficulty(block.index)
        if block.current_hash != block.calc_current_hash():
            raise InvalidHash(f'Incompatible Block Hash: {block.current_hash}')
        if block.merkle_root != block.calc_merkle_root():
            raise BlockchainException(f'Incompatible Block merkle root: {block.merkle_root}')
        if block.current_hash[:hash_difficulty].count('0') < hash_difficulty:
            raise InvalidHash(f'Incompatible Block Hash: {block.current_hash}')
        return

    def _check_index_and_previous_hash(self, block):
        latest_block = self.get_latest_block()
        if latest_block.index != block.index - 1:
            raise ChainContinuityError(f'Incompatible block index: {block.index}')
        if latest_block.current_hash != block.previous_hash:
            raise ChainContinuityError(f'Incompatible block hash: {block.index} and hash: {block.previous_hash}')

    def _check_transactions_and_block_reward(self, block):
        reward_amount = self.get_reward(block.index)
        payers = dict()
        for transaction in block.transactions[:-1]:
            if self.find_duplicate_transactions(transaction.tx_hash):
                raise InvalidTransactions('Transactions not valid.  Duplicate transaction detected')
            if not transaction.verify():
                raise InvalidTransactions('Transactions not valid.  Invalid Transaction signature')
            if transaction.source in payers:
                payers[transaction.source] += transaction.amount + transaction.fee
            else:
                payers[transaction.source] = transaction.amount + transaction.fee
            reward_amount += transaction.fee
        for key in payers:
            balance = self.get_balance(key)
            if payers[key] > balance:
                raise InvalidTransactions('Transactions not valid.  Insufficient funds')
        # last transaction is block reward
        reward_transaction = block.transactions[-1]
        if reward_transaction.amount != reward_amount or reward_transaction.source != '0':
            raise InvalidCoinbaseTransaction('Transactions not valid.  Incorrect block reward')

    def _count_blocks(self):
        if self.mongo:
            return self._blocks.count()
        else:
            return len(self._blocks)

    def _mblocks(self):
        return self._blocks.find({}, {'_id': 0}).sort('index')

    def _mpending_transactions(self):
        return self._pending_transactions.find({}, {'_id': 0})

    @property
    def blocks(self) -> Iterator[Block]:
        if self.mongo:
            return (Block.from_dict(b) for b in self._mblocks())
        return (b for b in self._blocks)

    @property
    def pending_transactions(self) -> Iterator[Transaction]:
        if self.mongo:
            return (Transaction.from_dict(t) for t in self._mpending_transactions())
        return (t for t in self.pending_transactions)
