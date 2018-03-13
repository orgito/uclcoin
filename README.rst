UCLCoin
========
.. image:: https://img.shields.io/pypi/v/uclcoin.svg?style=flat-square
    :target: https://pypi.org/project/uclcoin

.. image:: https://img.shields.io/pypi/pyversions/uclcoin.svg?style=flat-square
    :target: https://pypi.org/project/uclcoin

.. image:: https://img.shields.io/pypi/l/uclcoin.svg?style=flat-square
    :target: https://pypi.org/project/uclcoin

-----

A naive blockchain/cryptocurrency implementation for educational purposes.


Installation
------------

UCLCoin is distributed on PyPI and is available on Linux/macOS and Windows and supports Python 3.6+.

.. code-block:: bash

    $ pip install -U uclcoin

Examples
--------

For the following code examples it is assumed that the necessary dependecies were imported.

.. code-block:: python

    >>> from uclcoin import KeyPair, Transaction, Block, BlockChain

Generating your key pair
^^^^^^^^^^^^^^^^^^^^^^^^

The private key is used to sign transactions and the public key is your UCLCoin address. It is used
to receive coins from transactions and rewards from mining.

Use the ``KeyPair`` class to generate your keys

.. code-block:: python

    >>> wallet = KeyPair()
    >>> address = wallet.public_key
    >>> address
    '03d70f9a58c9bc6d8fdc47f96d6931f14a7abb0d72cd76886ee05047023fd49471'

To reuse your key pair instantiate the class using your private key ``client.private_key``

.. code-block:: python

    >>> wallet = KeyPair('your-private-key')

BlockChain
^^^^^^^^^^

Create a new BlockChain for doing your tests:

.. code-block:: python

    >>> blockchain = BlockChain()

Your ``blockchain`` will contain only the Genesis block. It is ready to accept
transactions, but you can't send any coins if your balance is zero.

.. code-block:: python

    >>> blockchain.get_balance(client.public_key)
    0

Mining a block
^^^^^^^^^^^^^^

Get a new minable block from the blockchain:

.. code-block:: python

    >>> new_block = blockchain.get_minable_block(wallet.public_key)

The blockchain returns a new block with the next valid index, any pending
transactions and a coinbase (reward) transaction to your public key (wallet.public_key)

UCLCoin the proof of work consists on manipulating the ``nonce`` field and recalculating
the block hash until it starts with ``N`` zeros. The current difficulty can be obtained with the
``calculate_hash_difficulty`` method.

.. code-block:: python

    >>> N = blockchain.calculate_hash_difficulty()

A simple mining method is to increment the nonce until you get a valid hash:

.. code-block:: python

    >>> while new_block.current_hash[:N].count('0') < N:
    ...     new_block.nonce +=1
    ...     new_block.recalculate_hash()

The operation will block while the hash is calculated. After finishing just submit the
new block to the blockchain. If it is accepted your balance will be updated.

.. code-block:: python

   >>> blockchain.add_block(new_block)
   True
   >>> blockchain.get_balance(wallet.public_key)
   10

Sending a transaction
^^^^^^^^^^^^^^^^^^^^^

You can now spent your new coins.

.. code-block:: python

   >>> destination = 'public_key_of_the_receiver'
   >>> value = wallet.create_transaction(destination, 2)
   >>> blockchain.add_transaction(value)
   True

Your transaction will be added to the pending transactions queue. It will only be confirmed after being
included in a mined block.

.. code-block:: python

   >>> blockchain.get_balance(wallet.public_key)
   10

You can check your balance including the pending transactions

.. code-block:: python

   >>> blockchain.get_balance_pending(wallet.public_key)
   8
   