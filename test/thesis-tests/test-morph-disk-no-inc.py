__test__ = "gtfs-bench-csv-morph-disk-no-inc"
__mapping_file__ = "mapping.csv.ttl"
__keep_snapshot__ = False
__update_data__ = [
    { # First iteration (Adding data)
        "add": {
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
    },
    { # Second iteration (Updating data)
        "add": {
            "data/AGENCY.csv": {
                "agency_id": "00000000000000200000",
                "agency_name": "00000000000000000001",
                "agency_url": "http://www.crtm.es",
                "agency_timezone": "00000000000000000001",
                "agency_lang": "00000000000000000001",
                "agency_phone": "00000000000000000001",
                "agency_fare_url": "https://www.crtm.es/billetes-y-tarifas",
                },
        },
        "remove": {
            "data/AGENCY.csv": {
                "agency_id": "00000000000000100000",
                "agency_name": "00000000000000000001",
                "agency_url": "http://www.crtm.es",
                "agency_timezone": "00000000000000000001",
                "agency_lang": "00000000000000000001",
                "agency_phone": "00000000000000000001",
                "agency_fare_url": "https://www.crtm.es/billetes-y-tarifas",
                },
        },
    },
]

import sys
sys.path.append('../../test/')
import test_utils

import time

import morph_kgc
import os

results = []
updated_files = {}
file_extensions = {}

print("Running test %s" % __test__)
start_t = time.time()

# Run first materialization
print("Loading new graph...")
start = time.time()
config = """[incremental-kgc]\nmappings: %s""" % __mapping_file__
g = morph_kgc.materialize(config=config)
end = time.time()
total_time = end-start
results.append((len(g), total_time))
print("Loaded new graph in %.2fs" % (total_time))

# Materialize for each update
for update in __update_data__:
    print("Updating data source...")
    new = update.get('add', {})
    remove = update.get('remove', {})

    # Add new data
    for file in new:
        print("\tAdding data to %s... " % file, end='')
        if file not in file_extensions:
            _, extension = os.path.splitext(file)
            file_extensions[file] = extension
        else:
            extension = file_extensions[file]
        aux = test_utils.__store_data(file=file,
                            data=new[file],
                            extension=extension)
        if file not in updated_files:
            updated_files[file] = aux
        print("OK")
    
    # Remove data
    for file in remove:
        print("\tRemoving data from %s... " % file, end='')
        if file not in file_extensions:
            _, extension = os.path.splitext(file)
            file_extensions[file] = extension
        else:
            extension = file_extensions[file]
        aux = test_utils.__remove_data(file=file,
                            data=remove[file],
                            extension=extension)
        if file not in updated_files:
            updated_files[file] = aux
        print("OK")

    print("Finished updating data source.")

    print("Updating graph...")
    start = time.time()
    g = morph_kgc.materialize(config=config)
    end = time.time()
    total_time = end-start
    results.append((len(g), total_time))
    print("Finished updating graph in %.2fs." % (total_time))

print("Restoring data sources...")
for file in updated_files:
    print("\tRestoring %s... " % file, end='')
    test_utils.__restore_data(file, updated_files[file], file_extensions[file])
    print("OK")
print("Restored data sources.")

end_t = time.time()
print("\n------------------------------------------------------")
print("Finished running test in %.2fs." % (end_t-start_t))

print("Summary:")
print("\tCreated new version in %.2fs (%d triples)" % (results[0][1], results[0][0]))

for r in results[1:]:
    print("\tUpdated in %.2fs (%d triples)" % (r[1], r[0]))
