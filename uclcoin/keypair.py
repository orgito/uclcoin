import coincurve

from uclcoin.transaction import Transaction


class KeyPair(object):
    def __init__(self, private_key=None):
        if private_key:
            self._private_key = coincurve.PrivateKey.from_hex(private_key)
        else:
            self._private_key = coincurve.PrivateKey()
        self._public_key = self._private_key.public_key

    def create_transaction(self, destination, amount):
        transaction = Transaction(self.public_key, destination, amount)
        transaction.sign(self.private_key)
        return transaction

    def sign(self, message):
        if type(message) is not bytes:
            message = str(message).encode()
        return self._private_key.sign(message).hex()

    def verify(self, signature, message):
        if type(message) is not bytes:
            message = str(message).encode()
        return self._public_key.verify(bytes.fromhex(signature), message)

    @property
    def private_key(self):
        return self._private_key.to_hex()

    @property
    def public_key(self):
        return self._public_key.format().hex()

    def __repr__(self):
        return f'<Address {self.public_key}>'
