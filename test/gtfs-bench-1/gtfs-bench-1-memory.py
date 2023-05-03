# Import src
import sys
sys.path.append('../../src/')

__test__ = "gtfs-bench-1-memory"
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

print("Running test %s" % __test__)

import incremental_kg as inc
import time
import pandas as pd

print("Loading new graph...")

print("#" * 60)

start = time.time()
# Load new graph
g = inc.load_kg_aux_to_mem(
    aux_data_path='.aux',
    mapping_file='mapping.csv.ttl',
    snapshot_file='.aux/snapshot.pkl',
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
    aux_data_path='.aux',
    mapping_file='mapping.csv.ttl',
    snapshot_file='.aux/snapshot.pkl',
    old_graph=g)
end = time.time()

print("Loaded new graph in %.2fs" % (end-start))

print("#" * 60)

print("Restoring %s..." % __update_file__)

agency_df.to_csv(__update_file__, index=False)

print("Restored %s." % __update_file__)
