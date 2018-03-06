import json
import time

import coincurve


class Transaction(object):
    def __init__(self, source, destination, amount, fee=0, timestamp=None, signature=None):
        self.source = source
        self.destination = destination
        self.amount = amount
        self.fee = fee
        self.timestamp = timestamp if timestamp is not None else int(time.time())
        self.tx_hash = None
        self.signature = signature
        if signature is not None:
            self.tx_hash = self.calc_hash()

    @staticmethod
    def from_dict(transaction_dict):
        transaction =  Transaction(
            source=transaction_dict['source'],
            destination=transaction_dict['destination'],
            amount=transaction_dict['amount'],
            fee=transaction_dict['fee'],
            timestamp=transaction_dict['timestamp'],
            signature=transaction_dict['signature']
        )
        transaction.tx_hash = transaction_dict['tx_hash']
        transaction.timestamp = transaction_dict['timestamp']
        return transaction

    def sign(self, private_key):
        private_key = coincurve.PrivateKey.from_hex(private_key)
        self.signature = private_key.sign(self._signable()).hex()
        self.tx_hash = self.calc_hash()
        return self.signature

    def verify(self):
        return coincurve.verify_signature(bytes.fromhex(self.signature), self._signable(), bytes.fromhex(self.source))

    def verify_hash(self):
        return self.tx_hash == self.calc_hash()

    def calc_hash(self):
        data = self.__dict__.copy()
        del data['tx_hash']
        data_json = json.dumps(data, sort_keys=True).encode()
        return coincurve.utils.sha256(data_json).hex()

    def _signable(self):
        return ':'.join((self.source, self.destination, str(self.amount), str(self.fee), str(self.timestamp))).encode()

    def __iter__(self):
        for key in self.__dict__:
            yield (key, self.__dict__[key])

    def __repr__(self):
        return "<Transaction {}>".format(self.tx_hash)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
