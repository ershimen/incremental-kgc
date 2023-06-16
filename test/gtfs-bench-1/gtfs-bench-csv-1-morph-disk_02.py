__test__ = "gtfs-bench-csv-1-morph-disk"
__mapping_file__ = "mapping.csv.ttl"
__aux_data_path__ = '.aux'
__snapshot_file__ = '.aux/snapshot.pkl'
__keep_snapshot__ = False
__method__ = 'disk'
__engine__ = 'morph'
__update_data__ = [
    { # First iteration
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
    { # Second iteration
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
        }
    },
]

import sys
sys.path.append('../../test/')
import test_utils

import time

print("Running test %s" % __test__)
start = time.time()
res = test_utils.run_test(update_data=__update_data__,
                          mapping_file=__mapping_file__,
                          snapshot_file=__snapshot_file__,
                          aux_data_path=__aux_data_path__,
                          method=__method__,
                          engine=__engine__,
                          keep_snapshot=__keep_snapshot__)
end = time.time()
print("\n------------------------------------------------------")
print("Finished running test in %.2fs." % (end-start))

print("Summary:")
print("\tCreated new version in %.2fs (%d triples)" % (res[0][1], res[0][0]))

for r in res[1:]:
    print("\tUpdated in %.2fs (%d triples)" % (r[1], r[0]))
