This is currently a (unorganized) collection of python scripts I'm putting together for blender.

Some of these may be better accomplished by not using scripts, but rather templates or custom startup files, or linking in things from saved blender files..

But this way it seems most distributable, and most explicit about what settings have been changed (as opposed to loading a custom startup file without knowing exactly what has been set up).



caption.py
----------

This is a handy module to make quick work of setting up simple colored text captions, as you might see in some gifs. It creates simple materials for fast rendering, and does repetitive scene and camera settings for you. It allows you to use Blender Internal or Cycles seamlessly.

Once run, load up the movie clip editor, add your footage, do any tracking necessary, set as background to the 3D camera view. Then create and animate the text as necessary. There is a checkbox in the compositor node tree for optionally blurring the text shadow.


materials.py
------------

Running this will simply create several material node groups. They can be accessed in the materials node editor with add > Group > [Group Name].

These are physically-based materials pulled from the tutorials by [CynicatPro](https://www.youtube.com/channel/UCqoc1p9ov0CwzvKObvrKxMA) on youtube. The specific videos are referenced in the code.
