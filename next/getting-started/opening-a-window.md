Opening a window
================

```{lit-setup}
:tangle-root: 001 - Opening a window - next
:parent: 000 - Project setup - next
:fetch-files: ../data/glfw.zip
```

*Resulting code:* [`step001`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001)

```{note}
When using Dawn, make sure to add the `webgpu` directory **after** you add `glfw`, otherwise Dawn provides its own version (which may be fine sometimes, but you don't get to chose the version).
```

Before being able to render anything on screen, we need to ask the Operating System to hand us some place where to draw things, something commonly known as a **window**.

Unfortunately, the process to open a window depends a lot on the OS, so we use a little library called [GLFW](https://www.glfw.org/) which unifies the different window management APIs and enables our code to be **agnostic** in the OS.

```{note}
I try to use as little libraries as I can, but this one is required to make our code cross-platform, which feels even more important to me than writing code from scratch. It is furthermore a very common choice and quite minimal in its design.
```

```{admonition} Headless mode
WebGPU **does not require a window** to work actually, it may also run headless. Since this is not a use case as common as drawing in a window, I leave the details of this option to [a dedicated chapter](../advanced-techniques/headless.md) of the advanced section.
```

```{admonition} SDL
Another popular choice for window management is the SDL library. It is not as lightweight as GLFW but provides more features, like support for sound and Android/iOS targets. [A dedicated appendix](../appendices/using-sdl.md) shows what to change to the main guide when using SDL.
```

Installation of GLFW
--------------------

We do **not need to install** it, we just need to add the code of GLFW to our project directory. Download the file [glfw.zip](../data/glfw.zip) (621 KB) and **unzip** it in your project. This is a stripped down version of the official release where I removed documentation, examples and tests so that it is more **lightweight**.

To integrate GLFW in your project, we first add its directory to our root `CMakeLists.txt`:

```{lit} CMake, Dependency subdirectories (insert in {{Define app target}} before "add_executable")
add_subdirectory(glfw)
```

```{important}
The name 'glfw' here designate the directory where GLFW is located, so there should be a file `glfw/CMakeLists.txt`. Otherwise it means that `glfw.zip` was not decompressed in the correct directory; you may either move it or adapt the `add_subdirectory` directive.
```

Then, we must tell CMake to link our application to this library (after `add_executable(App main.cpp)`):

```{lit} CMake, Link libraries (insert in {{Define app target}} after "add_executable")
target_link_libraries(App PRIVATE glfw)
```

```{tip}
This time, the name 'glfw' is one of the *target* defined in `glfw/CMakeLists.txt` by calling `add_library(glfw ...)`, it is not related to a directory name.
```

You should now be able to build the application and add `#include <GLFW/glfw3.h>` at the beginning of the main file.

```{lit} C++, Includes (hidden)
#include <iostream>
#include <GLFW/glfw3.h>
```

If you are on a linux system, make sure to install the package `xorg-dev`, which GLFW depends on.

Basic usage
-----------

First of all, any call to the GLFW library must be between its initialization and termination:

```{lit} C++, Main Content
glfwInit();
{{Use GLFW}}
glfwTerminate();
```

The init function returns false when it could not setup things up:

```{lit} C++, Use GLFW
if (!glfwInit()) {
	std::cerr << "Could not initialize GLFW!" << std::endl;
	return 1;
}
{{Create and destroy window (hidden)}}
```

Once the library has been initialized, we may create a window:

```{lit} C++, Create and destroy window
// Create the window
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);

{{Use the window}}

// At the end of the program, destroy the window
glfwDestroyWindow(window);
```

Here again, we may add some error management:

```{lit} C++, Use the window
if (!window) {
	std::cerr << "Could not open window!" << std::endl;
	glfwTerminate();
	return 1;
}
{{Main loop (hidden)}}
```

At this point, the window opens and closes immediately after. To address this, we add the application's **main loop**:

```{lit} C++, Main loop
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

```{lit} C++, file: main.cpp (hidden)
{{Includes}}

int main (int, char**) {
    {{Main Content}}
    return 0;
}
```

The Surface
-----------

```{lit-setup}
:tangle-root: 010 - The Adapter - Part B - next
:parent: 010 - The Adapter - Part A - next
:fetch-files: ../data/glfw3webgpu-v1.1.0.zip
```

We actually need to pass an option to the adapter request: the **surface** onto which we draw.

```{lit} C++, Request adapter (replace)
{{Get the surface}}

WGPURequestAdapterOptions adapterOpts = {};
adapterOpts.nextInChain = nullptr;
adapterOpts.compatibleSurface = surface;

WGPUAdapter adapter = requestAdapter(instance, &adapterOpts);
```

How do we get the surface? This depends on the OS, and GLFW does not handle this for us, for it does not know WebGPU (yet?). So I provide you this function, in a little extension to GLFW3 called [`glfw3webgpu`](https://github.com/eliemichel/glfw3webgpu).

### GLFW3 WebGPU Extension

Download and unzip [glfw3webgpu.zip](https://github.com/eliemichel/glfw3webgpu/releases/download/v1.1.0/glfw3webgpu-v1.1.0.zip) in your project's directory. There should now be a directory `glfw3webgpu` sitting next to your `main.cpp`. Like we have done before, we can add this directory and link the target it creates to our App:

```{lit} CMake, Dependency subdirectories (append)
add_subdirectory(glfw3webgpu)
```

```{lit} CMake, Link libraries (replace)
target_link_libraries(App PRIVATE glfw webgpu glfw3webgpu)
target_copy_webgpu_binaries(App)
```

```{note}
The `glfw3webgpu` library is very simple, it is only made of 2 files so we could have almost included them directly in our project's source tree. However, it requires some special compilation flags in macOS that we would have had to deal with (you can see them in the `CMakeLists.txt`).
```

You can now `#include <glfw3webgpu.h>` at the beginning of your `main.cpp` and get the surface by simply doing:

```{lit} C++, Get the surface
WGPUSurface surface = glfwGetWGPUSurface(instance, window);
```

```{lit} C++, Includes (append, hidden)
#include <glfw3webgpu.h>
```

Also don't forget to release the surface at the end:

```{lit} C++, Destroy surface
wgpuSurfaceRelease(surface);
```

```{lit} C++, Destroy things (replace, hidden)
{{Destroy surface}}
{{Destroy adapter}}
{{Destroy WebGPU instance}}
```

One last thing: we can **tell GLFW not to care about the graphics API** setup, as it does not know WebGPU and we won't use what it could set up by default for other APIs:

```{lit} C++, Create window
glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API); // NEW
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);
```

```{lit} C++, Create things (prepend, hidden)
glfwInit();
{{Create window}}
```

```{lit} C++, Main body (replace, hidden)
{{Main loop}}
```

```{lit} C++, Destroy things (append, hidden)
glfwDestroyWindow(window);
glfwTerminate();
```

The `glfwWindowHint` function is a way to pass optional arguments to `glfwCreateWindow`. Here we tell it to initialize no particular graphics API by default, as we manage this ourselves.

```{tip}
I invite you to look at the documentation of GLFW to know more about [`glfwCreateWindow`](https://www.glfw.org/docs/latest/group__window.html#ga3555a418df92ad53f917597fe2f64aeb) and other related functions.
```

*Resulting code:* [`step001`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001)
