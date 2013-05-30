#! /usr/bin/python

import textwrap
import sys
from itertools import izip

# only for testing
tab = 8
width = 20
text = open("lorem.txt", "r").read()
delimiter = "\n"
settings = ("top_begin \n '/*'\n tf \n '123456'\n top_end \n 'DD'\n "
            "top_ljust \n False\n "
            "w \n 60\n left_wall \n '* '\n "
            "right_wall \n ' *'\n bottom_begin \n ''\n bottom_fill \n '*'\n "
            "bottom_ljust \n False\n"
            "bottom_end \n '*/'")
# end only for testing

settings_abbrevs = {"tb": "top_begin", "tf": "top_fill", "te": "top_end",
                    "tl": "top_ljust", "lw": "left_wall", "rw": "right_wall",
                    "bb": "bottom_begin", "bf": "bottom_fill", 
                    "be": "bottom_end", "bl": "bottom_ljust", "w": "width"}

class commentator:
    """Class for generating boxed comments according to a specifications 
    string.

    Data members:
    top_begin, top_fill, top_end: describe the top of the boxed section;
      top_fill is repeated as many times as possible to fill the space
      between top_begin and top_end.  
    top_ljust: If the space cannot be filled evenly, by repetitions of 
      top_fill, top_ljust decides whether to cut off the beginning or the 
      end of the string it creates.
    left_wall, right_wall: vertical boundaries around comment region.
    bottom_begin, bottom_fill, bottom_end, bottom_fill: behave like
      their counterparts on top."""

    def __init__(self, settings = "", delim = "\n"):
        """Initialize a commentator according to settings string."""
        self.width = 2
        self.swap_in(settings, delim)

    def clear_all(self):
        """Clear all the values stored in all the data members.
        only really here for testing."""
        for field in vars(self):
            setattr(self, field, "")

    def swap_in(self, settings, delim):
        """Applies settings to existing commentator, expands settings as 
        needed.

        settings: a list of alternating variables and values.  Variables
          are data members of the commentator class.
        delim: character that separates settings from values as well as 
          setting/value pairs in the settings string.  delim must not appear
          in either the name of a setting or the value presented."""
        interleaved = settings.split(delim)
        for name, value in izip(interleaved[::2], interleaved[1::2]):
            name = name.strip(" ")
            self.set_value(name, eval(value))

    def set_value(self, name, value):
        """Set a single value; easier to read for humans."""
        if name in settings_abbrevs:
            name = settings_abbrevs[name]
        setattr(self, name, value)
        self.validate()

    def validate(self):
        def sr(s):
            """Safe reference; if the commentator contains a member by the
            given name, return the value in that member.  Else, return
            empty string."""
            try:
                return getattr(self, s)
            except:
                return ""
        top = len(sr("top_begin")) + len(sr("top_end"))
        mid = len(sr("left_wall")) + 1 + len(sr("right_wall"))
        # need to add at least one for the text
        low = len(sr("bottom_begin")) + len(sr("bottom_end"))
        min_width = max(top, mid, low)
        if self.width < min_width:
            self.width = min_width

    def get_horizontal(self, side):
        """Generate a horizontal boundary string according to previously
        recorded settings.  Generates top or bottom depending on 
        the variable side.

        side: must be top or bottom; used to retreive variables"""
        if side not in ["top", "bottom"]:
            # raise error
            pass
        d = {}
        names = ["begin", "fill", "end", "ljust"]
        for name in names:
            try:
                d[name] = getattr(self, side + "_" + name)
            except:
                d[name] = " "
        if not d["fill"]:
            if d["end"]:
                # replace fill with space to position end
                d["fill"] = " "
            else:
                # shortcut
                return d["begin"]
        fill_space = self.width - (len(d["begin"]) + len(d["end"]))
        # if filler length not a multiple of fill space, we need overspill
        must_fill = fill_space + (len(d["fill"]) - 1)
        fill_times = must_fill / len(d["fill"])
        filler = d["fill"] * fill_times
        if len(filler) > fill_space:
            diff = len(filler) - fill_space
            if d["ljust"]:
                filler = filler[:len(filler) - diff]
            else:
                filler = filler[diff:]            
        return "%s%s%s" % (d["begin"], filler, d["end"])

    def get_boxed(self, text):
        """Enclose text in a comment box according to the settings.

        text: any printable text."""
        lines = []
        lines.append(self.get_horizontal("top"))
        text = text.expandtabs(tab)
        walls_width = len(self.left_wall + self.right_wall)
        line_width = self.width - walls_width
        for line in textwrap.wrap(text, line_width):
            nspaces = self.width - (walls_width + len(line))
            lines.append("%s%s%s%s" % (self.left_wall, line, " " * nspaces,
                                       self.right_wall))
        lines.append(self.get_horizontal("bottom"))
        return "\n".join(lines)
        
if __name__ == "__main__":
    com = commentator(settings, delimiter)
    print com.get_boxed(text)
    
    