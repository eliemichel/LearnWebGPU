The Adapter
===========

```{lit-setup}
:tangle-root: 010 - The Adapter - Part A
:parent: 005 - Hello WebGPU
:fetch-files: ../data/webgpu-release.h
```

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)

Requesting the adapter
----------------------

The first thing we need to do in order to dialog with our GPU is to get a WebGPU **adapter**. It is the main entry point of the library, and the same host system may expose multiple adapters if it has multiple implementations of the WebGPU backend (e.g., a high performance one, a low energy consumption one, etc.).

In JavaScript, this would be:

```js
const adapter = await navigator.gpu.requestAdapter(options);
// do something with the adapter
```

The equivalent in the C API is a bit more complexe because there is no such thing as [promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) in C, but the logic is very similar.

Without the `await` keyword, the JavaScript version can be rewritten as:

```js
function onAdapterRequestEnded(adapter) {
	// do something with the adapter
}
navigator.gpu.requestAdapter(options).then(onAdapterRequestEnded);
```

which is close enough to the C/C++ version (minus the boilerplate):

```C++
void onAdapterRequestEnded(
	WGPURequestAdapterStatus status, // a success status
	WGPUAdapter adapter, // the returned adapter
	char const* message, // error message, or nullptr
	void* userdata // custom user data, as provided when requesting the adapter
) {
	// [...] Do something with the adapter
}
wgpuInstanceRequestAdapter(
	instance /* equivalent of navigator.gpu */,
	&options,
	onAdapterRequestEnded,
	nullptr // custom user data, see bellow
);
```

````{note}
The names of the procedure provided by `webgpu.h` always follow the same construction:

```C
wgpuSomethingSomeAction(something, ...)
             ^^^^^^^^^^ // What to do...
    ^^^^^^^^^ // ...on what type of object
^^^^ // (Common prefix to allow naming collisions)
```

The first argument of the fonction is always a "handle" (a blind pointer) representing an object of type "Something".
````

### Request

We can wrap this in a `requestAdapter()` function that mimicks the JS `await requestAdapter()`:

```{lit} C++, Includes (append)
#include <cassert>
```

```{lit} C++, Request adapter function
/**
 * Utility function to get a WebGPU adapter, so that
 *     WGPUAdapter adapter = requestAdapter(options);
 * is roughly equivalent to
 *     const adapter = await navigator.gpu.requestAdapter(options);
 */
WGPUAdapter requestAdapter(WGPUInstance instance, WGPURequestAdapterOptions const * options) {
	// A simple structure holding the local information shared with the
	// onAdapterRequestEnded callback.
	struct UserData {
		WGPUAdapter adapter = nullptr;
		bool requestEnded = false;
	};
	UserData userData;

	// Callback called by wgpuInstanceRequestAdapter when the request returns
	// This is a C++ lambda function, but could be any function defined in the
	// global scope. It must be non-capturing (the brackets [] are empty) so
	// that it behaves like a regular C function pointer, which is what
	// wgpuInstanceRequestAdapter expects (WebGPU being a C API). The workaround
	// is to convey what we want to capture through the pUserData pointer,
	// provided as the last argument of wgpuInstanceRequestAdapter and received
	// by the callback as its last argument.
	auto onAdapterRequestEnded = [](WGPURequestAdapterStatus status, WGPUAdapter adapter, char const * message, void * pUserData) {
		UserData& userData = *reinterpret_cast<UserData*>(pUserData);
		if (status == WGPURequestAdapterStatus_Success) {
			userData.adapter = adapter;
		} else {
			std::cout << "Could not get WebGPU adapter: " << message << std::endl;
		}
		userData.requestEnded = true;
	};

	// Call to the WebGPU request adapter procedure
	wgpuInstanceRequestAdapter(
		instance /* equivalent of navigator.gpu */,
		options,
		onAdapterRequestEnded,
		(void*)&userData
	);

	// In theory we should wait until onAdapterReady has been called, which
	// could take some time (what the 'await' keyword does in the JavaScript
	// code). In practice, we know that when the wgpuInstanceRequestAdapter()
	// function returns its callback has been called.
	assert(userData.requestEnded);

	return userData.adapter;
}
```

In the main function, after opening the window, we can get the adapter:

