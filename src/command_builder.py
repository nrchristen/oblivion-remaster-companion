# Placeholder for command construction logic 

def build_simple_command(command_name):
    """Builds simple commands like 'walk' or 'ghost'."""
    # Currently just returns the name, but could add validation/formatting
    if isinstance(command_name, str) and command_name:
        return command_name.strip()
    return None

def build_placeatme_command(item_id, quantity):
    """Builds the 'player.placeatme' command."""
    if not isinstance(item_id, str) or not item_id:
        return None
    if not isinstance(quantity, int) or quantity <= 0:
        return None
    return f"player.placeatme {item_id.strip()} {quantity}"

def build_additem_command(item_id, quantity):
    """Builds the 'player.additem' command."""
    if not isinstance(item_id, str) or not item_id:
        return None
    if not isinstance(quantity, int) or quantity <= 0:
        return None
    return f"player.additem {item_id.strip()} {int(quantity)}"

def build_teleport_command(location_id):
    """Builds the 'coc' (Center on Cell) command.

    Args:
        location_id (str): The target location ID (cell name).

    Returns:
        str: The formatted console command, or None if input is invalid.
    """
    if not location_id or not isinstance(location_id, str) or not location_id.strip():
        return None
    # No complex validation needed for location IDs usually, they are strings.
    return f"coc {location_id.strip()}" 