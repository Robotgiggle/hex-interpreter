import matplotlib.pyplot as plt
from matplotlib import colormaps
import math

def parse(raw_input):
    unit = math.pi/3
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
        x += math.cos(angle)
        y += math.sin(angle)
        x_vals.append(x)
        y_vals.append(y)
    return (x_vals,y_vals)

def plot_gradient(x_vals,y_vals,max_width,lines):
    colors = colormaps["cool"]
    for i in range(lines):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors(1-i/lines),lw=5/math.log(max_width,1.5)+1.1)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=10/math.log(max_width,1.5)+2.2)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=10/math.log(max_width,1.5)+2.2)

def plot_intersect(x_vals,y_vals,max_width,lines):
    used_points = []
    colors = [colormaps["cool"](1-c/3) for c in (0,1,2,3,2,1)]
    color_index = 0
    for i in range(lines):
        point = (x_vals[i],y_vals[i],color_index)
        repeats = False
        for j in used_points:
            if abs(point[0]-j[0])<0.1 and abs(point[1]-j[1])<0.1 and j[2]==color_index:
                repeats = True
                used_points[used_points.index(j)] = (j[0],j[1],j[2]+1)
        if repeats:
            color_index += 1
            color_index %= 6
            back_half = ((x_vals[i-1]+point[0])/2,(y_vals[i-1]+point[1])/2)
            plt.plot((point[0],back_half[0]),(point[1],back_half[1]),color=colors[color_index],lw=5/math.log(max_width,1.5)+1.1)
            plt.plot(back_half[0],back_half[1],marker="h",color=colors[color_index],ms=7.5/math.log(max_width,1.5)+2.2)
        else:
            used_points.append(point)
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=colors[color_index],lw=5/math.log(max_width,1.5)+1.1)
        plt.plot(point[0],point[1],'ko',ms=10/math.log(max_width,1.5)+2.2)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=10/math.log(max_width,1.5)+2.2)

def main():
    (x_vals,y_vals) = parse(input("Enter hexpattern: "))
    choice = input("Intersect mode (y/n): ")
    max_width = max([max(x_vals)-min(x_vals),max(y_vals)-min(y_vals)])
    lines = len(x_vals)-1
    ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
    ax.set_aspect("equal")
    ax.axis("off")
    match choice:
        case "n":
            plot_gradient(x_vals,y_vals,max_width,lines)
        case "y":
            plot_intersect(x_vals,y_vals,max_width,lines)
        case _:
            print("Invalid choice, defaulting to no")
            plot_gradient(x_vals,y_vals,max_width,lines) 
    plt.show()

main()
