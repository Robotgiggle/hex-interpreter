import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from functools import partial
from os.path import isfile
import json

def animate_pattern(f,anim_data):
    x_anim,y_anim,scale = anim_data

    # starting point
    if x_anim[f] is None:
        plt.plot(x_anim[1],y_anim[1],marker='o',ms=1.8*scale,mew=0.4*scale,mec="black",c="#ff6bff")

    # segment going into a point
    if f%5 == 1:
        plt.plot(x_anim[f-1:f+1],y_anim[f-1:f+1],c="#ff6bff",lw=scale)
        plt.plot(x_anim[f],y_anim[f],marker='o',ms=1.8*scale,mew=0.4*scale,mec="black",c="#ff6bff")
    # segment coming out of a point
    elif f%5 == 2:
        plt.plot(x_anim[f-1:f+1],y_anim[f-1:f+1],c="#ff6bff",lw=scale)
        plt.plot(x_anim[f-1],y_anim[f-1],marker='o',ms=1.8*scale,mew=0.4*scale,mec="black",c="#ff6bff")
    # all other segments
    else:
        plt.plot(x_anim[f-1:f+1],y_anim[f-1:f+1],c="#ff6bff",lw=scale)
        
def init_pattern(plot_data,settings):
    x_vals,y_vals,scale = plot_data[:3]

    # clear the canvas
    plt.cla()
    plt.gca().axis("off")

    # draw the full pattern in the background
    for i in range(len(x_vals)-1):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],color=settings["monochrome_color"],lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale)

def anim_interpolate(plot_data):
    x_vals,y_vals,scale = plot_data[:3]
    x_anim,y_anim = [None],[None]
    
    # create five interpolated points after each point
    for i in range(len(x_vals)-1):
        x_dist = x_vals[i+1] - x_vals[i]
        y_dist = y_vals[i+1] - y_vals[i]

        x_anim += [x_vals[i]+x_dist*0.20*j for j in range(5)]
        y_anim += [y_vals[i]+y_dist*0.20*j for j in range(5)]

    # add the last point
    x_anim.append(x_vals[-1])
    y_anim.append(y_vals[-1])

    return x_anim,y_anim,scale

def plot_animated(plot_data,settings,):
    # convert basic pointlist into special version for animating
    anim_data = anim_interpolate(plot_data)
    
    # create animation object by repeatedly invoking animate_pattern()
    ani = FuncAnimation(plt.gcf(),
                        func=animate_pattern,
                        fargs=[anim_data],
                        frames=len(anim_data[0]),
                        init_func=partial(init_pattern,plot_data,settings),
                        interval=200,
                        repeat=True)

    return ani

if __name__ == "__main__":
    with open("settings.json",mode="r") as file:
        settings = json.load(file)

    from hex_draw import convert_to_points
    plot_data = convert_to_points("aqqqqq","east",settings)
    ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
    ax.set_aspect("equal")
    plot_animated(plot_data,settings)
