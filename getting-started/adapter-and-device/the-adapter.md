The Adapter <span class="bullet">🟢</span>
===========

```{lit-setup}
:tangle-root: 005 - The Adapter
:parent: 001 - Hello WebGPU
```

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)

Before getting our hand on a **device**, we need to select an **adapter**. The same host system may expose **multiple adapters** if it has access to multiple physical GPUs. It may also have an adapter that represents an emulated/virtual device.

```{note}
It is common that high-end laptops have **two physical GPUs**, a **high performance** one and a **low energy** consumption one (that is usually integrated inside the CPU chip).
```

Each adapter advertises a list of optional **features** and **supported limits** that it can handle. These are used to determine the overall capabilities of the system before **requesting the device**.

> 🤔 Why do we have both an **adapter** and then a **device** abstraction?

The idea is to limit the "it worked on my machine" issue you could encounter when trying your program on a different machine. The **adapter** is used to **access the capabilities** of the user's hardware, which are used to select the behavior of your application among very different code paths. Once a code path is chosen, a **device** is created with **the capabilities we choose**.

Only the capabilities selected for this device are then allowed in the rest of the application. This way, it is **not possible to inadvertently rely on capabilities specific to your own machine**.

```{themed-figure} /images/the-adapter/limit-tiers_{theme}.svg
:align: center
In an advanced use of the adapter/device duality, we can set up multiple limit presets and select one depending on the adapter. In our case, we have a single preset and abort early if it is not supported.
```


Requesting the adapter
----------------------

An adapter is not something we *create*, but rather something that we *request* using the function `wgpuInstanceRequestAdapter`.

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

So, as suggested by the name, the first argument is the `WGPUInstance` that we created in the previous chapter. What about the others?

```C++
// Signature of the wgpuInstanceRequestAdapter function as defined in webgpu.h
void wgpuInstanceRequestAdapter(
	WGPUInstance instance,
	WGPU_NULLABLE WGPURequestAdapterOptions const * options,
	WGPURequestAdapterCallback callback,
	void * userdata
);
```

```{note}
It is always informative to have a look at how a function is defined in `webgpu.h`!
```

The second argument is a set of **options**, that is a bit like the **descriptor** that we find in `wgpuCreateSomething` functions, we detail them below. The `WGPU_NULLABLE` flag is an empty define that is only here to tell the reader (i.e., us) that it is allowed to leave the argument to `nullptr` to use **default options**.

### Asynchronous function

The last two arguments go together, and reveal yet another **WebGPU idiom**. Indeed, the function `wgpuInstanceRequestAdapter` is **asynchronous**. This means that instead of directly returning a `WGPUAdapter` object, this request function remembers a **callback**, i.e. a function that will be called whenever the request ends.

```{note}
Asynchronous functions are used in multiple places in the WebGPU API, whenever an operation may take time. Actually, **none of the WebGPU functions** takes time to return. This way, the CPU program that we are writing never gets blocked by a lengthy operation!
```

To understand this callback mechanism a bit better, here is the definition of the `WGPURequestAdapterCallback` function type:

```C++
// Definition of the WGPURequestAdapterCallback function type as defined in webgpu.h
typedef void (*WGPURequestAdapterCallback)(
	WGPURequestAdapterStatus status,
	WGPUAdapter adapter,
	char const * message,
	void * userdata
);
```

The callback is a **function** that receives the **requested adapter** as an argument, together with **status** information (that tells whether the request failed and why), as well as this mysterious `userdata` **pointer**.

This `userdata` pointer can be anything, it is not interpreted by WebGPU, but only **forwarded** from the initial call to `wgpuInstanceRequestAdapter` to the callback, as a mean to **share some context information**:

