Opening a window
================

*Resulting code:* [`step001`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001)

Before being able to render anything on screen, we need to ask the Operating System to hand us some place where to draw things, something commonly known as a **window**.

Unfortunately, the process to open a window depends a lot on the OS, so we use a little library called [GLFW](https://www.glfw.org/) which unifies the different window management APIs and enables our code to be **agnostic** in the OS.

```{note}
I try to use as little libraries as I can, but this one is required to make our code cross-platform, which feels even more important to me than writing code from scratch. It is furthermore a very common choice and quite minimal in its design.
```

Installation of GLFW
--------------------

We do **not need to install** it, we just need to add the code of GLFW to our project directory. Download the file [glfw.zip](../data/glfw.zip) (621 KB) and **unzip** it in your project. This is a stripped down version of the official release where I removed documentation, examples and tests so that it is more **lightweight**.

To integrate GLFW in your project, we first add its directory to our root `CMakeLists.txt`:

```CMake
add_subdirectory(glfw)
```

```{important}
The name 'glfw' here designate the directory where GLFW is located, so there should be a file `glfw/CMakeLists.txt`. Otherwise it means that `glfw.zip` was not decompressed in the correct directory; you may either move it or adapt the `add_subdirectory` directive.
```

Then, we must tell CMake to link our application to this library (after `add_executable(App main.cpp)`):

```CMake
target_link_libraries(App PRIVATE glfw)
```

```{tip}
This time, the name 'glfw' is the one of the *target* defined in `glfw/CMakeLists.txt` by calling `add_library(glfw ...)`, it is not related to a directory name.
```

You should now be able to build the application and add `#include <GLFW/glfw3.h>` at the beginning of the main file.

If you are on a linux system, make sure to install the package `xorg-dev`, which GLFW depends on.

Basic usage
-----------

First of all, any call to the GLFW library must be between its initialization and termination:

```C++
glfwInit();
// [...] Use GLFW
glfwTerminate();
```

The init function returns false when it could not setup things up:

```C++
if (!glfwInit()) {
	std::cerr << "Could not initialize GLFW!" << std::endl;
	return 1;
}
```

Once the library has been initialized, we may create a window:

```C++
glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);
// [...] Use the window
glfwDestroyWindow(window);
```

The `glfwWindowHint` function is a way to pass optional arguments to `glfwCreateWindow`. Here we tell it to initialize no particular graphics API by default, as we manage this ourselves.

```{tip}
I invite you to look at the documentation of GLFW to know more about [`glfwCreateWindow`](https://www.glfw.org/docs/latest/group__window.html#ga3555a418df92ad53f917597fe2f64aeb) and other related functions.
```

Here again, we may add some error management:

```C++
if (!window) {
	std::cerr << "Could not open window!" << std::endl;
	glfwTerminate();
	return 1;
}
```

At this point, the window opens and closes immediately after. To address this, we add the application's **main loop**:

```C++
while (!glfwWindowShouldClose(window)) {
	// Check whether the user clicked on the close button (and any other
	// mouse/key event, which we don't use so far)
	glfwPollEvents();
}
```

```{note}
This main loop is where most of the application's logic occurs. We will repeatedly clear and redraw the whole image, and check for new user input.
```

```{figure} /images/glfw-boilerplate.png
:align: center
:class: with-shadow
Our first window, using the GLFW library.
```

*Resulting code:* [`step001`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001)
