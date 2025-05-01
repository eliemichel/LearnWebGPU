The Device <span class="bullet">🟢</span>
==========

```{lit-setup}
:tangle-root: 010 - The Device - Next
:parent: 005 - The Adapter - Next
```

*Resulting code:* [`step010-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010-next)

A WebGPU **device** represents a **context** of use of the API. All the objects that we create (geometry, textures, etc.) are owned by the device.

The device is requested from an **adapter** by specifying the **subset of limits and features** that we are interesed in. Once the device is created, the adapter is generally no longer used: **the only capabilities that matter** to the rest of the application are the one of the device.

Device request
--------------

### Helper function

Requesting the device **looks a lot like requesting the adapter**, so we will start from a similar function. The key differences lie in the **device descriptor**, which we detail below.

```{lit} C++, Utility functions (append, hidden)
{{Request device function}}
```

```{lit} C++, Request device function
/**
 * Utility function to get a WebGPU device, so that
 *     WGPUDevice device = requestDeviceSync(adapter, options);
 * is roughly equivalent to
 *     const device = await adapter.requestDevice(descriptor);
 * It is very similar to requestAdapter
 */
WGPUDevice requestDeviceSync(WGPUInstance instance, WGPUAdapter adapter, WGPUDeviceDescriptor const * descriptor) {
	struct UserData {
		WGPUDevice device = nullptr;
		bool requestEnded = false;
	};
	UserData userData;

	// The callback
	auto onDeviceRequestEnded = [](
		WGPURequestDeviceStatus status,
		WGPUDevice device,
		WGPUStringView message,
		void* userdata1,
		void* /* userdata2 */
	) {
		UserData& userData = *reinterpret_cast<UserData*>(userdata1);
		if (status == WGPURequestDeviceStatus_Success) {
			userData.device = device;
		} else {
			std::cerr << "Error while requesting device: " << toStdStringView(message) << std::endl;
		}
		userData.requestEnded = true;
	};

	// Build the callback info
	WGPURequestDeviceCallbackInfo callbackInfo = {
		/* nextInChain = */ nullptr,
		/* mode = */ WGPUCallbackMode_AllowProcessEvents,
		/* callback = */ onDeviceRequestEnded,
		/* userdata1 = */ &userData,
		/* userdata2 = */ nullptr
	};

	// Call to the WebGPU request adapter procedure
	wgpuAdapterRequestDevice(adapter, descriptor, callbackInfo);

	// Hand the execution to the WebGPU instance until the request ended
	wgpuInstanceProcessEvents(instance);
	while (!userData.requestEnded) {
		sleepForMilliseconds(200);
		wgpuInstanceProcessEvents(instance);
	}

	return userData.device;
}
```

In the **accompanying code** ([`step010-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010-next)), I move these utility functions into `webgpu-utils.cpp`. Unfold the following note to detail all the changes that this implies.

````{admonition} Note - Moving utilities to webgpu-utils.cpp
:class: foldable note

First, we declare our utility functions in a new header file `webgpu-utils.h`:

```{lit} C++, file: webgpu-utils.h
#pragma once

#include <webgpu/webgpu.h>

#include <string_view>

/**
 * Convert a WebGPU string view into a C++ std::string_view.
 */
std::string_view toStdStringView(WGPUStringView wgpuStringView);

/**
 * Convert a C++ std::string_view into a WebGPU string view.
 */
WGPUStringView toWgpuStringView(std::string_view stdStringView);

/**
 * Convert a C string into a WebGPU string view
 */
WGPUStringView toWgpuStringView(const char* cString);

/**
 * Sleep for a given number of milliseconds.
 * This works with both native builds and emscripten, provided that -sASYNCIFY
 * compile option is provided when building with emscripten.
 */
void sleepForMilliseconds(unsigned int milliseconds);

/**
 * Utility function to get a WebGPU adapter, so that
 *     WGPUAdapter adapter = requestAdapter(options);
 * is roughly equivalent to
 *     const adapter = await navigator.gpu.requestAdapter(options);
 */
WGPUAdapter requestAdapterSync(WGPUInstance instance, WGPURequestAdapterOptions const * options);

/**
 * Utility function to get a WebGPU device, so that
 *     WGPUAdapter device = requestDevice(adapter, options);
 * is roughly equivalent to
 *     const device = await adapter.requestDevice(descriptor);
 * It is very similar to requestAdapter
 */
WGPUDevice requestDeviceSync(WGPUInstance instance, WGPUAdapter adapter, WGPUDeviceDescriptor const * descriptor);

/**
 * An example of how we can inspect the capabilities of the hardware through
 * the adapter object.
 */
void inspectAdapter(WGPUAdapter adapter);
```

