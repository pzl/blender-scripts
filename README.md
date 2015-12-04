This is currently a (unorganized) collection of python scripts I'm putting together for blender.


I am new to blender in general, not just scripting of blender, but all of the program itself. So some of these things may be unoptimal or the "wrong way" to do it in blender. I would be happy to take any corrections and updates on the better blender way to accomplish some of these.

As well, I haven't looked too much into blender script conventions in general, so these scripts may not follow usual blender script guidelines. Also happy to adapt to those, given some examples or documentation to follow.

Some of these may also be better accomplished by not using scripts, but rather templates or custom startup files, or linking in things from saved blender files..

But this way it seems most distributable, and most explicit about what settings have been changed (as opposed to loading a custom startup file without knowing exactly what has been set up).



caption.py
----------

This is intended to be run once, as a sort of a custom startup file for a specific workflow: captioning movies. This actually started as a `.blend` file I would load as a startup file, that just sets up the camera for adding orthographic 2D text to footage, speeds up render settings for extremely simple objects, and sets up the compositor to overlay the text.

Once run, load up the movie clip editor, add your footage, do any tracking necessary, set as background to the 3D camera view. Then create and animate the text as necessary. There is a checkbox in the compositor node tree for optionally blurring the text shadow.


materials.py
------------

Running this will simply create several material node groups. They can be accessed in the materials node editor with add > Group > [Group Name].

These are physically-based materials pulled from the tutorials by [CynicatPro](https://www.youtube.com/channel/UCqoc1p9ov0CwzvKObvrKxMA) on youtube. The specific videos are referenced in the code.
