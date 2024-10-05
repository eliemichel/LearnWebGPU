Refactoring <span class="bullet">🟡</span>
===========

````{tab} With webgpu.hpp
*Resulting code:* [`step080`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step080-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080-vanilla)
````

The goal of this chapter is to **add some interactivity** to our viewer. From a WebGPU standpoint, we know everything we need for this. For instance enabling the user to turn around the object using the mouse is only about **updating the view matrix**.

However, it is also the occasion to **organize a bit our code base**, which we have not been discussing much until now. It was not the primary topic, and the size of the code was still manageable as mostly a big main function, but this never holds for bigger applications.

An application structure
------------------------

### Main class

I am going to **avoid over-engineering** things since each use case is different, so you will customize the details for your needs. Nevertheless it always starts with a class (or struct) that holds all the global state of the application.

We implement this in two new files `Application.h` and `Application.cpp`, where the behavior of the application is distributed across **event handlers**. To make this logic clear, handles start with "on", like `onFrame`. We can already think of three events: init, frame and finish.

```C++
// In Application.h
#pragma once
#include <webgpu/webgpu.hpp>

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
	wgpu::Instance m_instance = nullptr;
	wgpu::Surface m_surface = nullptr;
	// [...]
};
```

```{note}
I prefix private attribute names with `m_` to better distinguish them from local variables when reading the code. This is a common practice (some people also prefer using only `_foo`, or full caml case `mFoo`).
```

````{important}
When using the C++ wrapper, it is important to initialize WebGPU handles to null (e.g., `m_instance = nullptr`) because they have no default constructor. Otherwise you will experience this kind of error:

```
error: 'Application::Application(void)': attempting to reference a deleted function
```
````

Before actually implementing these methods, we can already try draft how this will be used in our `main` function:

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

We hence see that we also need to add a `isRunning` method, that simply calls `glfwWindowShouldClose` behinds the hoods but without exposing the GLFW window to the "client" code (namely the main function).

```C++
// In Application.h
#include <GLFW/glfw3.h>

class Application {
public:
	// A function that tells if the application is still running.
	bool isRunning();
	// [...]

private:
	GLFWwindow* m_window = nullptr;
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

bool Application::isRunning() {
	return !glfwWindowShouldClose(m_window);
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

### Initialization steps

The part of our code that is the **most monolithic** is by far the initialization step. We thus split it into various (private) methods:

```C++
bool Application::onInit() {
	if (!initWindowAndDevice()) return false;
	if (!initSwapChain()) return false;
	if (!initDepthBuffer()) return false;
	if (!initRenderPipeline()) return false;
	if (!initTexture()) return false;
	if (!initGeometry()) return false;
	if (!initUniforms()) return false;
	if (!initBindGroup()) return false;
	return true;
}
```

And each `initSomething` step comes with a `terminateSomething` that is called at the end in reverse order:

```C++
void Application::onFinish() {
	terminateBindGroup();
	terminateUniforms();
	terminateGeometry();
	terminateTexture();
	terminateRenderPipeline();
	terminateDepthBuffer();
	terminateSwapChain();
	terminateWindowAndDevice();
}
```

This way, it is easier to keep track of what must be released at the end of the application. You can also group the attributes by step when declaring them in `Application.h`.

I let you **move the largest chunks of code by yourself**, otherwise this chapter would look like a big listing. Most parts of the old `main.cpp` should end up in `Application.cpp`; you can check it against [the reference code](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080) from this chapter of course.

The next sections present some **additional design choices** I made on the course of refactoring the code. You may or may not follow them.

Design choices
--------------

### Resource manager

Our three procedure for loading external resources can be moved into a separate namespace or class with only static members.

We create a `ResourceManager.h` and `ResourceManager.cpp` files, add them to the CMakeLists and move resource loaders there.

```C++
// In ResourceManager.h
#pragma once
// [...] Includes

class ResourceManager {
public:
	// (Just aliases to make notations lighter)
	using path = std::filesystem::path;
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
#include <webgpu/webgpu.hpp>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

### Callback handles

```{important}
This section is **specific to the WebGPU C++ wrapper** I provide. When using the raw C API, the callback cannot be a lambda function and must rather be defined in the global scope.
```

In order to prevent the uncaptured error callback from being freed too early, we need to store the handle returned by `device.setUncapturedErrorCallback`. So far this was just done by defining a variable `h` that lives for the whole main function:

```C++
// Until now, we just stored the handle in a variable local to the main function
auto h = device.setUncapturedErrorCallback([](ErrorType type, char const* message) {
	std::cout << "Device error: type " << type;
	if (message) std::cout << " (message: " << message << ")";
	std::cout << std::endl;
});
```

Since we no longer define this in the main function directly but rather in the `Application`'s init, we must store the `h` handle as a class member:

```C++
// In Application.h
class Application {
private:
	// Keep the error callback alive
	std::unique_ptr<wgpu::ErrorCallback> m_errorCallbackHandle;
}

// In Application.cpp, in onInit()
m_errorCallbackHandle = device.setUncapturedErrorCallback([](ErrorType type, char const* message) {
	std::cout << "Device error: type " << type;
	if (message) std::cout << " (message: " << message << ")";
	std::cout << std::endl;
});
```

This way, the callback is released only when the Application object is destroyed.

Conclusion
----------

We now have a much more mature code base, that will be way easier to extend as we introduce new features in the next chapters!

Remember that any time you add something in an `init` step, you should likely release it in the matching `terminate` method.

````{tab} With webgpu.hpp
*Resulting code:* [`step080`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step080-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step080-vanilla)
````