Then, we move the "Utility functions" block in a new `webgpu-utils.cpp` file. Do not forget to copy relevant includes:

```{lit} C++, file: webgpu-utils.cpp
#include "webgpu-utils.h"

#include <iostream>
#include <vector>
#include <cassert>

#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#else // __EMSCRIPTEN__
#  include <thread>
#  include <chrono>
#endif // __EMSCRIPTEN__

{{Utility functions}}
```

We remove utility functions from main.cpp and include our new `webgpu-utils.h` in `main.cpp` instead:

```{lit} C++, Includes (prepend)
#include "webgpu-utils.h"
```

```{lit} C++, Utility functions in main.cpp (replace)
```

In `CMakeLists.txt`, we now have multiple source files in our executable. We list all our source files; header files are optional, but including them helps IDEs display them correctly in the project's structure:

```{lit} CMake, App source files
main.cpp
webgpu-utils.h
webgpu-utils.cpp
```

These go in the call to `add_executable` that define our `App` target:

```{lit} CMake, Define app target (replace)
{{Dependency subdirectories}}

add_executable(App
	{{App source files}}
)

{{Link libraries}}
```
````

### Usage

In the main function, after getting the adapter, we can request the device:

```{lit} C++, Request device
std::cout << "Requesting device..." << std::endl;

WGPUDeviceDescriptor deviceDesc = WGPU_DEVICE_DESCRIPTOR_INIT;
{{Build device descriptor}}
WGPUDevice device = requestDeviceSync(instance, adapter, &deviceDesc);

std::cout << "Got device: " << device << std::endl;
```

```{lit} C++, Create things (append, hidden)
{{Request device}}
```

```{tip}
I use here the `WGPU_DEVICE_DESCRIPTOR_INIT` macro defined in `webgpu.h` to assign **default values to all fields** of `deviceDesc`. Such an initializer macro is **available for all structs** of `webgpu.h`, I recommend using them!
```

```{admonition} wgpu-native
As of `v24.0.0.2`, wgpu-native does not support init macros yet. It should come shortly though.
```

And of course, we release the device when the program ends:

```{lit} C++, Release things (prepend)
wgpuDeviceRelease(device);
```

````{note}
The adapter can be **released before the device**. Actually we often release it as soon as we have our device and never use it again.

```{lit} C++, Create things (append)
// We no longer need to access the adapter once we have the device
{{Release adapter}}
```

```{lit} C++, Release things (replace)
wgpuDeviceRelease(device);
{{Release WebGPU instance}}
```

````

```{important}
An adapter **may only provide one device** during its lifetime. It is then "**consumed**", meaning that if you need to **create another device**, you also need to **request a new adapter** (which may correspond to the same underlying physical device).
```

Device descriptor
-----------------

A lot goes in the device descriptor, so let us have a look at its definition:

```C++
// Definition of the WGPUDeviceDescriptor struct in webgpu.h
struct WGPUDeviceDescriptor {
    WGPUChainedStruct * nextInChain;
    WGPUStringView label;
    size_t requiredFeatureCount;
    WGPUFeatureName const * requiredFeatures;
    WGPU_NULLABLE WGPULimits const * requiredLimits;
    WGPUQueueDescriptor defaultQueue;
    WGPUDeviceLostCallbackInfo deviceLostCallbackInfo;
    WGPUUncapturedErrorCallbackInfo uncapturedErrorCallbackInfo;
};
```

First of all, we recognize the now usual `nextInChain` pointer that starts all such structures. We **do not use any extension** for now so we can leave it to `nullptr`, which the `WGPU_DEVICE_DESCRIPTOR_INIT` macro ensured.

```C++
// This is only needed if not using WGPU_DEVICE_DESCRIPTOR_INIT
deviceDesc.nextInChain = nullptr;
```

### Label

Then comes the **label**, which is present in almost all descriptors as well. This is used to give a name to your WebGPU objects, so that **error messages get easier to read**.

```{lit} C++, Build device descriptor
// Any name works here, that's your call
deviceDesc.label = toWgpuStringView("My Device");
```

After this message will say something like *"error with device 'My Device'..."*, which is not that important for devices because you will typically only have one, but **when it comes to buffers or textures**, it is very helpful to **know which one is causing an issue**!

### Features

In the previous chapter, we saw that adapters can list *features* which may or may not be available. We can pick a subset of the list of **available features** and request the device to support them.

