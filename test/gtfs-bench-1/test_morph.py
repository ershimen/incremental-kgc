__test__ = "test-morph-crash"
__mapping_file__ = "mapping.csv.ttl"

import time
from morph_kgc import materialize

print("Running test %s" % __test__)
start = time.time()

config = "[GTFS-Madrid-Bench]\nmappings: %s" % __mapping_file__
g = materialize(config=config)
end = time.time()
print("\n------------------------------------------------------")
print("Finished running test in %.2fs." % (end-start))

print("Summary:")
print("\tCreated new version in %.2fs (%d triples)" % (end-start, len(g)))
