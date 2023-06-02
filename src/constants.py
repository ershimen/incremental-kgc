QUERY_DISK = """
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>

    DELETE { ?h rml:source ?source }
    INSERT { ?h rml:source ?new_source }
    WHERE {
        ?h rml:source ?source .
        BIND(CONCAT(".aux/", ?source) AS ?new_source) .
    }
"""

QUERY_MEMORY = """
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