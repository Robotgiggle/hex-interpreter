import matplotlib.pyplot as plt
from matplotlib import colormaps
import math

def parse(raw_input):
    unit = math.pi/3
    # separate the input string into a turn list and a start direction
    letters = raw_input[:raw_input.index(" ")]
    start = raw_input[raw_input.index(" ")+1:]
    match start:
        case "east":
            x=1
            y=0
            angle = 0
        case "west":
            x=-1
            y=0
            angle = 0
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
            print("Invalid start direction, defaulting to east")
            x=1
            y=0
            angle = 0
    # initialize the x and y lists with the first two points
    # these are always (0,0) and the endpoint of the first line
    x_vals = [0,x]
    y_vals = [0,y]
    for char in letters:
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
                print("Invalid char, defaulting to w")
        # convert from polar to cartesian coordinates
        # then add the new point to the x and y lists
        x += math.cos(angle)
        y += math.sin(angle)
        x_vals.append(x)
        y_vals.append(y)
    return (x_vals,y_vals)

def plot_gradient(x_vals,y_vals,scale,line_count):
    colors = colormaps["cool"]
    for i in range(line_count):
        # create the pattern segment-by-segment, so the color gradient can be applied
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors(1-i/line_count),lw=scale+1.1)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale+2.2)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale+2.2)

def plot_intersect(x_vals,y_vals,scale,line_count):
    used_points = []
    colors = [colormaps["cool"](1-c/3) for c in (0,1,2,3,2,1)]
    color_index = 0
    for i in range(lines+1):
        point = (x_vals[i],y_vals[i],color_index)
        repeats = False
        # check if we've already been to this point, with this line color
        # doing this with if(j==point) doesn't work because of floating-point jank
        for j in used_points:
            if abs(point[0]-j[0])<0.1 and abs(point[1]-j[1])<0.1 and j[2]==color_index:
                repeats = True
                used_points[used_points.index(j)] = (j[0],j[1],j[2]+1)
        # if the condition is true, cycle the line color to the next option
        # then draw a half-line backwards to mark the beginning of the new segment
        if repeats:
            color_index += 1
            color_index %= 6
            back_half = ((x_vals[i-1]+point[0])/2,(y_vals[i-1]+point[1])/2)
            plt.plot((point[0],back_half[0]),(point[1],back_half[1]),color=colors[color_index],lw=scale+1.1)
            plt.plot(back_half[0],back_half[1],marker="h",color=colors[color_index],ms=1.5*scale+2.2)
        else:
            used_points.append(point)
        # only draw a line segement if we're not at the final point
        if(i!=line_count):
            plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors[color_index],lw=scale+1.1)
        # here's the final point itself
        plt.plot(point[0],point[1],'ko',ms=2*scale+2.2)

def main():
    (x_vals,y_vals) = parse(input("Enter hexpattern: "))
    line_count = len(x_vals)-1
    choice = input("Intersect mode (y/n): ")
    # find the furthest distance from the start point, and apply some transformations to it
    # this value is used to scale the lines and points based on graph size
    max_width = max([max(x_vals)-min(x_vals),max(y_vals)-min(y_vals)])
    scale = 5/math.log(max_width,1.5)
    # create a square plot and hide the axes
    ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
    ax.set_aspect("equal")
    ax.axis("off")
    match choice:
        case "n":
            plot_gradient(x_vals,y_vals,scale,line_count)
        case "y":
            plot_intersect(x_vals,y_vals,scale,line_count)
        case _:
            print("Invalid choice, defaulting to no")
            plot_gradient(x_vals,y_vals,scale,line_count) 
    plt.show()

main()
