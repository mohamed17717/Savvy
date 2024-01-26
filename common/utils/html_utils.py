from meta_tags_parser import parse_snippets_from_source


class OneMetaTag:
    def __init__(self, **attributes: dict):
        self.attributes = attributes

    def __str__(self):
        attributes = ''
        for name, value in self.attributes.items():
            attributes += f'{name}="{value}" '
        return f'<meta {attributes} />'


def extract_image_from_meta(tags: list[dict]):
    tags = ''.join([str(OneMetaTag(**tag)) for tag in tags])
    parsed_meta = parse_snippets_from_source(tags)

    return parsed_meta.open_graph.image or parsed_meta.twitter.image
