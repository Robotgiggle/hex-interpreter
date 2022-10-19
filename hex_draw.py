import matplotlib.pyplot as plt
from matplotlib import colormaps
from matplotlib import colors
from os.path import isfile
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
            print("Invalid start direction - defaulted to east")
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
    if(max_width<=1.01): max_width = 1.25
    scale = settings["scale_factor"]/math.log(max_width,1.5)+1.1
   
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

def plot_monochrome(x_vals,y_vals,scale,line_count,monochrome_color):
    for i in range(line_count):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=monochrome_color,lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale)

def plot_gradient(x_vals,y_vals,scale,line_count,start_angle,settings):
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

def plot_intersect(x_vals,y_vals,scale,line_count,start_angle,settings):
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
            color_index %= 4
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

def main(raw_input,registry,settings,ax):
    # remove HexPattern() wrapper, if present
    if(raw_input.startswith("hexpattern")):
        raw_input = raw_input[11:-1]

    # if patterns was given by name, use that
    if all(registry):
        matches = []
        for name in registry[2]:
            if raw_input == name.lower():
                matches = [name]
                angle_sig = registry[2][name][0]
                start_dir = registry[2][name][1]
                force_mono = registry[2][name][2]
                break
            elif raw_input in name.lower():
                matches.append(name)
                angle_sig = registry[2][name][0]
                start_dir = registry[2][name][1]
                force_mono = registry[2][name][2]
        if len(matches) == 0:
            by_name = False
        elif len(matches) == 1:
            by_name = True
        else:
            print("Found multiple matches for '"+raw_input+"':")
            for match in matches: print("- "+match)
            print("Try entering something more specific.\n-----")
            return None
    else:
        by_name = False

    # if not, attempt to parse a hexpattern
    if not by_name:
        force_mono = False
        raw_input = raw_input.replace("_","")
        
        # make sure there even is a start direction
        if raw_input.find(" ") == -1:
            if not settings["list_mode"]: print("Error - no start direction.\n-----")
            return None
        
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
                return None

    # convert input to x and y values
    (x_vals,y_vals,scale,start_angle) = convert_to_points(angle_sig,start_dir,settings)
    if not x_vals:
        if settings["list_mode"]: output = "Invalid Pattern (self-overlapping)"
        else: print("Error - that pattern overlaps itself.\n-----")
    elif not y_vals:
        if settings["list_mode"]: output = "Invalid Pattern (unreadable)"
        else: print("Error - invalid character in angle signature.\n-----")
    line_count = len(x_vals)-1

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
            if settings["list_mode"]: output = "Unknown Pattern (no pattern registry)"
            else: result = "Unknown - no pattern registry"

        # dispel rain override
        if result == "Summon Rain" and x_vals[0]-x_vals[-1] < 0.1:
            result = "Dispel Rain"

        # if no matches found, pattern is unrecognized
        if not result:
            if settings["list_mode"]: output = "Unknown Pattern ("+angle_sig+")"
            else: result = "Unknown - unrecognized pattern"

        # deal with result based on mode
        if(settings["list_mode"]): output = result
        else: print("This pattern is: "+result)

    # pre-plot scaling for list mode
    if settings["list_mode"]:
        scale *= 0.8
        if scale > 2.5: scale = 2.5
        elif scale < 1.9: settings["arrow_scale"] -= 0.5
        else: settings["arrow_scale"] -= 0.3
        
    # pre-plot scaling for single mode
    else:
        ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
        ax.set_aspect("equal")
        ax.axis("off")
    
    # run the selected draw function
    if force_mono:
        plot_monochrome(x_vals,y_vals,scale,line_count,settings["monochrome_color"])
    else:
        match settings["draw_mode"]:
            case "intersect":
                plot_intersect(x_vals,y_vals,scale,line_count,start_angle,settings)
            case "gradient":
                plot_gradient(x_vals,y_vals,scale,line_count,start_angle,settings)
            case "monochrome":
                plot_monochrome(x_vals,y_vals,scale,line_count,settings["monochrome_color"])
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
        if(settings["output_path"]=="here"): filename = angle_sig
        else: filename = settings["output_path"]+"/"+angle_sig
        num = 1
        while(isfile(filename+".png")):
            if(filename[-1]==str(num-1)): filename = filename[:-1]+str(num)
            else: filename += ("_"+str(num))
            num += 1
        plt.savefig(filename+".png")
    
    # display the final image, if enabled
    if settings["list_mode"]: return output
    elif settings["draw_mode"] == "disabled": plt.close()
    else: plt.show()
    
    print("-----")

