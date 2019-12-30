### main program
# directory to open - full path or HOME
FOLDER_TO_OPEN = "HOME"
# thumbnailers: 0 no - 1 yes
USE_THUMB = 1
# icon cell width - greater than ICON_SIZE
ITEM_WIDTH = 180
# icon cell height
ITEM_HEIGHT = 180
# icon size
ICON_SIZE = 160
# thumb size
THUMB_SIZE = 160
# other icons size: link and permissions
ICON_SIZE2 = 48
# space between items
ITEM_SPACE = 25
# font size to use
FONT_SIZE = 12
# show delete context menu entry that bypass the trashcan: 0 no - 1 yes
USE_DELETE = 1
# use the Paste and Merge action - at your own risk: 0 no - 1 yes
USE_PM = 1 
# load the trash module: 0 no - 1 yes
USE_TRASH = 0
# load the media module: 0 no - 1 yes
USE_MEDIA = 0
# Paste and Merge, how to backup the new files: 0 add progressive number
# in the form _(#) - 1 add date and time (without checking eventually
# existing file at destination with same date and time suffix) 
# in the form _yy.mm.dd_hh.mm.ss
USE_DATE = 1
# use background colour in the listview widgets: 0 no - 1 yes
USE_BACKGROUND_COLOUR = 1
# listview background color: red, green, blue
ORED = 235
OGREEN = 235
OBLUE = 235
# icon theme name - the qt5ct program overrides this
ICON_THEME = "breeze"

### needed by pythumb
# border color of the thumbnails
BORDER_COLOR_R = 0
BORDER_COLOR_G = 0
BORDER_COLOR_B = 0
# thumbnail images cache
XDG_CACHE_LARGE = "sh_thumbnails/large/"
