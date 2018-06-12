class BlockchainException(Exception):
    pass

class InvalidHash(BlockchainException):
    pass

class ChainContinuityError(BlockchainException):
    pass

class InvalidTransactions(BlockchainException):
    pass

class GenesisBlockMismatch(BlockchainException):
    pass

class InvalidCoinbaseTransaction(BlockchainException):
    pass
