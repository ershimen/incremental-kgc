# Import src
import sys
sys.path.append('../../src/')

__test__ = "gtfs-bench-10-memory"
__mapping_file__ = "mapping.csv.ttl"
__update_file__ = "data/AGENCY.csv"
__update_data__ = {
    "agency_id": "00000000000000100000",
    "agency_name": "00000000000000000001",
    "agency_url": "http://www.crtm.es",
    "agency_timezone": "00000000000000000001",
    "agency_lang": "00000000000000000001",
    "agency_phone": "00000000000000000001",
    "agency_fare_url": "https://www.crtm.es/billetes-y-tarifas",
    }
__aux_data_path__ = '.aux'
__snapshot_file__ = '.aux/snapshot.pkl'
__keep_snapshot__ = False

print("Running test %s" % __test__)

import incremental_kg as inc
import time
import pandas as pd
import os

print("Loading new graph...")

print("#" * 60)

start = time.time()
# Load new graph
g = inc.load_kg_aux_to_mem(
    aux_data_path=__aux_data_path__,
    mapping_file=__mapping_file__,
    snapshot_file=__snapshot_file__,
    old_graph=None)
end = time.time()

print("#" * 60)

print("Loaded new graph in %.2fs" % (end-start))

print("Adding data to %s..." % __update_file__)
agency_df = pd.read_csv(__update_file__, dtype=str)
agency_df_new = pd.concat([agency_df, pd.DataFrame([__update_data__])])
agency_df_new.to_csv(__update_file__, index=False)
print("Added new data to %s." % __update_file__)

print("Adding new triples...")

print("#" * 60)

start = time.time()
g = inc.load_kg_aux_to_mem(
    aux_data_path=__aux_data_path__,
    mapping_file=__mapping_file__,
    snapshot_file=__snapshot_file__,
    old_graph=g)
end = time.time()

print("Loaded new graph in %.2fs" % (end-start))

print("#" * 60)

print("Restoring %s..." % __update_file__)

agency_df.to_csv(__update_file__, index=False)

print("Restored %s." % __update_file__)

if not __keep_snapshot__:
    print("Deleting %s..." % __snapshot_file__)
    os.remove(__snapshot_file__)
    print("Deleted snapshot file.")
