The Device <span class="bullet">🟢</span>
==========

```{lit-setup}
:tangle-root: 010 - The Device
:parent: 005 - The Adapter
```

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)

A WebGPU **device** represents a **context** of use of the API. All the objects that we create (geometry, textures, etc.) are owned by the device.

The device is requested from an **adapter** by specifying the **subset of limits and features** that we are interesed in. Once the device is created, the adapter should no longer be used. **The only capabilities that matter** to the application are the ones of the device.

Device request
--------------

Requesting the device looks a lot like requesting the adapter, so we will use a very similar function:

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
WGPUDevice requestDeviceSync(WGPUAdapter adapter, WGPUDeviceDescriptor const * descriptor) {
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

#ifdef __EMSCRIPTEN__
	while (!userData.requestEnded) {
		emscripten_sleep(100);
	}
#endif // __EMSCRIPTEN__

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
WGPUAdapter requestAdapterSync(WGPUInstance instance, WGPURequestAdapterOptions const * options);

/**
 * Utility function to get a WebGPU device, so that
 *     WGPUAdapter device = requestDevice(adapter, options);
 * is roughly equivalent to
 *     const device = await adapter.requestDevice(descriptor);
 * It is very similar to requestAdapter
 */
WGPUDevice requestDeviceSync(WGPUAdapter adapter, WGPUDeviceDescriptor const * descriptor);

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

#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#endif // __EMSCRIPTEN__

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
WGPUDevice device = requestDeviceSync(adapter, &deviceDesc);

std::cout << "Got device: " << device << std::endl;
```

```{lit} C++, Create things (append, hidden)
{{Request device}}
{{Setup device callbacks}}
```

And of course, we release the device when the program ends:

```{lit} C++, Destroy things (prepend)
wgpuDeviceRelease(device);
```

````{note}
The adapter can be **released before the device**. Actually it is good practice to release it as soon as we have our device and never use it again.

```{lit} C++, Create things (append, hidden)
// We no longer need to access the adapter once we have the device
{{Destroy adapter}}
```

```{lit} C++, Destroy things (replace)
wgpuAdapterRelease(adapter);
```

````

Device descriptor
-----------------

Let us look in `webgpu.h` what the descriptor looks like:

```C++
typedef struct WGPUDeviceDescriptor {
	WGPUChainedStruct const * nextInChain;
	WGPU_NULLABLE char const * label;
	size_t requiredFeatureCount;
	WGPUFeatureName const * requiredFeatures;
	WGPU_NULLABLE WGPURequiredLimits const * requiredLimits;
	WGPUQueueDescriptor defaultQueue;
	WGPUDeviceLostCallback deviceLostCallback;
	void * deviceLostUserdata;
} WGPUDeviceDescriptor;

// (this struct definition is actually above)
typedef struct WGPUQueueDescriptor {
	WGPUChainedStruct const * nextInChain;
	WGPU_NULLABLE char const * label;
} WGPUQueueDescriptor;
```

For now we will initialize this to a very minimal option, requiring no special feature and using default limits:

```{lit} C++, Build device descriptor
deviceDesc.nextInChain = nullptr;
deviceDesc.label = "My Device"; // anything works here, that's your call
deviceDesc.requiredFeatureCount = 0; // we do not require any specific feature
deviceDesc.requiredLimits = nullptr; // we do not require any specific limit
deviceDesc.defaultQueue.nextInChain = nullptr;
deviceDesc.defaultQueue.label = "The default queue";
{{Set device lost callback}}
```

```{lit} C++, Set device lost callback
// Null for now, see below
deviceDesc.deviceLostCallback = nullptr;
```

We will come back here and refine these options whenever we will need some more capabilities from the device.

```{note}
The `label` is **used in error messages** to help you debug where something went wrong, so it is good practice to use it as soon as you get multiple objects of the same type. Currently, this is only used by Dawn.
```

Inspecting the device
---------------------

Like the adapter, the device has its own set of capabilities.

```{lit} C++, Utility functions (append)
// We also add an inspect device function:
void inspectDevice(WGPUDevice device) {
	std::vector<WGPUFeatureName> features;
	size_t featureCount = wgpuDeviceEnumerateFeatures(device, nullptr);
	features.resize(featureCount);
	wgpuDeviceEnumerateFeatures(device, features.data());

	std::cout << "Device features:" << std::endl;
	std::cout << std::hex;
	for (auto f : features) {
		std::cout << " - 0x" << f << std::endl;
	}
	std::cout << std::dec;

	WGPUSupportedLimits limits = {};
	limits.nextInChain = nullptr;

#ifdef WEBGPU_BACKEND_DAWN
	bool success = wgpuDeviceGetLimits(device, &limits) == WGPUStatus_Success;
#else
	bool success = wgpuDeviceGetLimits(device, &limits);
#endif

	if (success) {
		std::cout << "Device limits:" << std::endl;
		std::cout << " - maxTextureDimension1D: " << limits.limits.maxTextureDimension1D << std::endl;
		std::cout << " - maxTextureDimension2D: " << limits.limits.maxTextureDimension2D << std::endl;
		std::cout << " - maxTextureDimension3D: " << limits.limits.maxTextureDimension3D << std::endl;
		std::cout << " - maxTextureArrayLayers: " << limits.limits.maxTextureArrayLayers << std::endl;
		{{Extra device limits}}
	}
}
```

```{lit} C++, Extra device limits (hidden)
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
```

```{lit} C++, Create things (append, hidden)
inspectDevice(device);
```

```{admonition} Implementation divergences
Like for `wgpuAdapterGetLimits`, the procedure `wgpuDeviceGetLimits` returns a boolean in `wgpu-native` but a `WGPUStatus` in Dawn.
```

We can see that by default the device limits are not the same as what the adapter supports. Setting `deviceDesc.requiredLimits` to `nullptr` above corresponded to ask for minimal limits:

```
Device limits:
 - maxTextureDimension1D: 8192
 - maxTextureDimension2D: 8192
 - maxTextureDimension3D: 2048
 - maxTextureArrayLayers: 256
```

Device callbacks
----------------

In order to **get notified** when the device undergoes an error or when it is no longer available, we may set up **callback** functions. These really **helps debugging**, so I encourage you to do it although it is optional.

### Device Lost Callback

As we briefly saw above, the device lost callback is provided through the device descriptor's `deviceLostCallback` field:

```{lit} C++, Set device lost callback (replace)
// A function that is invoked whenever the device stops being available.
deviceDesc.deviceLostCallback = [](WGPUDeviceLostReason reason, char const* message, void* /* pUserData */) {
	std::cout << "Device lost: reason " << reason;
	if (message) std::cout << " (" << message << ")";
	std::cout << std::endl;
};
```

```{note}
We use a [C++ lambda](https://en.cppreference.com/w/cpp/language/lambda) here, but `deviceDesc.deviceLostCallback` could also get assigned the name of a regular function.
```

The device is always "lost" when it is destroyed by the ultimate call to `wgpuDeviceRelease`. It may also be lost for other reasons, mostly meaning that the backend implementation panicked and crashed.

```{important}
The `deviceLostCallback` must outlive the device, so that when the latter gets destroyed the callback is still valid.
```

### Uncaptured Error Callback

The uncaptured error callback is invoked whenever we misuse the API, and gives very informative feedback about what went wrong. It only set after the creation of the device, by calling `wgpuDeviceSetUncapturedErrorCallback`:

```{lit} C++, Setup device callbacks
auto onDeviceError = [](WGPUErrorType type, char const* message, void* /* pUserData */) {
	std::cout << "Uncaptured device error: type " << type;
	if (message) std::cout << " (" << message << ")";
	std::cout << std::endl;
};
wgpuDeviceSetUncapturedErrorCallback(device, onDeviceError, nullptr /* pUserData */);
```

If you use a debugger (which I recommend), like `gdb` or your IDE, I recommend you **put a breakpoint** in this callback, so that your program pauses and provides you with a call stack whenever WebGPU encounters an unexpected error.

````{admonition} Dawn
**By default** Dawn runs callbacks only when the device "ticks", so the error callbacks are invoked in a **different call stack** than where the error occurred, making the breakpoint less informative. To force Dawn to invoke error callbacks as soon as there is an error, you can enable an instance **toggle**:

```C++
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;

#ifdef WEBGPU_BACKEND_DAWN
// Make sure the uncaptured error callback is called as soon as an error
// occurs rather than at the next call to "wgpuDeviceTick".
WGPUDawnTogglesDescriptor toggles;
toggles.chain.next = nullptr;
toggles.chain.sType = WGPUSType_DawnTogglesDescriptor;
toggles.disabledToggleCount = 0;
toggles.enabledToggleCount = 1;
const char* toggleName = "enable_immediate_error_handling";
toggles.enabledToggles = &toggleName;

desc.nextInChain = &toggles.chain;
#endif // WEBGPU_BACKEND_DAWN

WGPUInstance instance = wgpuCreateInstance(&desc);
```

Toggles are Dawn's special way of enabling/disabling features at the scale of the whole WebGPU instance. See the whole list in [`Toggle.cpp`](https://dawn.googlesource.com/dawn/+/refs/heads/main/src/dawn/native/Toggles.cpp#33).
````

Conclusion
----------

 - We now have our **device**, from which we can create all other WebGPU objects.
 - **Important:** Once the device is created, the adapter should in general no longer be used. The only capabilities that matter to the application are the one of the device.
 - Default limits are minimal limits, rather than what the adapter supports. This helps ensuring consistency across devices.

*Resulting code:* [`step010`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step010)
