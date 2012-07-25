

def comparable_name(name):
    name = name.lower()
    name = name.replace('.', '')
    name = name.replace('-', '')
    name = name.replace('_', '')

    return name
