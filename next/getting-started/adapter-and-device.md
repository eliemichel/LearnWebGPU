Adapter and Device
==================

```{lit-setup}
:tangle-root: 010 - The Adapter - Part A - next
:parent: 005 - Hello WebGPU - next
```

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)

The **device** is the **main object** we interact with when using WebGPU. It is the object from which we can **create** all other ones (textures, buffers, pipelines, etc.), **send instructions** to the GPU, and **handle errors**.

This chapter describes the **device initialization process**, which is where we also **check the capabilities** of the end user's physical device.

**WIP**

Requesting the adapter
----------------------

The first thing we need to do in order to dialog with our GPU is to get a WebGPU **adapter**. It is the main entry point of the library, and the same host system may expose multiple adapters if it has multiple implementations of the WebGPU backend (e.g., a high performance one, a low energy consumption one, etc.).

In JavaScript, this would be:

```js
const adapter = await navigator.gpu.requestAdapter(options);
// do something with the adapter
```

The equivalent in the C API is a bit more complex because there is no such thing as [promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) in C, but the logic is very similar.

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
	nullptr // custom user data, see below
);
```

````{note}
The names of the procedure provided by `webgpu.h` always follow the same construction:

```C
wgpuSomethingSomeAction(something, ...)
             ^^^^^^^^^^ // What to do...
    ^^^^^^^^^ // ...on what type of object
^^^^ // (Common prefix to avoid naming collisions)
```

The first argument of the function is always a "handle" (a blind pointer) representing an object of type "Something".
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

```{lit} C++, Includes (append, hidden)
#include <webgpu/webgpu.h>
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

The Device
==========

```{lit-setup}
:tangle-root: 015 - The Device - next
:parent: 010 - The Adapter - Part B - next
```

*Resulting code:* [`step015`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015)

A WebGPU **device** represents a **context** of use of the API. All the objects that we create (geometry, textures, etc.) are owned by the device.

> 🤔 Why do we have both an **adapter** and then a **device** abstraction?

The idea is to limit the "it worked on my machine" issue you could encounter when trying your program on a different machine. The **adapter** is used to **access the capabilities** of the user's hardware, which are used to select the behavior of your application among very different code paths. Once a code path is chosen, a **device** is created with **the capabilities we choose**.

Only the capabilities selected for this device are then allowed in the rest of the application. This way, it is **not possible to inadvertently rely on capabilities specific to your own machine**.

```{figure} /images/device-creation.png
:align: center
In an advanced use of the adapter/device duality, we can set up multiple limit presets and select one depending on the adapter. In our case, we have a single preset and abort early if it is not supported.
```

Device request
--------------

Requesting the device looks a lot like requesting the adapter, so we will use a very similar function:

```{lit} C++, Utility functions (append, hidden)
{{Request device function}}
```

```{lit} C++, Request device function
/**
 * Utility function to get a WebGPU device, so that
 *     WGPUAdapter device = requestDevice(adapter, options);
 * is roughly equivalent to
 *     const device = await adapter.requestDevice(descriptor);
 * It is very similar to requestAdapter
 */
WGPUDevice requestDevice(WGPUAdapter adapter, WGPUDeviceDescriptor const * descriptor) {
	struct UserData {
		WGPUDevice device = nullptr;
		bool requestEnded = false;
	};
	UserData userData;

	auto onDeviceRequestEnded = [](WGPURequestDeviceStatus status, WGPUDevice device, char const * message, void * pUserData) {
		UserData& userData = *reinterpret_cast<UserData*>(pUserData);
		if (status == WGPURequestDeviceStatus_Success) {
			userData.device = device;
		} else {
			std::cout << "Could not get WebGPU device: " << message << std::endl;
		}
		userData.requestEnded = true;
	};

	wgpuAdapterRequestDevice(
		adapter,
		descriptor,
		onDeviceRequestEnded,
		(void*)&userData
	);

	assert(userData.requestEnded);

	return userData.device;
}
```

```{note}
In the accompanying code, I moved these utility functions into `webgpu-utils.cpp`
```

```{lit} C++, file: webgpu-utils.h (hidden)
#pragma once

#include <webgpu/webgpu.h>

/**
 * Utility function to get a WebGPU adapter, so that
 *     WGPUAdapter adapter = requestAdapter(options);
 * is roughly equivalent to
 *     const adapter = await navigator.gpu.requestAdapter(options);
 */
WGPUAdapter requestAdapter(WGPUInstance instance, WGPURequestAdapterOptions const * options);

/**
 * Utility function to get a WebGPU device, so that
 *     WGPUAdapter device = requestDevice(adapter, options);
 * is roughly equivalent to
 *     const device = await adapter.requestDevice(descriptor);
 * It is very similar to requestAdapter
 */
WGPUDevice requestDevice(WGPUAdapter adapter, WGPUDeviceDescriptor const * descriptor);

/**
 * An example of how we can inspect the capabilities of the hardware through
 * the adapter object.
 */
void inspectAdapter(WGPUAdapter adapter);

/**
 * Display information about a device
 */
void inspectDevice(WGPUDevice device);
```

```{lit} C++, file: webgpu-utils.cpp (hidden)
#include "webgpu-utils.h"

#include <iostream>
#include <vector>
#include <cassert>

{{Utility functions}}
```