def string_to_spell(raw_input):
    nested = 0
    raw_input = raw_input[1:-1].replace(";",",")
    for i in range(len(raw_input)):
        if raw_input[i] in ("[","("): nested += 1
        elif raw_input[i] in ("]",")"): nested -= 1
        elif nested > 0 and raw_input[i] == ",":
            raw_input = raw_input[:i]+";"+raw_input[i+1:]
    spell = raw_input.split(", ")
    return spell

def parse_spell_list(spell,registry,settings,meta):
    output_list = []

    # create figure to plot patterns into
    rows = (len(spell)+2)//9 + 1
    cols = len(spell)+2 if rows==1 else 9
    fig = plt.figure(figsize=(cols+1,rows+1))
    index = 1

    # interpret each iota
    ax = fig.add_subplot(rows,cols,index,aspect="equal")
    ax.axis("off")
    main("introspection",registry,settings,ax)
    indents = meta + 1
    for iota in spell:
        # create subplot for this pattern
        index += 1
        ax = fig.add_subplot(rows,cols,index,aspect="equal")
        ax.axis("off")
        
        # add result to list of outputs
        if name := main(iota.lower(),registry,settings,ax): output_list.append(name)
        elif iota[0]=="[" or meta: output_list.append(iota)
        else: output_list.append("NON-PATTERN: "+iota)

        # indentation handling
        if name == "Introspection":
            output_list[-1] = ("{",indents)
            indents += 1
        elif name == "Retrospection":
            indents -= 1
            output_list[-1] = ("}",indents)
        elif name == "Consideration" and not meta:
            output_list[-1] = (output_list[-1],indents)
            for i in range(2**indents-1):
                index += 1
                ax = fig.add_subplot(rows,cols,index,aspect="equal")
                ax.axis("off")
                main(iota.lower(),registry,settings,ax)
                output_list.append(("Consideration",indents))
        else:
            output_list[-1] = (output_list[-1],indents)

        # draw placeholder symbol for non-pattern or meta-eval
        if iota[0] == "[":
            ax.plot(0,0,marker="$[]$",ms=50,c=settings["monochrome_color"])
        elif iota[0] == "(":
            ax.plot(0,0,marker="$\u27E8\u27E9$",ms=50,c=settings["monochrome_color"])
        elif iota.isnumeric():
            ax.plot(0,0,marker="$\#$",ms=50,c=settings["monochrome_color"])
        elif iota in ("Null","arimfexendrapuse"):
            ax.plot(0,0,marker="$?$",ms=50,c=settings["monochrome_color"])
        elif not (meta or name):
            ax.plot(0,0,marker="$@$",ms=50,c=settings["monochrome_color"])
    ax = fig.add_subplot(rows,cols,index+1,aspect="equal")
    ax.axis("off")
    main("retrospection",registry,settings,ax)
    
    # print result line by line
    if not meta: print("This spell consists of:\n{")
    for name in output_list:
        if name[0][0]=="[":
            print("  "*name[1]+"[")
            parse_spell_list(string_to_spell(name[0]),registry,settings,name[1])
            print("  "*name[1]+"]")
        elif name[0][-1]==")":
            print("  "*name[1]+name[0].replace(";",","))
        else:
            print("  "*name[1]+name[0])
    if not meta: print("}")

    # print final figure
    if meta or len(output_list) > 43 or settings["draw_mode"] == "disabled":
        plt.close()
    else:
        fig.tight_layout(pad=0)
        plt.show()

    if not meta: print("-----")
  
