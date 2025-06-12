Project setup <span class="bullet">🟢</span>
=============

```{lit-setup}
:tangle-root: 000 - Project setup - Next
```

*Resulting code:* [`step000`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step000)

In the recurring example we build throughout the chapters of this guide, we use [CMake](https://cmake.org/) to organize the compilation of the code. This is a **very standard** way of handling **cross-platform builds** in C++, and we follow the idioms of [Modern CMake](https://cliutils.gitlab.io/modern-cmake/).

In this first chapter, we set up a very basic C++ project, with **one source file** and **one `CMakeLists.txt` file** to tell how to build it in a cross-platform way.

Requirements
------------

All we need to install is CMake and a C++ compiler, instructions are detailed below per OS.

```{hint}
**After the installation**, you can type `which cmake` (linux/macOS) or `where cmake` (Windows) to see whether your command line finds the full path to the `cmake` command. If not, make sure your `PATH` environment variable contains the directory where CMake is installed.
```

### Linux

If you are under an Ubuntu/Debian distribution, install the following packages:

```bash
sudo apt install cmake build-essential
```

Other distributions have equivalent packages, make sure you have the commands `cmake`, `make` and `g++` working.

### Windows

Download and install CMake from [the download page](https://cmake.org/download/). You may use either [Visual Studio](https://visualstudio.microsoft.com/downloads/) or [MinGW](https://www.mingw-w64.org/) as the C++ compiler toolkit.

### MacOS

You can install CMake using `brew install cmake`, and [XCode](https://developer.apple.com/xcode/) to build the project.

Minimal project
---------------

The most minimal project consists then in a `main.cpp` **source file**, and a `CMakeLists.txt` **build file**.

Let us start with the classic **hello world** in `main.cpp`:

```{lit} C++, file: main.cpp
// In file 'main.cpp'
#include <iostream>

int main (int, char**) {
	std::cout << "Hello, world!" << std::endl;
	return 0;
}
```

In `CMakeLists.txt`, we specify that we want to create a **target** of type **executable**, called "App" (this will also be the name of the executable file), and whose source code is `main.cpp`:

```{lit} CMake, Define app target
# In file 'CMakeLists.txt'
add_executable(App main.cpp)
```

CMake also expects at the beginning of `CMakeLists.txt` to know the version of CMake the file is written for (minimum supported...your version) and some information about the project:

```{lit} CMake, file: CMakeLists.txt
cmake_minimum_required(VERSION 3.16...3.30)
project(
	LearnWebGPU # name of the project, which will also be the name of the visual studio solution if you use it
	VERSION 0.1.0 # any version number
	LANGUAGES CXX C # programming languages used by the project
)

{{Define app target}}

{{Recommended extras}}
```

Building
--------

We are now ready to **build our minimal project**. Open a **terminal** and go to the directory where you have the `CMakeLists.txt` and `main.cpp` files:

```bash
cd your/project/directory
```

```{hint}
From a **Windows** file explorer showing your project's directory, press Ctrl+L, then type `cmd` and hit return. This **opens a terminal in the current directory**.
```

Let us now ask CMake to create the build files for our project. We ask it to **isolate the build files** from our source code by placing them in a `build/` directory with the `-B build` option. This way, we can easily **distinguish** the generated build files from the ones we manually wrote (a.k.a. the source files):

```bash
cmake . -B build
```

```{tip}
If you are using [`git`](https://git-scm.com/) to version your project (which I recommend), you may create a `.gitignore` file and add a line with `build/` in it to **prevent git from versioning** the generated build files.
```

After running the CMake command above, you should see a `build/` directory which contains either a `Makefile` for `make`, a `.sln` file for Visual Studio or an XCode project, depending on your system.

```{important}
Calling CMake just **_prepared_** the project for your compiler, but did not build anything. The idea is that our `CMakeLists.txt` file is the **source of truth** of compilation options, and CMake is able to adapt it to whichever platform you build for.
```

```{note}
You can use the `-G` options to **force a particular build system** (make, Visual Studio, XCode, ninja, etc.), see `cmake -h` for more info.
```

To finally **build** the program and generate the `App` (or `App.exe`) executable, you can either open the generated Visual Studio or XCode solution, or type in the terminal:

```bash
cmake --build build
```

Then **run** the resulting program:

```bash
build/App  # linux/macOS
build\Debug\App.exe  # Windows
```

You should see the **expected output**:

```
Hello, world!
```

Recommended extras
------------------

Good, we have a very minimal cross-platform C++ project running. Let us nonetheless **set up some key properties** of the target `App`.

```{important}
Some suggestions below are **specific** to a particular build tool (e.g., XCode, Visual Studio, emscripten, etc.). I recommend to **include all of them** even if you do not use that tool for now: it is harmless because we guard them with a proper `if ()` condition, and they **will come handy** the day you try to build for a different platform.
```

### C++ version

Somewhere **after** the `add_executable` statement in `CMakeLists.txt`, we call the `set_target_properties` command:

```{lit} CMake, Recommended extras
set_target_properties(App PROPERTIES
	CXX_STANDARD 17
	CXX_STANDARD_REQUIRED ON
	CXX_EXTENSIONS OFF
	COMPILE_WARNING_AS_ERROR ON
)
```

The `CXX_STANDARD` property is set to 17 to mean that we require **C++17** (this will enable us to use some syntactic tricks later on, but is not mandatory *per se*). The `CXX_STANDARD_REQUIRED` property ensures that configuration fails if C++17 is not supported.

The `CXX_EXTENSIONS` property is set to `OFF` to **disable compiler specific extensions** (for example, on GCC this will make CMake use `-std=c++17` rather than `-std=gnu++17` in the list of compilation flags). This will ease our **cross-platform development**.

The `COMPILE_WARNING_AS_ERROR` is turned on as a **good practice**, to make sure **no warning is left ignored**. Warnings are actually **important**, especially when learning a new language/library. To make sure we even have as many warnings as possible, we **add some compile options**:

```{lit} CMake, Recommended extras (append)
if (MSVC)
	target_compile_options(App PRIVATE /W4)
else()
	target_compile_options(App PRIVATE -Wall -Wextra -pedantic)
endif()
```

```{note}
In the **accompanying code**, I hid these details in the `target_treat_all_warnings_as_errors()` function defined in `utils.cmake` and included at the beginning of the `CMakeLists.txt`.
```

### XCode

When **CMake detects that we build with XCode**, the `XCODE` variable is turned on. We use this to set XCode-specific properties on our `App` target:

```{lit} CMake, Recommended extras (append)
if (XCODE)
	set_target_properties(App PROPERTIES
		XCODE_GENERATE_SCHEME ON
		XCODE_SCHEME_ENABLE_GPU_FRAME_CAPTURE_MODE "Metal"
	)
endif()
```

The `XCODE_GENERATE_SCHEME` instructs CMake to generate what XCode calls a **schema** for our target. If we do not set this up, CMake does not provide any schema, and in consequence XCode will generate one for each CMake target (including all our dependencies).

The `XCODE_SCHEME_ENABLE_GPU_FRAME_CAPTURE_MODE` property lets you run XCode's [Metal Debugger](https://developer.apple.com/documentation/xcode/metal-debugger) on our application. This may greatly help you on the long run, giving insights about what is happening on the GPU.

### Visual Studio

When using Visual Studio, we can **specify the default target** that builds and runs when pressing F5 (or hitting the "Run local debugger" button). This is done by setting the `VS_STARTUP_PROJECT` property of the project's root directory:

```{lit} CMake, Recommended extras (append)
# NB: This only works if put in the top-level CMakeLists.txt
set_directory_properties(PROPERTIES
	VS_STARTUP_PROJECT App
)
```

```{note}
No need to check that we are building with Visual Studio. **If we are not**, this directory property is just ignored.
```

### VS Code

When building with `make` or [`ninja`](https://ninja-build.org/) and editing the code with VS Code (and potentially some other text editors that rely on [LSP](https://microsoft.github.io/language-server-protocol/)), we can ask CMake to generate a `compile_commands.json` file that helps the text editor figure out how the project is organized:

```CMake
# In CMakeLists.txt before defining targets
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

Instead of hardcoding it into the CMakeList, you may prefer to specify it through the command line:

```bash
# Alternatively, specify this when configuring
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

```{note}
If you configure using the [CMake Tools](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cmake-tools) extension for VS Code, it should automatically turn `CMAKE_EXPORT_COMPILE_COMMANDS` on.
```

### Building for the Web

One nice benefits of using WebGPU as our graphics API is that we can **build our application to run in a Web page**.

````{note}
To get started with [Emscripten](https://emscripten.org/docs/getting_started/downloads.html) and **cross-compile our app to WebAssembly**, you can consult [the dedicated appendix](../appendices/building-for-the-web.md).

What you mostly need to remember is to wrap the first call to CMake in `emcmake`:

```
# Create a build-web directory in which we configured the project to build
# with emscripten. You may use any regular cmake command line option here.
emcmake cmake -B build-web
```
````

We add a section dedicated to emscripten-specific options at the end of our `CMakeLists.txt`:

```{lit} CMake, file: CMakeLists.txt (append)
# Options that are specific to Emscripten
if (EMSCRIPTEN)
    {{Emscripten-specific options}}
endif()
```

For now we only **change the output extension** so that it is an HTML web page (rather than a WebAssembly module or JavaScript library):

```{lit} CMake, Emscripten-specific options
# Generate a full web page rather than a simple WebAssembly module
set_target_properties(App PROPERTIES SUFFIX ".html")
```

```{note}
If you forget this, the cross-compilation will generate a `.wasm` and a `.js` file, but no `.html`.
```

Conclusion
----------

We now have a good **basic project configuration**, that we will build upon in the next chapters. In the next chapters, we will see how to [integrate WebGPU](hello-webgpu.md) to our project, how to [initialize it](adapter-and-device/index.md), and how to [open a window](opening-a-window.md) into which to draw.

*Resulting code:* [`step000`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step000)
