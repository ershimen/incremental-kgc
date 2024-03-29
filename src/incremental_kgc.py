import pandas as pd
import rdflib
import os
import pickle
import time

import constants

def _get_sources_from_mapping(mapping_graph: rdflib.Graph):
    """Retrieves a list of sources from the mappings.

    Args:
        mapping_graph:
            A rdflib.Graph that contains the mapping triples.

    Returns:
        A list[str] with the sources.
    """

    mapping_query = """
            PREFIX rml: <http://semweb.mmlab.be/ns/rml#>

            SELECT ?source {
                ?h rml:source ?source
            }
        """
    query_res = mapping_graph.query(mapping_query)
    all_sources = set([str(row['source']) for row in query_res]) # Ignore duplicates TODO: ??
    return all_sources


def _process_source(source_file: str, snapshot: dict, new_version: bool, extension: str):
    """Process a source according to the type. It reads the data from 'source_file' and returns
    the current, new and removed data.

    Args:
        source_file:
            The source file name.
        snapshot:
            The snapshot that contains the old data.
        new_version:
            True if it is the first materialization.
        extension:
            Extension of 'source_file'.

    Returns:
        A triple (current_data, new_data, removed_data). The type depends on 'extension'.
        new_data and removed_data have null intersection (no duplicates between them).
            - current_data: data from source_file.
            - new_data: data that is in source_file and not in snapshot.
            - removed_data: data that is in snapshot and not in source_file.
    """

    if extension == '.csv':
        # Read new data
        df_ds = pd.read_csv(source_file, dtype=str) # source dataframe

        # Read dataframe from snapshot
        df_sp = pd.DataFrame(columns=df_ds.columns) if new_version else snapshot[source_file]
        
        # Calculate simmetric differences
        # This retrieves new data + removed data
        #   - New data: data that is present in df_ds but not in df_sp
        #   - Removed data: data that is present in df_sp but not in df_ds
        diff = pd.concat([df_sp, df_ds]).drop_duplicates(keep=False)
        
        # Calculate removed data
        removed_data = pd.merge(df_sp, diff, how='inner')

        # Calculate new data
        new_data = pd.merge(df_ds, diff, how='inner')

        return df_ds, new_data, removed_data
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')


def _save_data_to_file(data_path:str, source_file: str, extension: str, data: object):
    """Saves 'data' to 'aux_data_pah', with 'source_file' name, and returns the new full file name.

    Args:
        aux_data_pah:
            The destiny directory path.
        source_file:
            The file name.
        extension:
            The extension of 'source_file'.
        data:
            The data that is stored. The type depends on 'extension':
                .csv: python dictionary.

    Returns:
        The name of the new file created.
    """

    # Create file name
    new_file_path = data_path + '/' + source_file
    # Create directories for aux file
    # TODO: verify that this does not need to be run with every data source
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    # Save data
    if extension == '.csv':
        data.to_csv(new_file_path, index=False)
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')

    return new_file_path


def _update_mappings(mapping_graph: rdflib.Graph, query_update: str, data_path: str, mapping_file: str):
    """Updates the 'mapping_graph' with the query 'query_update' and saves the mapping to 'data_path'/'mapping_file'.

    Args:
        mapping_graph:
            A rdflib.Graph that stores the mapping rules.
        query_update:
            The query that is going to be executed on the graph.
        data_path:
            The path where the new mapping will be stored.
        mapping_file:
            The name of the new mapping file.

    Returns:
        The path of the new mapping file.
    """
    mapping_graph.update(query_update)
    # Save new mappings to file
    new_mapping_file = data_path + '/.aux_' + mapping_file
    # Create parent dirs
    os.makedirs(os.path.dirname(new_mapping_file), exist_ok=True)
    mapping_graph.serialize(new_mapping_file)

    return new_mapping_file