```C++
void onAdapterRequestEnded(
	WGPURequestAdapterStatus status, // a success status
	WGPUAdapter adapter, // the returned adapter
	char const* message, // error message, or nullptr
	void* userdata // custom user data, as provided when requesting the adapter
) {
	// [...] Do something with the adapter

	// Manipulate user data
	bool* pRequestEnded = reinterpret_cast<bool*>(userdata);
	*pRequestEnded = true;
}

// [...]

// In main():
bool requestEnded = false;
wgpuInstanceRequestAdapter(
	instance /* equivalent of navigator.gpu */,
	&options,
	onAdapterRequestEnded,
	&requestEnded // custom user data is simply a pointer to a boolean in this case
);
```

We see in the next section a more advanced use of this context in order to retrieve the adapter once the request is done.

````{admonition} Note - JavaScript API
:class: foldable note

In the **JavaScript API** of WebGPU, asynchronous functions use the built-in [Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) mechanism:

```js
const adapterPromise = navigator.gpu.requestAdapter(options);
// The "promise" has no value yet, it is rather a handle that we may connect to callbacks:
adapterPromise.then(onAdapterRequestEnded).catch(onAdapterRequestFailed);

// [...]

// Instead of a 'status' argument, we have multiple callbacks:
function onAdapterRequestEnded(adapter) {
	// do something with the adapter
}
function onAdapterRequestFailed(error) {
	// display the error message
}
```

The JavaScript language later introduced a mechanism [`async` function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function), which enables **"awaiting"** for an asynchronous function without explicitly creating a callback:

```js
// (From within an async function)
const adapter = await navigator.gpu.requestAdapter(options);
// do something with the adapter
```

