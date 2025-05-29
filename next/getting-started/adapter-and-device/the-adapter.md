The Adapter <span class="bullet">🟢</span>
===========

```{lit-setup}
:tangle-root: 005 - The Adapter - Next
:parent: 001 - Hello WebGPU - Next
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

#### Callback info

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
	WGPURequestAdapterStatus /* status */, // a success status
	WGPUAdapter /* adapter */, // the returned adapter
	WGPUStringView /* message */, // optional error message
	void* userdata1, // custom user data, as provided when requesting the adapter
	void* /* userdata2 */  // second custom user data
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
		/* mode = */ WGPUCallbackMode_AllowProcessEvents, // more on this later
		/* callback = */ onAdapterRequestEnded,
		/* userdata1 = */ &requestEnded, // custom user data is simply a pointer to a boolean in this case
		/* userdata2 = */ nullptr
	};

	// Adapter options
	WGPURequestAdapterOptions options = {};
	options.nextInChain = nullptr;

	// Start the request
	wgpuInstanceRequestAdapter(instance, &options, callbackInfo);

	// [...]
}
```

#### Waiting for the request to end

We know how to **start the request** and how to **handle the response**. But we do not know yet **how to wait** for the request to end before returning to the main function.

##### The bad idea

It might be tempting to just wait in a loop until the value of `requestEnded` becomes true, but this is a **terrible idea**.

```C++
// Start the request
wgpuInstanceRequestAdapter(instance, &options, callbackInfo);

// Do NOT do this! It is a BAD IDEA
while (!requestEnded) {
	// Even if waiting for 200ms before testing again, this is a terrible idea
	std::this_thread::sleep_for(std::chrono::milliseconds(200));
}
```

````{note}
This requires the following includes:

```{lit} C++, Includes (append)
#include <thread>
#include <chrono>
```
````

This could work if the asynchronous operation was running in a different thread, but **asynchronous does not mean multi-threaded**! Nothing can happen magically while our program is "busy" with this **infinite loop**.

The idea is rather that **we regularly hand out the execution to the WebGPU instance**, so that the instances checks on what async operation it can complete, and it is only within these moments that callbacks may get invoked.

```{admonition} wgpu-native
As of version `v24.0.0.2`, `wgpu-native` does not fully implement the asynchronous operation API and is thus sometimes **more permissive**. In this case, it would work because the callback is actually invoked right away within the call to `wgpuInstanceRequestAdapter`, even though we did not set the callback mode to `WGPUCallbackMode_AllowSpontaneous`.
```

##### A good way

The closer correct solution to what we have been trying to do is to **ask WebGPU to process pending operations** within the loop:

```C++
// Start the request
wgpuInstanceRequestAdapter(instance, &options, callbackInfo);

while (!requestEnded) {
	// Hand the execution to the WebGPU instance so that it can check for
	// pending async operations, in which case it invokes our callbacks.
	wgpuInstanceProcessEvents(instance);

	// Waiting for 200ms to avoid asking too often to process events
	std::this_thread::sleep_for(std::chrono::milliseconds(200));
}
```

```{note}
This works, as long as the **callback mode** we set in the callback info is at least `WGPUCallbackMode_AllowProcessEvents` but would not work with `WGPUCallbackMode_WaitAnyOnly`.
```

```{admonition} wgpu-native
As of version `v24.0.0.2`, `wgpu-native` does not implement `wgpuInstanceProcessEvents`. In this very case, we may skip it because the adapter requests ends right within the call to `wgpuInstanceRequestAdapter`.
```

This is an OK solution, although we still need to manage ourselves the `requestEnded` test and the `sleep()` operation. This solution is **all right for the adapter/device request** and many simple cases.

I do not want to make this chapter any longer, so I detail the **more advanced** approach in the [*Futures and asynchronous operations*](../../appendices/futures-and-asynchronous-operations.md) appendix.

##### With emscripten

When our code runs in the main thread of a web page, **it must not completely sleep** like we do with `this_thread::sleep_for`, otherwise the page becomes unresponsive.

