QUERY_DISK = """
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>

    DELETE { ?h rml:source ?source }
    INSERT { ?h rml:source ?new_source }
    WHERE {
        ?h rml:source ?source .
        BIND(CONCAT("%s/", ?source) AS ?new_source) .
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

QUERY_SOURCES = """
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    
    SELECT ?s ?p ?o
    WHERE {
        {
            # rml:source
            ?s rml:source ?s_filter  .
            FILTER (?s_filter IN (%s)) .
            ?s ?p ?o .
        }
        UNION
        {
            # rml:logicalSource
            ?source rml:source ?s_filter .
            FILTER (?s_filter IN (%s)) .
            ?s rml:logicalSource ?source .
            ?s ?p ?o
        }
        UNION
        {
            # rr:predicateObjectMap
            ?source rml:source ?s_filter  .
            FILTER (?s_filter IN (%s)) .
            ?ls rml:logicalSource ?source .
            ?ls rr:predicateObjectMap ?s .
            ?s ?p ?o .
        }
        UNION
        {
            # rr:objectMap
            ?source rml:source ?s_filter  .
            FILTER (?s_filter IN (%s)) .
            ?ls rml:logicalSource ?source .
            ?ls rr:predicateObjectMap ?pom .
            ?pom rr:objectMap ?s .
            ?s ?p ?o .
        }
        UNION
        {
            # rr:predicateMap
            ?source rml:source ?s_filter  .
            FILTER (?s_filter IN (%s)) .
            ?ls rml:logicalSource ?source .
            ?ls rr:predicateObjectMap ?pom .
            ?pom rr:predicateMap ?s .
            ?s ?p ?o .
        }
        UNION
        {
            # rr:subjectMap
            ?source rml:source ?s_filter  .
            FILTER (?s_filter IN (%s)) .
            ?ls rml:logicalSource ?source .
            ?ls rr:subjectMap ?s .
            ?s ?p ?o .
        }
        UNION
        {
            # rr:joinCondition
            ?source rml:source ?s_filter  .
            FILTER (?s_filter IN (%s)) .
            ?ls rml:logicalSource ?source .
            ?ls rr:predicateObjectMap ?pom .
            ?pom rr:objectMap ?om .
            ?om rr:joinCondition ?s .
            ?s ?p ?o .
        }
    }
"""