This mechanism now exists in other languages such as [Python](https://docs.python.org/3/library/asyncio-task.html), and has even been introduced in C++20 with [coroutines](https://en.cppreference.com/w/cpp/language/coroutines).

I try however to **avoid stacking up too many levels of abstraction** in this guide so we will not use these (and also stick to C++17), but advanced readers may want to create their own WebGPU wrapper that relies on coroutines.
````

### Request

We can wrap the whole adapter request in the following `requestAdapterSync()` function, which I provide so that we do not spend too much time on **boilerplate** code (the important part here is that you get the idea of the **asynchronous callback** described above):

```{lit} C++, Includes (append)
#include <cassert>
```

```{lit} C++, Request adapter function
/**
 * Utility function to get a WebGPU adapter, so that
 *     WGPUAdapter adapter = requestAdapterSync(options);
 * is roughly equivalent to
 *     const adapter = await navigator.gpu.requestAdapter(options);
 */
WGPUAdapter requestAdapterSync(WGPUInstance instance, WGPURequestAdapterOptions const * options) {
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

	// We wait until userData.requestEnded gets true
	{{Wait for request to end}}

	assert(userData.requestEnded);

	return userData.adapter;
}
```

```{lit} C++, Utility functions (hidden)
// All utility functions are regrouped here
{{Request adapter function}}
```

In the main function, after creating the WebGPU instance, we can get the adapter:

```{lit} C++, Request adapter
std::cout << "Requesting adapter..." << std::endl;

WGPURequestAdapterOptions adapterOpts = {};
adapterOpts.nextInChain = nullptr;
WGPUAdapter adapter = requestAdapterSync(instance, &adapterOpts);

std::cout << "Got adapter: " << adapter << std::endl;
```

#### Waiting for the request to end

You may have noticed the comment above saying **we need to wait** for the request to end, i.e. for the callback to be invoked, before returning.

When using the **native** API (Dawn or `wgpu-native`), it is in practice **not needed**, we know that when the `wgpuInstanceRequestAdapter` function returns its callback has been called.

However, when using **Emscripten**, we need to hand the control **back to the browser** until the adapter is ready. In JavaScript, this would be using the `await` keyword. Instead, Emscripten provides the `emscripten_sleep` function that interrupts the C++ module for a couple of milliseconds:

```{lit} C++, Wait for request to end
#ifdef __EMSCRIPTEN__
	while (!userData.requestEnded) {
		emscripten_sleep(100);
	}
#endif // __EMSCRIPTEN__
```

In order to use this, we must add a **custom link option** in `CMakeLists.txt`, in the `if (EMSCRIPTEN)` block:

```{lit} CMake, Emscripten-specific options (append)
# Enable the use of emscripten_sleep()
target_link_options(App PRIVATE -sASYNCIFY)
```

Also do not forget to include `emscripten.h` in order to use `emscripten_sleep`:

```{lit} C++, Includes (append)
#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#endif // __EMSCRIPTEN__
```

### Destruction

Like for the WebGPU instance, we must release the adapter:

```{lit} C++, Destroy adapter
wgpuAdapterRelease(adapter);
```

````{note}
We will no longer need to use the `instance` once we have selected our **adapter**, so we can call `wgpuInstanceRelease(instance)` right after the adapter request **instead of at the very end**. The **underlying instance** object will keep on living until the adapter gets released but we do not need to manage this.

```{lit} C++, Create things (hidden)
{{Create WebGPU instance}}
{{Check WebGPU instance}}
{{Request adapter}}
// We no longer need to use the instance once we have the adapter
{{Destroy WebGPU instance}}
```
````

```{lit} C++, file: main.cpp (replace, hidden)
{{Includes}}

{{Utility functions in main.cpp}}

int main() {
	{{Create things}}

	{{Main body}}

	{{Destroy things}}

	return 0;
}
```

```{lit} C++, Utility functions in main.cpp (hidden)
{{Utility functions}}
```

```{lit} C++, Main body (hidden)
```

```{lit} C++, Destroy things (hidden)
{{Destroy adapter}}
```

Inspecting the adapter
----------------------

The adapter object provides **information about the underlying implementation** and hardware, and about what it is able or not to do. It advertises the following information:

 - **Limits** regroup all the **maximum and minimum** values that may limit the behavior of the underlying GPU and its driver. A typical examples is the maximum texture size. Supported limits are retrieved using `wgpuAdapterGetLimits`.
 - **Features** are non-mandatory **extensions** of WebGPU, that adapters may or may not support. They can be listed using `wgpuAdapterEnumerateFeatures` or tested individually with `wgpuAdapterHasFeature`.
 - **Properties** are extra information about the adapter, like its name, vendor, etc. Properties are retrieved using `wgpuAdapterGetProperties`.

```{note}
In the accompanying code, adapter capability inspection is enclosed in the `inspectAdapter()` function.
```

```{lit} C++, Utility functions (append, hidden)
void inspectAdapter(WGPUAdapter adapter) {
	{{Inspect adapter}}
}
```

```{lit} C++, Request adapter (append, hidden)
inspectAdapter(adapter);
```

### Limits

We can first list the limits that our adapter supports with `wgpuAdapterGetLimits`. This function takes as argument a `WGPUSupportedLimits` object where it writes the limits:

```{lit} C++, Inspect adapter
#ifndef __EMSCRIPTEN__
WGPUSupportedLimits supportedLimits = {};
supportedLimits.nextInChain = nullptr;

#ifdef WEBGPU_BACKEND_DAWN
bool success = wgpuAdapterGetLimits(adapter, &supportedLimits) == WGPUStatus_Success;
#else
bool success = wgpuAdapterGetLimits(adapter, &supportedLimits);
#endif

if (success) {
	std::cout << "Adapter limits:" << std::endl;
	std::cout << " - maxTextureDimension1D: " << supportedLimits.limits.maxTextureDimension1D << std::endl;
	std::cout << " - maxTextureDimension2D: " << supportedLimits.limits.maxTextureDimension2D << std::endl;
	std::cout << " - maxTextureDimension3D: " << supportedLimits.limits.maxTextureDimension3D << std::endl;
	std::cout << " - maxTextureArrayLayers: " << supportedLimits.limits.maxTextureArrayLayers << std::endl;
}
#endif // NOT __EMSCRIPTEN__
```

```{admonition} Implementation divergences
The procedure `wgpuAdapterGetLimits` returns a boolean in `wgpu-native` but a `WGPUStatus` in Dawn.

Also, as of April 1st, 2024, `wgpuAdapterGetLimits` is not implemented yet on Google Chrome, hence the `#ifndef __EMSCRIPTEN__` above.
```

Here is an example of what you could see:

```
Adapter limits:
 - maxTextureDimension1D: 32768
 - maxTextureDimension2D: 32768
 - maxTextureDimension3D: 16384
 - maxTextureArrayLayers: 2048
```

This means for instance that my GPU can handle 2D textures up to 32k, 3D textures up to 16k and texture arrays up to 2k layers.

```{note}
There are **many more limits**, that we will progressively introduce in the next chapters. The **full list** is [available in the spec](https://www.w3.org/TR/webgpu/#limits), together with their **default values**, which is also expected to be the minimum for an adapter to claim support for WebGPU.
```

### Features

Let us now focus on the `wgpuAdapterEnumerateFeatures` function, which enumerates the features of the WebGPU implementation, because its usage is very typical from WebGPU native.

We call the function **twice**. The **first time**, we provide a null pointer as the return, and as a consequence the function only returns the **number of features**, but not the features themselves.

We then dynamically **allocate memory** for storing this many items of result, and call the same function a **second time**, this time with a pointer to where the result should store its result.

```{lit} C++, Includes (append)
#include <vector>
```

```{lit} C++, Inspect adapter (append)
std::vector<WGPUFeatureName> features;

// Call the function a first time with a null return address, just to get
// the entry count.
size_t featureCount = wgpuAdapterEnumerateFeatures(adapter, nullptr);

// Allocate memory (could be a new, or a malloc() if this were a C program)
features.resize(featureCount);

// Call the function a second time, with a non-null return address
wgpuAdapterEnumerateFeatures(adapter, features.data());

std::cout << "Adapter features:" << std::endl;
std::cout << std::hex; // Write integers as hexadecimal to ease comparison with webgpu.h literals
for (auto f : features) {
	std::cout << " - 0x" << f << std::endl;
}
std::cout << std::dec; // Restore decimal numbers
```

The features are numbers corresponding to the enum `WGPUFeatureName` defined in `webgpu.h`. We use `std::hex` to display them as hexadecimal values, because this is how they are listed in `webgpu.h`.

You may notice very high numbers apparently not defined in this enum. These are **extensions** provided by our native implementation (e.g., defined in `wgpu.h` instead of `webgpu.h` in the case of `wgpu-native`).

### Properties

Lastly we can have a look at the adapter's properties, that contain information that we may want to display to the end user:

```{lit} C++, Inspect adapter (append)
WGPUAdapterProperties properties = {};
properties.nextInChain = nullptr;
wgpuAdapterGetProperties(adapter, &properties);
std::cout << "Adapter properties:" << std::endl;
std::cout << " - vendorID: " << properties.vendorID << std::endl;
if (properties.vendorName) {
	std::cout << " - vendorName: " << properties.vendorName << std::endl;
}
if (properties.architecture) {
	std::cout << " - architecture: " << properties.architecture << std::endl;
}
std::cout << " - deviceID: " << properties.deviceID << std::endl;
if (properties.name) {
	std::cout << " - name: " << properties.name << std::endl;
}
if (properties.driverDescription) {
	std::cout << " - driverDescription: " << properties.driverDescription << std::endl;
}
std::cout << std::hex;
std::cout << " - adapterType: 0x" << properties.adapterType << std::endl;
std::cout << " - backendType: 0x" << properties.backendType << std::endl;
std::cout << std::dec; // Restore decimal numbers
```

Here is a sample result with my nice Titan RTX:

```
Adapter properties:
 - vendorID: 4318
 - vendorName: NVIDIA
 - architecture:
 - deviceID: 7682
 - name: NVIDIA TITAN RTX
 - driverDescription: 536.23
 - adapterType: 0x0
 - backendType: 0x5
```

Conclusion
----------

 - The very first thing to do with WebGPU is to get the **adapter**.
 - Once we have an adapter, we can inspect its **capabilities** (limits, features) and properties.
 - We learned to use **asynchronous functions** and **double call** enumeration functions.

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)
