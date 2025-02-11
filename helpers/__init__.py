import re

def make_url_compatible(input_string: str) -> str:
    # Define a regex pattern to match invalid URL characters
    invalid_characters = r"[^a-zA-Z0-9\-_]"

    # Replace spaces, commas, and dots with underscores
    input_string = input_string.replace(' ', '_').replace(',', '_').replace('.', '_').lower()

    # Strip out invalid URL characters
    cleaned_string = re.sub(invalid_characters, '', input_string)

    return cleaned_string
