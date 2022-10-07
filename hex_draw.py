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
                print("Invalid char - defaulted to w")
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
            if (abs(x_vals[i]-checked[j][0]) < 0.1 and
                abs(y_vals[i]-checked[j][1]) < 0.1 and
                abs(x_vals[i+1]-checked[j+1][0]) < 0.1 and
                abs(y_vals[i+1]-checked[j+1][1]) < 0.1):
                return (None,None,None,None)
        checked.append((x_vals[i],y_vals[i]))

    # find the width or height, whichever is largest, and apply some transformations to it
    # this value is used when drawing to scale the lines and points based on graph size
    max_width = max([max(x_vals)-min(x_vals),max(y_vals)-min(y_vals)])
    if(max_width<=1): max_width = 1.25
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
        if(char in ("e","w")):
            output += "-"
        elif(char=="d"):
            output += "v"
            skip = True
        elif(char=="a"):
            output = output[:-1]+"v"
        else: return None
    return "Bookkeeper's Gambit ("+output+")"

def dict_lookup(angle_sig,pattern_dict):
    try:
        output = pattern_dict[angle_sig]
        return output     
    except KeyError:
        return None

def gs_lookup(x_vals,y_vals,great_spells):
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

def plot_gradient(x_vals,y_vals,scale,line_count,gradient_colormap):
    colors = colormaps[gradient_colormap]
    for i in range(line_count):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors(1-i/line_count),lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale)

def plot_intersect(x_vals,y_vals,scale,line_count,settings):
    used_points = []
    colors = settings["intersect_colors"]
    color_index = 0
    for i in range(line_count+1):
        point = [x_vals[i],y_vals[i],color_index,]
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

        # only draw a line segement extending from the point if we're not at the end
        if(i!=line_count):
            plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors[color_index],lw=scale)

        # draw the point itself
        plt.plot(point[0],point[1],'ko',ms=2*scale)

def main(raw_input,registry,settings):
    # remove HexPattern() wrapper, if present
    if(raw_input.startswith("hexpattern")):
        raw_input = raw_input[11:-1]

    # parse in-game hexpattern syntax
    if(raw_input.startswith(("east","west","northeast","northwest","southeast","southwest"))):
        try:
            space = raw_input.index(" ")
            start_dir = raw_input[:space]
            angle_sig = raw_input[space+1:]
        except ValueError:
            angle_sig = ""
            start_dir = raw_input

    # parse discord bot syntax
    elif not settings["list_mode"]:
        try:
            space = raw_input.index(" ")
            angle_sig = raw_input[:space]
            start_dir = raw_input[space+1:]
        except ValueError:
            angle_sig = raw_input
            start_dir = "east"

    # handle non-pattern iotas if list mode is enabled
    else: return None

    # convert input to x and y values
    (x_vals,y_vals,scale,start_angle) = convert_to_points(angle_sig,start_dir,settings)
    if not x_vals:
        if not settings["list_mode"]: print("Error - that pattern overlaps itself.\n-----")
        return "Invalid Pattern (self-overlapping)"
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
        except TypeError: result = "Unknown - no pattern registry"

        # if no matches found, pattern is unrecognized
        if not result:
            if settings["list_mode"]: return "Unrecognized Pattern ("+angle_sig+")"
            else: result = "Unknown - unrecognized pattern"

        # deal with result based on mode
        if(settings["list_mode"]): return result
        else: print("This pattern is: "+result)

    # create a square plot and hide the axes
    ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
    ax.set_aspect("equal")
    ax.axis("off")
    
    # run the selected draw function
    match settings["draw_mode"]:
        case "intersect":
            plt.plot(x_vals[1]/2.15,y_vals[1]/2.15,color=settings["intersect_colors"][0],marker=(3,0,start_angle),ms=2.6*settings["arrow_scale"]*scale)
            plot_intersect(x_vals,y_vals,scale,line_count,settings)
        case "gradient":
            plt.plot(x_vals[1]/2.15,y_vals[1]/2.15,color=colormaps[settings["gradient_colormap"]](0.999),marker=(3,0,start_angle),ms=2.6*settings["arrow_scale"]*scale)
            plot_gradient(x_vals,y_vals,scale,line_count,settings["gradient_colormap"])
        case "monochrome":
            plot_monochrome(x_vals,y_vals,scale,line_count,settings["monochrome_color"])
        case "disabled":
            pass
        case _:
            print("Config error, this shouldn't happen")

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
    if not(settings["draw_mode"]=="disabled"):
        plt.show()
    print("-----")

def collect_list(subspell):
    contents = []
    count = 0
    subspell_iter = iter(subspell)

    for sub_iota in subspell_iter:
        # even subber list handing
        if sub_iota[0] == "[" and subspell.index(sub_iota) != 0:
            (sub_iota, sub_skip) = collect_list(subspell[subspell.index(sub_iota):])
            for i in range(sub_skip):
                next(subspell_iter)
            count += sub_skip
        # end sublist collection, return contents as a single iota
        elif sub_iota[-1] == "]":
            contents.append(sub_iota)
            return ", ".join(contents), count
        # add iota to sublist contents
        contents.append(sub_iota)
        count += 1

