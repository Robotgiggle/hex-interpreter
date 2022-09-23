import matplotlib.pyplot as plt
from matplotlib import colormaps
import pickle
import math

def convert_to_points(angle_sig,start_dir):
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

    # find the furthest distance from the start point, and apply some transformations to it
    # this value is used when drawing to scale the lines and points based on graph size
    max_width = max([max(x_vals)-min(x_vals),max(y_vals)-min(y_vals)])
    scale = 5/math.log(max_width,1.5)+1.1

    # draw a triangle to show where the pattern starts, using the start angle from ealier
    plt.plot(x_vals[1]/2.15,y_vals[1]/2.15,color=colormaps["cool"](0.999),marker=(3,0,start_angle),ms=(13/5)*scale)

    return (x_vals,y_vals,scale)

def parse_number(angle_sig,negative):
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
    if negative:
        output *= -1
    return "Number Literal ("+str(output)+")"

def parse_bookkeeper(angle_sig):
    if(angle_sig[:3]=="ada"):
        output = "vv"
        angle_sig = angle_sig[2:]
    else:
        output = "v-"
        angle_sig = angle_sig[1:]
    angle_sig += "z"
    for i in range(len(angle_sig)-1):
        if(angle_sig[i:i+3]=="ada" or angle_sig[i:i+3]=="eea" or angle_sig[i:i+3]=="wea"):
            output += "v"
            i += 1
        elif(angle_sig[i:i+2]=="ae" or angle_sig[i:i+2]=="ew" or angle_sig[i:i+2]=="ww"):
            output += "-"
    return "Bookkeeper's Gambit ("+output+")"

def dict_lookup(angle_sig,pattern_dict):
    try:
        output = pattern_dict[angle_sig]
        return output     
    except KeyError:
        return "Unknown"

def gs_lookup(x_vals,y_vals,great_spells):
    # convert the x and y lists into a single list of points
    points = []
    for i in range(len(x_vals)):
        points.append((x_vals[i],y_vals[i]))

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
        points[i] = (points[i][0]-lowest[0],points[i][1]-lowest[1])

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
        # if a pointset matches, return its associated great spell
        if same and len(entry[0])==len(points):
            return entry[1]
            break
    
    return "Unknown - unrecoginized pattern"

def plot_gradient(x_vals,y_vals,scale,line_count):
    colors = colormaps["cool"]
    for i in range(line_count):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors(1-i/line_count),lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale)

def plot_intersect(x_vals,y_vals,scale,line_count):
    used_points = []
    colors = [colormaps["cool"](1-c/3) for c in (0,1,2,3,2,1)]
    color_index = 0
    for i in range(line_count+1):
        point = (x_vals[i],y_vals[i],color_index)
        repeats = False

        # check if we've already been to this point, with this line color
        # doing this with if(j==point) doesn't work because of floating-point jank
        for j in used_points:
            if abs(point[0]-j[0])<0.1 and abs(point[1]-j[1])<0.1 and j[2]==point[2]:
                repeats = True
                used_points[used_points.index(j)] = (j[0],j[1],j[2]+1)

        # if the condition is true, cycle the line color to the next option
        # then draw a half-line backwards to mark the beginning of the new segment
        if repeats:
            color_index += 1
            color_index %= 6
            back_half = ((x_vals[i-1]+point[0])/2,(y_vals[i-1]+point[1])/2)
            plt.plot((point[0],back_half[0]),(point[1],back_half[1]),color=colors[color_index],lw=scale)

            # draw a triangle to mark the direction of the new color
            if(abs(y_vals[i]-y_vals[i-1])<0.1):
                if(x_vals[i]>x_vals[i-1]):
                    angle = 270
                else:
                    angle = 90
            elif(y_vals[i]>y_vals[i-1]):
                if(x_vals[i]>x_vals[i-1]):
                    angle = 330
                else:
                    angle = 30
            else:
                if(x_vals[i]>x_vals[i-1]):
                    angle = 210
                else:
                    angle = 150
            plt.plot(back_half[0],back_half[1],marker=(3,0,angle),color=colors[color_index],ms=2*scale)
        else:
            used_points.append(point)

        # only draw a line segement extending from the point if we're not at the end
        if(i!=line_count):
            plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors[color_index],lw=scale)

        # draw the point itself
        plt.plot(point[0],point[1],'ko',ms=2*scale)

def main():
    # create a square plot and hide the axes
    ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
    ax.set_aspect("equal")
    ax.axis("off")

    # load registry for pattern and great spell names
    try:
        with open("pattern_registry.pickle",mode="rb") as file:
            (pattern_dict,great_spells) = pickle.load(file)
        loaded = True
    except FileNotFoundError:
        print("Error - pattern registry not found")
        loaded = False

    # get the pattern to draw from the user
    raw_input = input("Enter hexpattern: ")
    choice = input("Gradient mode (y/n): ")

    # split input into angle signature and start direction
    try:
        space = raw_input.index(" ")
    except ValueError:
        space = len(raw_input)
        raw_input += " east"
    angle_sig = raw_input[:space]
    start_dir = raw_input[space+1:]

    # check for various special cases
    if(angle_sig[:4]=="aqaa"):
        result = parse_number(angle_sig,False)
    elif(angle_sig[:4]=="dedd"):
        result = parse_number(angle_sig,True)
    elif(angle_sig[:3]=="ada" or angle_sig[:2]=="ae"):
        result = parse_bookkeeper(angle_sig)
    elif(loaded):
        result = dict_lookup(angle_sig,pattern_dict)
    else:
        result = "Unknown - no pattern registry"

    (x_vals,y_vals,scale) = convert_to_points(angle_sig,start_dir)
    line_count = len(x_vals)-1
    
    # if no match was found for the pattern, check if it's a great spell
    if(result=="Unknown"):
        result = gs_lookup(x_vals,y_vals,great_spells)

    print("This pattern is: "+result)
    
    # run the selected draw function
    match choice:
        case "y":
            plot_gradient(x_vals,y_vals,scale,line_count)
        case "n":
            plot_intersect(x_vals,y_vals,scale,line_count)
        case _:
            print("Invalid choice, defaulting to no")
            plot_intersect(x_vals,y_vals,scale,line_count)

    # show the final image
    plt.show()

main()
