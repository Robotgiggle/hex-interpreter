import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from functools import partial
from os.path import isfile
import json

end_marker = [None]

def animate_pattern(f,anim_data,ax,settings):
    speed = 51-settings["anim_speed"]
    x_anim,y_anim,scale = anim_data
    global end_marker

    # starting point
    if x_anim[f] is None:
        end_marker = plt.plot(x_anim[1],y_anim[1],marker='o',ms=1.8*scale,mew=0.4*scale,mec="black",c="#ff6bff")
        
    # segment going into a point
    if f%speed == 1:
        ax.plot(x_anim[f-1:f+1],y_anim[f-1:f+1],c=settings["animated_colors"][1],lw=scale)
        ax.plot(x_anim[f],y_anim[f],marker='o',ms=1.8*scale,mew=0.4*scale,mec="black",c=settings["animated_colors"][1])
    # segment coming out of a point
    elif f%speed in (2,4):
        ax.plot(x_anim[f-1:f+1],y_anim[f-1:f+1],c=settings["animated_colors"][1],lw=scale)
        ax.plot(x_anim[f-f%speed+1],y_anim[f-f%speed+1],marker='o',ms=1.8*scale,mew=0.4*scale,mec="black",c=settings["animated_colors"][1])
    # all other segments
    else:
        ax.plot(x_anim[f-1:f+1],y_anim[f-1:f+1],c=settings["animated_colors"][1],lw=scale)

    # marker for current endpoint of animated line
    if x_anim[f]:
        end_marker[0].remove()
        end_marker = ax.plot(x_anim[f],y_anim[f],marker='h',ms=2.4*scale,mew=0.5*scale,mec=settings["animated_colors"][3],c=settings["animated_colors"][2])
        
def init_pattern(plot_data,settings):
    x_vals,y_vals,scale = plot_data[:3]

    # clear the canvas
    plt.cla()
    plt.gca().axis("off")

    # draw the full pattern in the background
    for i in range(len(x_vals)-1):
        plt.plot(x_vals[i:i+2],y_vals[i:i+2],c=settings["animated_colors"][0],lw=scale)
        plt.plot(x_vals[i],y_vals[i],'ko',ms=2*scale)
    plt.plot(x_vals[-1],y_vals[-1],'ko',ms=2*scale)
'''
def debug_init(plot_data,settings):
    plt.cla()
    plt.gca().axis("off")
    plt.plot(1,1,'go',2)

def debug_animate(f,anim_data):
    plt.plot(1+f,1,'go',2)
'''
def anim_interpolate(plot_data,speed):
    x_vals,y_vals,scale = plot_data[:3]
    x_anim,y_anim = [None],[None]
    
    # create five interpolated points after each point
    for i in range(len(x_vals)-1):
        x_dist = x_vals[i+1] - x_vals[i]
        y_dist = y_vals[i+1] - y_vals[i]

        x_anim += [x_vals[i]+x_dist*(1/speed)*j for j in range(speed)]
        y_anim += [y_vals[i]+y_dist*(1/speed)*j for j in range(speed)]

    # add the last point
    x_anim.append(x_vals[-1])
    y_anim.append(y_vals[-1])

    return x_anim,y_anim,scale

def plot_animated(plot_data,settings,ax):
    # convert basic pointlist into special version for animating
    anim_data = anim_interpolate(plot_data,51-settings["anim_speed"])

    # create animation object by repeatedly invoking animate_pattern()
    ani = FuncAnimation(plt.gcf(),
                        func=animate_pattern,
                        fargs=[anim_data,ax,settings],
                        frames=len(anim_data[0]),
                        init_func=partial(init_pattern,plot_data,settings),
                        interval=25,
                        repeat=True)
    return ani

if __name__ == "__main__":
    with open("settings.json",mode="r") as file:
        settings = json.load(file)

    from hex_draw import convert_to_points
    print("Displaying test animation...")
    plot_data = convert_to_points("qeewdweddw","northeast",settings)
    ax = plt.figure(figsize=(4,4)).add_axes([0,0,1,1])
    ax.set_aspect("equal")
    ani = plot_animated(plot_data,settings,ax)
    plt.show()
    print("Animation test complete.")
