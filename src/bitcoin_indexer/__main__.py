import logger
import rpc as rpc
import db as db

#todo
import cProfile
import pstats

from sqlalchemy.engine import Engine

logger = logger.setup_logging(__name__)


def insert_block_with_txs(block_number: int, engine: Engine):
    block = rpc.Blocks()
    block_hash = block.get_block_hash(block_number)
    b = block.get_block(block_hash, verbosity=2)
    db.insert_all(b, engine)

if __name__ == "__main__":
    # -----------
    #  MVP
    # -----------
    with cProfile.Profile() as profile:
        block_number = 957361
        engine = db.set_up_db()
        insert_block_with_txs(block_number, engine)
    
    results = pstats.Stats(profile)
    results.sort_stats(pstats.SortKey.TIME)
    results.dump_stats("./var/results.prof")
