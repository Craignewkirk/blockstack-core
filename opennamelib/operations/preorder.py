from coinkit import embed_data_in_blockchain, BlockchainInfoClient, \
    bin_hash160, BitcoinPrivateKey, script_to_hex
from utilitybelt import is_hex
from binascii import hexlify, unhexlify

from ..b40 import b40_to_hex
from ..config import *
from ..scripts import name_script_to_hex, add_magic_bytes
from ..hashing import hash_name, calculate_consensus_hash128, gen_name_salt


def build(name, script_pubkey, consensus_hash, salt=None, testset=False):
    """ Takes in an ascii string as a name and an optional hex salt.
    """
    if salt:
        if not is_hex(salt) and len(unhexlify(salt)) == LENGTHS['salt']:
            raise ValueError('Invalid salt')
    else:
        salt = hexlify(gen_name_salt())

    name_hash = hash_name(name, salt, script_pubkey)

    script = 'NAME_PREORDER %s %s' % (name_hash, consensus_hash)
    hex_script = name_script_to_hex(script)
    packaged_script = add_magic_bytes(hex_script, testset=testset)

    return packaged_script, salt


def broadcast(name, consensus_hash, private_key, salt=None,
              blockchain_client=BlockchainInfoClient(), testset=False):
    """ Builds and broadcasts a preorder transaction.
    """
    hash160 = BitcoinPrivateKey(private_key).public_key().hash160()
    script_pubkey = script_to_hex(
        'OP_DUP OP_HASH160 %s OP_EQUALVERIFY OP_CHECKSIG' % hash160)
    nulldata, salt = build(
        name, script_pubkey, consensus_hash, testset=testset, salt=salt)
    response = embed_data_in_blockchain(
        nulldata, private_key, blockchain_client, format='hex')
    # response = {'success': True }
    response.update(
        {'data': nulldata, 'salt': salt, 'consensus_hash': consensus_hash})
    return response


def parse(bin_payload):
    name_hash = bin_payload[0:LENGTHS['name_hash']]
    consensus_hash = bin_payload[LENGTHS['name_hash']:]
    return {
        'opcode': 'NAME_PREORDER',
        'name_hash': hexlify(name_hash),
        'consensus_hash': hexlify(consensus_hash)
    }
