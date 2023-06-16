import pandas as pd

import sys
sys.path.append('../../src/')
import incremental_kgc as inc

import time
import os

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


def __remove_data(file: str, data: object, extension: str):
    """Removes 'data' from 'file' and returns the data in 'file' prior to the change.

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
        aux_data = pd.DataFrame([data])
        df_new = pd.concat([df, aux_data, aux_data]).drop_duplicates(keep=False)
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


def run_test(update_data: list,
             mapping_file: str,
             snapshot_file: str,
             aux_data_path: str,
             method: str,
             engine: str,
             keep_snapshot: bool):
    """Performs a first version materialization, and then one update for each value in update_data.

    Args:
        update_data:
            A list of updates. The items are dictionaries with keys 'new' and 'remove' (can be absent),
            and values with a dictionary where the key is a file and the value is the data to add/remove.
            The following example adds on the first iteration the value '1' to the column "a" in "file1.csv".
            On the second iteration the value '1' from column "a" from "file1.csv" is removed, and value '3'
            from column "b" from "file1.csv" is added.

            update_data = [
                { # First update
                    "add": {
                        "file1.csv": {
                            "a": 1
                        }
                    }
                },
                { # Second update
                    "add": {
                        "file1.csv": {
                            "b": 3
                        }
                    },
                    "remove": {
                        "file1.csv": {
                            "a": 1
                        }
                    }
                }
            ]
        mapping_file:
            The file name that contains the mappings.
        snapshot_file:
            The snapshot file name.
        aux_data_path:
            The path of an auxiliary directory.
        method:
            A string that determines how the auxiliary data is threated:
                - 'disk': The auxiliary data is stored in the disk, under the 'aux_data_path' directory.
                - 'memory': The auxiliary data is stored in memory.
        engine:
            The name of the mapping engine to materialize the graph:
                - 'morph': https://github.com/morph-kgc/morph-kgc.
        keep_snapshot:
            A boolean value that indicates if the snapshot file should be kept after performing the test.
        
    Returns:
        The data in 'file' prior to the update. The type of the object returned depends 'extension':
            .csv: returns pandas.DataFrame
    """
    results = []
    updated_files = {}
    file_extensions = {}

    # Run first materialization
    print("Loading new graph...")
    start = time.time()
    g = inc.load_kg(mapping_file=mapping_file,
                    snapshot_file=snapshot_file,
                    aux_data_path=aux_data_path,
                    old_graph=None,
                    method=method,
                    engine=engine)
    end = time.time()
    total_time = end-start
    results.append((len(g), total_time))
    print("Loaded new graph in %.2fs" % (total_time))

    # Materialize for each update
    for update in update_data:
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
            aux = __store_data(file=file,
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
            aux = __remove_data(file=file,
                               data=remove[file],
                               extension=extension)
            if file not in updated_files:
                updated_files[file] = aux
            print("OK")

        print("Finished updating data source.")

        print("Updating graph...")
        start = time.time()
        g = inc.load_kg(mapping_file=mapping_file,
                        snapshot_file=snapshot_file,
                        aux_data_path=aux_data_path,
                        old_graph=g,
                        method=method,
                        engine=engine)
        end = time.time()
        total_time = end-start
        results.append((len(g), total_time))
        print("Finished updating graph in %.2fs." % (total_time))
    
    print("Restoring data sources...")
    for file in updated_files:
        print("\tRestoring %s... " % file, end='')
        __restore_data(file, updated_files[file], file_extensions[file])
        print("OK")
    print("Restored data sources.")

    if not keep_snapshot:
        print("Deleting %s... " % snapshot_file, end='')
        os.remove(snapshot_file)
        print("OK")
    
    return results
