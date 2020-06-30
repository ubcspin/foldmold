Note: you may need to change version numbers, i.e., 3.7 -> 3.8, or 2.81 -> 2.90. Although 3.8 is giving some segfaults.

## Pre-requisite
1. Xcode (>=8.5)
2. Python 3.7 (In `/Library/Frameworks/Python.framework/Versions/3.7`)
	I personally downloaded a new one on my machine globally [here](https://www.python.org/downloads/mac-osx/) 
Note that you may need to install specific command line tools for xcode if SVN blows up. 

```
sudo rm -rf /Library/Developer/CommandLineTools xcode-select --install
```
Always be careful with `sudo` and `rm -rf`.

If that fails with an SVN error again, try `brew install svn`.


## Compilation
(Reference [here](https://wiki.blender.org/wiki/Building_Blender/Mac) & [here](https://wiki.blender.org/wiki/Building_Blender/Other/BlenderAsPyModule))

### Download Sources and Libraries
Now you are ready to get the latest Blender source code from Blender.org's Git repository. Copy and paste the following instructions into a terminal window. These will create a blender-git folder off your home directory and download the latest source code, as well as addons and external libraries.
```
mkdir ~/blender-git
cd ~/blender-git
git clone https://git.blender.org/blender.git
cd blender
make update
```
### Building python module
Make a directory: `mkdir ~/blender-git/build_bpy_darwin`
```
cd ~/blender-git/build_bpy_darwin
cmake ../blender -DWITH_PLAYER=OFF -DWITH_PYTHON_INSTALL=OFF -DWITH_PYTHON_MODULE=ON -DWITH_OPENMP=OFF -DWITH_AUDASPACE=OFF
```
According to various [posts](https://devtalk.blender.org/t/macos-blender-as-a-python-module-build-errors/10165/9), we need to disable `WITH_OPENMP` and `WITH_AUDASPACE` in addition to the ones that blender documentation points out.
Then run
```
make  install
```

## Install python module
Copy needed files to your python framework
```
cp ./bin/bpy.so /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages/
mkdir -p /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/Resources
cp -R ./bin/2.81 /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/Resources/
```
### Testing
I used 
```
alias python37="usr/local/bin/python3.7"
```
Then we can test installation by
```
python37 -c "import bpy; bpy.context.scene.render.engine = 'CYCLES'; bpy.ops.render.render(write_still=True)
```

## Adding svglib to Blender's python
```
cd /path/to/blender/python/bin
./pythonX.XX -m ensurepip
./pythonX.XX -m pip install svglib
```
where XX.X should be replaced by the version number. In my setup it looks like:

```
cd /Applications/Blender.app/Contents/Resources/2.82/python/bin
./python3.7m -m ensurepip
./python3.7m -m pip install svglib
```

Once that's run, you can run this from anywhere for any new package:

```
/Applications/Blender.app/Contents/Resources/2.82/python/bin/python3.7m -m pip install <packagename>
```

### Trouble shooting
I ran into segmentation fault with 
```
Python 3.7.6 (default, Jan  8 2020, 13:42:34)
[Clang 4.0.1 (tags/RELEASE_401/final)] :: Anaconda, Inc. on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import bpy
fish: Job 2, 'python3  $argv' terminated by signal SIGSEGV (Address boundary error)
```
if I copy this into Anaconda virtual environment (the same issue from [this post](https://github.com/TylerGubala/blenderpy/issues/2#issuecomment-610899632)) Working from the system python resolves the issue.

Segfault persists with Python 3.8.
