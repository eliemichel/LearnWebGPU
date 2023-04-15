The Device
==========

```{lit-setup}
:tangle-root: 015 - The Device
:parent: 010 - The Adapter - Part B
```

*Resulting code:* [`step015`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015)

A WebGPU **device** represents a **context** of use of the API. All the objects that we create (geometry, textures, etc.) are owned by the device.

> 🤔 Why do we have both an **adapter** and then a **device** abstraction?

The idea is to limit the "it worked on my machine" issue you could encounter when trying your program on a different machine. The **adapter** is used to **access the capabilities** of the customer's hardware, which are used to select the behavior of your application among very different code paths. Once a code path is chosen, a **device** is created with **the capabilities we choose**.

Only the capabilities selected for this device are then allowed in the rest of the application. This way, it is **not possible to inadvertedly rely on capabilities specific to your own machine**.

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
			std::cout << "Could not get WebGPU adapter: " << message << std::endl;
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

If you use a debugger (which I recommend), like `gdb` or you IDE, I recommend you **put a breakpoint** in this callback, so that your program pauses and provides you with a call stack whenever WebGPU encounters an unexpected error.

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
