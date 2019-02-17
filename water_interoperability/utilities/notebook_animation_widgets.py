from IPython.display import HTML, display, Image
from tempfile import NamedTemporaryFile
import matplotlib.pyplot as plt
plt.rcParams["animation.html"] = "jshtml"
import matplotlib.animation as animation
from skimage.transform import resize as imresize


def create_movie_on_np_array(frames,
                 title = "",
                 text=None,
                 fps=5,
                 width=10,
                 height=5,
                 align=True,
                 alphas=None, 
                 cmap = "Blues"):
    
    if text is None:
        text = ['' for s in range(len(frames))]
    
    ref_shape = frames[0].shape
    
    fig, ax = plt.subplots()
    ax.set_title = title + "\n" + text[0]
    
    ax.set_aspect('equal')
    ax.axis('off')
    
    im = ax.imshow(frames[0], cmap = cmap)
    _text = ax.text(20, 100, text[0], fontsize=14, color='white')
    im.set_clim([0,1])
    fig.set_size_inches([width,height])
    plt.tight_layout()
    
    def update_img(n):
        frame = imresize(frames[n], ref_shape, order=3)
    
        _text.set_text(text[n])
        im.set_data(frame)
        return im,
    
    def init():
        im.set_data(frames[0])
        return im,
       
    anim = animation.FuncAnimation(fig, update_img, len(frames), init_func=init, interval=1000);
        
    plt.close(anim._fig)
    return display(HTML(anim.to_jshtml()));