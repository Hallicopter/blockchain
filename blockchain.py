import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request


class Blockchain(object):

	def __init__(self):
		self.chain=[]
		self.current_transactions=[]

		# Create a new genesis block
		self.new_block(previous_hash=1, proof=100)

	def new_block(self, proof,  previous_hash=None):
		'''
		Create a new Block in the Blockchain

		:param proof: <int> the proof given by the Proof of work algorithm
		:param previous_hash: (Optional) <str> Hash of the previous Block
		:return: <dict> New Block
		'''
		
		block = {
			'index': len(self.chain)+1,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash':previous_hash or self.hash(self.chain[-1]),
		}

		# Reset the current list of transactions
		self.current_transactions = []

		self.chain.append(block)
		return block

	def new_transaction(self, sender, recipient, amount):
		"""
		Creates a new transaction to go into the next mined Block

		:param sender: <str> Address of the sender
		:param recipient: <str> Address of the Recipient
		:param amount: <int> Amount
		:return <int> the index of the block that will hold this transaction
		"""

		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
		})
		
		return self.last_block['index']+1

	@staticmethod
	def hash(block):
		'''
		Creates a SHA-256 hash of the Block

		:param block: <dict> Block
		:return: <str>
		'''
		# Encodes after json dumping it in a sorted manner since
		# python dictionaries are inherently orderless, and we need
		# consistency in ordering.
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	@property
	def last_block(self):
		# Returns the last block in the chain
		return self.chain[-1]

	def proof_of_work(self, last_proof):
		'''
		Simple proof of work algorithm:
		- find p' such that hash(pp') contains leading 4 zeroes,
		  where p is the previous p'
		- p is the previous proof, p' is the new proof

		:param last_proof: <int>
		:return: <int>
		'''

		proof = 0
		while self.valid_proof(last_proof, proof) is False:
			proof+=1

		return proof

	@staticmethod
	def valid_proof(last_proof, proof):
		'''
		Validates the Proof: Ie checks whether hash(last_proof, proof)
							 contains 4 leading zeroes.
		:param last_proof: <int> Previous Proof
		:param proof: <int> Current Proof
		:return: <bool> true if correct, False if not.
		'''

		guess = '{}{}'.format(last_proof, proof).encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == '0000'

# Instantiate our Node
app = Flask(__name__)

# Generate globally unique address for this node
node_identifier = str(uuid4()).replace('-','')

# Instantiate the Blockchain

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
	# We run the proof of work algorith to get the next proof
	last_block = blockchain.last_block
	last_proof = last_block['proof']
	proof = blockchain.proof_of_work(last_proof)

	# Miner needs to be rewarded for finding proof
	# The sender field is 0 to denote it as a reward, ie. a newly mined coin.
	blockchain.new_transaction(
		sender='0',
		recipient = node_identifier,
		amount = 1,
	)

	# Forge the new Block by adding it to the chain
	block = blockchain.new_block(proof)

	response = {
		'message': 'New block forged',
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}

	return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	values = request.get_json()

	# Check that therequired fields are in the POST'ed data
	required = ['sender', 'recipient','amount']
	if not all(k in values for k in required):
		return 'Missing values', 400

	# Create a new Transaction
	index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

	response = {'message': 'Transaction will be added to Block {}'.format(index)}
	return jsonify(response), 201	

@app.route('/chain', methods=['GET'])
def full_chain():
	response = {
		'chain' : blockchain.chain,
		'length' : len(blockchain.chain),
	}
	return jsonify(response), 200

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)