import time

import coincurve

from uclcoin.exceptions import BlockchainException, InvalidHash, InvalidTransactions
from uclcoin.transaction import Transaction


class Block(object):
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.version = 1
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp is not None else int(time.time())
        self.nonce = nonce
        self.merkle_root = self.calc_merkle_root()
        self.current_hash = self.calc_current_hash()

    def calc_current_hash(self):
        return coincurve.utils.sha256(self._to_hashable()).hex()

    def recalculate_hash(self):
        self.current_hash = self.calc_current_hash()

    @property
    def hash_difficulty(self):
        difficulty = 0
        for c in self.current_hash:
            if c != '0':
                break
            difficulty += 1
        return difficulty

    @staticmethod
    def from_dict(block_dict):
        block = Block(
            index=block_dict['index'],
            transactions=[Transaction.from_dict(tx) for tx in block_dict['transactions']],
            previous_hash=block_dict['previous_hash'],
            timestamp=block_dict['timestamp'],
            nonce=block_dict['nonce']
        )
        block.merkle_root = block_dict['merkle_root']
        block.current_hash = block_dict['current_hash']
        block.timestamp = block_dict['timestamp']
        return block

    def _to_hashable(self):
        return ''.join((
            '%08d' % self.version,
            self.previous_hash,
            self.merkle_root,
            '%x' % self.timestamp,
            '%08d' % self.nonce
        )).encode()

    def calc_merkle_root(self):
        if len(self.transactions) < 1:
            raise InvalidTransactions(self.index, "Zero transactions in block. Coinbase transaction required")
        merkle = [t.tx_hash for t in self.transactions]
        while len(merkle) > 1:
            t_merkle = []
            for i in range(0, len(merkle), 2):
                if i == len(merkle) - 1:
                    mhash = coincurve.utils.sha256(bytes.fromhex(merkle[i])).hex()
                else:
                    mhash = coincurve.utils.sha256(bytes.fromhex(merkle[i] + merkle[i+1])).hex()
                t_merkle.append(mhash)
            merkle = t_merkle
        return merkle[0]

    def __iter__(self):
        block = self.__dict__.copy()
        block['transactions'] = [dict(t) for t in self.transactions]
        block['current_hash'] = self.current_hash
        for key in block:
            yield (key, block[key])

    def __repr__(self):
        return f'<Block #{self.index}>'

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