```{lit} C++, Request adapter
std::cout << "Requesting adapter..." << std::endl;

WGPURequestAdapterOptions adapterOpts = {};
WGPUAdapter adapter = requestAdapter(instance, &adapterOpts);

std::cout << "Got adapter: " << adapter << std::endl;
```

### Destruction

Like for the WebGPU instance, we must destroy the adapter:

```{lit} C++, Destroy adapter
wgpuAdapterRelease(adapter);
```

Here again we face the difference between `wgpu-native` and Dawn, so we need to set up an alias to use the "release" version. To make things easier, I made a little [`webgpu-release.h`](../data/webgpu-release.h) file that defines such an alias for all types of objects. You can save next to your `main.cpp` and include:

```{lit} C++, Includes (append, hidden)
#include <webgpu/webgpu.h>
```

```{lit} C++, Includes (prepend)
#include "webgpu-release.h"
```

```{lit} C++, file: main.cpp (hidden)
{{Includes}}

{{Utility functions in main.cpp}}

int main() {
	{{Create things}}

	{{Main body}}

	{{Destroy things}}
}
```

```{lit} C++, Utility functions in main.cpp (hidden)
{{Utility functions}}
```

```{lit} C++, Utility functions (hidden)
{{Request adapter function}}
```

```{lit} C++, Create things (hidden)
{{Create WebGPU instance}}
{{Request adapter}}
```

```{lit} C++, Main body (hidden)
```

```{lit} C++, Destroy things (hidden)
{{Destroy adapter}}
{{Destroy WebGPU instance}}
```

The Surface
-----------

```{lit-setup}
:tangle-root: 010 - The Adapter - Part B
:parent: 010 - The Adapter - Part A
:fetch-files: ../data/glfw3webgpu.zip
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

Download and unzip [glfw3webgpu.zip](https://github.com/eliemichel/glfw3webgpu/releases/download/v1.0.1/glfw3webgpu-v1.0.1.zip) in your project's directory. There should now be a directory `glfw3webgpu` sitting next to your `main.cpp`. Like we have done before, we can add this directory and link the target it creates to our App:

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

Inspecting the adapter
----------------------

The adapter object provides **information about the underlying implementation** and hardware, and about what it is able or not to do.

Let us focus on the `wgpuAdapterEnumerateFeatures` function, which enumerates the features of the WebGPU implementation, because its usage is very typical from WebGPU native.

We call the function **twice**. The **first time**, we provide a null pointer as the return, and as a consequence the function only returns the **number of features**, but not the features themselves.

We then dynamically **allocate memory** for storing this many items of result, and call the same function a **second time**, this time with a pointer to where the result should store its result.

```{lit} C++, Includes (append)
#include <vector>
```

```{lit} C++, Utility functions (append, hidden)
void inspectAdapter(WGPUAdapter adapter) {
	{{Inspect adapter}}
}
```

```{lit} C++, Request adapter (append, hidden)
inspectAdapter(adapter);
```

```{lit} C++, Inspect adapter
std::vector<WGPUFeatureName> features;

// Call the function a first time with a null return address, just to get
// the entry count.
size_t featureCount = wgpuAdapterEnumerateFeatures(adapter, nullptr);

// Allocate memory (could be a new, or a malloc() if this were a C program)
features.resize(featureCount);

// Call the function a second time, with a non-null return address
wgpuAdapterEnumerateFeatures(adapter, features.data());

