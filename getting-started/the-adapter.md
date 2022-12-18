The Adapter
===========

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)

Requesting the adapter
----------------------

The first thing we need to do in order to dialog with our GPU is to get a WebGPU *adapter*. It is the main entry point of the library, and the same host system may expose multiple adapters if it has multiple implementations of the WebGPU backend (e.g., a high performance one, a low energy consumption one, etc.).

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

which is close enough to the C++ version:

```C++
void onAdapterRequestEnded(WGPURequestAdapterStatus status, WGPUAdapter adapter, char const * message, void * userdata) {
	// do something with the adapter
}
wgpuInstanceRequestAdapter(
	instance /* equivalent of navigator.gpu */,
	&options,
	onAdapterRequestEnded,
	nullptr // custom user data, see bellow
);
```

We can wrap this in a `requestAdapter()` function that mimicks the JS `await requestAdapter()`:

```C++
#include <cassert>

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

```C++
std::cout << "Requesting adapter..." << std::endl;

WGPURequestAdapterOptions adapterOpts = {};
WGPUAdapter adapter = requestAdapter(instance, &adapterOpts);

std::cout << "Got adapter: " << adapter << std::endl;
```

The Surface
-----------

We actually need to pass an option to the adapter request: the *surface* onto which we draw.

```C++
WGPUSurface surface = ???;

WGPURequestAdapterOptions adapterOpts = {};
adapterOpts.nextInChain = nullptr;
adapterOpts.compatibleSurface = surface;

WGPUAdapter adapter = requestAdapter(instance, &adapterOpts);
```

How do we get the surface? This depends on the OS, and GLFW does not handle this for us, for it does not know WebGPU (yet?). So I provide you this function, in a little extension to GLFW3 called `glfw3webgpu`.

### GLFW3 WebGPU Extension

Download and unzip [glfw3webgpu.zip](../data/glfw3webgpu.zip) in your project's directory. There should be two new files sitting next to your `main.cpp`, which we add to our application's source list:

```CMake
add_executable(App
	main.cpp
	# We directly add the glfw3webgpu source files to our project
	glfw3webgpu.h
	glfw3webgpu.c
)
```

You can now `#include "glfw3webgpu.h"` at the beginning of your `main.cpp` and get the surface by simply doing:

```C++
WGPUSurface surface = glfwGetWGPUSurface(instance, window);
```

One last thing: we can tell GLFW not to care about the graphics API setup, as it does not know WebGPU and we won't use what it could set up by default for other APIs:

```C++
glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API); // NEW
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);
// [...]
```

Inspecting the adapter
----------------------

The adapter object provides information about the underlying implementation and hardware, and about what it is able or not to do.

Let us focus on the `wgpuAdapterEnumerateFeatures` function, which enumerates the features of the WebGPU implementation, because its usage is very typical from WebGPU native.

We call the function twice. The first time, we provide a null pointer as the return, and as a consequence the function only returns the number of features, but not the features themselves. We then dynamically allocate memory for storing this many items of result, and call the same function a second time, this time with a pointer to where the result should store its result.

```C++
#include <vector>
// [...]

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

The features are numbers corresponding to the enum `WGPUFeatureName` defined in `webgpu.h`. You may notice very high numbers apparently not defined in this enum. These are extensions provided by our native implementation.

```{note}
In the accompanying code, extra information retrieval is exemplified in the `inspectAdapter()` function. Look in `webgpu.h` for function that starts with `wgpuAdapter` to find other adapter methods.
```

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)
