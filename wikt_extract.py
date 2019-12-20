import requests
import lxml.html
from lxml import etree
import re


class WiktExtract:
    """ Class that represent Wiktionart (french) data about words as an xml"""
    def __init__(self, path_xml = ''):
        if path_xml:
            self.tree = etree.parse(path_xml)
        else:
            self.tree = etree.Element("words")

    def __repr__(self, pretty_print=True):
        return etree.tostring(self.tree, encoding='unicode',pretty_print=pretty_print)

    def save(path_xml):
        str_xml = etree.tostring(tree, encoding='unicode',pretty_print=True)
        with open(path_xml, 'w') as f:
            f.write(str_xml)

    def add_word(self, word):
        xml_word = etree.SubElement(self.tree, 'word', name=word)
        url = "https://fr.wiktionary.org/wiki/{}".format(word)
        page = requests.get(url)
        fr_part = get_french_h2(page.text)

        if fr_part:
            for h3_part in re.split('(?=<h3>)' ,fr_part, flags=re.DOTALL):
                if """<h3><span class="mw-headline""" in h3_part:
                    cat_h3 = re.search('<h3><span class="mw-headline" id="(.+?)"', h3_part).group(1)
                    if cat_h3 in ['Prononciation', 'Anagrammes', 'Voir_aussi']:
                        continue
                    xml_category = etree.SubElement(xml_word, 'category', name=cat_h3)
                    tree = lxml.html.fromstring(h3_part)
                    for node in tree.xpath('//ol/li'):
                        definition = etree.tostring(node, encoding='unicode')
                        if 'id="' in definition:
                            cat_def = re.search('id="(.+?)"', definition).group(1)
                        else:
                            cat_def = "NA"
                        definition = re.sub('<ul>(.*)</ul>', '', definition, flags=re.DOTALL)
                        definition = re.sub('<.*?>', '', definition)
                        definition = re.sub('\s*\n', '', definition)

                        xml_definition = etree.SubElement(xml_category, 'definition', category=cat_def)
                        xml_definition.text = definition
                        for n, exemple in enumerate(node.xpath('ul/li')):
                            exemple = etree.tostring(exemple, encoding='unicode')
                            exemple = re.sub('<span(.*)</span>', '', exemple)
                            exemple = re.sub('<.*?>', '', exemple)
                            exemple = re.sub('\s*\n', '', exemple)
                            xml_exemple = etree.SubElement(xml_definition, 'exemple')
                            xml_exemple.text = exemple
        else:
            print("the word {} doesn't exist or doesn't have french data".format(word))


def get_french_h2(page_text):
    sanity_n_fr = 0
    fr_part = None
    for h2_part in re.split('(?=<h2>)' ,page_text, re.DOTALL):
        if 'id="Français"' in h2_part:
            fr_part = h2_part
            sanity_n_fr += 1
    if sanity_n_fr == 0:
        print("no french h2 part")
    if sanity_n_fr == 1:
        print("french part found")
    if sanity_n_fr > 1:
        print("found 2 french part, you need to go more deep in this wikt page")

    return(fr_part)



# Exemple of utilisation
if __name__ == "__main__":
    wkt = WiktExtract()
    wkt.add_word("manger")
    wkt.add_word("maison")
    print(wkt)
