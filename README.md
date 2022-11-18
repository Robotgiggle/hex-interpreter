# hex-interpreter
### The Basics

A hexpattern consists of a string of letters representing turn directions, and a direction from which to start.
Here's some examples:
- `qeewdweddw northeast`
- `southeast aqaawwa`
- `northwest`
- `HexPattern(NORTH_WEST qaq)`
- `HexPattern(EAST eadaewea)`

This tool interprets hexpatterns, translating them into a more readable format. To use the tool, just download the files from the latest release, run the main script (hex_draw.py), and enter your hexpattern. You'll get back the pattern's name, if it has one, along with an image of the pattern. By default, the displayed image will show the stroke order for the pattern, so you'll know exactly what order to draw it in. 

### List Mode

Alternatively, you can provide a list of multiple hexpatterns rather than just one. To do this, enter your patterns within a set of square brackets, separated by a comma and a space. The program will return a line-by-line list of the patterns necessary to create whatever list you entered, along with an image of all those patterns drawn out.

By default, the program will assume that a provided spell is intended to be be used as a list iota. For this reason, it will automatically add an introspection/retrospection pair around the entire thing. To prevent this - for example, if your spell is meant to be cast manually - just add the prefix `by_hand` to your input string, before the opening bracket.

List mode can also handle non-pattern iotas – things like vectors, entity references, or even nested pattern lists. In the line-by-line translation of your list, non-pattern iotas will be displayed as `NON-PATTERN: <iota text>`. In the image display, non-patterns will be represented by various symbols based on the nature of that particular iota. Nested lists will be displayed as `[]`, vectors will be displayed as `⟨⟩`, numbers will be displayed as `#`, widgets (stuff like Null and Garbage) will be displayed as `?`, and anything else will be assumed to be the name of a player or entity and displayed as `@`.

### File Mode

Sometimes, lists of patterns are too long or unwieldy to be entered as a string. To deal with this, you can provide your input in the form of a text file. To interpret a list from a text file, enter the name of the file into the main prompt. The necessary formatting for reading from a text file is a bit looser than the normal requirements for list mode - you can use newlines and indents without causing any problems. The only requirement is that each line of the file contains only one iota to be interpreted.

### Pattern Names

In both modes, you can input a pattern's name (official or internal) rather than a hexpattern code. Capitalization doesn't matter, and you don't even need to enter the full name - as long as you've provided enough of the name to avoid ambiguity, it will work. Entering a pattern by name will function identically to entering the associated hexpattern, although the start direction will be automatically set to the default for that pattern.

In the settings menu, you can create an alias for any existing pattern. Once created, entering the alias will have the same effect as having entered the associated pattern. This can be very helpful if the pattern names you're inputting are written in shorthand.

### Customization

The built-in settings menu, accessed by entering "s" in the main prompt, allows you to customize your experience in numerous ways. Options include adding custom patterns to the registry, changing the scale and style of the output images, saving the output images to your device as PNG files, and much more. Normally, the changes you make in the settings menu are only for the current session – but the "save current settings as default" option allows you to save your personal preferences directly into the settings.json file.

There is also an admin menu, which can be accessed by entering the word "admin" in the main prompt. The admin menu provides more direct access to both the program settings and the pattern registry, and also allows you to easily view the entire list of registered patterns. This can be more useful than the normal settings menu if you're planning on making your own modifications to the program, but it can cause serious errors if misused. If you use this feature, make sure you know what you're doing!
