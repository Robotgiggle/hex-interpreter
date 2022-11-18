import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter
from matplotlib import colormaps
from matplotlib import colors
from os import chdir
from os import path
import hex_anim
import pickle
import json
import math

def convert_to_points(angle_sig,start_dir,settings):
    unit = math.pi/3

    # define the first two points and the starting angle based on start_dir
    match start_dir:
        case "east":
            x=1
            y=0
            angle = 0
        case "west":
            x=-1
            y=0
            angle = math.pi
        case "northeast":
            x=0.5
            y=0.866
            angle = unit
        case "northwest":
            x=-0.5
            y=0.866
            angle = 2*unit
        case "southeast":
            x=0.5
            y=-0.866
            angle = -unit
        case "southwest":
            x=-0.5
            y=-0.866
            angle = -2*unit
        case _:
            print("Invalid start direction '"+start_dir+"' - defaulted to east")
            x=1
            y=0
            angle = 0

    # initialize the x and y lists with the first two points
    x_vals = [0,x]
    y_vals = [0,y]

    # calculate the start angle in degrees, for later use
    start_angle = round((angle*180/math.pi)-90,0)

    # parse the angle signature, one character at a time
    for char in angle_sig:
        match char:
            case 'a':
                angle += 2*unit
            case 'q':
                angle += unit
            case 'w':
                pass
            case 'e':
                angle -= unit
            case 'd':
                angle -= 2*unit
            case _:
                return (x_vals,None,0,start_angle)
        # convert from polar to cartesian coordinates
        # then add the new point to the x and y lists
        x += math.cos(angle)
        y += math.sin(angle)
        x_vals.append(x)
        y_vals.append(y)

    # check if pattern overlaps itself
    checked = []
    for i in range(len(x_vals)-1):
        for j in range(len(checked)-1):
            if (abs(x_vals[i]-checked[j][0]) < 0.1 and     # overlap in same direction
                abs(y_vals[i]-checked[j][1]) < 0.1 and
                abs(x_vals[i+1]-checked[j+1][0]) < 0.1 and
                abs(y_vals[i+1]-checked[j+1][1]) < 0.1 or
                abs(x_vals[i]-checked[j+1][0]) < 0.1 and   # overlap in opposite direction
                abs(y_vals[i]-checked[j+1][1]) < 0.1 and
                abs(x_vals[i+1]-checked[j][0]) < 0.1 and
                abs(y_vals[i+1]-checked[j][1]) < 0.1):
                return (None,y_vals,0,start_angle)
        checked.append((x_vals[i],y_vals[i]))

    # find the width or height, whichever is largest, and apply some transformations to it
    # this value is used when drawing to scale the lines and points based on graph size
    max_width = max([max(x_vals)-min(x_vals),max(y_vals)-min(y_vals)])
    if max_width<=1.0: max_width = 1.25
    scale = settings["scale_factor"]/math.log(max_width,1.5)+1.1

    # scale tweaks for list mode
    if settings["list_mode"]:
        scale *= 0.8
        scale = min((scale,2.5))
   
    return (x_vals,y_vals,scale,start_angle)

def parse_number(angle_sig):
    output = 0
    for char in angle_sig[4:]:
        match char:
            case 'a':
                output *= 2
            case 'q':
                output += 5
            case 'w':
                output += 1
            case 'e':
                output += 10
            case 'd':
                output /= 2
            case _:
                print("Invalid char - skipped")
    if angle_sig[:4]=="dedd":
        output *= -1
    return "Numerical Reflection ("+str(output)+")"

def parse_bookkeeper(angle_sig):
    if not angle_sig: return "Bookkeeper's Gambit (-)"
    if angle_sig[0]=="a":
        output = "v"
        skip = True
    elif angle_sig.startswith(("e","w")):
        output = "-"
        skip = False
    else:
        return None
    for char in angle_sig:
        if(skip):
            skip = False
            continue
        if(char=="w" and output[-1]=="-"):
            output += "-"
        elif(char=="e"):
            if(output[-1]=="v"):
                output += "-"
            elif(output[-1]=="-"):
                output += "v"
                skip = True
            else: return None
        elif(char=="d"):
            output += "v"
            skip = True
        else: return None
    return "Bookkeeper's Gambit ("+output+")"

def dict_lookup(angle_sig,pattern_dict):
    if not pattern_dict: return None
    try:
        output = pattern_dict[angle_sig]
        return output     
    except KeyError:
        return None

def gs_lookup(x_vals,y_vals,great_spells):
    if not great_spells: return None
    # convert the x and y lists into a single list of points
    points = []
    for i in range(len(x_vals)):
        points.append([x_vals[i],y_vals[i]])

    # remove duplicate points
    for point in points:
            new_list = [point]
            for other_point in points:
                if not(abs(point[0]-other_point[0])<0.1 and abs(point[1]-other_point[1])<0.1):
                    new_list.append(other_point)
            points = new_list

    # shift pointlist so the location (0,0) is the bottom left corner
    lowest = [min(x_vals),min(y_vals)]
    for i in range(len(points)):
        points[i][0] -= lowest[0]
        points[i][1] -= lowest[1]

    # compare pointlist to all possible great spell pointlists
    for entry in great_spells:
        same = True
        for check in entry[0]:
            matched = False
            for point in points:
                if(abs(point[0]-check[0])<0.1 and abs(point[1]-check[1])<0.1):
                    matched = True
            if not matched:
                same = False
        # if a pointlist matches, return its associated great spell
        if same and len(entry[0])==len(points):
            return entry[1]

    # if no matches were found, it's not a known great spell
    return None

