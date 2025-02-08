Using SDL for Window Management <span class="bullet">🟡</span>
===============================

````{tab} With webgpu.hpp
*Resulting code:* [`step030-sdl`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-sdl)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-sdl-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-sdl-vanilla)
````

The main part of this guide uses GLFW for window management because it is very lightweight. However, another popular choice is to use the [SDL](https://wiki.libsdl.org/SDL2/FrontPage) (*Simple DirectMedia Layer*).

The SDL has support for **Android and iOS** and brings other nice capabilities for writing video games, like **sound manipulation** for instance.

This appendix shows how to **replace GLFW with SDL2** on the simple example of the [Hello Triangle](../basic-3d-rendering/hello-triangle.md) chapter.

Dependencies
------------

Start by removing the `glfw` and `glfw3webgpu` directories. We replace them with their SDL equivalent:

 1. Download the source code of [the latest release of SDL](https://github.com/libsdl-org/SDL/releases/latest) (tested with 2.28.5), unzip it so that you have a file `SDL2/README-SDL.txt`.

 2. Download the equivalent of `glfw3webgpu` for SDL2, namely [`sdl2webgpu`](https://github.com/eliemichel/sdl2webgpu/archive/refs/heads/main.zip). Unzip it so that you have a file `sdl2webgpu/CMakeLists.txt`.

In the main `CMakeLists.txt`, replace GLFW with SDL2:

```diff
- add_subdirectory(glfw)
+ add_subdirectory(SDL2)
add_subdirectory(webgpu)
- add_subdirectory(glfw3webgpu)
+ add_subdirectory(sdl2webgpu)

add_executable(App
	main.cpp
)

- target_link_libraries(App PRIVATE glfw webgpu glfw3webgpu)
+ target_link_libraries(App PRIVATE SDL2::SDL2 webgpu sdl2webgpu)
```

Code
----

At the beginning of `main.cpp`, replace the inclusion of `GLFW` and `glfw3webgpu`:

```C++
#include <glfw3webgpu.h>
#include <GLFW/glfw3.h>
```

becomes:

```C++
#define SDL_MAIN_HANDLED
#include <sdl2webgpu.h>
#include <SDL2/SDL.h>
```

```{note}
Defining `SDL_MAIN_HANDLED` prevents SDL from creating its own `main` function, which would conflict with yours.
```

In the `main` function, replace call to `glfwInit()`:

```C++
// Remove
if (!glfwInit()) {
	std::cerr << "Could not initialize GLFW!" << std::endl;
	return 1;
}
```

becomes:

```C++
// Add
SDL_SetMainReady();
if (SDL_Init(SDL_INIT_VIDEO) < 0) {
	std::cerr << "Could not initialize SDL! Error: " << SDL_GetError() << std::endl;
	return 1;
}
```

```{note}
Calling `SDL_SetMainReady()` is needed when using `SDL_MAIN_HANDLED` instead of letting SDL automatically manage the main function.
```

Change the creation of the window:

```C++
// Remove
glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);
glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);
```

becomes:

```C++
// Add
int windowFlags = 0;
SDL_Window *window = SDL_CreateWindow("Learn WebGPU", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 640, 480, windowFlags);
```

Change the name of the function to get a surface:

```C++
// Remove
Surface surface = glfwGetWGPUSurface(instance, window);
```

becomes:

```C++
// Add
Surface surface = SDL_GetWGPUSurface(instance, window);
```

The main loop also changes:

```C++
// Remove
while (!glfwWindowShouldClose(window)) {
	glfwPollEvents();
	// [...]
}
```

becomes:

```C++
// Add
bool shouldClose = false;
while (!shouldClose) {

	// Poll events and handle them.
	// (contrary to GLFW, close event is not automatically managed, and there
	// is no callback mechanism by default.)
	SDL_Event event;
	while (SDL_PollEvent(&event))
	{
		switch (event.type)
		{
		case SDL_QUIT:
			shouldClose = true;
			break;

		default:
			break;
		}
	}

	// [...]
}
```

Finally, clean up is done this way:

```C++
// Remove
glfwDestroyWindow(window);
glfwTerminate();
```

becomes:

```C++
// Add
SDL_DestroyWindow(window);
SDL_Quit();
```

Conclusion
----------

You now have a good base to work with SDL. If you want to port a more advanced chapter, you may need to adapt the event handling to have SDL event trigger the callback we used to pass to GLFW (like window resize, mouse move, click, keyboard, etc.).

```{important}
Let me know if sdl2webgpu does not work on your platform as I did not intensively check yet. I also did not adapt it to Android and iOS yet.
```

````{tab} With webgpu.hpp
*Resulting code:* [`step030-sdl`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-sdl)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-sdl-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-sdl-vanilla)
````
