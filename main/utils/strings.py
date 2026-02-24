def truncate(text:str, length:int) -> str:
    """Cut off at given length while keeping words intact"""
    return " ".join(text[:length].split()[:-2])