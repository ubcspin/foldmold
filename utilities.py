class Utilities:
    def __init__(self):
        print("Initiated utilities.")

    def first_letters(self, text):
        """Iterator over the first letter of each word"""
        first_letters.pattern = re_compile("((?<!\w)\w)|\d")
        for match in first_letters.pattern.finditer(text):
            yield text[match.start()]
        


    def is_upsidedown_wrong(self, name):
        """Tell if the string would get a different meaning if written upside down"""
        chars = set(name)
        mistakable = set("69NZMWpbqd")
        rotatable = set("80oOxXIl").union(mistakable)
        print("is_upsidedown_wrong worked")
        return chars.issubset(rotatable) and not chars.isdisjoint(mistakable)

    def hello(self, hi):
        print("Hi w %s" % hi)