def _materialize_set(engine: str, mapping_function, new_mapping_file: str, method: str, data_dict: dict, aux_data_path: str, type_p: str):
    """Runs the 'engine' mapping engine and returns the generated triples.

    Args:
        engine:
            The name of the mapping engine to materialize the graph: 'morph', 'rdfizer'.
        mapping_function:
            The function that performs the materialization.
        new_mapping_file:
            The file name that contains the mappings.
        method:
            A string that determines how the auxiliary data is threated.
        data_dict:
            If 'method' is 'memory', the dictionary with the auxiliary data.
        aux_data_path:
            The path of an auxiliary directory.
        type_p:
            Either 'new' or 'removed'. It is used by some engines to write the config.

    Returns:
        A rdflib.Graph 
    """
    if engine == 'morph':
        config = "[inc]\nmappings: %s" % new_mapping_file
        if method == 'disk':
            triples = mapping_function(config)
            #triples = morph_kgc.materialize(config)
        elif method == 'memory':
            triples = mapping_function(config, data_dict)
            #triples = morph_kgc.materialize(config, data_dict)
    elif engine == 'rdfizer':
        if type_p == 'new':
            sub_dir = 'new_data'
        elif type_p == 'removed':
            sub_dir = 'removed_data'
        else:
            raise TypeError("%s is not 'new' or 'removed'!")
        
        config = """
        [default]
        main_directory: %s/%s/data

        [datasets]
        number_of_datasets: 1
        output_folder: %s/%s
        all_in_one_file: no
        remove_duplicate: yes
        enrichment: yes
        name: output
        ordered: yes

        [dataset1]
        name: %s
        mapping: %s
        """
        
        with open(aux_data_path + '/%s/rdfizer_config.ini' % sub_dir, "w") as f:
            f.write(config % (aux_data_path, sub_dir, aux_data_path, sub_dir, sub_dir, new_mapping_file))

        mapping_function(config_path=aux_data_path + '/%s/rdfizer_config.ini' % sub_dir)
        #semantify(config_path=aux_data_path + '/%s/rdfizer_config.ini' % sub_dir)

        # Read the output of semantify()
        triples = rdflib.Graph().parse(aux_data_path + '/%s/%s.nt' % (sub_dir, sub_dir))
    else:
        raise RuntimeError('%s is not supported yet!' % engine)
    
    return triples