Instead, we use the special `emscripten_sleep()`, which yields the control **back to the browser** for some time (a bit like calling `setTimeout` in JavaScript). We thus add an `#ifdef` branch inside our wait loop:

```C++
while (!requestEnded) {
	wgpuInstanceProcessEvents(instance);

	// Waiting for 200ms to avoid asking too often to process events
#ifdef __EMSCRIPTEN__
	emscripten_sleep(100);
#else
	std::this_thread::sleep_for(std::chrono::milliseconds(200));
#endif
}
```

This requires to add `emscripten.h` to our includes:

```{lit} C++, Includes (append)
#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#endif
```

```{note}
Since we are yielding back to the browser, it is not 100% necessary to call `wgpuInstanceProcessEvents` in this very case because the browser already does this during our 200 ms of sleep.
```

In order to use `emscripten_sleep()` with emscripten, we must add a **custom link option** in `CMakeLists.txt`, in the `if (EMSCRIPTEN)` block:

```{lit} CMake, Emscripten-specific options (append)
# Enable the use of emscripten_sleep()
target_link_options(App PRIVATE -sASYNCIFY)
```

```{note}
Using `ASYNCIFY` has an impact on the size of the WebAssembly module. It is possible to avoid using this option by moving all steps of the app initialization into the main animation callback. This is exemplified in [`step030-no-asyncify`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-no-asyncify) (slightly outdated, but the design pattern holds).
```

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

We can now wrap the whole adapter request in the following `requestAdapterSync()` function, which I provide so that we do not spend too much time on **boilerplate** code (the important part here is that you get the idea of the **asynchronous callback** described above):

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
		/* mode = */ WGPUCallbackMode_AllowProcessEvents,
		/* callback = */ onAdapterRequestEnded,
		/* userdata1 = */ &userData,
		/* userdata2 = */ nullptr
	};

	// Call to the WebGPU request adapter procedure
	wgpuInstanceRequestAdapter(instance, options, callbackInfo);

	// We wait until userData.requestEnded gets true

	// Hand the execution to the WebGPU instance so that it can check for
	// pending async operations, in which case it invokes our callbacks.
	// NB: We test once before the loop not to wait for 200ms in case it is
	// already ready
	wgpuInstanceProcessEvents(instance);

	while (!userData.requestEnded) {
		// Waiting for 200 ms to avoid asking too often to process events
		sleepForMilliseconds(200);

		wgpuInstanceProcessEvents(instance);
	}

	return userData.adapter;
}
```

```{lit} C++, Utility functions (hidden)
// All utility functions are regrouped here
{{Request adapter function}}
```

````{note}
Since we are going to use it a couple of times, **I moved the `#ifdef EMSCRIPTEN` exception into a dedicated utility function** `sleepForMilliseconds()` that we define before `requestAdapterSync()`:

```{lit} C++, Utility functions (prepend, hidden)
{{Define sleepForMilliseconds}}
```

```{lit} C++, Define sleepForMilliseconds
void sleepForMilliseconds(unsigned int milliseconds) {
#ifdef __EMSCRIPTEN__
	emscripten_sleep(milliseconds);
#else
	std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
#endif
}
```
````

The only **missing block** in this function is **the handling error messages**, which has type `WGPUStringView`.

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
		wgpuStringView.data == nullptr
		? std::string_view()
		: wgpuStringView.length == WGPU_STRLEN
		? std::string_view(wgpuStringView.data)
		: std::string_view(wgpuStringView.data, wgpuStringView.length);
}
```

Note that this requires the `string_view` header:

```{lit} C++, Includes (append)
#include <string_view>
```

And since we are at it, I suggest we define some opposite conversion functions:

```{lit} C++, Define toWgpuStringView
WGPUStringView toWgpuStringView(std::string_view stdStringView) {
	return { stdStringView.data(), stdStringView.size() };
}
WGPUStringView toWgpuStringView(const char* cString) {
	return { cString, WGPU_STRLEN };
}
```

````{note}
We define these **before** the `requestAdapterSync` function:

```{lit} C++, Utility functions (prepend)
{{Define toStdStringView}}
{{Define toWgpuStringView}}
```
````

Finally, to display the error message, we may now use a regular `std::cout`:

```{lit} C++, Display error message
std::cerr << "Error while requesting adapter: " << toStdStringView(message) << std::endl;
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

