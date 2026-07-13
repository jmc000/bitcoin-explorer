import os

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError

import logger
import context_manager

logger = logger.setup_logging(__name__)
Base = declarative_base()

DEFAULT_SQLITE_URL = "sqlite:///var/bitcoin_indexer.db"

# ------------------------------------------------------------
# DB Tables
# ------------------------------------------------------------
# Everything but:
# - tx (dedicated table transactions.db, link to block hash FK)
# - nextblockhash (derivable from the next block’s previousblockhash)
# NOTE: confirmations (can become stale, need to be updated periodically)
# TODO: define constraints -> eg. nullable=False, String(50), unique=True
BLOCK_FIELDS = {
    "hash":               (String,  {"primary_key": True}),
    "height":             (Integer, {}),
    "size":               (Integer, {}),
    "strippedsize":       (Integer, {}),
    "weight":             (Integer, {}),
    "version":            (Integer, {}),
    "versionHex":         (String,  {}),
    "merkleroot":         (String,  {}),
    "time":               (Integer, {}),
    "mediantime":         (Integer, {}),
    "confirmations":      (Integer, {}),
    "nonce":              (Integer, {}),
    "bits":               (String,  {}),
    "difficulty":         (Float,   {}),
    "chainwork":          (String,  {}),
    "nTx":                (Integer, {}),
    "previousblockhash":  (String,  {}),
}

TRANSACTION_FIELDS = {
    "txid":               (String,  { "primary_key": True }),
    "hash":               (String,  {}),
    "in_active_chain":    (Boolean, {}),
    "hex":                (String,  {}),
    "size":               (Integer, {}),
    "vsize":              (Integer, {}),
    "weight":             (Integer, {}),
    "version":            (Integer, {}),
    "locktime":           (Integer, {}),
    "blockhash":          (String,  {"foreign_key": "blocks.hash"}),
    "confirmations":      (Integer, {}),
    "blocktime":          (Integer, {}),
    "time":               (Integer, {}),
}

# TX_INPUTS / TX_OUTPUTS
# --> composite primary key: PRIMARY KEY (txid, input_index/output_index)
#   "vin" : [                          (json array)
#     {                                (json object)
#       "txid" : "hex",                (string) The transaction id
#       "vout" : n,                    (numeric) The output number
#       "scriptSig" : {                (json object) The script
#         "asm" : "str",               (string) asm
#         "hex" : "hex"                (string) hex
#       },
#       "sequence" : n,                (numeric) The script sequence number
#       "txinwitness" : [              (json array)
#         "hex",                       (string) hex-encoded witness data (if any)
#         ...
#       ]
#     },
#     ...
#   ],
#   "vout" : [                         (json array)
#     {                                (json object)
#       "value" : n,                   (numeric) The value in BTC
#       "n" : n,                       (numeric) index
#       "scriptPubKey" : {             (json object)
#         "asm" : "str",               (string) the asm
#         "hex" : "str",               (string) the hex
#         "reqSigs" : n,               (numeric) The required sigs
#         "type" : "str",              (string) The type, eg 'pubkeyhash'
#         "addresses" : [              (json array)
#           "str",                     (string) bitcoin address
#           ...
#         ]
#       }
#     },
#     ...
#   ],

def _model(name: str, tablename: str, fields: dict):
    attrs = {"__tablename__": tablename}
    for col_name, (col_type, kwargs) in fields.items():
        kwargs = kwargs.copy()
        fk = kwargs.pop("foreign_key", None)
        args = (ForeignKey(fk),) if fk else ()
        attrs[col_name] = Column(col_type, *args, **kwargs)
    return type(name, (Base,), attrs)


Blocks = _model("Blocks", "blocks", BLOCK_FIELDS)
Transactions = _model("Transactions", "transactions", TRANSACTION_FIELDS)



# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def get_database_url() -> str:
    load_dotenv()
    return os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)


def create_db_engine(url: str | None = None):
    url = url or get_database_url()
    connect_args = {}
    if url.startswith("sqlite"):
        # Required when the engine is shared across threads?
        connect_args["check_same_thread"] = False
    return create_engine(url, echo=False, connect_args=connect_args)

def create_tables(engine: Engine) -> None:
    #TODO: for later use Alembic instead
    Base.metadata.create_all(engine)

def open_session(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine)

def insert_block(block: Blocks, s: Session):
    s.add(block)
    s.commit()
def insert_blocks(blocks: [Blocks], s: Session):
    s.add_all(blocks)
    s.commit()
def insert_block_from_dict(data: dict, s: Session):
    """ If input data in a dict format, unpack it dynamically while creating an object """
    b = Blocks(**data)
    s.add(b)
    s.commit()
def insert_blocks_from_dict(list: list[dict], s: Session):
    blocks = []
    for data in list:
        b = Blocks(**data)
        blocks.append(b)
    s.add_all(blocks)
    s.commit()

@event.listens_for(Blocks, 'before_insert')
def before_insert_hook(mapper, s: Session, new_block: Blocks):
    print(f"2. session: {s}")
    #todo: what about the error rasing management for db.py?
    try:
        existing_block = s.get(Blocks, new_block.hash)
        if existing_block is not None:
            # TODO: create a central logger
            # log.error()
            raise IntegrityError(f"Block {new_block.hash} already exists")
    except IntegrityError:
        # TODO: create a central logger
        # log.error()
        raise  IntegrityError(f"Block {new_block.hash} already exists")



# Transactions
def insert_tx(tx: Transactions, s: sessionmaker):
    s.add(tx)
    s.commit()
def insert_txs(txs: [Transactions], s: sessionmaker):
    s.add_all(txs)
    s.commit()
def insert_tx_from_dict(data: dict, s: sessionmaker):
    """ If input data in a dict format, unpack it dynamically while creating an object """
    t = Transactions(**data)
    s.add(t)
    s.commit()
def insert_transactions_from_dict(list: list[dict], s: sessionmaker):
    txs = []
    for data in list:
        t = Transactions(**data)
        txs.append(t)
    s.add_all(txs)
    s.commit()


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    db_url=get_database_url()
    engine = create_db_engine(db_url)
    create_tables(engine)

    S = sessionmaker(bind=engine)
    print(type(S))
