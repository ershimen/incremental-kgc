# Incremental Knowledge Graph Construction

Incremental-KGC is a Python package that allows to efficiently materialize subsequent versions of knowledge graphs. It utilizes the previous version of a snapshot of the data source and the knowledge graph to materialize only the modified data. Currently it supports both additions and deletions in the data source.

## Usage 

The functionality is provided through the `load_kg()` function, which has the following arguments:

* `mapping_file`: The path of the mapping file.
* `snapshot_file`: The path of the snapshot file.
* `aux_data_path`: The path of the auxiliary directory.
* `old_graph`: A `rdflib.Graph` that contains the version previously generated, or `None`.
* `engine`: The name of the mapping engine to materialize the graph. Currently only [`morph`](https://github.com/morph-kgc/morph-kgc) and [`rdfizer`](https://github.com/SDM-TIB/SDM-RDFizer) are supported.
* `method`: either `disk` or `memory`. If `disk`, the auxiliary data is stored in the disk, under the `aux_data_path` directory. If `memory`, the auxiliary data is stored in memory. `memory` is only supported when `engine` is `morph`.
* `mapping_optimization`: If `True` (default), the mappings are reduced to contain only the rules from the data sources that are updated.

The behavior depends on whether it is the first version or not.

### First Version

When materializing for the first time, the argument `old_graph` should be `None`. An example is shown below.

```Python
g = load_kg(mapping_file='mapping.csv.ttl',
            snapshot_file='snapshot_file',
            aux_data_path='./.aux',
            old_graph=None,
            method='disk',
            engine='morph',
            mapping_optimization=True)
```

This call to `load_kg()` returns the new version of the knowledge graph as a `rdflib.Graph` instance. It also saves the snapshot to `snapshot_file`, which is necessary for further updates.

### Subsequent Updates

For subsequent updates, the argument `old_graph` should be a `rdflib.Graph` instance that was generated from the same mapping file. An example is shown below. Note that the graph `g` from the previous snippet is passed as `old_graph`.

```Python
g = load_kg(mapping_file='mapping.csv.ttl',
            snapshot_file='snapshot_file',
            aux_data_path='./.aux',
            old_graph=g,
            method='disk',
            engine='morph',
            mapping_optimization=True)
```

## Supported Data Sources

Currently only CSV data sources are supported. If you are interested in supporting more, please read the [Contributing section](#contributing).

## Supported Mapping Engines

Currently only the [Morph-KGC](https://github.com/morph-kgc/morph-kgc) and [SDM-RDFizer](https://github.com/SDM-TIB/SDM-RDFizer) mapping engines are supported. If you are interested in supporting more, please read the [Contributing section](#contributing).

## Contributing

If you are interested in contributing to the project, please make sure to open a pull request with the changes, the corresponding tests and documentation. The following sections describe the process of supporting new data source types and mapping engines, however any additional improvement or extension is welcome.

### Supporting new data source types

To support a new data source, the first step is to think a Python object that can represent one file. For instance, a CSV file can be represented as a `pandas.Dataframe`. Then, the following functions need to be expanded. Please read the documentation of each function before writing changes.

* `_process_source()`. The function must return three Python objects, each one with the following information.
    - The set of new data, which represents the data present in the data source but not in the snapshot.
    - The set of removed data, which represents the data present in the snapshot but not in the data source.
    - The set of old data, which represents the data from the snapshot.

* `_save_data_to_file()`. This function must serialize the Python object used to represent each source.

* `_calculate_new_snapshot_df()`. This function calculates the new snapshot data by adding the set of new data and subtracting the set of removed data. These sets of data are the ones returned by `_process_source()`.

### Supporting new mapping engines

In order to support a new mapping engine, the function `_materialize_set()` must be expanded. The function should return a `rdflib.Graph` containing the generated triples. Note that if the new mapping engine is not written in python, it could be possible to run a script with `subprocess.run` and then read the output triples with `rdflib`.

Additionally, in the case the engine is a Python library, in `load_kg()`, the import statement should be added.

### Adding tests

Tests are placed under the `test/` directory. Feel free to add new tests and create new directories.