Looking at the overall structure of our program, this goes right after the creation of the instance, before the main part of the program:

```{lit} C++, Create things
// Create all WebGPU object we use throughout the program
{{Create WebGPU instance}}
{{Check WebGPU instance}}
{{Request adapter}}
```

```{lit} C++, file: main.cpp (replace)
{{Includes}}

{{Utility functions in main.cpp}}

int main() {
	{{Create things}}

	{{Main body}}

	{{Release things}}

	return 0;
}
```

```{lit} C++, Utility functions in main.cpp (hidden)
{{Utility functions}}
```

```{lit} C++, Main body (hidden)
```


### Destruction

Like for the WebGPU instance, we must release the adapter once we no longer use it:

```{lit} C++, Release adapter
wgpuAdapterRelease(adapter);
```

This goes next to destroying the instance:

```{lit} C++, Release things
{{Release adapter}}
{{Release WebGPU instance}}
```

```{note}
The adapter keeps a reference to its parent instance, so it is OK to release the instance first, it will keep on living until the adapter is destroyed and releases on its turn the instance.
```

Inspecting the adapter
----------------------

All right, **we finally have an adapter**!

The adapter object provides **information about the underlying implementation** and hardware, and about what it is able or not to do. It advertises the following information:

 - **Limits** regroup all the **maximum and minimum** values that may limit the behavior of the underlying GPU and its driver. A typical examples is the maximum texture size. Supported limits are retrieved using `wgpuAdapterGetLimits`.
 - **Features** are non-mandatory **extensions** of WebGPU, that adapters may or may not support. They can be listed using `wgpuAdapterEnumerateFeatures` or tested individually with `wgpuAdapterHasFeature`.
 - **Properties** are extra information about the adapter, like its name, vendor, etc. Properties are retrieved using `wgpuAdapterGetProperties`.

````{note}
To avoid ending up with a huge `main()` function, I suggest to enclose the adapter capability inspection in a dedicated `inspectAdapter()` function:

```{lit} C++, Utility functions (append)
void inspectAdapter(WGPUAdapter adapter) {
	{{Inspect adapter}}
}
```

We call this right after creating the adapter:

```{lit} C++, Create things (append)
inspectAdapter(adapter);
```
````

### Limits

We can first list the limits that our adapter supports with `wgpuAdapterGetLimits`. This function takes as argument a `WGPUSupportedLimits` object where it writes the limits:

```{lit} C++, Inspect adapter
WGPULimits supportedLimits = {};
supportedLimits.nextInChain = nullptr;

bool success = wgpuAdapterGetLimits(adapter, &supportedLimits) == WGPUStatus_Success;

if (success) {
	std::cout << "Adapter limits:" << std::endl;
	std::cout << " - maxTextureDimension1D: " << supportedLimits.maxTextureDimension1D << std::endl;
	std::cout << " - maxTextureDimension2D: " << supportedLimits.maxTextureDimension2D << std::endl;
	std::cout << " - maxTextureDimension3D: " << supportedLimits.maxTextureDimension3D << std::endl;
	std::cout << " - maxTextureArrayLayers: " << supportedLimits.maxTextureArrayLayers << std::endl;
}
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

Let us now focus on the `wgpuAdapterGetFeatures` function, which enumerates the features of the WebGPU implementation, because its usage is very typical from WebGPU native.

This is a *getter* function that may dynamically allocate memory, for the array of features. For this reason, it is accompanied with a freeing counterpart, namely `wgpuSupportedFeaturesFreeMembers`:

```{lit} C++, Inspect adapter (append)
// Prepare the struct where features will be listed
WGPUSupportedFeatures features;

