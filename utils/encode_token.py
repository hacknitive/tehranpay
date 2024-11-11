from django.conf import settings
from jwt import encode


def encode_token(payload: dict) -> str:
    """Encodes a payload into a JWT token using the RS256 algorithm.

    This function takes a dictionary `payload` and encodes it into a JSON Web Token
    (JWT) using the RS256 algorithm. The encoding process utilizes a private key
    specified in the Django settings (`JWT_PRIVATE_KEY`).

    Args:
        payload (dict): The payload data to encode into the token.

    Returns:
        str: The encoded JWT token as a string.

    Raises:
        jwt.PyJWTError: If the token encoding fails due to an invalid payload or key.
    """
    return encode(
        payload=payload,
        key=settings.JWT_PRIVATE_KEY,
        algorithm="RS256",
    )