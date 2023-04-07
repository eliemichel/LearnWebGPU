Refactoring
===========

````{tab} With webgpu.hpp
*Resulting code:* [`step080`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step080-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080-vanilla)
````

The goal of this chapter is to add some interactivity to our viewer. From a WebGPU standpoint, we know everything we need for this. For instance enabling the user to turn around the object using the mouse is only about **updating the view matrix**.

However, it is also the occasion to **organize a bit our code base**, which we have not been discussing much until now. It was not the primary topic, and the size of the code was still manageable as mostly a big main function, but this never holds for bigger applications.

An application structure
------------------------

I am going to avoid over-engineering things since each use case is different, so you will customize the details for your needs. Nevertheless it always starts with a class (or struct) that holds all the global state of the application.

We implement this in two new files `Application.h` and `Application.cpp`, where the behavior of the application is distributed across **event handlers**. To make this logic clear, handles start with "on", like `onFrame`.

```C++
// In Application.h
#pragma once
#include <webgpu.hpp>

class Application {
public:
	// A function called only once at the beginning. Returns false is init failed.
	bool onInit();

	// A function called at each frame, guaranteed never to be called before `onInit`.
	void onFrame();

	// A function called only once at the very end.
	void onFinish();

private:
	// Everything that is initialized in `onInit` and needed in `onFrame`.
	wgpu::Instance instance = nullptr;
	wgpu::Surface surface = nullptr;
	// [...]
};
```

```C++
// In Application.cpp
#include "Application.h"

bool Application::onInit() {
	// [...]
}

void Application::onFrame() {
	// [...]
}

void Application::onFinish() {
	// [...]
}
```

Do not forget to add these file (most importantly the .cpp) to the source files listed in `CMakeLists.txt`:

```CMake
add_executable(App
	Application.h  # optional, just to show it in your IDE
	Application.cpp
	main.cpp
)
```

When outlining the main function, we realize we also need a fourth method in our application structure: `isRunning` (which basically calls `glfwWindowShouldClose`).

```C++
// In main.cpp
#include "Application.h"

int main(int, char**) {
	Application app;
	if (!app.onInit()) return 1;

	while (app.isRunning()) {
		app.onFrame();
	}

	app.onFinish();
	return 0;
}
```

```C++
// In Application.h
#include <GLFW/glfw3.h>

class Application {
public:
	// A function that tells if the application is still running.
	bool isRunning();
	// [...]

private:
	GLFWwindow* window;
	// [...]
};

// In Application.cpp
bool Application::isRunning() {
	return !glfwWindowShouldClose(window);
}
```

### Resource manager

Our three procedure for loading external resources can be moved into a separate namespace or class with only static members.

We create a `ResourceManager.h` and `ResourceManager.cpp` files, add them to the CMakeLists and move resource loaders there.

```C++
// In ResourceManager.h
class ResourceManager {
public:
	using vec3 = glm::vec3;
	using vec2 = glm::vec2;

	/**
	 * A structure that describes the data layout in the vertex buffer,
	 * used by loadGeometryFromObj and used it in `sizeof` and `offsetof`
	 * when uploading data to the GPU.
	 */
	struct VertexAttributes {
		vec3 position;
		vec3 normal;
		vec3 color;
		vec2 uv;
	};

	// (Just an alias to make notations lighter)
	using path = std::filesystem::path;

	// Load a shader from a WGSL file into a new shader module
	static wgpu::ShaderModule loadShaderModule(const path& path, wgpu::Device device);

	// Load an 3D mesh from a standard .obj file into a vertex data buffer
	static bool loadGeometryFromObj(const path& path, std::vector<VertexAttributes>& vertexData);

	// Load an image from a standard image file into a new texture object
	// NB: The texture must be destroyed after use
	static wgpu::Texture loadTexture(const path& path, wgpu::Device device, wgpu::TextureView* pTextureView = nullptr);
};
```

### Library implementation

As we start including our libraries in multiple files, we must remember that the `#define FOO_IMPLEMENTATION` that some of them require **must appear in only one** C++ file, and the include must be placed before any other one that may recursively include it.

To avoid some unexpected complication, I recommend to create a file `implementations.cpp` to be the place for this and only this:

```C++
// In implementations.cpp
#define TINYOBJLOADER_IMPLEMENTATION
#include "tiny_obj_loader.h"

#define WEBGPU_CPP_IMPLEMENTATION
#include <webgpu.hpp>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

Conclusion
----------

I let you move the largest chunks of code by yourself, otherwise this chapter would look like a big listing. You can check it against the reference code from this chapter of course.

````{tab} With webgpu.hpp
*Resulting code:* [`step080`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step080-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080-vanilla)
````
