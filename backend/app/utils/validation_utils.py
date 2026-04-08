from app.config.logging_config import get_logger

logger = get_logger("validation_utils")

def is_dict(obj):
    """Check if the object is a dictionary."""
    if not isinstance(obj, dict):
        logger.warning(f"Expected dict but got {type(obj)}")
        return False
    return True

def has_keys(obj, required_keys):
    """
    Check if all required keys exist in a dictionary.
    - obj: dict
    - required_keys: list of strings
    """
    if not is_dict(obj):
        return False
    missing = [key for key in required_keys if key not in obj]
    if missing:
        logger.warning(f"Missing keys: {missing}")
        return False
    return True

def is_not_empty(value):
    """Check if a value is not None or empty."""
    if value is None or (hasattr(value, "__len__") and len(value) == 0):
        logger.warning("Value is empty or None")
        return False
    return True

def validate_list_of_dicts(data, required_keys=None):
    """
    Validate a list of dictionaries.
    - Checks each element is a dict
    - Optionally checks required keys in each dict
    """
    if not isinstance(data, list):
        logger.warning(f"Expected list but got {type(data)}")
        return False

    for i, item in enumerate(data):
        if not is_dict(item):
            logger.warning(f"Item {i} is not a dict")
            return False
        if required_keys and not has_keys(item, required_keys):
            logger.warning(f"Item {i} missing required keys")
            return False
    return True