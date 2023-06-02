import pandas as pd
import rdflib
import os
import pickle

import morph_kgc

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
    the old, new and removed data.

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
        A triple (old_data, new_data, removed_data). The type depends on 'extension'. All three items
        have null intersection (no duplicates between them). TODO: ??
            - old_data: data that is in snapshot.
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

        return df_sp, new_data, removed_data
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')


def _save_data_to_file(aux_data_path:str, source_file: str, extension: str, data: object):
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
    new_file_path = aux_data_path.decode('utf-8') + '/' + source_file
    # Create directories for aux file
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    # Save data
    if extension == '.csv':
        data.to_csv(new_file_path, index=False)
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')

    return new_file_path


def _calculate_new_snapshot_df(old_data: object, new_data: object, removed_data: object, extension: str):
    """Calculates the new snapshot data (old + new - removed). The type of 'old_data', 'new_data' and 'removed_data'
    depends on 'extension'.

    Args:
        old_data:
            The old data in the snapshot.
        new_data:
            The new data.
        removed_data:
            The removed data.
        extension:
            The extension. It determines how to handle the other parameters:
                .csv: python dictionary.

    Returns:
        The resulting data from the operation old_data + new_data - removed_data.
    """

    # New snapshot data = old_dataold_graph + new_data - removed_data
    if extension == '.csv':
        old_plus_new = pd.concat([old_data, new_data]) # no need to drop duplicates because there should not be any
        old_plus_new_minus_rm = pd.concat([old_plus_new, removed_data]) # No need to concat two times removed_data (pd.concat([old_plus_new, removed_data, removed_data])) because there should not be any data in removed_data that is not already in old_plus_new
        return old_plus_new_minus_rm
    elif extension == '.json':
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    else:
        raise NotImplementedError(f'The file type {extension} is not supported yet!')
    pass


def _load_kg_aux_to_disk(aux_data_path: str,
                        mapping_file: str,
                        snapshot_file: str,
                        old_graph: rdflib.Graph,
                        engine: str):
    """DEPRECATED
    """
    # load snapshot
    if os.path.exists(snapshot_file):
        new_version = False
        # snapshot exists
        with open(snapshot_file, 'rb') as f:
            sp = pickle.load(file=f)
    else:
        new_version = True
        # first version
        sp = dict()
    
    # Read mapping
    mapping_graph = rdflib.Graph().parse(mapping_file)
    
    # Extract sources from mapping
    all_sources = _get_sources_from_mapping(mapping_graph)

    # Create auxiliary data directory
    aux_data_path = os.fsencode(aux_data_path) # TODO: quitar '/' si aparece al final
    if not os.path.exists(aux_data_path):
        os.makedirs(aux_data_path)
    
    # Calculate diff between every new and old file
    for source_file in all_sources:
        
        old_file_object = pd.DataFrame() if new_version else sp[source_file]
        new_data = _process_source(source_file=source_file,
                                   old_file_object=old_file_object)

        # save new data to new_data_dir
        new_file_path = aux_data_path.decode('utf-8') + '/' + source_file
        
        # Create directories for aux file
        os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
        # Save aux file
        new_data.to_csv(new_file_path, index=False)
        if len(new_data) == 0:
            print("No new data in %s, created empty file %s." % (source_file, new_file_path))
        else:
            print("Found new data in %s, saved to file %s." % (source_file, new_file_path))
        
        # save current snapshot = old + new
        sp[source_file] = pd.concat([old_file_object, new_data]) # should not have duplicates
    
    # Save snaphsot
    # TODO: Create parent dir if it does not exist
    with open(snapshot_file, 'wb') as f:
        pickle.dump(obj=sp, file=f)
        print("Saved snapshot to", snapshot_file)
    
    # Change source paths from mapping
    ## for every foaf:member_name, add foaf:name and remove foaf:member_name
    #for s, p, o in g.triples((None, FOAF['member_name'], None)):
    #   g.add((s, FOAF['name'], o))
    #   g.remove((s, FOAF['member_name'], o))
    query_update = """
            PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
            
            DELETE { ?h rml:source ?source }
            INSERT { ?h rml:source ?new_source }
            WHERE {
                ?h rml:source ?source .
                BIND(CONCAT(".aux/", ?source) AS ?new_source) .
            }
        """
    print("Updating mappings...")
    mapping_graph.update(query_update)
    
    # Save new mapping
    new_mapping_file = aux_data_path.decode('utf-8') + '/.aux_' + mapping_file
    mapping_graph.serialize(new_mapping_file)
    print("Updated mappings.")

    print("Materializing graph...")
    config = "[GTFS-Madrid-Bench]\nmappings: %s" % new_mapping_file
    new_graph = morph_kgc.materialize(config)
    print("Materialized graph.")
    # TODO: delete temp data dir?

    # return old_graph + new_graph
    if old_graph is None:
        return new_graph
    
    print("Concatenaing old and new graphs...")
    for triple in new_graph:
        old_graph.add(triple)
    print("Concatenated old and new graphs.")
    return old_graph


