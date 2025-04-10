The Adapter <span class="bullet">🟢</span>
===========

```{lit-setup}
:tangle-root: 005 - The Adapter - Next
:parent: 001 - Hello WebGPU - Next
:debug:
```

*Resulting code:* [`step005-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005-next)

Before getting our hands on a WebGPU **device**, we need to select an **adapter**.

```{tip}
This chapter is a bit dense because it is also the occasion to **introduce multiple key concepts** of the WebGPU API, in particular the **asynchronous functions** and the `WGPUStringView` (that represents **character strings**).

Take the time to understand these concepts, it is going to pay off later on!
```

Why do we need an adapter?
--------------------------

The same host system may expose **multiple adapters** if it has access to multiple physical GPUs. It may also have an adapter that represents an emulated/virtual device.

```{note}
It is common that high-end laptops have **two physical GPUs**, a **high performance** one (sometimes called *discrete*) and a **low energy** consumption one (that is usually integrated inside the CPU chip).
```

Each adapter advertises a list of optional **features** and **supported limits** that it can handle. These are used to determine the overall capabilities of the system before **requesting the device**.

> 🤔 Why do we have both an **adapter** and then a **device** abstraction?

The idea is to limit the "it worked on my machine" issue you could encounter when trying your program on a different machine. The **adapter** is used to **access the capabilities** of the user's hardware, which are used to select the behavior of your application among very different code paths. Once a code path is chosen, a **device** is created with **the capabilities we choose**.

Only the capabilities selected for this device are then allowed in the rest of the application. This way, it is **not possible to inadvertently rely on capabilities specific to your own machine**.

```{figure} /images/device-creation.png
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
WGPUFuture wgpuInstanceRequestAdapter(
	WGPUInstance instance,
	WGPU_NULLABLE WGPURequestAdapterOptions const * options,
	WGPURequestAdapterCallbackInfo callbackInfo
);
```

```{note}
It is always informative to have a look at how a function is defined in `webgpu.h`!
```

The second argument is a set of **options**, that is a bit like the **descriptor** that we find in `wgpuCreateSomething` functions, we detail them below. The `WGPU_NULLABLE` flag is an empty define that is only here to tell the human reader (i.e., us) that it is allowed to leave the argument to `nullptr` to use **default options**.

### Asynchronous function

The last argument and the return type `WGPUFuture` go together, and reveal yet another **WebGPU idiom**. Indeed, the function `wgpuInstanceRequestAdapter` is **asynchronous**. This means that instead of directly returning a `WGPUAdapter` object, this request function remembers a **callback**, i.e., a function that will be called whenever the request ends.

```{note}
Asynchronous functions are used in multiple places in the WebGPU API, whenever an operation may take time. Actually, **none of the WebGPU functions** takes time to return. This way, the CPU program that we are writing never gets blocked by a lengthy operation!
```

Let us now look at the **callback info** that `wgpuInstanceRequestAdapter` expects. Here is the definition of the `WGPURequestAdapterCallbackInfo` function type:

```C++
// Definition of the WGPURequestAdapterCallbackInfo function type as defined in webgpu.h
struct WGPURequestAdapterCallbackInfo {
    WGPUChainedStruct * nextInChain;
    WGPUCallbackMode mode;
    WGPURequestAdapterCallback callback;
    WGPU_NULLABLE void* userdata1;
    WGPU_NULLABLE void* userdata2;
};
```

The main element of this structure is the `callback` field, which is a **function pointer** whose type `WGPURequestAdapterCallback` is defined as follows:

```C++
// Definition of the WGPURequestAdapterCallback function type as defined in webgpu.h
typedef void (*WGPURequestAdapterCallback)(
	WGPURequestAdapterStatus status,
	WGPUAdapter adapter,
	struct WGPUStringView message,
	void* userdata1,
	void* userdata2
);
```

This is the **callback function** that receives the **requested adapter** as an argument, together with **status** information (that tells whether the request failed and why), when the request ends.

This function also also receive these mysterious `userdata` **pointers** that have the same name than in the **callback info**. These pointers can be **anything you want**, they are a mean to **pass some context information** from the call to `wgpuInstanceRequestAdapter` to the body of the callback.

```{note}
When directly using the C API like we do here, we generally only need one of the two `userdata` pointers. The second is used when building higher level abstractions around the callback.
```

Here is a rough example to **illustrate the `userdata` mechanism**:

```C++
// This is our callback function, whose signature corresponds to WGPURequestAdapterCallback
void onAdapterRequestEnded(
	WGPURequestAdapterStatus status, // a success status
	WGPUAdapter adapter, // the returned adapter
	WGPUStringView message, // optional error message
	void* userdata1, // custom user data, as provided when requesting the adapter
	void* userdata2  // second custom user data
) {
	// [...] Do something with the adapter

	// Manipulate user data: we access here the 'requestEnded' variable
	// that is defined in the main() function below.
	bool* pRequestEnded = reinterpret_cast<bool*>(userdata1);
	*pRequestEnded = true;
}

int main(int, char**) {
	// [...]

	bool requestEnded = false;

	// Build callback info
	WGPURequestAdapterCallbackInfo callbackInfo = {
	    /* nextInChain = */ nullptr,
	    /* mode = */ WGPUCallbackMode_AllowSpontaneous,
	    /* callback = */ onAdapterRequestEnded,
	    /* userdata1 = */ &requestEnded, // custom user data is simply a pointer to a boolean in this case
	    /* userdata2 = */ false
	};

	// Start the request
	wgpuInstanceRequestAdapter(instance, &options, callbackInfo);

	// [...]
}
```

We see in the next section a **more complete use** of this context in order to retrieve the adapter once the request is done.

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
 * is roughly equivalent to the JavaScript
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
	// is to convey what we want to capture through the userdata1 pointer,
	// provided as the last argument of wgpuInstanceRequestAdapter and received
	// by the callback as its last argument.
	auto onAdapterRequestEnded = [](
		WGPURequestAdapterStatus status,
		WGPUAdapter adapter,
		WGPUStringView message,
		void* userdata1,
		void* /* userdata2 */
	) {
		UserData& userData = *reinterpret_cast<UserData*>(userdata1);
		if (status == WGPURequestAdapterStatus_Success) {
			userData.adapter = adapter;
		} else {
			{{Display error message}}
		}
		userData.requestEnded = true;
	};

	// Build the callback info
	WGPURequestAdapterCallbackInfo callbackInfo = {
		/* nextInChain = */ nullptr,
		/* mode = */ WGPUCallbackMode_AllowSpontaneous,
		/* callback = */ onAdapterRequestEnded,
		/* userdata1 = */ &userData,
		/* userdata2 = */ false
	};

	// Call to the WebGPU request adapter procedure
	wgpuInstanceRequestAdapter(instance, options, callbackInfo);

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

There are **two missing blocks** in this function: **(a)** handling the error message, which has type `WGPUStringView` and **(b)** waiting for the request to end.

#### Displaying `WGPUStringView`

All strings of text in the WebGPU native API use the type `WGPUStringView`. This is very close to a regular `const char *`, except that it **may or may not be null terminated**. Let's has a look at its definition:

```C++
struct WGPUStringView {
    WGPU_NULLABLE char const * data;
    size_t length;
};
```

The `data` field is the address of the **first character** of the string. The `length` field tells how many consecutive characters after this address constitute the string. In this regard, it is close to a [`std::string_view`](https://en.cppreference.com/w/cpp/string/basic_string_view).

**But** the `length` field may also be set to the **special value** `WGPU_STRLEN`. In this case, the string is **null-terminated**, meaning it consists in all the characters that follow the address at which `data` points, until one of them is the special null character `'\0'`.

This special case makes it easy enough to build a `WGPUStringView`:

```C++
WGPUStringView myStringView = {
    /* data = */ "lorem ipsum, dolor sit amet", // string literals like this one have an implicit \0 at the end
    /* length = */ WGPU_STRLEN; // special value meaning "look for \0 to find the end of the string"
};
```

In order to convert back, I suggest we create a **small utility function** to turn a `WGPUStringView` into a `std::string_view`, which plays along well with C++ standard library:

```{lit} C++, Define toStdStringView
std::string_view toStdStringView(WGPUStringView wgpuStringView) {
	return
		wgpuStringView.length == WGPU_STRLEN
		? std::string_view(wgpuStringView.data)
		: std::string_view(wgpuStringView.data, wgpuStringView.length);
}
```

Note that this requires the `string_view` header:

```{lit} C++, Includes (append)
#include <string_view>
```

````{note}
We define this **before** the `requestAdapterSync` function:

```{lit} C++, Utility functions (prepend)
{{Define toStdStringView}}
```
````

Finally, to display the error message, we may now use a regular `std::cout`:

```{lit} C++, Display error message
std::cerr << "Error while requesting adapter: " << toStdStringView(message) << std::endl;
```

#### Waiting for the request to end

We know how to request the adpater, and how to handle the response. But we do not know yet **how to wait** for the request to end before returning to the main function.

To keep track of ongoing asynchronous operations, each function that starts such an operation **returns a `WGPUFuture`**, which is some sort of internal ID that **identifies the operation**.

```C++
WGPUFuture adapterRequest = wgpuInstanceRequestAdapter(instance, &options, callbackInfo);
```

```{note}
Although it is technically just an integer value, the `WGPUFuture` should be treated as an **opaque handle**, i.e., one should not try to deduce anything from the very value of this ID.
```

**WIP line** *Maybe move this section up after Asynchronous function*

```C++
WGPUWaitStatus wgpuInstanceWaitAny(WGPUInstance, size_t futureCount, WGPUFutureWaitInfo * futures, 0 /* timeoutNS */);
```

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

#### Using our helper function

Now that our `requestAdapterSync` function is complete, we can call it in out main function. After creating the WebGPU instance, we get the adapter as follows:

```{lit} C++, Request adapter
std::cout << "Requesting adapter..." << std::endl;

WGPURequestAdapterOptions adapterOpts = {};
adapterOpts.nextInChain = nullptr;
WGPUAdapter adapter = requestAdapterSync(instance, &adapterOpts);

std::cout << "Got adapter: " << adapter << std::endl;
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
 - We learned to use **asynchronous functions**.
 - We have learned about `WGPUStringView`.

```{note}
For more information about asynchronous operations in WebGPU, you may consult the [official specification](https://webgpu-native.github.io/webgpu-headers/Asynchronous-Operations.html).
```

*Resulting code:* [`step005-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005-next)
