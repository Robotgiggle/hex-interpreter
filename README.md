# hex-interpreter
Hexpattern interpreter for the Hex Casting mod.

A hexpattern consists of a string of letters representing turn directions, and a direction from which to start.
Here's some examples:
- `qeewdweddw northeast`
- `southeast aqaawwa`
- `northwest`
- `HexPattern(NORTH_WEST qaq)`
- `HexPattern(EAST eadaewea)`

To use this tool, just run the python script and input your hexpattern. You'll get back the pattern's name (if it has one), along with an image of the pattern which includes stroke order. You can customize your experience in multiple ways via the built-in settings menu. Options include adding custom patterns to the name registry, changing the scale and style of the pattern images, and saving the pattern images to your device as PNG files.

You can also provide a list of multiple hexpatterns, rather than just a single one. This has a much more specific syntax, as it's designed to parse pattern lists taken directly from the Hex Casting mod. If you want to manually input a list of hexpatterns, make sure it uses the following format:  
`[HexPattern(START_DIRECTION angles), HexPattern(START_DIRECTION angles), HexPattern(START_DIRECTION angles), etc]`  
The program will return a translated list of pattern names, given line-by-line. When using pattern-list mode, images of the patterns will not be produced.
