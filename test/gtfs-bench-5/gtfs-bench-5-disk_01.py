__test__ = "gtfs-bench-5-disk"
__mapping_file__ = "mapping.csv.ttl"
__update_data__ = [
    { # First iteration
        "data/AGENCY.csv": {
            "agency_id": "00000000000000100000",
            "agency_name": "00000000000000000001",
            "agency_url": "http://www.crtm.es",
            "agency_timezone": "00000000000000000001",
            "agency_lang": "00000000000000000001",
            "agency_phone": "00000000000000000001",
            "agency_fare_url": "https://www.crtm.es/billetes-y-tarifas",
            },
        "data/FEED_INFO.csv": {
            "feed_publisher_name": "0000000000000010000",
            "feed_publisher_url": "http://www.crtm.es",
            "feed_lang": "00000000000000000001",
            "feed_start_date": "1970-01-02",
            "feed_end_date": "1970-01-02",
            "feed_version": "00000000000000000001"
            },
    },
    ]
__aux_data_path__ = '.aux'
__snapshot_file__ = '.aux/snapshot.pkl'
__keep_snapshot__ = False
__method__ = 'disk'
__engine__ = 'morph'


import sys
sys.path.append('../../src/')
sys.path.append('../../test/')

import incremental_kgc as inc
import test_utils
import time
import os

print("Running test %s" % __test__)

print("Loading new graph...")

start = time.time()
# Load new graph
g = inc.load_kg(mapping_file=__mapping_file__,
                snapshot_file=__snapshot_file__,
                aux_data_path=__aux_data_path__,
                old_graph=None,
                method=__method__,
                engine=__engine__)
end = time.time()

new_version_time = end-start
new_version_triples = len(g)

print("Loaded new graph in %.2fs" % (new_version_time))

print("Adding new data to data source...")
updated_files = {}
file_extensions = {}
for file in __update_data__[0]: # First iteration
    _, extension = os.path.splitext(file)
    file_extensions[file] = extension
    print("\tAdding data to %s... " % file, end='')
    updated_files[file] = test_utils.__store_data(file=file,
                                       data=__update_data__[0][file],
                                       extension=extension)
    print("OK")

print("Finished adding new data to source.")

print("Adding new triples...")

start = time.time()
g = inc.load_kg(mapping_file=__mapping_file__,
                snapshot_file=__snapshot_file__,
                aux_data_path=__aux_data_path__,
                old_graph=g,
                method=__method__,
                engine=__engine__)
end = time.time()

update_time = end-start
update_triples = len(g)

print("Loaded new triples in %.2fs" % (end-start))

print("Restoring data sources...")
for file in updated_files:
    print("\tRestoring %s... " % file, end='')
    test_utils.__restore_data(file, updated_files[file], file_extensions[file])
    print("OK")

print("Restored data sources.")

if not __keep_snapshot__:
    print("Deleting %s... " % __snapshot_file__, end='')
    os.remove(__snapshot_file__)
    print("OK")

print("Summary:")
print("\tCreated new version in %.2fs (%d triples)" % (new_version_time, new_version_triples))
print("\tUpdated in %.2fs (%d triples)" % (update_time, update_triples))
