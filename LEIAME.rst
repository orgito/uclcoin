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

Nos exemplos abaixo assume-se que a classe apropriada foi previamente importada.

.. code-block:: python

    >>> from uclcoin import KeyPair, Transaction, Block, BlockChain

Gerando suas chaves
^^^^^^^^^^^^^^^^^^^

A chave privada é usada para assinar suas transações e a chave pública é o seu endereço
para receber moedas e recompensas de mineiração.

Você pode gerar um novo par de chaves instanciando a classe ``KeyPair``

.. code-block:: python

    >>> cliente = KeyPair()
    >>> endereco = cliente.public_key
    >>> endereco
    '03d70f9a58c9bc6d8fdc47f96d6931f14a7abb0d72cd76886ee05047023fd49471'

No futuro instancie a classe KeyPair usando sua chave privada ``client.private_key``.

.. code-block:: python

    >>> cliente = KeyPair('sua-chave-privada')

BlockChain
^^^^^^^^^^

Crie uma BlockChain vazia para realizar seus testes

.. code-block:: python

    >>> blockchain = BlockChain()

Sua ``blockchain`` contem apenas o bloco Gênesis. A blockchain está pronta para aceitar
transações, mas você não poderá enviar valores com saldo zerado.

.. code-block:: python

    >>> blockchain.get_balance(client.public_key)
    0

Mineirando um bloco
^^^^^^^^^^^^^^^^^^^

Obtenha um bloco a ser mineirado à blockchain.

.. code-block:: python

    >>> novo_bloco = blockchain.get_minable_block(client.public_key)

A blockchain retorna um novo block com um índice igual ao índice do último bloco
incrementado de 1, contendo as transações pendentes e uma transação coinbase
(de recompensa) destinada à sua chave publica (client.public_key)

A prova de trabalho na UCLCoin consiste em alterar o ``nonce`` do bloco até
produzir um hash iniciando com N zeros, onde N é a dificuldade configurada
na blockchain. A dificuldade atual pode ser obtida pelo metodo ``calculate_hash_dificulty``

.. code-block:: python

    >>> dificuldade = blockchain.calculate_hash_dificulty()

Um método simples para mineirar o bloco é incrementar o nonce até produzir um hash válido

.. code-block:: python

    >>> while novo_bloco.current_hash[:dificuldade].count('0') < dificuldade:
    ...     novo_bloco.nonce +=1
    ...     novo_bloco.recalculate_hash()

Esta operação vai bloquear enquanto hash é calculado. Após mineirado submeta o
novo bloco. Se ele for aceito seu saldo será atualizado.

.. code-block:: python

   >>> blockchain.add_block(novo_bloco)
   True
   >>> blockchain.get_balance(cliente.public_key)
   10

Enviando uma transação
^^^^^^^^^^^^^^^^^^^^^^

Agora você pode gastar suas moedas.

.. code-block:: python

   >>> destinatario = '02ff420a5768ca5a97f0eedc2400e72bf1d084ed0c075e90a33f10a8d50d94071d'
   >>> gasto = cliente.create_transaction(destinatario)
   >>> blockchain.add_transaction(gasto)
   True

Sua transação agora está pendente. Ela só será confirmada após ser incluída em um bloco
mineirado.

.. code-block:: python

   >>> blockchain.get_balance(cliente.public_key)
   10

Você pode verificar seu saldo incluindo as transações não confirmadas, se desejar.

.. code-block:: python

   >>> blockchain.get_balance_pending(cliente.public_key)
   8
