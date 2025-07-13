Project setup <span class="bullet">🟢</span>
=============

```{lit-setup}
:tangle-root: 000 - Project setup
```

*Resulting code:* [`step000`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step000)

In our running example, we use [CMake](https://cmake.org/) to organize the compilation of the code. This is a very standard way of handling cross-platform builds, and we follow the idioms of [modern cmake](https://cliutils.gitlab.io/modern-cmake/).

Requirements
------------

All we need is CMake and a C++ compiler, instructions are detailed below per OS.

```{hint}
After the installation, you can type `which cmake` (linux/macOS) or `where cmake` (Windows) to see whether your command line finds the full path to the `cmake` command. If not, make sure your `PATH` environment variable contains the directory where CMake is installed.
```

### Linux

If you are under an Ubuntu/Debian distribution, install the following packages:

```bash
sudo apt install cmake build-essential
```

Other distributions have equivalent packages, make sure you have the commands `cmake`, `make` and `g++` working.

### Windows

Download and install CMake from [the download page](https://cmake.org/download/). You may use either [Visual Studio](https://visualstudio.microsoft.com/downloads/) or [MinGW](https://www.mingw-w64.org/) as a compiler toolkit.

### MacOS

You can install CMake using `brew install cmake`, and [XCode](https://developer.apple.com/xcode/) to build the project.

Minimal project
---------------

The most minimal project consists then in a `main.cpp` source file, and a `CMakeLists.txt` build file.

Let us start with the classic hello world in `main.cpp`:

```{lit} C++, file: main.cpp
#include <iostream>

int main (int, char**) {
	std::cout << "Hello, world!" << std::endl;
	return 0;
}
```

In `CMakeLists.txt`, we specify that we want to create a *target* of type *executable*, called "App" (this will also be the name of the executable file), and whose source code is `main.cpp`:

```{lit} CMake, Define app target
add_executable(App main.cpp)
```

CMake also expects at the beginning of `CMakeLists.txt` to know the version of CMake the file is written for (minimum supported...your version) and some information about the project:

```{lit} CMake, file: CMakeLists.txt
cmake_minimum_required(VERSION 3.0...3.25)
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

We are now ready to build our minimal project. Open a terminal and go to the directory where you have the `CMakeLists.txt` and `main.cpp` files:

```bash
cd your/project/directory
```

```{hint}
From a Windows explorer window showing your project's directory, press Ctrl+L, then type `cmd` and hit return. This opens a terminal in the current directory.
```

Let us now ask CMake to create the build files for our project. We ask it to isolate the build files from our source code by placing them in a *build/* directory with the `-B build` option. This is very much recommended, in order to be able to easily distinguish these generated files from the ones we manually wrote (a.k.a. the source files):

```bash
cmake . -B build
```

This creates the build files for either `make`, Visual Studio or XCode depending on your system (you can use the `-G` options to force a particular build system, see `cmake -h` for more info). To finally build the program and generate the `App` (or `App.exe`) executable, you can either open the generated Visual Studio or XCode solution, or type in the terminal:

```bash
cmake --build build
```

Then run the resulting program:

```bash
build/App  # linux/macOS
build\Debug\App.exe  # Windows
```

Recommended extras
------------------

We set up some properties of the target `App` by calling somewhere after `add_executable` the `set_target_properties` command.

```{lit} CMake, Recommended extras
set_target_properties(App PROPERTIES
	CXX_STANDARD 17
	CXX_STANDARD_REQUIRED ON
	CXX_EXTENSIONS OFF
	COMPILE_WARNING_AS_ERROR ON
)
```

The `CXX_STANDARD` property is set to 17 to mean that we require C++17 (this will enable us to use some syntactic tricks later on, but is not mandatory per se). The `CXX_STANDARD_REQUIRED` property ensures that configuration fails if C++17 is not supported.

The `CXX_EXTENSIONS` property is set to `OFF` to disable compiler specific extensions (for example, on GCC this will make CMake use `-std=c++17` rather than `-std=gnu++17` in the list of compilation flags).

The `COMPILE_WARNING_AS_ERROR` is turned on as a good practice, to make sure no warning is left ignored. Warnings are actually important, especially when learning a new language/library. To make sure we even have as many warnings as possible, we add some compile options:

```{lit} CMake, Recommended extras (append)
if (MSVC)
	target_compile_options(App PRIVATE /W4)
else()
	target_compile_options(App PRIVATE -Wall -Wextra -pedantic)
endif()
```

```{note}
In the accompanying code, I hide these details in the `target_treat_all_warnings_as_errors()` function defined in `utils.cmake` and included at the beginning of the `CMakeLists.txt`.
```

On MacOS, CMake can generate XCode project files. However, by default, no *schemes* are
created, and XCode itself generates a scheme for each CMake target -- usually we only
want a scheme for our main target. Therefore, we set the `XCODE_GENERATE_SCHEME` property.
We will also already enable frame capture for GPU debugging.

```{lit} CMake, Recommended extras (append)
if (XCODE)
	set_target_properties(App PROPERTIES
		XCODE_GENERATE_SCHEME ON
		XCODE_SCHEME_ENABLE_GPU_FRAME_CAPTURE_MODE "Metal"
	)
endif()
```

Conclusion
----------

We now have a good **basic project configuration**, that we will build upon in the next chapters. In the next chapters, we will see how to [integrate WebGPU](hello-webgpu.md) to our project, how to [initialize it](adapter-and-device/index.md), and how to [open a window](opening-a-window.md) into which to draw.

*Resulting code:* [`step000`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step000)