This kind of **array argument** is always specified through **a pair of two fields** in a C API like WebGPU: **(a)** the number of items and **(b)** the address in memory of the first item, the other one being expected to lie **contiguously in memory**.

In our case, we do not need any feature for now, so we can leave this to an **empty array**:

```C++
deviceDesc.requiredFeatureCount = 0;
deviceDesc.requiredFeatures = nullptr;
```

````{note}
When we will want to request for some feature, we will typically do it through a `std::vector` like this:

```{lit} C++, Build device descriptor (append)
std::vector<WGPUFeatureName> features;
{{List required features}}
deviceDesc.requiredFeatureCount = features.size();
deviceDesc.requiredFeatures = features.data();
// Make sure 'features' lives until the call to wgpuAdapterRequestDevice!
```

```{lit} C++, List required features (hidden)
// No required feature for now
```

```{lit} C++, Includes (append)
#include <vector>
```
````

### Limits

We may specify limits that we need the device to support through the `requiredLimits` field. Note that this is a pointer marked as `WGPU_NULLABLE`, because we can set it to `nullptr` to let limits to the [default values](https://www.w3.org/TR/webgpu/#limit-default).

```C++
deviceDesc.requiredLimits = nullptr;
```

Alternatively, we can specify the address of a `WGPULimits` object:

```{lit} C++, Build device descriptor (append)
WGPULimits requiredLimits = WGPU_LIMITS_INIT;
{{Specify required limits}}
deviceDesc.requiredLimits = &requiredLimits;
// Make sure that the 'requiredLimits' variable lives until the call to wgpuAdapterRequestDevice!
```

```{note}
If you look at the actual values set by `WGPU_LIMITS_INIT` in `webgpu.h`, they seem to be different from the default values listed in the [WebGPU specification](https://www.w3.org/TR/webgpu/#limit-default) and look like `WGPU_LIMIT_U32_UNDEFINED`. These **special values** mean "use whatever the standard default is" to the WebGPU backend.
```

Let us use the default values of `requiredLimits` for now, I will try to **mention in each chapter which limit it is related to** so that we can progressively populate this.

```{lit} C++, Specify required limits
// We leave 'requiredLimits' untouched for now
```

### Queue

The field `defaultQueue` is a substructure of the device descriptor, which is pretty minimal but may become in future version of WebGPU and/or through extensions:

```C++
// Definition of the WGPUQueueDescriptor struct in webgpu.h
struct WGPUQueueDescriptor {
    WGPUChainedStruct * nextInChain;
    WGPUStringView label;
};
```

The value of `deviceDesc.defaultQueue.nextInChain` was automatically initialized to `nullptr` when using `WGPU_DEVICE_DESCRIPTOR_INIT`, so all we may do is give a name to the queue (which is optional because here again we only have one queue):

```{lit} C++, Build device descriptor (append)
deviceDesc.defaultQueue.label = toWgpuStringView("The Default Queue");
```

### Device Lost Callback

The last two fields of the descriptor are **callback info** structures, like we have seen with adapter and device request functions.

The only thing that changes from one `WGPUSomethingCallbackInfo` to another is the type of the core `callback` field, so let us have a look at `WGPUDeviceLostCallback` and define a function that has exactly that signature:

```{lit} C++, Device Lost Callback
auto onDeviceLost = [](
	WGPUDevice const * device,
	WGPUDeviceLostReason reason,
	struct WGPUStringView message,
	void* /* userdata1 */,
	void* /* userdata2 */
) {
	// All we do is display a message when the device is lost
    std::cout
    	<< "Device " << device << " was lost: reason " << reason
    	<< " (" << toStdStringView(message) << ")"
    	<< std::endl;
};
```

```{note}
I define this function using a [lambda expression](https://en.cppreference.com/w/cpp/language/lambda) (like we did in `requestDeviceSync`) in order to place it **close to the device descriptor definition**, but it could be a regular function.
```

The possible reasons for a lost device are listed in `webgpu.h`:

```C++
enum WGPUDeviceLostReason {
	// This is probably suspicious:
    WGPUDeviceLostReason_Unknown = 0x00000001,
    // This is raised at the end of your program if you call
    // wgpuInstanceProcessEvents after releasing the device:
    WGPUDeviceLostReason_Destroyed = 0x00000002,
    // This happens when the instance got destroyed by the web browser or the
    // program terminates without processing events after the device was
    // destroyed:
    WGPUDeviceLostReason_InstanceDropped = 0x00000003,
    // This happens when the device could not even be created:
    WGPUDeviceLostReason_FailedCreation = 0x00000004,
    // Special value, never used:
    WGPUDeviceLostReason_Force32 = 0x7FFFFFFF
};
```

We set this callback in our `deviceLostCallbackInfo`, and set the mode to `AllowProcessEvents` like we did with other callbacks:

```{lit} C++, Build device descriptor (append)
{{Device Lost Callback}}
deviceDesc.deviceLostCallbackInfo.callback = onDeviceLost;
deviceDesc.deviceLostCallbackInfo.mode = WGPUCallbackMode_AllowProcessEvents;
```

### Uncaptured Error Callback

This last callback is very important, as it defines a function that will be invoked **whenever something goes wrong** with the API. It this is very likely to happen, and the information messages passed to this callback are very valuable to help debugging our application, so we **must not overlook it**!

Here again, we define a callback that displays information about the device error:

```{lit} C++, Device Error Callback
auto onDeviceError = [](
	WGPUDevice const * device,
	WGPUErrorType type,
	struct WGPUStringView message,
	void* /* userdata1 */,
	void* /* userdata2 */
) {
    std::cout
    	<< "Uncaptured error in device " << device << ": type " << type
    	<< " (" << toStdStringView(message) << ")"
    	<< std::endl;
};
```

And we set this callback in the descriptor's `uncapturedErrorCallbackInfo` field:

```{lit} C++, Build device descriptor (append)
{{Device Error Callback}}
deviceDesc.uncapturedErrorCallbackInfo.callback = onDeviceError;
```

````{caution}
This callback info **does not have a `mode` field** because contrary to other callbacks, this one is en **event handler** that may be called repeatedly (as opposed to a *"future"* handler that is invoked only once).

```
// Definition of the WGPUUncapturedErrorCallbackInfo struct in webgpu.h
struct WGPUUncapturedErrorCallbackInfo {
    WGPUChainedStruct * nextInChain;
    // No 'mode' field! Callback may be invoked at any time.
    WGPUUncapturedErrorCallback callback;
    WGPU_NULLABLE void* userdata1;
    WGPU_NULLABLE void* userdata2;
};
```
````

Inspecting the device
---------------------

All right, our **descriptor is complete**, we now have a device!

Like the adapter, the device has its own set of capabilities that we can inspect at any time.

```{note}
At this point of the code -- where we just created the device -- we know its capabilities and limits because when the creation succeeded the device **corresponds to what we requested**. Being able to inspect the device is useful later on, or **when writing a library** that receives a `WGPUDevice` object that was created somewhere else.
```

```{lit} C++, Utility functions (append)
// We create a utility function to inspect the device:
void inspectDevice(WGPUDevice device) {
	
	WGPUSupportedFeatures features = WGPU_SUPPORTED_FEATURES_INIT;
	wgpuDeviceGetFeatures(device, &features);
	std::cout << "Device features:" << std::endl;
	std::cout << std::hex;
	for (size_t i = 0; i < features.featureCount; ++i) {
		std::cout << " - 0x" << features.features[i] << std::endl;
	}
	std::cout << std::dec;
	wgpuSupportedFeaturesFreeMembers(features);

	WGPULimits limits = WGPU_LIMITS_INIT;
	bool success = wgpuDeviceGetLimits(device, &limits) == WGPUStatus_Success;

	if (success) {
		std::cout << "Device limits:" << std::endl;
		std::cout << " - maxTextureDimension1D: " << limits.maxTextureDimension1D << std::endl;
		std::cout << " - maxTextureDimension2D: " << limits.maxTextureDimension2D << std::endl;
		std::cout << " - maxTextureDimension3D: " << limits.maxTextureDimension3D << std::endl;
		std::cout << " - maxTextureArrayLayers: " << limits.maxTextureArrayLayers << std::endl;
		{{Extra device limits}}
	}
}
```

```{lit} C++, Extra device limits (hidden)
std::cout << " - maxBindGroups: " << limits.maxBindGroups << std::endl;
std::cout << " - maxBindGroupsPlusVertexBuffers: " << limits.maxBindGroupsPlusVertexBuffers << std::endl;
std::cout << " - maxBindingsPerBindGroup: " << limits.maxBindingsPerBindGroup << std::endl;
std::cout << " - maxDynamicUniformBuffersPerPipelineLayout: " << limits.maxDynamicUniformBuffersPerPipelineLayout << std::endl;
std::cout << " - maxDynamicStorageBuffersPerPipelineLayout: " << limits.maxDynamicStorageBuffersPerPipelineLayout << std::endl;
std::cout << " - maxSampledTexturesPerShaderStage: " << limits.maxSampledTexturesPerShaderStage << std::endl;
std::cout << " - maxSamplersPerShaderStage: " << limits.maxSamplersPerShaderStage << std::endl;
std::cout << " - maxStorageBuffersPerShaderStage: " << limits.maxStorageBuffersPerShaderStage << std::endl;
std::cout << " - maxStorageTexturesPerShaderStage: " << limits.maxStorageTexturesPerShaderStage << std::endl;
std::cout << " - maxUniformBuffersPerShaderStage: " << limits.maxUniformBuffersPerShaderStage << std::endl;
std::cout << " - maxUniformBufferBindingSize: " << limits.maxUniformBufferBindingSize << std::endl;
std::cout << " - maxStorageBufferBindingSize: " << limits.maxStorageBufferBindingSize << std::endl;
std::cout << " - minUniformBufferOffsetAlignment: " << limits.minUniformBufferOffsetAlignment << std::endl;
std::cout << " - minStorageBufferOffsetAlignment: " << limits.minStorageBufferOffsetAlignment << std::endl;
std::cout << " - maxVertexBuffers: " << limits.maxVertexBuffers << std::endl;
std::cout << " - maxBufferSize: " << limits.maxBufferSize << std::endl;
std::cout << " - maxVertexAttributes: " << limits.maxVertexAttributes << std::endl;
std::cout << " - maxVertexBufferArrayStride: " << limits.maxVertexBufferArrayStride << std::endl;
std::cout << " - maxInterStageShaderVariables: " << limits.maxInterStageShaderVariables << std::endl;
std::cout << " - maxColorAttachments: " << limits.maxColorAttachments << std::endl;
std::cout << " - maxColorAttachmentBytesPerSample: " << limits.maxColorAttachmentBytesPerSample << std::endl;
std::cout << " - maxComputeWorkgroupStorageSize: " << limits.maxComputeWorkgroupStorageSize << std::endl;
std::cout << " - maxComputeInvocationsPerWorkgroup: " << limits.maxComputeInvocationsPerWorkgroup << std::endl;
std::cout << " - maxComputeWorkgroupSizeX: " << limits.maxComputeWorkgroupSizeX << std::endl;
std::cout << " - maxComputeWorkgroupSizeY: " << limits.maxComputeWorkgroupSizeY << std::endl;
std::cout << " - maxComputeWorkgroupSizeZ: " << limits.maxComputeWorkgroupSizeZ << std::endl;
std::cout << " - maxComputeWorkgroupsPerDimension: " << limits.maxComputeWorkgroupsPerDimension << std::endl;
std::cout << " - maxStorageBuffersInVertexStage: " << limits.maxStorageBuffersInVertexStage << std::endl;
std::cout << " - maxStorageTexturesInVertexStage: " << limits.maxStorageTexturesInVertexStage << std::endl;
std::cout << " - maxStorageBuffersInFragmentStage: " << limits.maxStorageBuffersInFragmentStage << std::endl;
std::cout << " - maxStorageTexturesInFragmentStage: " << limits.maxStorageTexturesInFragmentStage << std::endl;
```

If you define this function in `webgpu-utils.cpp`, do not forget to also declare it in `webgpu-utils.h`:

```{lit} C++, file: webgpu-utils.h (append)
/**
 * Display information about a device
 */
void inspectDevice(WGPUDevice device);
```

And we call this after creating the device:

```{lit} C++, Create things (append)
inspectDevice(device);
```

We can see that by default the device limits are not the same as what the adapter supports. Setting `deviceDesc.requiredLimits` to `nullptr` or using default limits from `WGPU_LIMITS_INIT` corresponded to ask for minimal limits:

```
Device limits:
 - maxTextureDimension1D: 8192
 - maxTextureDimension2D: 8192
 - maxTextureDimension3D: 2048
 - maxTextureArrayLayers: 256
 - ...
```

```{note}
One can also **retrieve the adapter** that was used to request the device using `wgpuDeviceGetAdapter`.
```

Conclusion
----------

 - We now have our **device**, from which we can create all other WebGPU objects.
 - **Important:** Once the device is created, the adapter should in general no longer be used. The only capabilities that matter to the application are the one of the device.
 - Default limits are minimal limits, rather than what the adapter supports. This helps ensuring consistency across devices.
 - The **uncaptured error callback** is where all of our issues will be reported, it is important to set it up.

We are now ready to **send instructions and data** to the device through the **command queue**!

*Resulting code:* [`step010-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010-next)
