import os
from dotenv import load_dotenv
from solana.rpc.api import Client
from spl.token.client import Token
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from spl.token.core import _TokenCore
from solana.rpc.commitment import Commitment
from spl.token.instructions import close_account, CloseAccountParams

from utils import Pool, get_token_account, make_swap_instruction
from solders.compute_budget import set_compute_unit_price, set_compute_unit_limit


load_dotenv()

RPC_URL, PRIVATE_KEY = os.getenv("RPC_URL"), os.getenv("PRIVATE_KEY")

client = Client(RPC_URL)
pool = Pool(client)


TOKEN = "T1Je4cRoQJjdympw4VhYk58Z42TnQk9mGqC9c3qGprZ"  # Carrot program ID
PAYER = Keypair.from_base58_string(PRIVATE_KEY)
TOKEN_MINT = Pubkey.from_string(TOKEN)

AMOUNT = 0.001  # Amount in sol
LAMPORTS_PER_SOL = 1_000_000_000


amount_in = int(AMOUNT * LAMPORTS_PER_SOL)
pool_keys = pool.get_pool_keys(str(TOKEN_MINT))


print("1. Get TOKEN_PROGRAM_ID...")
accountProgramId = client.get_account_info_json_parsed(TOKEN_MINT)
TOKEN_OWNER = accountProgramId.value.owner

print("2. Get Mint Token accounts addresses...")
swap_associated_token_address, swap_token_account_Instructions = get_token_account(client,
                                                                                   PAYER.pubkey(), TOKEN_MINT)

print("3. Create Wrap Sol Instructions...")
balance_needed = Token.get_min_balance_rent_for_exempt_for_account(client)

WSOL_token_account, swap_tx, payer, Wsol_account_keyPair, opts, = _TokenCore._create_wrapped_native_account_args(
    TOKEN_OWNER, PAYER.pubkey(), PAYER, amount_in,
    False, balance_needed, Commitment("confirmed"))


print("4. Create Swap Instructions...")
instructions_swap = make_swap_instruction(
    amount_in, WSOL_token_account, swap_associated_token_address, pool_keys, TOKEN_OWNER, payer)


print("5. Create Close Account Instructions...")
params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(), owner=payer.pubkey(),
                            program_id=TOKEN_OWNER)
closeAcc = close_account(params)


print("6. Add instructions to transaction...")
if swap_token_account_Instructions != None:
    swap_tx.add(swap_token_account_Instructions)
# Set your gas fees here in micro_lamports eg 1_000_000 ,20_400_000 choose amount in sol and multiply by microlamport eg 1000000000 =1 lamport
swap_tx.add(set_compute_unit_price(10_000))

# Retrieve a recent blockhash before building the transaction
recent_blockhash = client.get_latest_blockhash().value.blockhash

swap_tx.recent_blockhash = recent_blockhash  # Set the retrieved blockhash

swap_tx.add(instructions_swap)
swap_tx.add(closeAcc)

for i in range(5):
    try:
        print("7. Execute Transaction...")
        txn = client.send_transaction(
            swap_tx, payer, Wsol_account_keyPair, recent_blockhash=recent_blockhash)
        txid_string_sig = txn.value
        print("Here is the Transaction Signature NB Confirmation is just to wat for confirmation: ", txid_string_sig)
    except Exception as e:
        print("ERROR:", e)
    else:
        break


print("8. Confirm transaction...")