def _load_kg_aux_to_mem(aux_data_path: str,
                       mapping_file: str,
                       snapshot_file: str,
                       old_graph: rdflib.Graph,
                       engine: str):
    """DEPRECATED
    """
    # load snapshot
    if os.path.exists(snapshot_file):
        new_version = False
        # snapshot exists
        with open(snapshot_file, 'rb') as f:
            sp = pickle.load(file=f)
    else:
        new_version = True
        # first version
        sp = dict()
    
    # Read mapping
    mapping_graph = rdflib.Graph().parse(mapping_file)
    
    # Extract sources from mapping
    all_sources = _get_sources_from_mapping(mapping_graph)

    # Create auxiliary data directory
    aux_data_path = os.fsencode(aux_data_path) # TODO: quitar '/' si aparece al final
    if not os.path.exists(aux_data_path):
        os.makedirs(aux_data_path)

    # Create auxiliary dictionary for new data
    new_data_dict = {}
    
    # Calculate diff between every new and old file
    for source_file in all_sources:

        old_file_object = pd.DataFrame() if new_version else sp[source_file]
        new_data = _process_source(source_file=source_file,
                                   old_file_object=old_file_object)

        # Save new_data to new_data_dict
        new_data_dict[source_file] = new_data

        if len(new_data) == 0:
            print("No new data in %s, created empty dataframe." % (source_file))
        else:
            print("Found new data in %s, saved to dataframe." % (source_file))
        
        # save current snapshot = old + new
        sp[source_file] = pd.concat([old_file_object, new_data]) # should not have duplicates
    
    #print(new_data_dict)
    
    # Save snaphsot
    # TODO: Create parent dir if it does not exist
    with open(snapshot_file, 'wb') as f:
        pickle.dump(obj=sp, file=f)
        print("Saved snapshot to", snapshot_file)
    
    # Change source paths from mapping
    ## for every foaf:member_name, add foaf:name and remove foaf:member_name
    #for s, p, o in g.triples((None, FOAF['member_name'], None)):
    #   g.add((s, FOAF['name'], o))
    #   g.remove((s, FOAF['member_name'], o))
    query_update = """
        PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
        PREFIX sd: <https://w3id.org/okn/o/sd/>
        PREFIX ql: <http://semweb.mmlab.be/ns/ql#>
        PREFIX kg4di: <https://w3id.org/kg4di/definedBy>
            
        DELETE {
            ?source a rml:LogicalSource;
                rml:source ?source_file;
                rml:referenceFormulation ?format.
        }
        INSERT {
            #?source rml:source ?source_file. # TODO: remove this
            ?source a rml:LogicalSource;
                rml:source [
                    a sd:DatasetSpecification;
                    sd:name ?source_file;
                    sd:hasDataTransformation [
                        sd:hasSoftwareRequirements "pandas>=1.5.3";
                        sd:hasSourceCode [
                            sd:programmingLanguage "Python3.9";
			            ];
		            ];
                    
                ];
                rml:referenceFormulation ql:DataFrame.
            ql:DataFrame a rml:ReferenceFormulation;
	            kg4di:definedBy "Pandas".
        }
        WHERE {
            ?source a rml:LogicalSource;
                rml:source ?source_file;
                rml:referenceFormulation ?format.
        }
      """
    
    print("Updating mappings...")
    mapping_graph.update(query_update)
    
    # Save new mapping
    new_mapping_file = aux_data_path + '/.aux_' + mapping_file
    mapping_graph.serialize(new_mapping_file)
    print("Updated mappings.")

    print("Materializing graph...")
    config = "[GTFS-Madrid-Bench]\nmappings: %s" % new_mapping_file
    new_graph = morph_kgc.materialize(config, new_data_dict)
    print("Materialized graph.")

    # TODO: delete temp mapping file?

    # return old_graph + new_graph
    if old_graph is None:
        return new_graph

    print("Concatenaing old and new graphs...")
    for triple in new_graph:
        old_graph.add(triple)
    print("Concatenated old and new graphs.")
    return old_graph


