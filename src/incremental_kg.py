import pandas as pd
import rdflib
import os
import pickle

import sys
sys.path.append('../../morph-kgc-ram/src/morph_kgc')

import morph_kgc

def load_kg_aux_to_disk(aux_data_path: str, mapping_file: str, snapshot_file: str, old_graph: rdflib.Graph):
    """mapping: path to mapping file
    snapshot: path to snapshot file
    old_graph: None or old version
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
    mapping_query = """
            PREFIX rml: <http://semweb.mmlab.be/ns/rml#>

            SELECT ?source {
                ?h rml:source ?source
            }
        """
    query_res = mapping_graph.query(mapping_query)
    all_sources = set([str(row['source']) for row in query_res]) # Ignore duplicates

    # Create auxiliary data directory
    aux_data_path = os.fsencode(aux_data_path) # TODO: quitar '/' si aparece al final
    # create temp dir for new data
    if not os.path.exists(aux_data_path):
        os.makedirs(aux_data_path)
    
    # Calculate diff between every new and old file
    for source_file in all_sources:
        # read dataframes
        df_ds = pd.read_csv(source_file, dtype=str) # source dataframe
        df_sp = pd.DataFrame() if new_version else sp[source_file] # snapshot dataframe
        
        # find differences (assumes that new data is only in df_datasource)
        new_data = pd.concat([df_sp, df_ds]).drop_duplicates(keep=False)

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
        sp[source_file] = pd.concat([df_sp, new_data]) # should not have duplicates
    
    # Save snaphsot
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


def load_kg_aux_to_mem(aux_data_path: str, mapping_file: str, snapshot_file: str, old_graph: rdflib.Graph):
    """mapping: path to mapping file
    snapshot: path to snapshot file
    old_graph: None or old version
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
    mapping_query = """
            PREFIX rml: <http://semweb.mmlab.be/ns/rml#>

            SELECT ?source {
                ?h rml:source ?source
            }
        """
    query_res = mapping_graph.query(mapping_query)
    all_sources = set([str(row['source']) for row in query_res]) # Ignore duplicates

    # Create auxiliary dictionary for new data
    new_data_dict = {}
    
    # Calculate diff between every new and old file
    for source_file in all_sources:
        # read dataframes
        df_ds = pd.read_csv(source_file)#, dtype=str) # source dataframe
        df_sp = pd.DataFrame() if new_version else sp[source_file] # snapshot dataframe
        
        # find differences (assumes that new data is only in df_datasource)
        new_data = pd.concat([df_sp, df_ds]).drop_duplicates(keep=False)

        # Save new_data to new_data_dict
        new_data_dict[source_file] = new_data

        if len(new_data) == 0:
            print("No new data in %s, created empty dataframe." % (source_file))
        else:
            print("Found new data in %s, saved to dataframe." % (source_file))
        
        # save current snapshot = old + new
        sp[source_file] = pd.concat([df_sp, new_data]) # should not have duplicates
    
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


def _old_load_kg(aux_data_path: str, mapping_file: str, snapshot_file: str, old_graph: rdflib.Graph, method: str):
    if method == 'disk':
        load_kg_aux_to_disk(aux_data_path=aux_data_path,
                            mapping_file=mapping_file,
                            snapshot_file=snapshot_file,
                            old_graph=old_graph)
    elif method == 'memory':
        load_kg_aux_to_mem(aux_data_path=None,
                           mapping_file=mapping_file,
                           snapshot_file=snapshot_file,
                           old_graph=old_graph)
    else:
        print('Unknown method')
        pass
