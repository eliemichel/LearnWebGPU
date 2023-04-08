Building for the Web (🚧WIP)
====================

*Resulting code:* [`step095-emscripten`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-emscripten)

Even if this guide focuses on native application development, a nice byproduct of using WebGPU it to be able to compile our code as a Web page.

In such a case, we no longer need a distribution (wgpu-native or Dawn), we rather have the compiler map our calls to WebGPU symbols to calls to the actual JavaScript WebGPU API.

Build system changes
--------------------

WIP

```
emcmake cmake -B build-web
cmake --build build-web
python -m http.server -d build-web
# Browse to localhost:8000/App.html
```

Dependencies:

```CMake
if (NOT EMSCRIPTEN)
	add_subdirectory(glfw)
endif()
add_subdirectory(webgpu)
if (NOT EMSCRIPTEN)
	add_subdirectory(glfw3webgpu)
endif()
add_subdirectory(imgui)

# [...]

target_include_directories(App PRIVATE .)
target_link_libraries(App PRIVATE glfw webgpu imgui)
if (NOT EMSCRIPTEN)
	target_link_libraries(App PRIVATE glfw3webgpu)
endif()
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