def configure_settings(registry,settings):
    while True:
        print("-----\nSettings Menu - Enter a number to edit the associated setting.")
        print("1 - Select drawing mode (Current: "+settings["draw_mode"]+")")
        print("2 - Select image output path (Current: "+settings["output_path"]+")")
        print("3 - Customize visual appearance")
        print("4 - Toggle pattern identification (Current: "+settings["identify_pattern"]+")")
        print("5 - Register custom pattern")
        print("6 - Deregister custom pattern")
        print("7 - Save current settings as default")
        print("8 - Close settings menu")
        print("9 - Quit program")
        choice = int(input("> "))
        if(choice not in (9,3)): print("-----") 
        match choice:
            case 1:
                print("Select Drawing Mode - Enter a number from the options below.")
                print("1 - Intersect: the line will change color whenever it crosses over itself.")
                print("2 - Gradient: the line will steadily change color with each new segment.")
                print("3 - Monochrome: the line will remain the same color throughout the pattern.")
                print("4 - Disabled: the pattern will not be drawn at all.")
                match int(input("> ")):
                    case 1: settings["draw_mode"] = "intersect"
                    case 2: settings["draw_mode"] = "gradient"
                    case 3: settings["draw_mode"] = "monochrome"
                    case 4: settings["draw_mode"] = "disabled"
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
                    print("6 - Back to main menu")
                    choice2 = int(input("> "))
                    if(choice2!=6): print("-----")
                    match choice2:
                        case 1:
                            print("Select Intersect Mode Colors")
                            print("Enter four hex color codes to be used for drawing lines in intersect mode.")
                            print("The colors will be used in the order '1, 2, 3, 4, 3, 2' to form a continuous cycle.")
                            settings["intersect_colors"][0] = input("Enter the first color.\n> ")
                            settings["intersect_colors"][1] = input("Enter the second color.\n> ")
                            settings["intersect_colors"][2] = input("Enter the third color.\n> ")
                            settings["intersect_colors"][3] = input("Enter the color color.\n> ")
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
                        case _: break
            case 4:
                if(settings["identify_pattern"]=="on"): settings["identify_pattern"] = "off"
                else: settings["identify_pattern"] = "on"
                print("Toggled pattern identification.")
            case 5:
                if(not registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Register Custom Pattern")
                print("Create a custom pattern to be saved to the registry.")
                anglesig = input("Enter the angle signature first.\n> ")
                startdir = input("Now enter the default start direction.\n> ")
                name = input("Now enter the name.\n> ")+" (Custom)"
                great = input("Is this a great spell? (y/n)\n> ")
                if(great=="n"):
                    registry[0][anglesig] = name
                    registry[2][name] = (anglesig,startdir,False)
                    with open("pattern_registry.pickle",mode="wb") as file:
                        pickle.dump(registry,file)
                    print("Saved '"+anglesig+" = "+name+"' to pattern registry.")
                elif(great=="y"):
                    for direction in ["east","west","northeast","northwest","southeast","southwest"]:
                        (new_x,new_y,scale) = convert_to_points(anglesig,direction,settings)
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
                    registry[2][name] = (anglesig,startdir,True)
                    with open("pattern_registry.pickle",mode="wb") as file:
                        pickle.dump(registry,file)
                    print("Saved '"+name+"' to pattern registry as a great spell.")
                else:
                    print("That's not a valid input.")
            case 6:
                if(not registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Deregister Custom Pattern")
                print("Remove a custom pattern from the registry.")
                anglesig = input("Enter the angle signature. For great spells, any variant will work.\n> ")
                great = input("Is this a great spell? (y/n)\n> ")
                if(great=="n"):
                    if anglesig in registry[0]:
                        name = registry[0][anglesig]
                        if(name[-8:]=="(Custom)"):
                            del registry[0][anglesig]
                            del registry[2][name]
                            with open("pattern_registry.pickle",mode="wb") as file:
                                pickle.dump(registry,file)
                            print("Removed '"+anglesig+" = "+name+"' from pattern registry.")
                        else:
                            print("Can't deregister '"+anglesig+" = "+name+"' because it's not a custom pattern.")
                    else:
                        print("That angle signature doesn't have an associated pattern.")
                elif(great=="y"):
                    (target_x,target_y,scale,start_angle) = convert_to_points(anglesig,"east",settings)
                    plt.close()
                    name = gs_lookup(target_x,target_y,registry[1])
                    if(name):
                        if(name[-8:]=="(Custom)"):
                            registry = (registry[0],[entry for entry in registry[1] if entry[1]!=name],registry[2])
                            del registry[2][name]
                            with open("pattern_registry.pickle",mode="wb") as file:
                                pickle.dump(registry,file)
                            print("Removed '"+name+"' from pattern registry.")
                        else:
                            print("Can't deregister '"+name+"' because it's not a custom great spell.")
                    else:
                        print("That angle signature doesn't match any registered great spell.")
                else:
                    print("That's not a valid input.")
            case 7:
                with open("settings.json",mode="w") as file:
                    json.dump(settings,file)
                print("Settings saved to file.")
            case 8:
                return (registry,settings)
            case 9:
                return (registry,None)
            case _:
                print("Invalid input, please try again.")

def admin_configure(registry,settings):
    while True:
        print("-----\nAdmin Console - Allows direct edits to the settings and registry files.")
        print("May cause errors if used improperly. Use at your own risk.")
        print("1 - View settings values")
        print("2 - Add new settings field")
        print("3 - Remove settings field")
        print("4 - View pattern registry")
        print("5 - View great spell registry")
        print("6 - Register new pattern")
        print("7 - Deregister pattern")
        print("8 - Close admin console")
        print("9 - Quit program")
        choice = int(input("> "))
        if choice != 9: print("-----") 
        match choice:
            case 1:
                for name in settings:
                    print(name+": "+str(settings[name]))
            case 2:
                if(settings["file_missing"]):
                    print("Error - settings file is missing")
                    continue
                print("Add New Settings Field")
                print("Provide a name and value to be added to the settings file.")
                print("This won't have any immediate effects, unless you overwrite an existing field.")
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
            case 3:
                if(settings["file_missing"]):
                    print("Error - settings file is missing")
                    continue
                print("Remove Settings Field")
                print("Provide a name for a field to be removed from the settings file.")
                print("This can easily damage the program. Make sure you know what you're doing.")
                name = input("Enter the field name.\n> ")
                if name in settings:
                    del settings[name]
                    with open("settings.json",mode="w") as file:
                        json.dump(settings,file)
                    print("Removed the field '"+name+"'.")
                else:
                    print("There's no settings field by that name.")
            case 4:
                for anglesig in registry[0]:
                    print(anglesig+": "+registry[0][anglesig])
            case 5:
                print("Warning - This will be a very large wall of text.")
                print("Continue anyway? (y/n)")
                if input("> ").lower() != "y":
                    print("Registry print cancelled.")
                    continue
                print("\n")
                for pair in registry[1]:
                    print(str(pair[0])+"\n--> "+pair[1]+"\n")
            case 6:
                if(not registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Register New Pattern")
                print("Create a pattern to be saved to the registry.")
                anglesig = input("Enter the angle signature first.\n> ")
                startdir = input("Now enter the default start direction.\n> ")
                name = input("Now enter the name.\n> ")
                great = input("Is this a great spell? (y/n)\n> ")
                if(great=="n"):
                    registry[0][anglesig] = name
                    registry[2][name] = (anglesig,startdir,False)
                    with open("pattern_registry.pickle",mode="wb") as file:
                        pickle.dump(registry,file)
                    print("Saved '"+anglesig+" = "+name+"' to pattern registry.")
                elif(great=="y"):
                    for direction in ["east","west","northeast","northwest","southeast","southwest"]:
                        (new_x,new_y,scale,start_angle) = convert_to_points(anglesig,direction,settings)
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
                    registry[2][name] = (anglesig,startdir,True)
                    with open("pattern_registry.pickle",mode="wb") as file:
                        pickle.dump(registry,file)
                    print("Saved '"+name+"' to pattern registry as a great spell.")
                else:
                    print("That's not a valid input.")
            case 7:
                if(not registry):
                    print("Error - pattern registry is missing")
                    continue
                print("Deregister Pattern")
                print("Remove a pattern from the registry.")
                anglesig = input("Enter the angle signature. For great spells, any variant will work.\n> ")
                great = input("Is this a great spell? (y/n)\n> ")
                if(great=="n"):
                    if anglesig in registry[0]:
                        name = registry[0][anglesig]
                        del registry[0][anglesig]
                        del registry[2][name]
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        print("Removed '"+anglesig+" = "+name+"' from pattern registry.")
                    else:
                        print("That angle signature doesn't have an associated pattern.")
                elif(great=="y"):
                    (target_x,target_y,scale) = convert_to_points(anglesig,"east",settings)
                    plt.close()
                    name = gs_lookup(target_x,target_y,registry[1])
                    if(name):
                        registry = (registry[0],[entry for entry in registry[1] if entry[1]!=name],registry[2])
                        del registry[2][name]
                        with open("pattern_registry.pickle",mode="wb") as file:
                            pickle.dump(registry,file)
                        print("Removed '"+name+"' from pattern registry.")
                    else:
                        print("That angle signature doesn't match any registered great spell.")
                else:
                    print("That's not a valid input.")
            case 8:
                return (registry,settings)
            case 9:
                return (registry,None)
            case _:
                print("Invalid input, please try again.")

if __name__ == "__main__":
    # load registry for pattern and great spell names
    try:
        with open("pattern_registry.pickle",mode="rb") as file:
            registry = pickle.load(file)
    except FileNotFoundError:
        print("Warning - pattern_registry.pickle not found")
        registry = (None,None,None)

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
                    "intersect_colors":["#ff6bff","#a81ee3","#6490ed","#b189c7"],
                    "gradient_colormap":"cool",
                    "monochrome_color":"#a81ee3",
                    "identify_pattern":"on",
                    "list_mode":False,
                    "file_missing":True}
    
    # main program loop
    while settings:
        raw_input = input("Enter a hexpattern, or 'S' for settings: ")
        if(raw_input=="s"):
            (registry,settings) = configure_settings(registry,settings)
        elif(raw_input=="admin"):
            (registry,settings) = admin_configure(registry,settings)
        elif(raw_input.startswith("[")):
            settings["list_mode"] = True
            parse_spell_list(string_to_spell(raw_input),registry,settings,0)
            settings["list_mode"] = False
        else:
            main(raw_input.lower(),registry,settings,None)