std::cout << "Adapter features:" << std::endl;
for (auto f : features) {
	std::cout << " - " << f << std::endl;
}
```

The features are numbers corresponding to the enum `WGPUFeatureName` defined in `webgpu.h`.

You may notice very high numbers apparently not defined in this enum. These are **extensions** provided by our native implementation (e.g., defined in `wgpu.h` instead of `webgpu.h` in the case of `wgpu-native`).

```{note}
In the accompanying code, extra information retrieval is exemplified in the `inspectAdapter()` function. Look in `webgpu.h` for function that starts with `wgpuAdapter` to find other adapter methods.
```

```{lit} C++, Inspect adapter (append, hidden)
WGPUSupportedLimits limits = {};
limits.nextInChain = nullptr;
bool success = wgpuAdapterGetLimits(adapter, &limits);
if (success) {
	std::cout << "Adapter limits:" << std::endl;
	std::cout << " - maxTextureDimension1D: " << limits.limits.maxTextureDimension1D << std::endl;
	std::cout << " - maxTextureDimension2D: " << limits.limits.maxTextureDimension2D << std::endl;
	std::cout << " - maxTextureDimension3D: " << limits.limits.maxTextureDimension3D << std::endl;
	std::cout << " - maxTextureArrayLayers: " << limits.limits.maxTextureArrayLayers << std::endl;
	std::cout << " - maxBindGroups: " << limits.limits.maxBindGroups << std::endl;
	std::cout << " - maxDynamicUniformBuffersPerPipelineLayout: " << limits.limits.maxDynamicUniformBuffersPerPipelineLayout << std::endl;
	std::cout << " - maxDynamicStorageBuffersPerPipelineLayout: " << limits.limits.maxDynamicStorageBuffersPerPipelineLayout << std::endl;
	std::cout << " - maxSampledTexturesPerShaderStage: " << limits.limits.maxSampledTexturesPerShaderStage << std::endl;
	std::cout << " - maxSamplersPerShaderStage: " << limits.limits.maxSamplersPerShaderStage << std::endl;
	std::cout << " - maxStorageBuffersPerShaderStage: " << limits.limits.maxStorageBuffersPerShaderStage << std::endl;
	std::cout << " - maxStorageTexturesPerShaderStage: " << limits.limits.maxStorageTexturesPerShaderStage << std::endl;
	std::cout << " - maxUniformBuffersPerShaderStage: " << limits.limits.maxUniformBuffersPerShaderStage << std::endl;
	std::cout << " - maxUniformBufferBindingSize: " << limits.limits.maxUniformBufferBindingSize << std::endl;
	std::cout << " - maxStorageBufferBindingSize: " << limits.limits.maxStorageBufferBindingSize << std::endl;
	std::cout << " - minUniformBufferOffsetAlignment: " << limits.limits.minUniformBufferOffsetAlignment << std::endl;
	std::cout << " - minStorageBufferOffsetAlignment: " << limits.limits.minStorageBufferOffsetAlignment << std::endl;
	std::cout << " - maxVertexBuffers: " << limits.limits.maxVertexBuffers << std::endl;
	std::cout << " - maxVertexAttributes: " << limits.limits.maxVertexAttributes << std::endl;
	std::cout << " - maxVertexBufferArrayStride: " << limits.limits.maxVertexBufferArrayStride << std::endl;
	std::cout << " - maxInterStageShaderComponents: " << limits.limits.maxInterStageShaderComponents << std::endl;
	std::cout << " - maxComputeWorkgroupStorageSize: " << limits.limits.maxComputeWorkgroupStorageSize << std::endl;
	std::cout << " - maxComputeInvocationsPerWorkgroup: " << limits.limits.maxComputeInvocationsPerWorkgroup << std::endl;
	std::cout << " - maxComputeWorkgroupSizeX: " << limits.limits.maxComputeWorkgroupSizeX << std::endl;
	std::cout << " - maxComputeWorkgroupSizeY: " << limits.limits.maxComputeWorkgroupSizeY << std::endl;
	std::cout << " - maxComputeWorkgroupSizeZ: " << limits.limits.maxComputeWorkgroupSizeZ << std::endl;
	std::cout << " - maxComputeWorkgroupsPerDimension: " << limits.limits.maxComputeWorkgroupsPerDimension << std::endl;
}

WGPUAdapterProperties properties = {};
properties.nextInChain = nullptr;
wgpuAdapterGetProperties(adapter, &properties);
std::cout << "Adapter properties:" << std::endl;
std::cout << " - vendorID: " << properties.vendorID << std::endl;
std::cout << " - deviceID: " << properties.deviceID << std::endl;
std::cout << " - name: " << properties.name << std::endl;
if (properties.driverDescription) {
	std::cout << " - driverDescription: " << properties.driverDescription << std::endl;
}
std::cout << " - adapterType: " << properties.adapterType << std::endl;
std::cout << " - backendType: " << properties.backendType << std::endl;
```

Conclusion
----------

 - The very first thing to do with WebGPU is to get the **adapter**.
 - This adapter can have **options**, in particular the **surface** on which it draws.
 - To get a WebGPU surface from our GLFW window, we use a small **extension of GLFW** called `glfw3webgpu`.
 - Once we have an adapter, we can inspect its **capabilities**.

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)
