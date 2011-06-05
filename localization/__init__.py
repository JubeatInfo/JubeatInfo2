
from jubeatinfo.localization import dev

from jubeatinfo.localization import en
from jubeatinfo.localization import ko
from jubeatinfo.localization import zh_tw

locales = {
    'dev': dev,
    'en': en,
    'ko': ko,
    'zh-tw': zh_tw,
}

def message(locale, key):
    messages = locales[locale].messages
    try:
        return messages[key].decode('utf-8')
    except:
        pass
    try:
        return en.messages[key].decode('utf-8')
    except:
        pass
    return key

def contents(locale, value):
    contents = locales[locale].contents
    try:
        return contents[value].decode('utf-8')
    except:
        return value