def parse_spell_list(raw_input,registry,settings,meta):
    # convert string into proper list
    spell = raw_input[1:-1].split(", ")
    spell_iter = iter(spell)
    output_list = []

    # interpret each iota
    for iota in spell_iter:
        # vector handling
        if iota[0] == "(":
            iota += ", " + next(spell_iter)
            iota += ", " + next(spell_iter)
        
        # sublist handling
        elif iota[0] == "[":
            (iota, items_to_skip) = collect_list(spell[spell.index(iota):])
            for i in range(items_to_skip):
                next(spell_iter)

        # add result to list of outputs
        if name := main(iota.lower(),registry,settings): output_list.append(name)
        elif iota[0]=="[" or meta: output_list.append(iota)
        else: output_list.append("NON-PATTERN: "+iota)

    # print result line by line
    indents = meta + 1
    
    # to multiply considerations inside injected lists, do the following
    # replace "2**indents" in the range() function with "2**power"
    # then add "power += 1" into the first elif
    # then add "power -= 1" into the second elif
    # then uncomment the code below
    '''
    if meta: power = 0
    else: power = indents
    '''
    
    for name in output_list:
        if name=="Consideration" and not meta:
            for i in range(2**indents):
                print("  "*indents+"Consideration")
        elif name=="Introspection":
            print("  "*indents+"{")
            indents += 1
        elif name=="Retrospection":
            indents -= 1
            print("  "*indents+"}")
        elif name[0]=="[":
            print("  "*indents+"[")
            parse_spell_list(name,registry,settings,indents)
            print("  "*indents+"]")
        else:
            print("  "*indents+name)
  
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
                            try: new_scale = int(input("> "))
                            except ValueError: print("Invalid input.")
                            else: settings["scale_factor"] = new_scale
                            print("Saved new global scale factor.")
                        case 5:
                            print("Edit Arrow Scale Factor")
                            print("This value controls the size of the directional arrows relative to the points.")
                            print("A larger value will make the arrows larger compared to the points.")
                            try: new_scale = int(input("> "))
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
                print("Provide an angle signature and a pattern name to be saved to the registry.")
                anglesig = input("Enter the angle signature first.\n> ")
                name = input("Now enter the name.\n> ")+" (Custom)"
                great = input("Is this a great spell? (y/n)\n> ")
                if(great=="n"):
                    registry[0][anglesig] = name
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
                            with open("pattern_registry.pickle",mode="wb") as file:
                                pickle.dump(registry,file)
                            print("Removed '"+anglesig+" = "+name+"' from pattern registry.")
                        else:
                            print("Can't deregister '"+anglesig+" = "+name+"' because it's not a custom pattern.")
                    else:
                        print("That angle signature doesn't have an associated pattern.")
                elif(great=="y"):
                    (target_x,target_y,scale) = convert_to_points(anglesig,"east",settings)
                    plt.close()
                    name = gs_lookup(target_x,target_y,registry[1])
                    if(name):
                        if(name[-8:]=="(Custom)"):
                            registry = (registry[0],[entry for entry in registry[1] if entry[1]!=name])
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
                print("Provide an angle signature and a pattern name to be saved to the registry.")
                anglesig = input("Enter the angle signature first.\n> ")
                name = input("Now enter the name.\n> ")
                great = input("Is this a great spell? (y/n)\n> ")
                if(great=="n"):
                    registry[0][anglesig] = name
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
                        registry = (registry[0],[entry for entry in registry[1] if entry[1]!=name])
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
        registry = None

    # load config settings
    try:
        with open("settings.json",mode="r") as file:
            settings = json.load(file)
    except FileNotFoundError:
        print("Warning - settings.json not found")
        settings = {"draw_mode":"intersect",
                    "output_path":"none",
                    "scale_factor":5,
                    "arrow_scale":1,
                    "intersect_colors":["#ff6bff","#a81ee3","#6490ed","#b189c7"],
                    "gradient_colormap":"cool",
                    "monochrome_color":"#a81ee3",
                    "identify_pattern":"on",
                    "list_mode":False,
                    "file_missing":True}

    # main program loop
    while settings:
        raw_input = input("Enter a hexpattern, or 'S' for settings: ").replace("_","")
        if(raw_input=="s"):
            (registry,settings) = configure_settings(registry,settings)
        elif(raw_input=="admin"):
            (registry,settings) = admin_configure(registry,settings)
        elif(raw_input.startswith("[")):
            settings["list_mode"] = True
            print("-----\nThis spell consists of:\n{")
            parse_spell_list(raw_input,registry,settings,0)
            print("}\n-----")
            settings["list_mode"] = False
        else:
            main(raw_input.lower(),registry,settings)
