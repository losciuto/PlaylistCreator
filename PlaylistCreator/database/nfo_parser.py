import xml.etree.ElementTree as ET

def parse_nfo_file(nfo_path):
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()

        info = {
            'title': None,
            'genres': [],
            'year': None,
            'directors': [],
            'plot': None,
            'actors': [],
            'rating': None,
            'duration': None,
            'poster': None
        }

        # Estrazione titolo
        title_elem = root.find('title')
        if title_elem is not None and title_elem.text:
            info['title'] = title_elem.text

        # Estrazione generi
        if root.find('genre') is not None:
            info['genres'] = [genre.text for genre in root.findall('genre')]

        if root.find('year') is not None:
            info['year'] = root.find('year').text

        if root.find('director') is not None:
            info['directors'] = [director.text for director in root.findall('director')]

        if root.find('plot') is not None:
            info['plot'] = root.find('plot').text

        if root.find('actor') is not None:
            for actor in root.findall('actor'):
                name = actor.find('name')
                if name is not None:
                    info['actors'].append(name.text)

        # Estrazione rating IMDb
        for rating_elem in root.findall('rating'):
            rating_name = rating_elem.get('name', '').lower()
            if rating_name == 'imdb' and rating_elem.text:
                info['rating'] = rating_elem.text
                break

        if root.find('runtime') is not None:
            info['duration'] = root.find('runtime').text

        if root.find('thumb') is not None:
            info['poster'] = root.find('thumb').text

        return info

    except (ET.ParseError, FileNotFoundError):
        return None