```{lit} C++, Utility functions in main.cpp (replace, hidden)
```

```{lit} C++, Includes (prepend, hidden)
#include "webgpu-utils.h"
```

```{lit} CMake, Define app target (replace, hidden)
{{Dependency subdirectories}}

add_executable(App
	{{App source files}}
)

{{Link libraries}}
```

```{lit} CMake, App source files (hidden)
main.cpp
webgpu-utils.h
webgpu-utils.cpp
```

In the main function, after getting the adapter, we can request the device:

```{lit} C++, Request device
std::cout << "Requesting device..." << std::endl;

WGPUDeviceDescriptor deviceDesc = {};
{{Build device descriptor}}
WGPUDevice device = requestDevice(adapter, &deviceDesc);

std::cout << "Got device: " << device << std::endl;
```

```{lit} C++, Create things (append, hidden)
{{Request device}}
{{Setup device callbacks}}
```

And before destroying the adapter, we release the device:

```{lit} C++, Destroy things (prepend)
wgpuDeviceRelease(device);
```

Device descriptor
-----------------

Let us look in `webgpu.h` what the descriptor looks like:

```C++
typedef struct WGPUDeviceDescriptor {
    WGPUChainedStruct const * nextInChain;
    char const * label;
    uint32_t requiredFeaturesCount;
    WGPUFeatureName const * requiredFeatures;
    WGPURequiredLimits const * requiredLimits;
    WGPUQueueDescriptor defaultQueue;
} WGPUDeviceDescriptor;

// (this struct definition is actually above)
typedef struct WGPUQueueDescriptor {
    WGPUChainedStruct const * nextInChain;
    char const * label;
} WGPUQueueDescriptor;
```

For now we will initialize this to a very minimal option:

```{lit} C++, Build device descriptor
deviceDesc.nextInChain = nullptr;
deviceDesc.label = "My Device"; // anything works here, that's your call
deviceDesc.requiredFeaturesCount = 0; // we do not require any specific feature
deviceDesc.requiredLimits = nullptr; // we do not require any specific limit
deviceDesc.defaultQueue.nextInChain = nullptr;
deviceDesc.defaultQueue.label = "The default queue";
```

We will come back here and refine these options whenever we will need some more capabilities from the device.

```{note}
The `label` is **used in error message** to help you debug where something went wrong, so it is good practice to use it as soon as you get multiple objects of the same type. Currently, this is only used by Dawn.
```

Device error callback
---------------------

Before moving on to the next section, I would like you to add this call after creating the device:

```{lit} C++, Setup device callbacks
auto onDeviceError = [](WGPUErrorType type, char const* message, void* /* pUserData */) {
	std::cout << "Uncaptured device error: type " << type;
	if (message) std::cout << " (" << message << ")";
	std::cout << std::endl;
};
wgpuDeviceSetUncapturedErrorCallback(device, onDeviceError, nullptr /* pUserData */);
```

This defines **a callback that gets executed upon errors**, which is very handy for debugging, especially when we will start using **asynchronous** operations.

If you use a debugger (which I recommend), like `gdb` or your IDE, I recommend you **put a breakpoint** in this callback, so that your program pauses and provides you with a call stack whenever WebGPU encounters an unexpected error.

````{admonition} Dawn
By default Dawn runs callbacks only when the device "ticks", so the error callbacks are invoked in a different call stack than where the error occurred, making the breakpoint less informative. To force Dawn to invoke error callbacks as soon as there is an error, you can set the environment variable `DAWN_DEBUG_BREAK_ON_ERROR` to a non-empty non-zero value.

To automatically set this up in Visual Studio from CMake, you can add the following to your `CMakeLists.txt`:

```CMake
set_target_properties(App PROPERTIES VS_DEBUGGER_ENVIRONMENT "DAWN_DEBUG_BREAK_ON_ERROR=1")
```

Note that **this feature is imperfect** and sometimes breaks in non-error cases. This [has been reported](https://bugs.chromium.org/p/dawn/issues/detail?id=1789&q=&can=4), in the meantime just press "Continue" in your IDE when this happens.
````

````{admonition} Dawn again
Dawn will show a warning about a missing **device lost callback**. You may set it in a very similar way than the error callback, except as of now (2023-07-04) the API is different in the official `webgpu.h` header, so I won't add it until this is settled.
````

*Resulting code:* [`step015`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015)

```{lit} C++, Utility functions (append, hidden)
// We also add an inspect device function:
void inspectDevice(WGPUDevice device) {
	std::vector<WGPUFeatureName> features;
	size_t featureCount = wgpuDeviceEnumerateFeatures(device, nullptr);
	features.resize(featureCount);
	wgpuDeviceEnumerateFeatures(device, features.data());

	std::cout << "Device features:" << std::endl;
	for (auto f : features) {
		std::cout << " - " << f << std::endl;
	}

	WGPUSupportedLimits limits = {};
	limits.nextInChain = nullptr;
	bool success = wgpuDeviceGetLimits(device, &limits);
	if (success) {
		std::cout << "Device limits:" << std::endl;
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
}
```

```{lit} C++, Create things (append, hidden)
inspectDevice(device);
```
