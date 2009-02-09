# the configuration file for reflections
#
#
#

# REQUIRED: the first element of the Admins list should
#           specify the admin's name and admin's public email
#           for this blog. It is also used for the
#           author information in the atom feed as well as on the
#           imprint page.
ADMINS = (
    ('John Doe', 'john@doe.com'),
)

# OPTIONAL: This is used for the imprint page.
#           You should modify it to suit your needs and legal
#           environment.
AUTHOR_SNAIL = 'John Doe, Where the pepper grows'

# REQUIRED: lists all allowed hosts. If the host on which the
#           request is received is not in the list, the request
#           will be redirected to the FIRST item of the list!
#           !! WITHOUT THE LEADING "http://" !!
ALLOWED_HOSTS = ('localhost','your-app.appspot.com',)

# REQUIRED: The title of your blog
BLOG_TITLE    = 'My first blog'

# REQUIRED: The subtitle of your blog
BLOG_SUBTITLE = ''

# OPTIONAL: this specifies the feedburner id as in
#           http://feeds2.feedburner.com/<feedburner_id>
FEEDBURNER_ID  = 'id'

# OPTIONAL: Hyphenation of the entries using Hyphenator.js
HYPHENATE = False

# OPTIONAL: This specified your google Analytics code.
GOOG_ANALYTICS = ''

# OPTIONAL: This specified your google AdSense code
GOOG_ADSENSE   = {
    'client': 'pub-xxxxxxxxxxxxxxxx',
    'slot':   'xxxxxxxxxxx',
    'width':  0,
    'height': 0 }

# OPTIONAL: The forum id of your disqus account. Make sure
#           that the forum is associated with your blog url!
DISQUS_FORUM   = ''

# OPTIONAL: want to display the django pony?
BADGES         = False

# OPTIONAL: adds "Save / Share" and/or "Subscribe" buttons
ADD_TO_ANY     = { 'add': False, 'subscribe': False }

DP_HIGHLIGHTER = True
