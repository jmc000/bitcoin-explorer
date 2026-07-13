import rpc as rpc
import db as db
import logger

from sqlalchemy.orm import Session

logger = logger.setup_logging(__name__)


if __name__ == "__main__":
    # -----------
    #  MVP
    # -----------
    
    # 1. Create DB engine and table
    db_url=db.get_database_url()
    engine = db.create_db_engine(db_url)
    db.create_tables(engine)

    # 2. Get a block
    block = rpc.Blocks()
    block_number = 957354
    block_hash = block.get_block_hash(block_number)
    # Note: getblock(verbosity=2) return list of tx in getrawtransaction format
    my_block = block.get_block(block_hash, verbosity=2)
    txs = my_block['tx']

    # 3. Get all the tx of this block
    # for 
    # transaction = Transactions()
    # my_transaction = transaction.get_transaction(first_txid)
    # print(json.dumps(my_transaction, indent=2))

    # 4. Populate the DB
    # i. session
    # s = db.open_session(engine)
    
    # ii. set db models
    # eg Product(name='Keyboard', price=29.99),
    # block_model = db.Blocks()
    
    # TODO? strim the JSON from the non used data then use insert_block_from_dict ?
    # remove: tx, nextblockhash
    print(f"before del: {my_block['nextblockhash']}")
    del my_block["tx"]
    del my_block["nextblockhash"]

    #TODO: keep them????
    del my_block["target"]
    del my_block["coinbase_tx"]

    # print(f"target: {my_block["target"]}")
    # try:
    #     a = my_block['nextblockhash']
    #     print(f"still here after del: {a}")
    # except:
    #     print("nextblockhash as been removed!")

    # iii. insert
    #TODO: why a with is required an not like in i. ?
    with Session(engine) as s:
        # s.add(some_object)
        # s.add(some_other_object)
        # s.commit()
        print(f"1. session: {s}")
        try:
            db.insert_block_from_dict(my_block,s)
        except Exception as e:
            print(f"error when inserting: {e}")
            logger.error(f"Error: {e}")



