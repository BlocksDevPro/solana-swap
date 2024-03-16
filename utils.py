import json
import requests
from cachetools import TTLCache
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.transaction import AccountMeta
from solders.instruction import Instruction
from solana.rpc.types import TokenAccountOpts
from spl.token.instructions import get_associated_token_address, create_associated_token_account

from layouts import SWAP_LAYOUT


LAMPORTS_PER_SOL = 1000000000
AMM_PROGRAM_ID = Pubkey.from_string(
    '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
SERUM_PROGRAM_ID = Pubkey.from_string(
    'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX')


POOLS_FILE = './assets/pools.json'


class Pool:
    def __init__(self, client: Client):
        self.client = client
        # TLCache(maxsize=100, ttl=60) it should refetch for new pools
        self.pools = {'data': True}

    def get_pools(self):
        with open(POOLS_FILE, 'r') as file:
            return json.load(file)

    def set_pools(self, data):
        with open(POOLS_FILE, 'w') as file:
            json.dump(data, file)

    def fetch_pools(self):
        if not self.pools.get('data'):
            try:
                response = requests.get(
                    'https://api.raydium.io/v2/sdk/liquidity/mainnet.json', stream=True)
                pools = response.json()
                pools = pools['official'] + pools['unOfficial']
                self.set_pools(pools)
                self.pools['data'] = True
            except:
                print('Error while fetching pools.')
        return self.get_pools()

    def get_pool(self, mint: str):
        pools = self.fetch_pools()
        for pool in pools:
            if pool['baseMint'] == mint and pool['quoteMint'] == 'So11111111111111111111111111111111111111112':
                return pool
            elif pool['quoteMint'] == mint and pool['baseMint'] == 'So11111111111111111111111111111111111111112':
                return pool

    def get_pool_keys(self, mint: str):
        pool = self.get_pool(mint)

        if not pool:
            return

        return {
            'amm_id': Pubkey.from_string(pool['id']),
            'authority': Pubkey.from_string(pool['authority']),
            'base_mint': Pubkey.from_string(pool['baseMint']),
            'base_decimals': pool['baseDecimals'],
            'quote_mint': Pubkey.from_string(pool['quoteMint']),
            'quote_decimals': pool['quoteDecimals'],
            'lp_mint': Pubkey.from_string(pool['lpMint']),
            'open_orders': Pubkey.from_string(pool['openOrders']),
            'target_orders': Pubkey.from_string(pool['targetOrders']),
            'base_vault': Pubkey.from_string(pool['baseVault']),
            'quote_vault': Pubkey.from_string(pool['quoteVault']),
            'market_id': Pubkey.from_string(pool['marketId']),
            'market_base_vault': Pubkey.from_string(pool['marketBaseVault']),
            'market_quote_vault': Pubkey.from_string(pool['marketQuoteVault']),
            'market_authority': Pubkey.from_string(pool['marketAuthority']),
            'bids': Pubkey.from_string(pool['marketBids']),
            'asks': Pubkey.from_string(pool['marketAsks']),
            'event_queue': Pubkey.from_string(pool['marketEventQueue'])
        }


def get_token_account(client: Client, owner: Pubkey, mint: Pubkey):
    try:
        account_data = client.get_token_accounts_by_owner(
            owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey, None
    except:
        swap_associated_token_address = get_associated_token_address(
            owner, mint)
        swap_token_account_Instructions = create_associated_token_account(
            owner, owner, mint)
        return swap_associated_token_address, swap_token_account_Instructions


def make_swap_instruction(amount_in: int, token_account_in: Pubkey.from_string, token_account_out: Pubkey.from_string,
                          accounts: dict, TOKEN_OWNER, owner) -> Instruction:

    keys = [
        AccountMeta(pubkey=TOKEN_OWNER,
                    is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["amm_id"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"],
                    is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["open_orders"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["target_orders"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["base_vault"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["quote_vault"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=SERUM_PROGRAM_ID,
                    is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["market_id"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["bids"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["asks"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["event_queue"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["market_base_vault"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["market_quote_vault"],
                    is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["market_authority"],
                    is_signer=False, is_writable=False),
        AccountMeta(pubkey=token_account_in, is_signer=False,
                    is_writable=True),  # UserSourceTokenAccount
        AccountMeta(pubkey=token_account_out, is_signer=False,
                    is_writable=True),  # UserDestTokenAccount
        AccountMeta(pubkey=owner.pubkey(), is_signer=True,
                    is_writable=False)  # UserOwner
    ]

    data = SWAP_LAYOUT.build(
        dict(
            instruction=9,
            amount_in=int(amount_in),
            min_amount_out=0
        )
    )
    return Instruction(AMM_PROGRAM_ID, data, keys)
