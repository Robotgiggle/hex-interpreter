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

    # find the width or height, whichever is largest, and apply some transformations to it
    # this value is used when drawing to scale the lines and points based on graph size
    max_width = max([max(x_vals)-min(x_vals),max(y_vals)-min(y_vals)])
    if(max_width<=1): max_width = 1.25
    scale = settings["scale_factor"]/math.log(max_width,1.5)+1.1

    # draw a triangle to show where the pattern starts, using the start angle from ealier
        
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
    return "Number Literal ("+str(output)+")"

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

    # if no matches were found, it's not a known pattern of any kind
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
    colors = [settings["intersect_colors"][c] for c in (0,1,2,3,2,1)]
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
            color_index %= 6
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
    else:
        try:
            space = raw_input.index(" ")
            angle_sig = raw_input[:space]
            start_dir = raw_input[space+1:]
        except ValueError:
            angle_sig = raw_input
            start_dir = "east"

    # convert input to x and y values
    (x_vals,y_vals,scale,start_angle) = convert_to_points(angle_sig,start_dir,settings)
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
        '''
        if(registry):
            result = dict_lookup(angle_sig,registry[0])
        if(registry and not result):
            result = gs_lookup(x_vals,y_vals,registry[1])
        if(angle_sig.startswith(("aqaa","dedd")) and not result):
            result = parse_number(angle_sig)
        if(angle_sig.startswith(("ada","ae","ea","w")) and not result):
            result = parse_bookkeeper(angle_sig)
        if(not registry and not result):
            result = "Unknown - no pattern registry"
        elif(settings["list_mode"] and not result):
            return "Unrecognized Pattern ("+angle_sig+")"
        elif(not result):
            result = "Unknown - unrecognized pattern"
        
        '''

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
            plt.plot(x_vals[1]/2.15,y_vals[1]/2.15,color=settings["gradient_colormap"][0],marker=(3,0,start_angle),ms=2.6*settings["arrow_scale"]*scale)
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
  
def configure_settings(settings,registry):
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
                    case _: pass
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
                return (settings,registry)
            case 9:
                return (None,registry)
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
                    "intersect_colors":["#ff00ff","#aa55ff","#55aaff","#0cf3ff"],
                    "gradient_colormap":"cool",
                    "monochrome_color":"#aa55ff",
                    "identify_pattern":"on",
                    "list_mode":False}

    # main program loop
    while settings:
        raw_input = input("Enter a hexpattern, or 'S' for settings: ").lower().replace("_","")
        if(raw_input=="s"):
            (settings,registry) = configure_settings(settings,registry)
        elif(raw_input.startswith("[")):
            spell = raw_input[1:-1].split(", ")
            output_list = []
            settings["list_mode"] = True
            for pattern in spell:
                output_list.append(main(pattern,registry,settings))
            settings["list_mode"] = False
            print("-----\nThis spell consists of:")
            for name in output_list:
                print(name)
            print("-----")
        else:
            main(raw_input,registry,settings)
