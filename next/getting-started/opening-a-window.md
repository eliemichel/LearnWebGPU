Opening a window
================

```{lit-setup}
:tangle-root: 020 - Opening a window - next
:parent: 015 - The Command Queue - next
:fetch-files: ../data/glfw.zip ../data/glfw3webgpu-v1.1.0.zip
```

*Resulting code:* [`step020-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020-next)

Before being able to render anything on screen, we need to ask the Operating System (OS) to hand us some place where to draw things, something commonly known as a **window**.

The process to open a window **depends a lot on the OS**, so we use a little library called [GLFW](https://www.glfw.org/) which unifies the different window management APIs and enables our code to be **agnostic** in the OS.

```{note}
I try to use as few libraries as I can, but this one is required to **make our code cross-platform**, which feels even more important to me than writing code from scratch. GLFW is furthermore **a very common choice** and quite minimal in its design.
```

```{admonition} Headless mode
WebGPU **does not require a window** to draw things actually, it may run headless and draw to offscreen textures. Since this is not a use case as common as drawing in a window, I leave the details of this option to [a dedicated chapter](../advanced-techniques/headless.md) of the advanced section.
```

```{admonition} SDL
**Another popular choice** for window management is the **SDL library**. It is not as lightweight as GLFW but provides more features, like support for sound and Android/iOS targets. [A dedicated appendix](../appendices/using-sdl.md) shows what to change to the main guide when using SDL.
```

Installation of GLFW
--------------------

We do **not really need to install** it, we just need to add the code of GLFW to our project directory. Download the file [glfw.zip](../data/glfw.zip) (621 KB) and **unzip** it in your project. This is a stripped down version of the official release where I removed documentation, examples and tests so that it is more **lightweight**.

To integrate GLFW in your project, we first add its directory to our root `CMakeLists.txt`:

```{lit} CMake, Dependency subdirectories (prepend)
if (NOT EMSCRIPTEN)
	add_subdirectory(glfw)
endif()
```

```{note}
When using **Dawn**, make sure to add the `glfw` directory **before** you add `webgpu`, otherwise Dawn provides its own version (which may be fine sometimes, but you don't get to chose the version). When using **Emscripten**, GLFW is handled by the compiler itself.
```

Then, we must tell CMake to link our application to this library, like we did for webgpu:

```{lit} CMake, Link libraries (replace)
# Add the 'glfw' target as a dependency of our App
target_link_libraries(App PRIVATE webgpu glfw)
```

You should now be able to build the application and add `#include <GLFW/glfw3.h>` at the beginning of the main file.

```{lit} C++, Includes (append)
#include <GLFW/glfw3.h>
```

```{important}
If you are on a **linux** system, make sure to install the package `xorg-dev`, which GLFW depends on.
```

Basic usage
-----------

### Initialization

First of all, any call to the GLFW library must be between its initialization and termination:

```{lit} C++, Main Content
glfwInit();
{{Use GLFW}}
glfwTerminate();
```

The init function returns **false** when it could not setup things up:

```{lit} C++, Use GLFW
if (!glfwInit()) {
	std::cerr << "Could not initialize GLFW!" << std::endl;
	return 1;
}
{{Create and destroy window (hidden)}}
```

Once the library has been initialized, we may **create a window**:

```{lit} C++, Create and destroy window
// Create the window
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);

{{Use the window}}

// At the end of the program, destroy the window
glfwDestroyWindow(window);
```

Here again, we may add some **error management**:

```{lit} C++, Use the window
if (!window) {
	std::cerr << "Could not open window!" << std::endl;
	glfwTerminate();
	return 1;
}
{{Main loop (hidden)}}
```

### Main loop

At this point, the window opens and **closes immediately** after. To address this, we add the application's **main loop** just before all the release/destroy/terminate calls:

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

```{warning}
This main loop will **not work** with **Emscripten**. In a Web page, the main loop is handled by the browser and we just tell it **what to call at each frame**.
```

Application class
-----------------

### Refactor

Let us **reorganize a bit our project** so that it is more Web-friendly and clearer about the **initialization** versus **main loop** separation.

We create functions `Initialize()`, `MainLoop()` and `Terminate()` to split up the three key parts of our program. We also put **all the variables** that these functions share in a common class/struct, that we call for instance `Application`. For better readability, we may have `Initialize()`, `MainLoop()` and `Terminate()` be members of this class:

```{lit} C++, Application class
class Application {
public:
	// Initialize everything and return true if it went all right
	bool Initialize();

	// Uninitialize everything that was initialized
	void Terminate();

	// Draw a frame and handle events
	void MainLoop();

	// Return true as long as the main loop should keep on running
	bool IsRunning();

private:
	// We put here all the variables that are shared between init and main loop
	{{Application attributes}}
};
```

Our main function becomes as simple as this:

```{lit} C++, main function
int main() {
	Application app;

	if (!app.Initialize()) {
		return 1;
	}

	// Warning: this is still not Emscripten-friendly
	while (app.IsRunning()) {
		app.MainLoop();
	}

	return 0;
}
```

And we can now move almost all our current code to `Initialize()`. The only thing that belongs to `MainLoop()` for now is the polling of GLFW events and WebGPU device:

```{lit} C++, main function
bool Application::Initialize() {
	// [...] Move the whole initialization here
	return true;
}

void Application::Terminate() {
	// [...] Move all the release/destroy/terminate calls here
}

void Application::MainLoop() {
	glfwPollEvents();

	// Also move here the tick/poll but NOT the emscripten sleep
#if defined(WEBGPU_BACKEND_DAWN)
	wgpuDeviceTick(device);
#elif defined(WEBGPU_BACKEND_WGPU)
	wgpuDevicePoll(device, false, nullptr);
#endif
}

bool Application::IsRunning() {
	return !glfwWindowShouldClose(window);
}
```

```{important}
So **not** move the `emscripten_sleep(100)` line to `MainLoop()`. This line is no longer needed once we **let the browser handle** the main loop, because the browser ticks its WebGPU backend itself.
```

Once you have move everything, you should end up with the following class attributes shared across init/main:

```{lit} C++, Application attributes

```

### Emscripten

The Surface
-----------

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

*Resulting code:* [`step020-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020-next)