def plot_monochrome(plot_data,settings):
    x_vals,y_vals,scale,start_angle = plot_data
    for i in range(len(x_vals)-1):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=settings["monochrome_color"],lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale)

def plot_gradient(plot_data,settings):
    x_vals,y_vals,scale,start_angle = plot_data
    line_count = len(x_vals)-1
    colors = colormaps[settings["gradient_colormap"]]

    # plot start-direction triangle
    plt.plot(x_vals[1]/2.15,y_vals[1]/2.15,color=colormaps[settings["gradient_colormap"]](0.999),marker=(3,0,start_angle),ms=2.9*settings["arrow_scale"]*scale)

    # draw the pttern
    for i in range(line_count):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors(1-i/line_count),lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)

    # mark the last point
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=3*scale)
    plt.plot(x_vals[-1],y_vals[-1],color=colors(0),marker='o',ms=1.5*scale)

    # mark the first point
    plt.plot(x_vals[0],y_vals[0],'ko',ms=3*scale)
    plt.plot(x_vals[0],y_vals[0],color=colors(0.999),marker='o',ms=1.5*scale) 

def plot_intersect(plot_data,settings):
    x_vals,y_vals,scale,start_angle = plot_data
    line_count = len(x_vals)-1
    used_points = []
    colors = settings["intersect_colors"]
    color_index = 0
    
    # plot start-direction triangle
    plt.plot(x_vals[1]/2.15,y_vals[1]/2.15,color=settings["intersect_colors"][0],marker=(3,0,start_angle),ms=2.9*settings["arrow_scale"]*scale)
    
    for i in range(line_count+1):
        point = [x_vals[i],y_vals[i],color_index]
        repeats = False

        # check if we've already been to this point, with this line color
        # doing this with if(j==point) doesn't work because of floating-point jank
        for j in used_points:
            same_color = color_index==j[2] or (3-color_index%3==j[2] and color_index>3)
            if abs(point[0]-j[0])<0.1 and abs(point[1]-j[1])<0.1 and same_color:
                repeats = True
                used_points[used_points.index(j)][2] += 1

        # if the condition is true, cycle the line color to the next option
        # then draw a half-line backwards to mark the beginning of the new segment
        if repeats:
            color_index += 1
            color_index %= len(colors)
            back_half = ((x_vals[i-1]+point[0])/2,(y_vals[i-1]+point[1])/2)
            plt.plot((point[0],back_half[0]),(point[1],back_half[1]),color=colors[color_index],lw=scale)

            # draw a triangle to mark the direction of the new color
            if(abs(y_vals[i]-y_vals[i-1])<0.1):
                if(x_vals[i]>x_vals[i-1]): angle = 270
                else: angle = 90
            elif(y_vals[i]>y_vals[i-1]):
                if(x_vals[i]>x_vals[i-1]): angle = 330
                else: angle = 30
            else:
                if(x_vals[i]>x_vals[i-1]): angle = 210
                else: angle = 150
            plt.plot(back_half[0],back_half[1],marker=(3,0,angle),color=colors[color_index],ms=2*settings["arrow_scale"]*scale)
        else:
            used_points.append(point)

        # only draw point+line if we're not at the end
        if(i!=line_count):
            plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors[color_index],lw=scale)
            plt.plot(point[0],point[1],'ko',ms=2*scale)       

    # mark the last point
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=3*scale)
    plt.plot(x_vals[-1],y_vals[-1],color=colors[color_index],marker='o',ms=1.5*scale)

    # mark the first point
    plt.plot(x_vals[0],y_vals[0],'ko',ms=3*scale)
    plt.plot(x_vals[0],y_vals[0],color=colors[0],marker='o',ms=1.5*scale)

