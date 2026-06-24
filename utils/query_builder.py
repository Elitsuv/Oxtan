from typing import Union, Dict, Any, Tuple, List

def build_where_clause(where: Union[str, Dict[str, Any], None]) -> Tuple[str, List[Any]]:
    """
    Constructs a SQL WHERE clause and its parameters.
    
    Args:
        where: A dictionary of key-value pairs or a string condition.
        
    Returns:
        A tuple containing the WHERE clause string and a list of parameters.
    """
    if not where:
        return "", []
        
    if isinstance(where, dict):
        clause = " WHERE " + " AND ".join([f"{k} = %s" for k in where.keys()])
        params = list(where.values())
        return clause, params
    elif isinstance(where, str):
        return f" WHERE {where}", []
    else:
        raise TypeError("where clause must be a dictionary or a string.")
