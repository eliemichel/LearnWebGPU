Opening a window <span class="bullet">🔴</span>
================

```{lit-setup}
:tangle-root: 020 - Opening a window - Next
:parent: 019 - Our first shader - Next
:fetch-files: ../../data/glfw-3.4.0-light.zip, ../../data/glfw3webgpu-v1.2.0.zip
:debug:
```

*Resulting code:* [`step020-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020-next)

Before being able to render anything on screen, we need to ask the Operating System (OS) to hand us some place where to draw things, something commonly known as a **window**.

The process to open a window **depends a lot on the OS**, so we use a little library called [GLFW](https://www.glfw.org/) which unifies the different window management APIs and enables our code to be **agnostic** in the OS.

```{note}
I try to use as few libraries as I can, but this one is required to **make our code cross-platform**, which feels even more important to me than writing code from scratch. GLFW is furthermore **a very common choice** and quite small in its design.
```

```{admonition} Headless mode
WebGPU **does not require a window** to draw things actually, it may run headless and draw to **offscreen textures**. Since this is not a use case as common as drawing in a window, I leave the details of this option to [a dedicated chapter](../../advanced-techniques/headless.md) of the advanced section.
```

```{admonition} SDL
**Another popular choice** for window management is the **SDL library**. It is not as lightweight as GLFW but provides more features, like support for sound and Android/iOS targets. [A dedicated appendix](../../appendices/using-sdl.md) shows what to change to the main guide when using SDL.
```

Integration of GLFW
-------------------

We do **not really need to install** it, we just need to add the code of GLFW to our project directory. Download the file [glfw.zip](../data/glfw-3.4.0-light.zip) (780 KB) and **unzip** it in your project. This is a stripped down version of the official release where I removed documentation, examples and tests so that it is more **lightweight**.

To **integrate GLFW** in our project, we add its directory to our root `CMakeLists.txt` with `add_subdirectory(glfw)`. We add an **exception for emscripten** because it has **built-in** support for GLFW; all we need in that case is to set the `-sUSE_GLFW=3` link option.

```{lit} CMake, Dependency subdirectories (prepend)
if (NOT EMSCRIPTEN)
	# Add the 'glfw' directory, which contains the definition of a 'glfw' target
	add_subdirectory(glfw)
else()
	# Create a mock 'glfw' target that just sets the `-sUSE_GLFW=3` link option:
	add_library(glfw INTERFACE)
	target_link_options(glfw INTERFACE -sUSE_GLFW=3)
endif()
# In both cases, we can now link to the 'glfw' target
```

```{note}
When using **Dawn**, make sure to add the `glfw` directory **before** you add `webgpu`, otherwise Dawn provides its own version (which may be fine sometimes, but you don't get to chose the version).
```

Then, we must tell CMake to **link our application to this library**, like we did for webgpu:

```{lit} CMake, Link libraries (replace)
# Add the 'glfw' target as a dependency of our App
target_link_libraries(App PRIVATE webgpu glfw)
```

You should now be able to build the application and add `#include <GLFW/glfw3.h>` at the beginning of the main file.

```{lit} C++, Includes (append)
#include <GLFW/glfw3.h>
```

````{important}
If you are on a **linux** system, make sure to install the [dependencies that GLFW require](https://www.glfw.org/docs/3.3/compile.html#compile_deps). By default, it tries to build for both **X11** and **Wayland** so you need both sets of dependencies. If you only want to use/install one of them, turn either `GLFW_BUILD_X11` or `GLFW_BUILD_WAYLAND` off when calling cmake, e.g.:

```
# Build with only X11 support
cmake -B build -DGLFW_BUILD_WAYLAND=OFF
```
````

Basic usage
-----------



Conclusion
----------

*Resulting code:* [`step020-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step020-next)
