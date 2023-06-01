import pandas as pd

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
