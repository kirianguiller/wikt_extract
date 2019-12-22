import requests
import lxml.html
from lxml import etree
from urllib.parse import unquote
import re


class WiktExtract:
    """ Class that represent Wiktionart (french) data about words as an xml"""
    def __init__(self, path_xml = ''):
        if path_xml:
            self.tree = etree.parse(path_xml)
            self.fetched_words = self.get_words()
        else:
            self.tree = etree.Element("words")
            self.fetched_words = []

    def __repr__(self, pretty_print=True):
        return etree.tostring(self.tree, encoding='unicode',pretty_print=pretty_print)

    def save(self, path_xml):
        str_xml = etree.tostring(self.tree, encoding='unicode',pretty_print=True)
        with open(path_xml, 'w') as f:
            f.write(str_xml)

    def fetch_word(self, word, return_follow_link=False):
        if word in self.fetched_words:
            print("'{}' already in tree".format(word))
            return []

        url = "https://fr.wiktionary.org/wiki/{}".format(word)
        page = requests.get(url)
        # word_str = re.search('<h1 id="firstHeading" class="firstHeading" lang="fr">(.+?)</h1>', page.text)[1]
        fr_part = get_french_h2(page.text)

        if fr_part:
            xml_word = etree.SubElement(self.tree, 'word', name=word)
            self.fetched_words.append(word)
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
            print("'{}' fetched".format(word))
            if return_follow_link:
                list_follow_link = []
                list_fetched_words = self.fetched_words
                for href in re.findall('<a href="/wiki/(.+?)"', fr_part):
                    if (':' in href) | ('#' in href) | (href in list_fetched_words) | (href.startswith('-')):
                        pass
                    else:
                        list_follow_link.append(unquote(href))
                return list_follow_link
        else:
            print("the word {} doesn't exist or doesn't have french data".format(word))
        return []


    def get_words(self):
        return self.tree.xpath('//word/@name')


    def fetch_loop(self, starting_words=['manger'], n_to_fetch=100):
        current_size = len(self.fetched_words)
        words_to_fetch = starting_words
        while (len(self.fetched_words) - current_size) < n_to_fetch:
            word = words_to_fetch.pop(0)
            if word in self.fetched_words:
                pass
            else:
                follow_link = self.fetch_word(word, return_follow_link=True)
                words_to_fetch += follow_link






def get_french_h2(page_text):
    sanity_n_fr = 0
    fr_part = None
    for h2_part in re.split('(?=<h2>)' ,page_text, re.DOTALL):
        if 'id="Français"' in h2_part:
            fr_part = h2_part
            sanity_n_fr += 1
    # if sanity_n_fr == 0:
    #     print("no french h2 part")
    # if sanity_n_fr == 1:
    #     print("french part found")
    # if sanity_n_fr > 1:
    #     print("found 2 french part, you need to go more deep in this wikt page")

    return(fr_part)



# Exemple of utilisation
if __name__ == "__main__":
    path_data = '../data/'
    wkt = WiktExtract()

    words_to_fetch = []
    with open(path_data + 'french_most_common_words.txt', 'r') as f:
        for line in f:
             words_to_fetch.append(line.split('\t')[0])

    for n, word in enumerate(words_to_fetch[:5000]):
        print(n, word)
        wkt.fetch_word(word, return_follow_link=False)

    # words_to_fetch = ['manger']
    # words_fetched = []
    # while len(words_fetched)<101:
    #     word = words_to_fetch.pop()
    #     if word in words_to_fetch:
    #         pass
    #     else:
    #         follow_link = wkt.fetch_word(word, return_follow_link=True)
    #         if len(follow_link) == 0:
    #             pass
    #         else:
    #             words_to_fetch += follow_link
    #             words_fetched.append(word)

    wkt.save(path_data + "{}MostCommonWords.xml".format(len(wkt.get_words())))

    # wkt.add_word("manger")
    # wkt.add_word("maison")
    # wkt.add_word("manger")



    # for k in range(3):

    # print(wkt.add_word("établissement", return_follow_link=True))


    # the following line is for saving the xml
    # wkt.save('words.xml')
    # print(wkt)
