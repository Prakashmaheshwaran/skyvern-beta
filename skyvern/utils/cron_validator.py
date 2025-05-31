import re
from typing import Dict, Tuple


def validate_cron_expression(cron_expression: str) -> Tuple[bool, str]:
    """
    Validates a cron expression.
    
    Args:
        cron_expression: The cron expression to validate (e.g., "0 9 * * MON-FRI")
        
    Returns:
        Tuple containing:
            - Boolean indicating if the cron expression is valid
            - String with error message if invalid, empty string if valid
    """
    if not cron_expression or not isinstance(cron_expression, str):
        return False, "Cron expression must be a non-empty string"
        
    # Remove any extra whitespace
    cron_expression = cron_expression.strip()
    
    # Split the expression into its components
    parts = cron_expression.split()
    
    # A standard cron expression has 5 parts: minute, hour, day of month, month, day of week
    if len(parts) != 5:
        return False, f"Cron expression must have exactly 5 fields, found {len(parts)}"
    
    # Define patterns for each field
    patterns = {
        "minute": r"^(\*|[0-5]?[0-9](-[0-5]?[0-9])?)(,(\*|[0-5]?[0-9](-[0-5]?[0-9])?))*$|^\*/[1-9][0-9]?$",
        "hour": r"^(\*|[01]?[0-9]|2[0-3])((-|\/)([01]?[0-9]|2[0-3]))?(,([01]?[0-9]|2[0-3])((-|\/)([01]?[0-9]|2[0-3]))?)*$|^\*/([1-9]|1[0-9]|2[0-3])$",
        "day_of_month": r"^(\*|[1-9]|[12][0-9]|3[01])((-|\/)(([1-9]|[12][0-9]|3[01])))?(,(([1-9]|[12][0-9]|3[01])((-|\/)(([1-9]|[12][0-9]|3[01])))?))*$|^\*/([1-9]|[12][0-9]|3[01])$|^\?$",
        "month": r"^(\*|[1-9]|1[0-2]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)((-|\/)(([1-9]|1[0-2]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)))?(,(([1-9]|1[0-2]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)((-|\/)(([1-9]|1[0-2]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)))?))*$|^\*/([1-9]|1[0-2])$",
        "day_of_week": r"^(\*|[0-7]|SUN|MON|TUE|WED|THU|FRI|SAT)((-|\/)([0-7]|SUN|MON|TUE|WED|THU|FRI|SAT))?(,(([0-7]|SUN|MON|TUE|WED|THU|FRI|SAT)((-|\/)([0-7]|SUN|MON|TUE|WED|THU|FRI|SAT)))?))*$|^\*/[1-7]$|^\?$"
    }
    
    field_names = ["minute", "hour", "day_of_month", "month", "day_of_week"]
    
    # Validate each field
    for i, (field, pattern) in enumerate(zip(field_names, patterns.values())):
        if not re.match(pattern, parts[i], re.IGNORECASE):
            return False, f"Invalid {field} field: '{parts[i]}'"
    
    # Check for logical constraints (e.g., day of month and day of week can't both be restricted)
    if parts[2] != "*" and parts[2] != "?" and parts[4] != "*" and parts[4] != "?":
        return False, "Day-of-month and day-of-week can't both be restricted"
        
    return True, ""


def get_next_run_description(cron_expression: str) -> str:
    """
    Returns a human-readable description of when the cron will next run.
    This is a simplified implementation that returns a general description.
    
    Args:
        cron_expression: A valid cron expression
        
    Returns:
        A string describing when the cron will next run
    """
    parts = cron_expression.split()
    if len(parts) != 5:
        return "Invalid cron expression"
        
    minute, hour, day_of_month, month, day_of_week = parts
    
    # Common patterns with descriptions
    if minute == "0" and hour == "0" and day_of_month == "*" and month == "*" and day_of_week == "*":
        return "Runs daily at midnight (00:00)"
        
    if minute == "0" and hour == "*" and day_of_month == "*" and month == "*" and day_of_week == "*":
        return "Runs hourly at the start of each hour"
        
    if minute == "0" and hour == "0" and day_of_month == "*" and month == "*" and day_of_week == "0":
        return "Runs weekly on Sunday at midnight (00:00)"
        
    if minute == "0" and hour == "0" and day_of_month == "1" and month == "*" and day_of_week == "*":
        return "Runs monthly on the 1st at midnight (00:00)"
        
    if minute == "0" and hour == "0" and day_of_month == "1" and month == "1" and day_of_week == "*":
        return "Runs yearly on January 1st at midnight (00:00)"
    
    if day_of_week in ["1-5", "MON-FRI"]:
        return f"Runs on weekdays (Monday-Friday) at {hour}:{minute}"
        
    # Generic description for other patterns
    return f"Runs according to cron schedule: {cron_expression}"
