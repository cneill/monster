#!/usr/bin/env python
"""MONSTER

Usage:
    monster.py spider URL OUTFILE
    monster.py attack URL INFILE [--fuzz_types=<ft>]
    monster.py rampage URL OUTFILE
    monster.py --help


Options:
    spider                 SPIDER!
    attack                 ATTACK!
    rampage                ATTACK + SPIDER!
    --help                 Show this help message
    --fuzz_types=<ft>      Comma-separated list of types of fuzz tests to run

"""
import json

from docopt import docopt
from selenium import webdriver

from tests import XSSTest


SET_ATTR_SCRIPT = """var elem = document.querySelector('{selector}');
elem.{attr} = {val};
"""

REMOVE_ATTR_SCRIPT = """var elem = document.querySelector('{selector}');
elem.removeAttribute("{attr}");
"""


class MonsterClient(object):

    def __init__(self, url):
        self.driver = webdriver.Firefox()
        self.base_url = url

    def get(self, url):
        self.driver.get(url)

    def get_elem_attrs(self, elem):
        attr_names = [
            'action', 'class', 'href', 'id', 'maxlength', 'name', 'type',
            'disabled', 'max', 'min', 'pattern', 'required', 'steps'
        ]
        attrs = {}
        for name in attr_names:
            attrs[name] = elem.get_attribute(name)
        return attrs

    def get_elem_children(self, elem):
        return elem.find_elements_by_css_selector('*')

    def get_elem_by_selector(self, selector, parent=None):
        try:
            if parent:
                return parent.find_element_by_css_selector(selector)
            else:
                return self.driver.find_element_by_css_selector(selector)
        except:
            print "NO ELEMENT FOUND"

    def get_best_selector(self, elem):
        attrs = self.get_elem_attrs(elem)
        if attrs['id']:
            return '#{0}'.format(attrs['id'])
        elif attrs['name']:
            return '[name={0}]'.format(attrs['name'])
        elif attrs['class']:
            return '.{0}'.format(attrs['class'])
        elif elem.tag_name:
            return elem.tag_name
        else:
            return False

    def set_elem_attr(self, elem, attr, val):
        selector = self.get_best_selector(elem)
        self.set_elem_attr_by_selector(selector, attr, val)

    def set_elem_attr_by_selector(self, selector, attr, val):
        self.driver.execute_script(SET_ATTR_SCRIPT.format(
            selector=selector, attr=attr, val=val
        ))

    def remove_elem_attr(self, elem, attr):
        selector = self.get_best_selector(elem)
        self.driver.execute_script(REMOVE_ATTR_SCRIPT.format(
            selector=selector, attr=attr
        ))


class MonsterSpider(MonsterClient):

    def __init__(self, url, outfile):
        super(MonsterSpider, self).__init__(url)
        self.outfile = outfile

    def get_forms(self, forms=[], depth=0, max_depth=4):
        if depth < max_depth:
            forms.extend(self.driver.find_elements_by_tag_name('form'))
            forms.extend(self.get_hard_forms(forms, depth=depth+1))
            forms = list(set(forms))
        return forms

    def get_hard_forms(self, forms=None, depth=0, max_depth=4):
        forms = []
        curr_url = self.base_url

        if depth < max_depth:
            buttons = self.get_buttons()
            button_selectors = []
            for button in buttons:
                button_selectors.append(self.get_best_selector(button))

            links = self.get_links()
            link_selectors = []
            for link in links:
                link_selectors.append(self.get_best_selector(link))

            for selector in button_selectors:
                button_elem = self.get_elem_by_selector(selector)
                button_elem.click()
                if self.driver.current_url != curr_url:
                    self.driver.back()
                else:
                    forms.extend(self.get_forms(forms, depth=depth+1))

            for selector in link_selectors:
                link_elem = self.get_elem_by_selector(selector)
                link_elem.click()
                if self.driver.current_url != curr_url:
                    self.driver.back()
                else:
                    forms.extend(self.get_forms(forms, depth=depth+1))

            return list(set(forms))

    def get_webelem_obj(self, elem):
        children = []
        attrs = self.get_elem_attrs(elem)
        children_elems = self.get_elem_children(elem)

        for child in children_elems:
            children.append(self.get_webelem_obj(child))

        return {
            'tag_name': elem.tag_name,
            'name': attrs['name'] or "UNNAMED OBJECT",
            'selector': self.get_best_selector(elem),
            'attrs': attrs,
            'children': children
        }

    def get_buttons(self):
        return self.driver.find_elements_by_tag_name('button')

    def get_links(self):
        return self.driver.find_elements_by_tag_name('a')

    def get_form_inputs(self, form):
        return form.find_elements_by_tag_name('input')

    def spider(self):
        forms = []
        links = []

        self.get(self.base_url)

        form_elems = self.get_forms()
        link_elems = self.get_links()

        for elem in form_elems:
            forms.append(self.get_webelem_obj(elem))

        for elem in link_elems:
            links.append(self.get_webelem_obj(elem))

        self.driver.close()

        result = {
            'base_url': self.base_url,
            'forms': forms,
            'links': links,
        }

        with open(self.outfile, 'w') as f:
            f.write(json.dumps(result, sort_keys=True, indent=4))


class MonsterAttacker(MonsterClient):

    def __init__(self, spider_log):
        with open(spider_log, 'r') as f:
            self.spider_log = json.loads(f.read())
        self.base_url = self.spider_log['base_url']
        super(MonsterAttacker, self).__init__(self.base_url)
        self.attacks = {
            'xss': XSSTest(self, self.base_url)
        }

    def go(self):
        self.get(self.base_url)

        for form in self.spider_log['forms']:
            form_elem = self.get_elem_by_selector(form['selector'])
            if form_elem:
                form_children = self.get_elem_children(form_elem)
                for child in form_children:
                    self.remove_elem_validation(child)

                self.attack_form(form_elem)

    def remove_elem_validation(self, elem):
        attrs = self.get_elem_attrs(elem)
        bad_types = [
            'color', 'date', 'datetime', 'datetime-local', 'email', 'month',
            'number', 'range', 'search', 'tel', 'time', 'url', 'week'
        ]
        attrs_to_remove = [
            'disabled', 'required', 'max', 'min', 'pattern', 'maxlength'
        ]
        if elem.tag_name == 'input':
            for attr in attrs_to_remove:
                if attrs[attr]:
                    if attr == 'maxlength':
                        self.remove_elem_attr(elem, 'maxLength')
                    else:
                        self.remove_elem_attr(elem, attr)

            if attrs['type']:
                if attrs['type'] in bad_types:
                    self.set_elem_attr(elem, 'type', '"text"')

    def attack_form(self, elem):
        for attack in self.attacks:
            self.attacks[attack].attack(elem)


def main(args):
    if args['attack']:
        ma = MonsterAttacker(args['INFILE'])
        ma.go()
    elif args['spider']:
        ms = MonsterSpider(args['URL'], args['OUTFILE'])
        ms.spider()
    elif args['rampage']:
        ms = MonsterSpider(args['URL'], args['OUTFILE'])
        ms.spider()
        ma = MonsterAttacker(args['OUTFILE'])
        ma.go()

if __name__ == '__main__':
    args = docopt(__doc__, version='0.0')
    main(args)
