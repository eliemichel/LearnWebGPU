Building for the Web (WIP)
====================

Even if this guide focuses on native application development, a nice byproduct of using WebGPU it to be able to compile our code as a Web page.

In such a case, we no longer need a distribution (wgpu-native or Dawn), we rather have the compiler map our calls to WebGPU symbols to calls to the actual JavaScript WebGPU API.

WIP

```
emcmake cmake -B build-web
cmake --build build-web
# Browse to build-web/App.html
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
