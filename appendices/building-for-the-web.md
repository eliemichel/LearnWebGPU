Building for the Web (🚧WIP)
====================

*Resulting code:* [`step095-emscripten`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-emscripten)

Even if this guide focuses on native application development, a nice byproduct of using WebGPU it to be able to compile our code as a Web page.

In such a case, we no longer need a distribution (wgpu-native or Dawn), we rather have the compiler map our calls to WebGPU symbols to calls to the actual JavaScript WebGPU API.

Build system changes
--------------------

### emscripten

Building C++ code into a web page requires a **specific compiler** that can target **WebAssembly** instead of native binaries. The typical choice is *Emcripten*, and I invite you to **follow the [installation instructions](https://emscripten.org/docs/getting_started/downloads.html)**.

Open a terminal and activate `emsdk` (see installation instruction), such that **the command `emcmake` is available** in the `PATH` (you may check with `where emcmake` on Windows `which emcmake` on others).

### Configure

This is a command provided by Emcripten to ease the compilation of CMake-based into WebAssembly. It must simply be used **as a prefix** of the `cmake` configuration call:

```bash
# Create a build-web directory in which we configured the project to be built
# with emscripten. You may use any regular cmake command line option here.
emcmake cmake -B build-web
```

```{note}
Prefixing with `emcmake` is **only needed for the first call** to CMake. Relevant information are then properly stored in the `CMakeCache.txt`, such that you can use CMake as usual afterwards.
```

Note however that it won't correctly run as is, we need to change a few things in the CMakeLists.

### CMake changes

Emscripten provides its own version of GLFW, because drawing on a Web page is very different from drawing on a native window. We thus tell CMake to include our own `glfw` directory only when **not** using Emscripten:

```CMake
if (NOT EMSCRIPTEN)
	# Do not include this with emscripten, it provides its own version.
	add_subdirectory(glfw)
endif()
```

Other dependencies (`webgpu`, `glfw3webgpu` and `imgui`) are not affected or already handle Emscripten internally.

However, in order to have Emscripten use its own GLFW when **linking** the application, we must tell it to use the `-sUSE_GLFW=3` argument. We also use `-sUSE_WEBGPU` to tell the linker that it must **handle WebGPU symbols** (and replace them with calls to the JavaScript API):

```CMake
# At the end of the CMakeLists.txt
if (EMSCRIPTEN)
	# Add Emscripten-specific link options
	target_link_options(App PRIVATE
		-sUSE_GLFW=3 # Use Emscripten-provided GLFW
		-sUSE_WEBGPU # Handle WebGPU symbols
	)
endif()
```

A last change to the `CMakeLists.txt` before we can build: **by default** Emscripten generates a **WebAssembly module**, but not a web page. In order to get a default web page around it, we must change the extension of the `App` target to `.html`:

```CMake
# in the 'if (EMSCRIPTEN)' block:
# Generate a full web page rather than a simple WebAssembly module
set_target_properties(App PROPERTIES SUFFIX ".html")
```

```{note}
We see below how to customize the HTML part of this web page (a.k.a. the *shell*).
```

### Build

Building the project is then simply the following, as usual with CMake:

```bash
cmake --build build-web
```

### Run

Once the build is ready, it creates an `App.html` page. In order to circumvent browser safety rules, you **must not** open it directly but rather run a **local server**, for instance using Python:

```bash
python -m http.server -d build-web
```

You may now browse to [`http://localhost:8000/App.html`](http://localhost:8000/App.html)!

```{important}
At this stage, the project should build successfully, but the web page **will not run correctly**.
```

Resources and shell
-------------------

WIP

We actually add a few more options after `-sUSE_WEBGPU`:

 - `-sALLOW_MEMORY_GROWTH` to avoid running out of memory during the execution of the WebAssembly module.
 - `--preload-file "${CMAKE_CURRENT_SOURCE_DIR}/resources"` makes the content of the `resource` directory available to the Web page.

```{warning}
The whole content of the `resource` directory will be downloaded by your end user. Make sure to **only include what is needed** here so that your web page is not too heavy! You may instead enumerate the required files individually.
```

emscripten-specific target properties:

```CMake
if (EMSCRIPTEN)
	set(SHELL_FILE shell.html)

	target_link_options(App PRIVATE
		-sUSE_GLFW=3
		-sUSE_WEBGPU
		-sALLOW_MEMORY_GROWTH
		--shell-file "${CMAKE_CURRENT_SOURCE_DIR}/${SHELL_FILE}"
		--preload-file "${CMAKE_CURRENT_SOURCE_DIR}/resources"
	)

	# Make sure to re-link when the shell file changes
	set_property(
		TARGET App
		PROPERTY LINK_DEPENDS
		"${CMAKE_CURRENT_SOURCE_DIR}/${SHELL_FILE}"
	)

	set_target_properties(App PROPERTIES SUFFIX ".html")
endif()
```

C++ changes
-----------

TODO (main loop, swap, surface creation)

```C++
// In main.cpp
#include "Application.h"

#ifdef __EMSCRIPTEN__
#include <emscripten/html5.h>
#endif

int main(int, char**) {
	Application app;
	app.onInit();

#ifdef __EMSCRIPTEN__

    emscripten_set_main_loop_arg(
        [](void *userData) {
            Application& app = *reinterpret_cast<Application*>(userData);
            app.onFrame();
        },
        (void*)&app,
        0, true
    );

#else // __EMSCRIPTEN__

	while (app.isRunning()) {
		app.onFrame();
	}
	app.onFinish();

#endif // __EMSCRIPTEN__

	return 0;
}
```

Conclusion
----------

*Resulting code:* [`step095-emscripten`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-emscripten)
