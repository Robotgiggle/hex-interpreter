# hex-interpreter
Hexpattern interpreter for the Hex Casting mod.

A hexpattern consists of a string of letters representing turn directions, and a direction from which to start.
Here's some examples:
- `qeewdweddw northeast`
- `southeast aqaawwa`
- `northwest`
- `HexPattern(NORTH_WEST qaq)`
- `HexPattern(EAST eadaewea)`

To use this tool, just run the python script and input your hexpattern. You'll get back the pattern's name (if it has one), along with an image of the pattern which includes stroke order. You can also customize your experience in multiple ways via the built-in settings menu. Options include adding custom patterns to the name registry, changing the scale and style of the pattern images, and saving the pattern images to your device as PNG files.

Alternatively, you can provide a list of multiple hexpatterns rather than just one. To do this, enter your patterns within a set of square brackets, separated by a comma and a space. Make sure to include a start direction for each pattern, or it won't be read properly. The program will return a translated list of pattern names, given line-by-line. When using pattern-list mode, images of the patterns will not be produced.

In both modes, you can input a pattern's name rather than a hexpattern code. Capitalization doesn't matter, and you don't even need to enter the full name - as long as you've provided enough of the name to avoid ambiguity, it will work. Entering a pattern by name will function identically to entering the associated hexpattern, although the start direction will be automatically set to the default for that pattern.