def load_kg(mapping_file: str,
            snapshot_file: str,
            aux_data_path: str = '.aux',
            old_graph: rdflib.Graph = None,
            method: str = 'memory',
            engine: str = 'morph',
            mapping_optimization: bool = True):
    """Materializes a knowledge graph given a data source and a mapping file. It also supports
    updating versions of previously generated graphs when 'snapshot_file' and 'old_graph' are provided.

    Args:
        mapping_file:
            The file name that contains the mappings.
        snapshot_file:
            The snapshot file name.
        aux_data_path:
            The path of an auxiliary directory.
        old_graph:
            A rdflib.Graph that contains the version previously generated. If None, it creates a graph
            from scratch.
        method:
            A string that determines how the auxiliary data is threated:
                - 'disk': The auxiliary data is stored in the disk, under the 'aux_data_path' directory.
                - 'memory': The auxiliary data is stored in memory.
        engine:
            The name of the mapping engine to materialize the graph:
                - 'morph': https://github.com/morph-kgc/morph-kgc.
                - 'rdfizer': https://github.com/SDM-TIB/SDM-RDFizer.
        mapping_optimization:
            If true, the mappings are reduced to contain the rules from the datasources that are updated.

    Returns:
        A new materialized graph when 'old_graph' is None, or a new version of 'old_graph'. The directory
        'aux_data_path' contains at the end:
            - A snapshot file named 'snapshot_file'. This file should not be deleted, since it is used
                with subsequent calls to load_kg().
            - An auxiliary mapping file. This file can be removed.
            - If 'method' is 'disk', the auxiliary data. It can be removed. 
    """

    # Argument checks
    if method not in ['disk', 'memory']:
        raise ValueError("'method' argument must be either 'disk' or 'memory'")
    if engine not in ['morph', 'rdfizer']:
        raise ValueError("'engine' argument must be 'morph' or 'rdfizer'")
    if engine == 'rdfizer' and method != 'disk':
        raise ValueError("'rdfizer' engine only supports 'disk' method")
    
    # Import only the used mapping engine
    if engine == 'morph':
        from morph_kgc import materialize
    elif engine == 'rdfizer':
        from rdfizer import semantify

    # Check if first version or not
    if old_graph is None:
        # First version
        new_version = True
        sp = dict()
    else:
        # Subsequent updates
        new_version = False
        with open(snapshot_file, 'rb') as f:
            sp = pickle.load(file=f)

    # Read mapping
    mapping_graph_new_data = rdflib.Graph().parse(mapping_file)
    mapping_graph_removed_data = rdflib.Graph().parse(mapping_file)

    # Extract sources from mapping
    all_sources = _get_sources_from_mapping(mapping_graph_new_data)

    # Create auxiliary data directory
    aux_data_path_enc = os.fsencode(aux_data_path) # TODO: quitar '/' si aparece al final
    if not os.path.exists(aux_data_path_enc):
        os.makedirs(aux_data_path_enc)
    
    # Create auxiliary dictionary for new data
    new_data_dict = {}
    removed_data_dict = {}
    
    has_new_data = False
    has_removed_data = False

    updated_new_sources = set()
    updated_removed_sources = set()

    start = time.time()
    # Process each source
    for source_file in all_sources:
        # Get extension from source file
        _, extension = os.path.splitext(source_file)
        
        # Calculate new and removed data
        current_data, new_data, removed_data = _process_source(source_file=source_file,
                                                snapshot=sp,
                                                new_version=new_version,
                                                extension=extension)
        
        # Save new and removed data
        if method == 'disk':
            # Save new data to disk if there is any
            if len(new_data) > 0:
                new_data_file_path = _save_data_to_file(data_path=aux_data_path + '/new_data',
                                source_file=source_file,
                                extension=extension,
                                data=new_data)
                msg_new_data = "\tFound new data, saved to %s." % new_data_file_path
                has_new_data = True
                updated_new_sources.add(source_file)
            else:
                if not mapping_optimization:
                    new_data_file_path = _save_data_to_file(data_path=aux_data_path + '/new_data',
                                    source_file=source_file,
                                    extension=extension,
                                    data=new_data)
                    msg_new_data = "\tNo new data, saved to %s." % new_data_file_path
                else:
                    msg_new_data = "\tNo new data."

            # Save removed data to disk if there is any
            if len(removed_data) > 0:
                removed_data_file_path = _save_data_to_file(data_path=aux_data_path + '/removed_data',
                                source_file=source_file,
                                extension=extension,
                                data=removed_data)
                msg_removed_data = "\tFound removed data, saved to %s." % removed_data_file_path
                has_removed_data = True
                updated_removed_sources.add(source_file)
            else:
                if not mapping_optimization:
                    removed_data_file_path = _save_data_to_file(data_path=aux_data_path + '/removed_data',
                                source_file=source_file,
                                extension=extension,
                                data=removed_data)
                    msg_removed_data = "\tNo removed data, saved to %s." % removed_data_file_path
                else:
                    msg_removed_data = "\tNo removed data."

        elif method == 'memory':
            # Save new data to in-memory dict if there is any
            if len(new_data) > 0:
                new_data_dict[source_file] = new_data
                msg_new_data = "\tFound new data, saved to dataframe."
                has_new_data = True
                updated_new_sources.add(source_file)
            else:
                if not mapping_optimization:
                    new_data_dict[source_file] = new_data
                    msg_new_data = "\tNo new data, saved to dataframe."
                else:
                    msg_new_data = "\tNo new data."
            
            # Save removed data to in-memory dict if there is any
            if len(removed_data) > 0:
                removed_data_dict[source_file] = removed_data
                msg_removed_data = "\tFound removed data, saved to dataframe."
                has_removed_data = True
                updated_removed_sources.add(source_file)
            else:
                if not mapping_optimization:
                    removed_data_dict[source_file] = removed_data
                    msg_removed_data = "\tNo removed data, saved to dataframe."
                else:
                    msg_removed_data = "\tNo removed data."
        else:
            raise RuntimeError('\'method\' is not \'disk\' or \'memory\', This should not happend :(')
        
        # Print messages
        print(source_file)
        print(msg_new_data)
        print(msg_removed_data)
        
        # Save the current in the snapshot
        sp[source_file] = current_data
        # Save current snapshot data = old + new_data - removed_data
        # updated_snapshot_data = _calculate_new_snapshot_df(old_data=old_data,
        #                                                    new_data=new_data,
        #                                                    removed_data=removed_data,
        #                                                    extension=extension)
        # sp[source_file] = updated_snapshot_data

    end = time.time()

    print("Finished calculating diff in %.2fs." % (end-start))

    # Save snapshot
    # TODO: Create parent dir if it does not exist
    with open(snapshot_file, 'wb') as f:
        pickle.dump(obj=sp, file=f)
        print("Saved snapshot to", snapshot_file)
    
    if mapping_optimization:
        # Calculate the mappings of the changed files
        if len(updated_new_sources) > 0:
            # Retrieve mappings related to the sources with new data
            query_update_sources = constants.QUERY_SOURCES % (tuple([", ".join(["\"%s\"" % e for e in updated_new_sources])] * 7))
            query_res = mapping_graph_new_data.query(query_update_sources)
            new_g = rdflib.Graph()
            for i in query_res:
                new_g.add(i)
            mapping_graph_new_data = new_g

        if len(updated_removed_sources) > 0:
            # Retrieve mappings related to the sources with removed data
            query_update_sources = constants.QUERY_SOURCES % (tuple([", ".join(["\"%s\"" % e for e in updated_removed_sources])] * 7))
            query_res = mapping_graph_removed_data.query(query_update_sources)
            new_g = rdflib.Graph()
            for i in query_res:
                new_g.add(i)
            mapping_graph_removed_data = new_g
    
    # Create queries for the mappings to support new sources
    if method == 'disk':
        query_update_new_data = constants.QUERY_DISK % (aux_data_path + '/new_data')
        query_update_removed_data = constants.QUERY_DISK % (aux_data_path + '/removed_data')
        pass
    elif method == 'memory':
        query_update_new_data = constants.QUERY_MEMORY
        query_update_removed_data = query_update_new_data # Same query in 'memory'
    else:
        raise RuntimeError('\'method\' is not \'disk\' or \'memory\', This should not happend :(')

    if engine == 'morph':
        mapping_func = materialize
    elif engine == 'rdfizer':
        mapping_func = semantify

    # Materialize new data
    print("Materializing graph...")
    start = time.time()
    if has_new_data:
        print("Updating mappings... ", end='')
        new_mapping_file = _update_mappings(mapping_graph=mapping_graph_new_data,
                                            query_update=query_update_new_data,
                                            data_path=aux_data_path + '/new_data',
                                            mapping_file=mapping_file)
        print("OK")
        print("Running mapping engine on the new data...")
        new_triples = _materialize_set(engine=engine,
                                       mapping_function=mapping_func,
                                       new_mapping_file=new_mapping_file,
                                       method=method,
                                       data_dict=new_data_dict,
                                       aux_data_path=aux_data_path,
                                       type_p='new')
    else:
        print("No new data detected in the data source, no need to run the mapping engine.")
        new_triples = rdflib.Graph()
    
    # Materialize removed data
    if has_removed_data:
        print("Updating mappings... ", end='')
        new_mapping_file = _update_mappings(mapping_graph=mapping_graph_removed_data,
                                            query_update=query_update_removed_data,
                                            data_path=aux_data_path + '/removed_data',
                                            mapping_file=mapping_file)
        print("OK")
        print("Running mapping engine on the removed data...")

        removed_triples = _materialize_set(engine=engine,
                                           mapping_function=mapping_func,
                                           new_mapping_file=new_mapping_file,
                                           method=method,
                                           data_dict=removed_data_dict,
                                           aux_data_path=aux_data_path,
                                           type_p='removed')
    else:
        print("No removed data detected in the data source, no need to run the mapping engine.")
        removed_triples = rdflib.Graph()
    
    end = time.time()
    print("Materialization complete in %.2fs" % (end-start))

    # Return the materialized graph if it is a new version
    if old_graph is None:
        return new_triples

    # Return the new graph = old graph + new graph - removed graph
    print("Constructing new graph... ", end='')
    start = time.time()
    # old_plus_new_graph = old_graph + new_graph
    for new_triple in new_triples:
        old_graph.add(new_triple)
    # old_plus_new_minus_rm_graph = old_plus_new_graph - removed_graph
    for removed_triple in removed_triples:
        old_graph.remove(removed_triple)
    # TODO: (optimization) check which of the graphs is larger, and run the for loop in the other (validate) 
    end = time.time()
    print("OK (%.2fs)" % (end-start))

    return old_graph
