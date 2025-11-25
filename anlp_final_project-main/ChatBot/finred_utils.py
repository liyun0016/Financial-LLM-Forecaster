from difflib import SequenceMatcher

def normalize_entity(entity: str) -> str:
    return entity.lower().strip().replace("’", "'").replace("`", "'")

def normalize_triple(triple):
    rel, head, tail = triple
    return (rel.lower().strip(), normalize_entity(head), normalize_entity(tail))

def extract_tuples(text: str):
    import re
    tuples = []
    for item in text.strip().strip('.').split(';'):
        match = re.match(r'^([a-z_]+):\s*(.*?),\s*(.*?)$', item.strip())
        if match:
            rel, h, t = match.groups()
            tuples.append((rel.strip(), h.strip(), t.strip()))
    return tuples