def format_pattern(raw_input,registry,settings):
    raw_input = raw_input.lower()
    
    # who tf decided to make 'const/vec/0' a valid pattern name
    if raw_input == "0":
        return (raw_input,None,None)

    # remove HexPattern() wrapper, if present
    if raw_input.startswith("hexpattern"):
        raw_input = raw_input[11:-1]

    # if input is a bookkeeper's gambit variant, parse it
    if raw_input.startswith("bookkeeper") or all(c in "v-" for c in raw_input):
        force_mono = False
        by_name = True
        v_ind = raw_input.find("v")
        dash_ind = raw_input.find("-")
        if -1 != v_ind < dash_ind != -1: start = v_ind
        elif -1 != dash_ind < v_ind != -1: start = dash_ind
        elif v_ind == -1: start = dash_ind
        else: start = v_ind
        if raw_input[start]=="v":
            start_dir = "southeast"
            angle_sig = "a"
        else:
            start_dir = "east"
            angle_sig = ""
        for i in range(start+1,len(raw_input)):
            char = raw_input[i]
            if char == "v":
                if raw_input[i-1] == "v":
                    angle_sig += "da"
                else:
                    angle_sig += "ea"
            elif char == "-":
                if raw_input[i-1] == "v":
                    angle_sig += "e"
                else:
                    angle_sig += "w"

    # elif input is the name of a pattern, use that
    elif all(registry):
        matches = []
        for name in registry[2]:
            if raw_input == name.lower():
                matches = [name]
                break
            elif raw_input in name.lower():
                matches.append(name)
        if len(matches) == 0:
            by_name = False
        elif len(matches) == 1:
            by_name = True
            name = matches[0]
            if registry[2][name][0]:
                ref_name = registry[2][name][1]
                angle_sig,start_dir,force_mono = registry[2][ref_name][1:]
            else:
                angle_sig,start_dir,force_mono = registry[2][name][1:]
        else:
            if not settings["list_mode"]:
                print("Found multiple matches for '"+raw_input+"':")
                for match in matches: print("- "+match)
                print("Try entering something more specific.\n-----")
            return (raw_input,None,None)
    else:
        by_name = False

    # else attempt to parse a hexpattern
    if not by_name:
        force_mono = False
        raw_input = raw_input.replace("_","")
        
        # make sure there even is a start direction
        if raw_input.find(" ") == -1:
            if not settings["list_mode"]: print("Error - no start direction.\n-----")
            return (raw_input,None,None)
        
        # parse in-game hexpattern syntax
        elif raw_input.startswith(("east","west","northeast","northwest","southeast","southwest")):
            space = raw_input.index(" ")
            start_dir = raw_input[:space]
            angle_sig = raw_input[space+1:]

        # parse discord bot syntax
        else:
            space = raw_input.index(" ")
            angle_sig = raw_input[:space]
            start_dir = raw_input[space+1:]
            if start_dir not in ("east","west","northeast","northwest","southeast","southwest"):
                if not settings["list_mode"]: print("Error - invalid start direction.\n-----")
                return (raw_input,None,None)

    # return properly formatted pattern info
    return angle_sig,start_dir,force_mono

def main(input_val,registry,settings,ax=None):
    if isinstance(input_val,str):
        angle_sig,start_dir,force_mono = format_pattern(input_val,registry,settings)
    else:
        angle_sig,start_dir,force_mono = input_val

    if not start_dir:
        return None
    
    # convert input to x and y values
    plot_data = convert_to_points(angle_sig,start_dir,settings)
    x_vals,y_vals,scale,start_angle = plot_data
    if not x_vals:
        if settings["list_mode"]: output = "Invalid Pattern (self-overlapping)"
        else: print("Error - that pattern overlaps itself.\n-----")
    elif not y_vals:
        if settings["list_mode"]: output = "Invalid Pattern (unreadable)"
        else: print("Error - invalid character in angle signature.\n-----")

    # pattern identification
    if settings["identify_pattern"]=="on" or settings["list_mode"]:
        result = None

        # attempt to identify pattern with various methods
        try:
            if result := dict_lookup(angle_sig,registry[0]): pass
            elif result := gs_lookup(x_vals,y_vals,registry[1]): pass
            elif result := parse_bookkeeper(angle_sig): pass
            elif angle_sig.startswith(("aqaa","dedd")): result = parse_number(angle_sig)
        except TypeError:
            if settings["list_mode"]: result = "Unknown Pattern (no pattern registry)"
            else: result = "Unknown - no pattern registry"

        # dispel rain override
        if result == "Summon Rain" and x_vals[0]-x_vals[-1] < 0.1:
            result = "Dispel Rain"

        # if no matches found, pattern is unrecognized
        if not result:
            if settings["list_mode"]: result = "Unknown Pattern ("+angle_sig+")"
            else: result = "Unknown - unrecognized pattern"

        # deal with result based on mode
        if(settings["list_mode"]): output = result
        else: print("This pattern is: "+result)

    # pre-plot scaling
    if settings["list_mode"]:
        if scale < 2.5: settings["arrow_scale"] -= 0.3
        elif scale < 1.9: settings["arrow_scale"] -= 0.5
    else:
        ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
        ax.set_aspect("equal")
        ax.axis("off")
    
    # run the selected draw function
    if force_mono:
        plot_monochrome(plot_data,settings)
    else:
        match settings["draw_mode"]:
            case "intersect":
                plot_intersect(plot_data,settings)
            case "monochrome":
                plot_monochrome(plot_data,settings)
            case "gradient":
                plot_gradient(plot_data,settings)
            case "animated":
                ani = hex_anim.plot_animated(plot_data,settings)            
            case "disabled":
                pass
            case _:
                print("Config error, this shouldn't happen")

    # post-plot scaling
    if settings["list_mode"]:
        if scale < 1.9: settings["arrow_scale"] += 0.5
        elif scale < 2.5: settings["arrow_scale"] += 0.3
        pad_factor = 5
    else:
        pad_factor = 20

    # pad edges to avoid dot cutoff
    x_min,x_max = ax.get_xlim()
    y_min,y_max = ax.get_ylim()
    pad = min((x_max-x_min)/pad_factor,(y_max-y_min)/pad_factor)
    ax.set_xlim(x_min-pad,x_max+pad)
    ax.set_ylim(y_min-pad,y_max+pad)

    # save the final image, if enabled
    if(settings["output_path"]!="none"):
        if settings["output_path"]=="here" : filename = start_dir+"_"+angle_sig
        else: filename = settings["output_path"]+"/"+start_dir+"_"+angle_sig
        num = 1
        while path.isfile(filename+".png") or path.isfile(filename+".gif"):
            if(filename[-1]==str(num-1)): filename = filename[:-1]+str(num)
            else: filename += ("_"+str(num))
            num += 1
        if settings["draw_mode"] == "animated": ani.save(filename+".gif",writer=PillowWriter(fps=40))
        else: plt.savefig(filename+".png")
    
    # display the final image, if enabled
    if settings["list_mode"]: return output
    elif settings["draw_mode"] == "disabled": plt.close()
    else: plt.show()
    print("done")
    
    print("-----")