def load_kg(mapping_file: str,
            snapshot_file: str,
            aux_data_path: str = '.aux',
            old_graph: rdflib.Graph = None,
            method: str = 'memory',
            engine: str = 'morph'):
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
    if engine not in ['morph']:
        raise ValueError("'engine' argument must be 'morph'")
    
    # load snapshot
    if os.path.exists(snapshot_file):
        new_version = False
        # snapshot exists
        with open(snapshot_file, 'rb') as f:
            sp = pickle.load(file=f)
    else:
        new_version = True
        # first version
        sp = dict()
    
    # Read mapping
    mapping_graph = rdflib.Graph().parse(mapping_file)

    # Extract sources from mapping
    all_sources = _get_sources_from_mapping(mapping_graph)

    # Create auxiliary data directory
    aux_data_path = os.fsencode(aux_data_path) # TODO: quitar '/' si aparece al final
    if not os.path.exists(aux_data_path):
        os.makedirs(aux_data_path)
    
    if method == 'memory':
        # Create auxiliary dictionary for new data
        new_data_dict = {}
        removed_data_dict = {}
    
    has_new_data = False
    has_removed_data = False
    
    # Process each source
    for source_file in all_sources:
        # Get extension from source file
        _, extension = os.path.splitext(source_file)
        
        # Calculate new and removed data
        old_data, new_data, removed_data = _process_source(source_file=source_file,
                                                snapshot=sp,
                                                new_version=new_version,
                                                extension=extension)
        
        # Save new and removed data
        if method == 'disk':
            # Save new data to disk
            new_file_path = _save_data_to_file(aux_data_path=aux_data_path,
                            source_file=source_file,
                            extension=extension,
                            data=new_data)
            msg = "\t%%s, %%s file %s." % (new_file_path)
            #msg_new_data = "%%s, %%s file %s." % (new_file_path)
            #msg_removed_data = "%%s, %%s file %s." % (new_file_path)
        elif method == 'memory':
            # Save data to in-memory dict
            new_data_dict[source_file] = new_data
            removed_data_dict[source_file] = removed_data
            msg = "\t%s, %s dataframe."
            #msg_new_data = "%%s, %%s dataframe."
            #msg_removed_data = "%%s, %%s dataframe."
        else:
            raise RuntimeError('\'method\' is not \'disk\' or \'memory\', This should not happend :(')
        
        # Print message and set has_new_data, has_removed_data flags
        print(source_file)
        if len(new_data) == 0:
            print(msg % ('No new data', 'created empty'))
        else:
            print(msg % ('Found new data', 'saved to'))
            has_new_data = True
        
        if len(removed_data) == 0:
            print(msg % ('No removed data', 'saved to'))
        else:
            print(msg % ('Found removed data', 'saved to'))
            has_removed_data = True
        
        # Save current snapshot data = old + new_data - removed_data
        updated_snapshot_data = _calculate_new_snapshot_df(old_data=old_data,
                                                           new_data=new_data,
                                                           removed_data=removed_data,
                                                           extension=extension)
        sp[source_file] = updated_snapshot_data

    # Save snapshot
    # TODO: Create parent dir if it does not exist
    with open(snapshot_file, 'wb') as f:
        pickle.dump(obj=sp, file=f)
        print("Saved snapshot to", snapshot_file)
    
    # Change mappings to support new sources
    if method == 'disk':
        # TODO: change ".aux/" to aux_data_path inside the query
        query_update = constants.QUERY_DISK
        pass
    elif method == 'memory':
        query_update = constants.QUERY_MEMORY
    else:
        raise RuntimeError('\'method\' is not \'disk\' or \'memory\', This should not happend :(')

    print("Updating mappings... ", end='')
    mapping_graph.update(query_update)

    # Save new mappings to file
    new_mapping_file = aux_data_path.decode('utf-8') + '/.aux_' + mapping_file
    mapping_graph.serialize(new_mapping_file)
    print("OK")

    # Materialize new data
    print("Materializing graph...")
    if engine == 'morph':
        config = "[GTFS-Madrid-Bench]\nmappings: %s" % new_mapping_file
        if method == 'disk':
            if has_new_data:
                print("Running mapping engine on the new data...")
                new_triples = morph_kgc.materialize(config)
            else:
                print("No new data detected in the data source, no need to run the mapping engine.")
                new_triples = rdflib.Graph()
            if has_removed_data:
                raise NotImplementedError("removed data in 'disk' is not implemented yet!")
        elif method == 'memory':
            # Run mapping engine with new data only if there is any
            if has_new_data:
                print("Running mapping engine on the new data...")
                new_triples = morph_kgc.materialize(config, new_data_dict)
            else:
                print("No new data detected in the data source, no need to run the mapping engine.")
                new_triples = rdflib.Graph()
            # Run mapping engine with removed data only if there is any
            if has_removed_data:
                print("Running mapping engine on the removed data...")
                removed_triples = morph_kgc.materialize(config, removed_data_dict)
            else:
                print("No removed data detected in the data source, no need to run the mapping engine.")
                removed_triples = rdflib.Graph()
        else:
            raise RuntimeError('\'method\' is not \'disk\' or \'memory\', This should not happend :(')
    else:
        raise RuntimeError('\'engine\' is not \'morph\', This should not happend :(')
    print("Materialized graph.")

    # TODO: calculate removed_graph

    # Return the materialized graph if it is a new version
    if old_graph is None:
        return new_triples

    # Return the new graph = old graph + new graph - removed graph
    print("Constructing new graph... ", end='')
    # old_plus_new_graph = old_graph + new_graph
    for new_triple in new_triples:
        old_graph.add(new_triple)
    # old_plus_new_minus_rm_graph = old_plus_new_graph - removed_graph
    for removed_triple in removed_triples:
        old_graph.remove(removed_triple)
    # TODO: (optimization) check which of the graphs is larger, and run the for loop in the other (validate) 
    print("OK")

    return old_graph
