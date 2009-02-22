# -*- coding: utf-8 -*-
from logging import info
import re
from decorators import jinja_filter, layout_filter
from urllib2 import quote, unquote

################################################################################
# Custom Filters
################################################################################
## datetimeformat
@jinja_filter
def date(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

## markdown
@jinja_filter
@layout_filter
def markdown(text,*args):
    try:
        from lib import markdown2
    except ImportError:
        info("Error in `markdown` filter: The Python markdown2 library isn't installed.")
        return text
    return markdown2.markdown(text,extras=args)

## truncatewords (from django)
@jinja_filter
def truncatewords(text, num=40):
    words = text.split()
    if len(words) <= num:
        return text
    words = words[:num]
    if not words[-1].endswith('...'):
        words.append('...')
    return u' '.join(words)

## striptags (from django)
@jinja_filter
def striptags(text):
    return re.sub(r'<[^>]*?>', '', text)

@jinja_filter
@layout_filter
def urlquote(text):
    return quote(text)

@jinja_filter
@layout_filter
def urlunquote(text):
    return unquote(text)

################################################################################
# Typogirfy Filters // Quick hack
################################################################################
## amp
@layout_filter
@jinja_filter
def amp(text):
    tag_pattern = '</?\w+((\s+\w+(\s*=\s*(?:".*?"|\'.*?\'|[^\'">\s]+))?)+\s*|\s*)/?>'
    amp_finder = re.compile(r"(\s|&nbsp;)(&|&amp;|&\#38;)(\s|&nbsp;)")
    intra_tag_finder = re.compile(r'(?P<prefix>(%s)?)(?P<text>([^<]*))(?P<suffix>(%s)?)' % (tag_pattern, tag_pattern))
    def _amp_process(groups):
        prefix = groups.group('prefix') or ''
        text = amp_finder.sub(r"""\1<span class="amp">&amp;</span>\3""", groups.group('text'))
        suffix = groups.group('suffix') or ''
        return prefix + text + suffix
    output = intra_tag_finder.sub(_amp_process, text)
    return output

## caps
@layout_filter
@jinja_filter
def caps(text):
    try:
        from lib import smartypants
    except ImportError:
        info("Error in `caps` filter: The Python SmartyPants library isn't installed.")
        return text

    tokens = smartypants._tokenize(text)
    result = []
    in_skipped_tag = False

    cap_finder = re.compile(r"""(
                            (\b[A-Z\d]*        # Group 2: Any amount of caps and digits
                            [A-Z]\d*[A-Z]      # A cap string much at least include two caps (but they can have digits between them)
                            [A-Z\d']*\b)       # Any amount of caps and digits or dumb apostsrophes
                            | (\b[A-Z]+\.\s?   # OR: Group 3: Some caps, followed by a '.' and an optional space
                            (?:[A-Z]+\.\s?)+)  # Followed by the same thing at least once more
                            (?:\s|\b|$))
                            """, re.VERBOSE)

    def _cap_wrapper(matchobj):
        """This is necessary to keep dotted cap strings to pick up extra spaces"""
        if matchobj.group(2):
            return """<span class="caps">%s</span>""" % matchobj.group(2)
        else:
            if matchobj.group(3)[-1] == " ":
                caps = matchobj.group(3)[:-1]
                tail = ' '
            else:
                caps = matchobj.group(3)
                tail = ''
            return """<span class="caps">%s</span>%s""" % (caps, tail)

    tags_to_skip_regex = re.compile("<(/)?(?:pre|code|kbd|script|math)[^>]*>", re.IGNORECASE)


    for token in tokens:
        if token[0] == "tag":
            # Don't mess with tags.
            result.append(token[1])
            close_match = tags_to_skip_regex.match(token[1])
            if close_match and close_match.group(1) == None:
                in_skipped_tag = True
            else:
                in_skipped_tag = False
        else:
            if in_skipped_tag:
                result.append(token[1])
            else:
                result.append(cap_finder.sub(_cap_wrapper, token[1]))
    output = "".join(result)
    return output

## initial_quotes
@layout_filter
@jinja_filter
def initial_quotes(text):
    quote_finder = re.compile(r"""((<(p|h[1-6]|li|dt|dd)[^>]*>|^)              # start with an opening p, h1-6, li, dd, dt or the start of the string
                                  \s*                                          # optional white space!
                                  (<(a|em|span|strong|i|b)[^>]*>\s*)*)         # optional opening inline tags, with more optional white space for each.
                                  (("|&ldquo;|&\#8220;)|('|&lsquo;|&\#8216;))  # Find me a quote! (only need to find the left quotes and the primes)
                                                                               # double quotes are in group 7, singles in group 8
                                  """, re.VERBOSE)
    def _quote_wrapper(matchobj):
        if matchobj.group(7):
            classname = "dquo"
            quote = matchobj.group(7)
        else:
            classname = "quo"
            quote = matchobj.group(8)
        return """%s<span class="%s">%s</span>""" % (matchobj.group(1), classname, quote)
    output = quote_finder.sub(_quote_wrapper, text)
    return text

## smartypants
@layout_filter
@jinja_filter
def smartypants(text):
    try:
        from lib import smartypants
    except ImportError:
        info("Error in `smartypants` filter: The Python smartypants library isn't installed.")
        return text
    else:
        output = smartypants.smartyPants(text)
        return output

## titlecase
@layout_filter
@jinja_filter
def titlecase(text):
    try:
        import titlecase
    except ImportError:
        info("Error in {% titlecase %} filter: The titlecase.py library isn't installed.")
        return text
    else:
        return titlecase.titlecase(text)

## widont
@layout_filter
@jinja_filter
def widont(text):
    widont_finder = re.compile(r"""((?:</?(?:a|em|span|strong|i|b)[^>]*>)|[^<>\s]) # must be proceeded by an approved inline opening or closing tag or a nontag/nonspace
                                   \s+                                             # the space to replace
                                   ([^<>\s]+                                       # must be flollowed by non-tag non-space characters
                                   \s*                                             # optional white space!
                                   (</(a|em|span|strong|i|b)>\s*)*                 # optional closing inline tags with optional white space after each
                                   ((</(p|h[1-6]|li|dt|dd)>)|$))                   # end with a closing p, h1-6, li or the end of the string
                                   """, re.VERBOSE)
    output = widont_finder.sub(r'\1&nbsp;\2', text)
    return output

## typogrify
@layout_filter
@jinja_filter
def typogrify(text):
    text = amp(text)
    text = widont(text)
    text = smartypants(text)
    text = caps(text)
    text = initial_quotes(text)
    return text