// Get adapter features. This may allocate memory that we must later free with wgpuSupportedFeaturesFreeMembers()
wgpuAdapterGetFeatures(adapter, &features);

std::cout << "Adapter features:" << std::endl;
std::cout << std::hex; // Write integers as hexadecimal to ease comparison with webgpu.h literals
for (size_t i = 0; i < features.featureCount; ++i) {
	std::cout << " - 0x" << features.features[i] << std::endl;
}
std::cout << std::dec; // Restore decimal numbers

// Free the memory that had potentially been allocated by wgpuAdapterGetFeatures()
wgpuSupportedFeaturesFreeMembers(features);
// One shall no longer use features beyond this line.
```

The features are numbers corresponding to the enum `WGPUFeatureName` defined in `webgpu.h`. We use `std::hex` to display them as hexadecimal values, because this is how they are listed in `webgpu.h`.

You may get for instance:

```
Adapter features:
 - 0x1
 - 0x2
 - 0x4
 - 0x3
 - 0x9
 - 0xa
 - 0xb
 - 0xc
 - 0xd
 - 0x10
 - 0x30001
 - 0x30002
 - 0x30003
 - 0x30004
 - 0x30005
 - 0x30006
 - 0x30007
 - 0x30008
 - 0x30009
 - 0x3000a
 - 0x3000b
 - 0x30025
 - 0x30024
 - 0x3000e
 - 0x3000f
 - 0x30010
 - 0x30017
 - 0x3001a
 - 0x3001b
 - 0x3001c
 - 0x3001d
 - 0x3001e
 - 0x3001f
 - 0x30021
 - 0x30022
 - 0x30023
```

You may notice very high numbers apparently not defined in this enum. These are **extensions** provided by our native implementation (e.g., defined in `wgpu.h` instead of `webgpu.h` in the case of `wgpu-native`).

### Information

Lastly we can have a look at the adapter information, which contain properties that we may want to display to the end user. Here again, there is both a getter (`wgpuAdapterGetInfo`) and a free function (`wgpuAdapterInfoFreeMembers`). Notice how we also reuse our `toStdStringView` utility function:

```{lit} C++, Inspect adapter (append)
WGPUAdapterInfo properties;
properties.nextInChain = nullptr;
wgpuAdapterGetInfo(adapter, &properties);
std::cout << "Adapter properties:" << std::endl;
std::cout << " - vendorID: " << properties.vendorID << std::endl;
std::cout << " - vendorName: " << toStdStringView(properties.vendor) << std::endl;
std::cout << " - architecture: " << toStdStringView(properties.architecture) << std::endl;
std::cout << " - deviceID: " << properties.deviceID << std::endl;
std::cout << " - name: " << toStdStringView(properties.device) << std::endl;
std::cout << " - driverDescription: " << toStdStringView(properties.description) << std::endl;
std::cout << std::hex;
std::cout << " - adapterType: 0x" << properties.adapterType << std::endl;
std::cout << " - backendType: 0x" << properties.backendType << std::endl;
std::cout << std::dec; // Restore decimal numbers
wgpuAdapterInfoFreeMembers(properties);
```

Here is a sample result with my nice Titan RTX:

```
Adapter properties:
 - vendorID: 4318
 - vendorName: NVIDIA
 - architecture:
 - deviceID: 7682
 - name: NVIDIA TITAN RTX
 - driverDescription: 560.94
 - adapterType: 0x1
 - backendType: 0x6
```

Conclusion
----------

Congratulation, this was not an easy chapter, but we met with **a lot of important idioms** that we will be able to reuse later on. We saw in particular that:

 - The very first thing to do with WebGPU is to get the **adapter**.
 - Once we have an adapter, we can inspect its **capabilities** (limits, features) and properties.
 - We learned to use **asynchronous functions**.
 - We have learned about `WGPUStringView`.

```{note}
For more information about asynchronous operations in WebGPU, you may consult the [official specification](https://webgpu-native.github.io/webgpu-headers/Asynchronous-Operations.html).
```

*Resulting code:* [`step005-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005-next)
