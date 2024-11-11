from jwt import InvalidTokenError


def extract_token(auth_header):
    """
    Extracts the JWT token from the Authorization header.

    Args:
        auth_header (str): The Authorization header value.

    Returns:
        str: The extracted JWT token.

    Raises:
        InvalidTokenError: If the token is not properly formatted.
    """
    parts = auth_header.split()
    if len(parts) == 1:  # Without fisrt "Bearer " string
        return parts[0]

    if len(parts) == 2:  # With fisrt "Bearer " string
        return parts[1]

    raise InvalidTokenError("Invalid Authorization header format.")