def string_to_spell(raw_input,wrapper=True):
    # split string into list of iotas
    nested = 0
    raw_input = raw_input.replace(";",",").replace(":"," -")[1:-1]
    for i in range(len(raw_input)):
        if raw_input[i] in ("[","("): nested += 1
        elif raw_input[i] in ("]",")"): nested -= 1
        elif nested > 0 and raw_input[i] == ",":
            raw_input = raw_input[:i]+";"+raw_input[i+1:]
    raw_list = raw_input.split(", ")

    # add intro/retro wrapper
    if wrapper:
        raw_list.insert(0,"qqq west")
        raw_list.append("eee east")

    # translate iotas to formatted patterns if possible
    nested = 0
    spell = []
    for iota in raw_list:
        formatted = format_pattern(iota,registry,settings)
        spell.append(formatted)
        if formatted[0] == "qqq": nested += 1
        elif formatted[0] == "eee": nested -= 1
        elif formatted[0] == "qqqaw":
            for i in range(2**nested-1):
                spell.append(formatted)

    return spell

def parse_spell_list(spell,registry,settings,meta=0):
    if settings["draw_mode"] == "animated":
        print("List mode does not currently support animated patterns.\n-----")
        return

    output_list = []

    # create figure to plot patterns into
    rows = math.ceil(len(spell)/settings["grid_dims"][0])
    cols = len(spell) if rows==1 else settings["grid_dims"][0]
    fig = plt.figure(figsize=(cols+1,rows+1))
    index = 1

    # interpret each iota
    indents = meta
    for pattern_data in spell:
        iota = pattern_data[0]
        
        # create subplot for this pattern
        ax = fig.add_subplot(rows,cols,index,aspect="equal")
        ax.axis("off")
        index += 1
        
        # add result to list of outputs
        if name := main(pattern_data,registry,settings,ax): output_list.append(name)
        elif iota[0]=="[" or meta: output_list.append(iota)
        else: output_list.append("NON-PATTERN: "+iota)

        # indentation handling
        if name == "Introspection":
            output_list[-1] = ("{",indents)
            indents += 1
        elif name == "Retrospection":
            indents -= 1
            output_list[-1] = ("}",indents)
        else:
            output_list[-1] = (output_list[-1],indents)

        # draw placeholder symbol for non-pattern or meta-eval
        if iota[0] == "[":
            ax.plot(0,0,marker="$[]$",ms=50,c=settings["monochrome_color"])
        elif iota[0] == "(":
            ax.plot(0,0,marker="$\u27E8\u27E9$",ms=50,c=settings["monochrome_color"])
        elif iota.replace(".","",1).isnumeric():
            ax.plot(0,0,marker="$\#$",ms=50,c=settings["monochrome_color"])
        elif iota in ("Null","arimfexendrapuse"):
            ax.plot(0,0,marker="$?$",ms=50,c=settings["monochrome_color"])
        elif not (meta or name):
            ax.plot(0,0,marker="$@$",ms=50,c=settings["monochrome_color"])
    
    # print result line by line
    if not meta: print("This spell consists of:")
    for name in output_list:
        if name[0][0]=="[":
            print("  "*name[1]+"[")
            parse_spell_list(string_to_spell(name[0],False),registry,settings,name[1]+1)
            print("  "*name[1]+"]")
        elif name[0][-1]==")":
            print("  "*name[1]+name[0].replace(";",","))
        else:
            print("  "*name[1]+name[0])

    # print final figure
    if meta or settings["draw_mode"] == "disabled":
        plt.close()
    elif len(output_list) > settings["grid_dims"][2]:
        plt.close()
        print("Warning - too many patterns for visual display")
    else:
        fig.tight_layout(pad=0)
        plt.show()

    if not meta: print("-----")

def parse_from_file(filename,registry,settings):
    if filename.startswith("by_hand"):
        wrapper = False
        filename = filename[8:]
    else:
        wrapper = True

    # get list of lines from file
    try:
        with open(filename,mode="r") as file: lines = file.readlines()
    except FileNotFoundError:
        print("Error - the file '"+filename+"' could not be found.")
        print("-----")
        return None

    # remove outer intro/retro if present
    if lines[0].strip() == "{" and lines[-1].strip() == "}":
        lines = lines[1:-1]

    # convert list of lines into readable string
    spell_string = ""
    for line in lines:
        line = line.strip()
        if line:
            if line == "[": spell_string += line
            elif line == "]": spell_string = spell_string[:-2] + line + ", "
            else: spell_string += line + ", "

    spell_string = "["+spell_string[:-2]+"]"

    # parse string in list mode
    settings["list_mode"] = True
    parse_spell_list(string_to_spell(spell_string,wrapper),registry,settings)
    settings["list_mode"] = False
  
