UCLCoin
========
.. image:: https://img.shields.io/pypi/v/uclcoin.svg?style=flat-square
    :target: https://pypi.org/project/uclcoin

.. image:: https://img.shields.io/pypi/pyversions/uclcoin.svg?style=flat-square
    :target: https://pypi.org/project/uclcoin

.. image:: https://img.shields.io/pypi/l/uclcoin.svg?style=flat-square
    :target: https://pypi.org/project/uclcoin

-----

Uma implementação simples de blockchain/criptomoeda comp propósitos educacionais.

INSTALAÇÃO
------------

UCLCoin é distribuido via PyPI, está disponível para Linux/macOS e Windows e suporta Python 3.6+.

.. code-block:: bash

    $ pip install -U uclcoin

Exemplos
--------

Nos exemplos abaixo assume-se que as dendencias necessárias foram previamente importadas.

.. code-block:: python

    >>> from uclcoin import KeyPair, Transaction, Block, BlockChain

Gerando suas chaves
^^^^^^^^^^^^^^^^^^^

A chave privada é usada para assinar suas transações e a chave pública é o seu endereço
para receber moedas e recompensas de mineração.

Você pode gerar um novo par de chaves instanciando a classe ``KeyPair``

.. code-block:: python

    >>> carteira = KeyPair()
    >>> endereco = carteira.public_key
    >>> endereco
    '03d70f9a58c9bc6d8fdc47f96d6931f14a7abb0d72cd76886ee05047023fd49471'

No futuro instancie a classe KeyPair usando sua chave privada ``wallet.private_key``.

.. code-block:: python

    >>> carteira = KeyPair('sua-chave-privada')

BlockChain
^^^^^^^^^^

Crie uma BlockChain vazia para realizar seus testes:

.. code-block:: python

    >>> blockchain = BlockChain()

Sua ``blockchain`` contem apenas o bloco Gênesis. A blockchain está pronta para aceitar
transações, mas você não poderá enviar valores com saldo zerado.

.. code-block:: python

    >>> blockchain.get_balance(wallet.public_key)
    0

Minerando um bloco
^^^^^^^^^^^^^^^^^^^

Obtenha um bloco a ser minerado à blockchain.

.. code-block:: python

    >>> novo_bloco = blockchain.get_minable_block(wallet.public_key)

A blockchain retorna um novo bloco com o próximo índice válido contendo as transações pendentes e uma transação coinbase
(de recompensa) destinada à sua chave publica (wallet.public_key)

A prova de trabalho na UCLCoin consiste em alterar o ``nonce`` do bloco até
produzir um hash iniciando com N zeros, onde N é a dificuldade configurada
na blockchain. A dificuldade atual pode ser obtida pelo metodo ``calculate_hash_difficulty``

.. code-block:: python

    >>> N = blockchain.calculate_hash_difficulty()

Um método simples para minerar o bloco é incrementar o nonce até produzir um hash válido

.. code-block:: python

    >>> while novo_bloco.current_hash[:N].count('0') < N:
    ...     novo_bloco.nonce +=1
    ...     novo_bloco.recalculate_hash()

Esta operação vai bloquear enquanto hash é calculado. Após minerado submeta o
novo bloco. Se ele for aceito seu saldo será atualizado.

.. code-block:: python

   >>> blockchain.add_block(novo_bloco)
   True
   >>> blockchain.get_balance(wallet.public_key)
   10

Enviando uma transação
^^^^^^^^^^^^^^^^^^^^^^

Agora você pode gastar suas moedas.

.. code-block:: python

   >>> destinatario = 'chave_publica_do_destinatario'
   >>> gasto = wallet.create_transaction(destinatario, 2)
   >>> blockchain.add_transaction(gasto)
   True

Sua transação agora está pendente. Ela só será confirmada após ser incluída em um bloco
minerado.

.. code-block:: python

   >>> blockchain.get_balance(wallet.public_key)
   10

Você pode verificar seu saldo incluindo as transações não confirmadas, se desejar.

.. code-block:: python

   >>> blockchain.get_balance_pending(wallet.public_key)
   8
