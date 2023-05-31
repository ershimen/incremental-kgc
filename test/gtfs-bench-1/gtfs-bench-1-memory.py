# Import src
import sys
sys.path.append('../../src/')

__test__ = "gtfs-bench-1-memory"
__mapping_file__ = "mapping.csv.ttl"
__update_data__ = {
    "data/AGENCY.csv": {
        "agency_id": "00000000000000100000",
        "agency_name": "00000000000000000001",
        "agency_url": "http://www.crtm.es",
        "agency_timezone": "00000000000000000001",
        "agency_lang": "00000000000000000001",
        "agency_phone": "00000000000000000001",
        "agency_fare_url": "https://www.crtm.es/billetes-y-tarifas",
        }
    }
__aux_data_path__ = '.aux'
__snapshot_file__ = '.aux/snapshot.pkl'
__keep_snapshot__ = False
__method__ = 'memory'
__engine__ = 'morph'

def __store_data(file: str, data: object, extension: str):
    """Stores 'data' to 'file' and returns the data in 'file' prior to the change.

    Args:
        file:
            A file name.
        data:
            A data object (for example json). The types supported are the following:
                .json: for .csv files
        extension:
            Extension of 'file'. This parameter determines how to open 'file' and the return type. 
        
    Returns:
        The data in 'file' prior to the update. The type of the object returned depends 'extension':
            .csv: returns pandas.DataFrame
    """
    if extension == '.csv':
        df = pd.read_csv(file, dtype=str)
        df_new = pd.concat([df, pd.DataFrame([data])])
        df_new.to_csv(file, index=False)
        return df
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')


def __restore_data(file: str, data: object, extension: str):
    """Restores 'data' to 'file'.

    Args:
        file:
            A file name.
        data:
            A data object (for example json). The types supported are the following:
                pandas.DataFrame: for .csv files
        extension:
            Extension of 'file'. This parameter determines how to store 'data' into 'file'. 
    """
    if extension == '.csv':
        data.to_csv(file, index=False)
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')


print("Running test %s" % __test__)

import incremental_kg as inc
import time
import pandas as pd
import os

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
for file in __update_data__:
    _, extension = os.path.splitext(file)
    file_extensions[file] = extension
    print("\tAdding data to %s... " % file, end='')
    updated_files[file] = __store_data(file=file,
                                       data=__update_data__[file],
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
    __restore_data(file, updated_files[file], file_extensions[file])
    print("OK")

print("Restored data sources.")

if not __keep_snapshot__:
    print("Deleting %s... " % __snapshot_file__, end='')
    os.remove(__snapshot_file__)
    print("OK")

print("Summary:")
print("\tCreated new version in %.2fs (%d triples)" % (new_version_time, new_version_triples))
print("\tUpdated in %.2fs (%d triples)" % (update_time, update_triples))