def configure_settings(registry,settings):
    while True:
        print("-----\nSettings Menu - Enter a number to edit the associated setting.")
        print("1 - Select drawing mode (Current: "+settings["draw_mode"]+")")
        print("2 - Select image output path (Current: "+settings["output_path"]+")")
        print("3 - Customize visual appearance")
        print("4 - Toggle pattern identification (Current: "+settings["identify_pattern"]+")")
        print("5 - Add/remove custom pattern")
        print("6 - Add/remove custom alias")
        print("7 - Save current settings to file")
        print("8 - Close settings menu")
        print("9 - Quit program")
        choice = int(input("> "))
        if(choice not in (9,3)): print("-----") 
        match choice:
            case 1:
                print("Select Drawing Mode - Enter a number from the options below.")
                print("1 - Intersect: the line will change color whenever it crosses over itself.")
                print("2 - Monochrome: the line will remain the same color throughout the pattern.")
                print("3 - Gradient: the line will steadily change color with each new segment.")
                print("4 - Animated: the stroke order will be shown in real time.")
                print("5 - Disabled: the pattern will not be drawn at all.")
                match int(input("> ")):
                    case 1: settings["draw_mode"] = "intersect"
                    case 2: settings["draw_mode"] = "monochrome"
                    case 3: settings["draw_mode"] = "gradient"
                    case 4: settings["draw_mode"] = "animated"
                    case 5: settings["draw_mode"] = "disabled"
                    case _:
                        print("Invalid input, drawing mode not changed.")
                        continue
                print("Saved new drawing mode.")
            case 2:
                print("Select Image Output Path")
                print("Provide a path to a folder for pattern images to be saved to.")
                print("For the current folder, enter 'here'. To disable image saving, enter 'none'.")
                settings["output_path"] = input("> ")
                print("Saved new output path.")
            case 3:
                while True:
                    print("-----\nCustomize Visual Appearance - Enter a number from the options below.")
                    print("1 - Select intersect mode colors (Current: "+", ".join(settings["intersect_colors"])+")")
                    print("2 - Select gradient mode colormap (Current: "+settings["gradient_colormap"]+")")
                    print("3 - Select monochrome mode color (Current: "+settings["monochrome_color"]+")")
                    print("4 - Edit global scale factor (Current: "+str(settings["scale_factor"])+")")
                    print("5 - Edit arrow scale factor (Current: "+str(settings["arrow_scale"])+")")
                    print("6 - Edit list-plot dimensions (Current: "+str(settings["grid_dims"][0])+"×"+str(settings["grid_dims"][1])+")")
                    print("7 - Back to main menu")
                    choice2 = int(input("> "))
                    if(choice2!=7): print("-----")
                    match choice2:
                        case 1:
                            print("Select Intersect Mode Colors")
                            print("Enter a list of hex color codes to be used for drawing lines in intersect mode.")
                            settings["intersect_colors"] = []
                            count = int(input("Enter the number of colors you want to use.\n> "))
                            for i in range(1,count+1):
                                settings["intersect_colors"].append(input("Enter a color. ("+str(i)+" of "+str(count)+")\n> "))
                            print("Saved new intersect mode colors.")
                        case 2:
                            print("Select Gradient Mode Colormap")
                            print("Enter a colormap to be used for drawing lines in gradient mode.")
                            print("Alternatively, enter 'list' to display a list of all available colormaps.")
                            choice = input("> ")
                            if(choice=="list"):
                                print(colormaps)
                            elif(choice in colormaps):
                                settings["gradient_colormap"] = choice
                                print("Saved new gradient mode colormap.")
                            else:
                                print("That's not a valid colormap.")
                        case 3:
                            print("Select Monochrome Mode Color")
                            print("Enter a hex color code to be used for drawing lines in monochrome mode.")
                            settings["monochrome_color"] = input("> ")
                            print("Saved new monochrome mode color.")
                        case 4:
                            print("Edit Global Scale Factor")
                            print("This value controls the size of the lines and points in drawn patterns.")
                            print("A larger value will make lines thicker, and points larger.")
                            try: new_scale = float(input("> "))
                            except ValueError: print("Invalid input.")
                            else: settings["scale_factor"] = new_scale
                            print("Saved new global scale factor.")
                        case 5:
                            print("Edit Arrow Scale Factor")
                            print("This value controls the size of the directional arrows relative to the points.")
                            print("A larger value will make the arrows larger compared to the points.")
                            try: new_scale = float(input("> "))
                            except ValueError: print("Invalid input.")
                            else: settings["arrow_scale"] = new_scale
                            print("Saved new arrow scale factor.")
                        case 6:
                            print("Edit List-Plot Dimensions")
                            print("These values control the size of the grid produced by plotting a pattern list.")
                            try:
                                cols = int(input("Enter the maximum number of patterns per row.\n> "))
                                rows = int(input("Enter the maximum number of rows.\n> "))
                                max_patterns = cols*rows-2
                            except ValueError: print("Invalid input.")
                            else: settings["grid_dims"] = [cols,rows,max_patterns]
                            print("Saved new list-plot dimensions.")
                        case _: break
            case 4:
                if(settings["identify_pattern"]=="on"): settings["identify_pattern"] = "off"
                else: settings["identify_pattern"] = "on"
                print("Toggled pattern identification.")
            case 5:
                if not all(registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Add/Remove Custom Pattern")
                print("Create a custom pattern to be saved to the registry.")
                print("Alternatively, remove a previously saved custom pattern.")
                choice2 = input("Enter 'add' or 'remove' to begin.\n> ")

                # add custom pattern
                if choice2 == "add":
                    anglesig = input("Enter the angle signature first.\n> ")
                    startdir = input("Now enter the default start direction.\n> ")
                    name = input("Now enter the name.\n> ")+" (Custom)"
                    great = input("Is this a great spell? (y/n)\n> ")
                    if(great=="n"):
                        registry[0][anglesig] = name
                        registry[2][name] = (False,anglesig,startdir,False)
                        print("Saved '"+anglesig+" = "+name+"' to current pattern registry.")
                        print("To keep this spell between sessions, make sure to save your settings to file.")
                    elif(great=="y"):
                        for direction in ["east","west","northeast","northwest","southeast","southwest"]:
                            new_x,new_y = convert_to_points(anglesig,direction,settings)[:2]
                            points = []
                            for i in range(len(new_x)):
                                points.append([new_x[i],new_y[i]])
                            for point in points:
                                    new_list = [point]
                                    for other_point in points:
                                        if not(abs(point[0]-other_point[0])<0.1 and abs(point[1]-other_point[1])<0.1):
                                            new_list.append(other_point)
                                    points = new_list
                            lowest = [min(new_x),min(new_y)]
                            for i in range(len(points)):
                                points[i][0] -= lowest[0]
                                points[i][1] -= lowest[1]
                            registry[1].append([points,name])
                        plt.close()
                        registry[2][name] = (False,anglesig,startdir,True)
                        print("Saved '"+name+"' to current pattern registry as a great spell.")
                        print("To keep this spell between sessions, make sure to save your settings to file.")
                    else:
                        print("That's not a valid input.")

                # remove custom pattern
                elif choice2 == "remove":
                    anglesig = input("Enter the angle signature. For great spells, any variant will work.\n> ")
                    great = input("Is this a great spell? (y/n)\n> ")
                    if(great=="n"):
                        if anglesig not in registry[0]:
                            print("That angle signature doesn't have an associated pattern.")
                            continue
                        name = registry[0][anglesig]
                        if name[-8:]!="(Custom)":
                            print("Can't deregister '"+anglesig+" = "+name+"' because it's not a custom pattern.")
                            continue
                        del registry[0][anglesig]
                        del registry[2][name]
                        print("Removed '"+anglesig+" = "+name+"' from current pattern registry.")
                        print("To permanently remove this spell, make sure to save your settings to file.")
                    elif(great=="y"):
                        (target_x,target_y,scale,start_angle) = convert_to_points(anglesig,"east",settings)
                        plt.close()
                        name = gs_lookup(target_x,target_y,registry[1])
                        if not name:
                            print("That angle signature doesn't match any registered great spell.")
                            continue
                        elif(name[-8:]!="(Custom)"):
                            print("Can't deregister '"+name+"' because it's not a custom great spell.")
                            continue
                        registry[1] = [entry for entry in registry[1] if entry[1]!=name]
                        del registry[2][name]
                        print("Removed '"+name+"' from current pattern registry.")
                        print("To permanently remove this spell, make sure to save your settings to file.")
                    else:
                        print("That's not a valid input.")
                else:
                    print("That's not a valid input.")
            case 6:
                if not all(registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Add/Remove Custom Alias")
                print("Create a custom alias for an existing pattern.")
                print("Alternatively, remove a previously saved custom alias.")
                choice2 = input("Enter 'add' or 'remove' to begin.\n> ")

                # add custom alias
                if choice2 == "add":
                    name = input("Enter the name of an existing pattern.\n> ")
                    if name not in registry[2]:
                        print("That's not a known pattern name.")
                        continue
                    elif registry[2][name][0]:
                        print("'"+name+"' isn't a pattern name, it's an alias for the name "+registry[2][name][1]+".")
                        print("You can't make an alias for an alias - try entering '"+registry[2][name][1]+"' instead.")
                        continue
                    alias = input("Now enter a name to be used as an alias for that pattern.\n> ")
                    if alias in registry[2]:
                        print("That name is already in use.")
                        continue
                    registry[2][alias] = (True,name)
                    print("Saved '"+alias+"' as a custom alias for '"+name+"'.")
                    print("To keep this alias between sessions, make sure to save your settings to file.")

                # remove custom alias
                elif choice2 == "remove":
                    alias = input("Enter an existing custom alias.\n> ")
                    if alias not in registry[2]:
                        print("That's not a known alias.")
                        continue
                    elif not registry[2][alias][0]:
                        print("'"+alias+"' is not an alias, so it can't be removed.")
                        continue
                    name = registry[2][alias][1]
                    del registry[2][alias]
                    print("Removed custom alias '"+alias+"' for '"+name+"' from current registry.")
                    print("To permanently remove this alias, make sure to save your settings to file.")
                else:
                    print("That's not a valid input.")
            case 7:
                with open("settings.json",mode="w") as file:
                    json.dump(settings,file)
                with open("pattern_registry.pickle",mode="wb") as file:
                    pickle.dump(registry,file)
                print("Settings saved to file.")
            case 8:
                return
            case 9:
                registry[3] = False
                return
            case _:
                print("Invalid input, please try again.")

def admin_configure(registry,settings):
    while True:
        print("-----\nAdmin Console - Allows direct edits to the settings and registry files.")
        print("May cause errors if used improperly. Use at your own risk.")
        print("1 - View settings values")
        print("2 - Add/remove settings field")
        print("3 - View pattern registry")
        print("4 - View great spell registry")
        print("5 - View name-recognition registry")
        print("6 - Alter pattern registry")
        print("7 - Alter name-recognition registry")
        print("8 - Close admin console")
        print("9 - Quit program")
        choice = int(input("> "))
        if choice != 9: print("-----") 
        match choice:
            case 1:
                for name in settings:
                    print(name+": "+str(settings[name]))
            case 2:
                print("Add/Remove New Settings Field")
                print("Add a new name-value pair to the settings file.")
                print("Alternatively, remove an existing name-value pair.")
                choice2 = input("Enter 'add' or 'remove' to begin.\n> ")

                # add settings field
                if choice2 == "add":
                    print("Adding a new field won't have any immediate effects, unless it overwrites an existing one.")
                    name = input("Enter the field name first.\n> ")
                    if name in settings:
                        print("That field already exists. Overwrite it with a new value? (y/n)")
                        if input("> ").lower() != "y":
                            print("Overwrite cancelled.")
                            continue
                    value = input("Enter the value for the field.\n> ")
                    try:
                        value = eval(value)
                        settings[name] = value
                    except NameError:
                        settings[name] = value
                        value = "'"+value+"'"
                    with open("settings.json",mode="w") as file:
                        json.dump(settings,file)
                    print("Saved field '"+name+"' with value "+str(value)+" to file.")

                # remove settings field
                elif choice2 == "remove":
                    print("Removing an important field can easily damage the program. Make sure you know what you're doing.")
                    name = input("Enter the field name.\n> ")
                    if name in settings:
                        del settings[name]
                        with open("settings.json",mode="w") as file:
                            json.dump(settings,file)
                        print("Removed the field '"+name+"'.")
                    else:
                        print("There's no settings field by that name.")
                else:
                    print("That's not a valid input")
            case 3:
                print("Warning - This will be a very large wall of text.")
                print("Continue anyway? (y/n)")
                if input("> ").lower() != "y":
                    print("Registry print cancelled.")
                    continue
                for anglesig in registry[0]:
                    print(anglesig+": "+registry[0][anglesig])
            case 4:
                print("Warning - This will be a very large wall of text.")
                print("Continue anyway? (y/n)")
                if input("> ").lower() != "y":
                    print("Registry print cancelled.")
                    continue
                print("\n")
                for pair in registry[1]:
                    print(str(pair[0])+"\n--> "+pair[1]+"\n")
            case 5:
                print("Warning - This will be a very large wall of text.")
                print("Continue anyway? (y/n)")
                if input("> ").lower() != "y":
                    print("Registry print cancelled.")
                    continue
                for name in registry[2]:
                    entry = registry[2][name]
                    if entry[0]:
                        print(name+": alias for "+entry[1])
                    else:
                        print(name+": "+entry[1]+" "+entry[2])
            case 6:
                if not all(registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Alter Pattern Registry")
                print("Create a new pattern to be saved to the registry.")
                print("Alternatively, remove a pattern from the registry.")
                choice2 = input("Enter 'add' or 'remove' to begin.\n> ")

                # add pattern
                if choice2 == "add":
                    anglesig = input("Enter the angle signature first.\n> ")
                    startdir = input("Now enter the default start direction.\n> ")
                    name = input("Now enter the name.\n> ")
                    great = input("Is this a great spell? (y/n)\n> ")
                    if(great=="n"):
                        registry[0][anglesig] = name
                        registry[2][name] = (False,anglesig,startdir,False)
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        print("Saved '"+anglesig+" = "+name+"' to pattern registry.")
                    elif(great=="y"):
                        for direction in ["east","west","northeast","northwest","southeast","southwest"]:
                            new_x,new_y = convert_to_points(anglesig,direction,settings)[:2]
                            points = []
                            for i in range(len(new_x)):
                                points.append([new_x[i],new_y[i]])
                            for point in points:
                                    new_list = [point]
                                    for other_point in points:
                                        if not(abs(point[0]-other_point[0])<0.1 and abs(point[1]-other_point[1])<0.1):
                                            new_list.append(other_point)
                                    points = new_list
                            lowest = [min(new_x),min(new_y)]
                            for i in range(len(points)):
                                points[i][0] -= lowest[0]
                                points[i][1] -= lowest[1]
                            registry[1].append([points,name])
                        plt.close()
                        registry[2][name] = (False,anglesig,startdir,True)
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        print("Saved '"+name+"' to pattern registry as a great spell.")
                    else:
                        print("That's not a valid input.")

                # remove pattern
                elif choice2 == "remove":
                    anglesig = input("Enter the angle signature. For great spells, any variant will work.\n> ")
                    great = input("Is this a great spell? (y/n)\n> ")
                    if(great=="n"):
                        if anglesig not in registry[0]:
                            print("That angle signature doesn't have an associated pattern.")
                            continue
                        name = registry[0][anglesig]
                        del registry[0][anglesig]
                        del registry[2][name]
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        print("Removed '"+anglesig+" = "+name+"' from pattern registry.")                
                    elif(great=="y"):
                        (target_x,target_y,scale,start_angle) = convert_to_points(anglesig,"east",settings)
                        plt.close()
                        name = gs_lookup(target_x,target_y,registry[1])
                        if not name:
                            print("That angle signature doesn't match any registered great spell.")
                            continue
                        registry[1] = [entry for entry in registry[1] if entry[1]!=name]
                        del registry[2][name]
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        print("Removed '"+name+"' from pattern registry.") 
                    else:
                        print("That's not a valid input.")
                else:
                    print("That's not a valid input.")
            case 7:
                if not all(registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Alter Name-Recognition Registry")
                print("Create a new name or alias to be saved to the registry.")
                print("Alternatively, remove a name or alias from the registry.")
                choice2 = input("Enter 'add' or 'remove' to begin.\n> ")

                # add name/alias
                if choice2 == "add":
                    name = input("Enter the name of a pattern.\n> ")
                    if name not in registry[2]:
                        print("That name is not in the name-recognition registry. Create a new entry? (y/n)")
                        if input("> ").lower() != "y":
                            print("Entry creation cancelled.")
                            continue
                        anglesig = input("Enter the angle signature first.\n> ")
                        startdir = input("Now enter the default start direction.\n> ")
                        if input("Is this a great spell? (y/n)\n> ").lower() != "y":
                            great = False
                        else:
                            great = True
                        registry[2][name] = (False,anglesig,startdir,great)
                        print("Saved new entry '"+name+" = "+anglesig+" "+startdir+"' to the registry.")
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        continue
                    elif registry[2][name][0]:
                        print("'"+name+"' isn't a pattern name, it's an alias for the name "+registry[2][name][1]+".")
                        print("You can't make an alias for an alias - try entering '"+registry[2][name][1]+"' instead.")
                        continue
                    alias = input("Now enter a name to be used as an alias for that pattern.\n> ")
                    if alias in registry[2]:
                        print("That name is already in use.")
                        continue
                    registry[2][alias] = (True,name)
                    print("Saved '"+alias+"' as an alias for '"+name+"'.")
                    with open("pattern_registry.pickle",mode="wb") as file:
                        pickle.dump(registry,file)

                # remove name/alias
                elif choice2 == "remove":
                    alias = input("Enter an existing name or alias.\n> ")
                    if alias not in registry[2]:
                        print("That's not a known alias.")
                    elif not registry[2][alias][0]:
                        print("'"+alias+"' is an actual pattern name, not an alias. Remove it anyway? (y/n)")
                        if input("> ").lower() != "y":
                            print("Removal cancelled.")
                            continue
                        entry = registry[2][alias]
                        del registry[2][alias]
                        print("Removed entry '"+alias+" = "+entry[1]+" "+entry[2]+"' from the registry.")
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                    else:
                        name = registry[2][alias][1]
                        del registry[2][alias]
                        print("Removedalias '"+alias+"' for '"+name+"'.")
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                else:
                    print("That's not a valid input.")
            case 8:
                return
            case 9:
                registry[3] = False
                return
            case _:
                print("Invalid input, please try again.")

if __name__ == "__main__":
    # change working directory to script folder
    chdir(path.dirname(path.abspath(__file__)))
    
    # load registry for pattern and great spell names
    try:
        with open("pattern_registry.pickle",mode="rb") as file:
            registry = pickle.load(file)
            registry[3] = True
    except FileNotFoundError:
        print("Warning - pattern_registry.pickle not found")
        registry = [None,None,None,True]

    # load config settings
    try:
        with open("settings.json",mode="r") as file:
            settings = json.load(file)
    except FileNotFoundError:
        print("Warning - settings.json not found")
        settings = {"draw_mode":"intersect",
                    "output_path":"none",
                    "scale_factor":5,
                    "arrow_scale":1.2,
                    "grid_dims":[9,5,43],
                    "intersect_colors":["#ff6bff","#a81ee3","#6490ed","#b189c7"],
                    "gradient_colormap":"cool",
                    "monochrome_color":"#a81ee3",
                    "identify_pattern":"on",
                    "list_mode":False}

    # main program loop
    while registry[3]:
        raw_input = input("Enter a hexpattern, a filename, or 'S' for settings: ")
        if raw_input=="s":
            configure_settings(registry,settings)
        elif raw_input=="admin":
            admin_configure(registry,settings)
        elif raw_input.startswith("["):
            settings["list_mode"] = True
            parse_spell_list(string_to_spell(raw_input),registry,settings)
            settings["list_mode"] = False
        elif raw_input[-4:] == ".txt":
            parse_from_file(raw_input,registry,settings)
        elif raw_input.startswith("by_hand"):
            start = raw_input.find("[")
            if start < 0:
                main(raw_input[8:],registry,settings)
            else:
                settings["list_mode"] = True
                parse_spell_list(string_to_spell(raw_input[start:],False),registry,settings)
                settings["list_mode"] = False
        else:
            main(raw_input,registry,settings)
