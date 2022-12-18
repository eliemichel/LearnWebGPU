The Device
==========

*Resulting code:* [`step015`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015)

A WebGPU *device* represents a *context* of use of the API. All the objects that will later be created (geometry, textures, etc.) will be owned by the device.

Why do we have both an *adapter* and then a *device* abstraction? The idea is to limit the "it worked on my machine" issue you could encounter when trying your program on a different machine. The adapter is used to access the capabilities of the customer's hardware, which are used to select the behavior of your application among very different code paths. Once a code path is chosen, a device is created with the available options we need, and only the capabilities selected for this device are then allowed in the rest of the application. This way, it is not possible to inadvertedly rely on capabilities specific to your own machine.

Requesting the device looks a lot like requesting the adapter, se we will use a very similar function:

```C++
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

In the main function, after getting the adapter, we can request the device:

```C++
std::cout << "Requesting device..." << std::endl;

WGPUDeviceDescriptor deviceDesc = {};
// (We will build the device descriptor here)
WGPUDevice device = requestDevice(adapter, &deviceDesc);

std::cout << "Got device: " << device << std::endl;
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

```C++
deviceDesc.nextInChain = nullptr;
deviceDesc.label = "My Device"; // anything works here, that's your call
deviceDesc.requiredFeaturesCount = 0; // we do not require any specific feature
deviceDesc.requiredLimits = nullptr; // we do not require any specific limit
deviceDesc.defaultQueue.nextInChain = nullptr;
deviceDesc.defaultQueue.label = "The default queue";
```

We will come back here and refine these options whenever we will need some more capabilities from the device.

Device descriptor
-----------------

Before moving on to the next section, I would like you to add this call after creating the device:

```C++
auto onDeviceError = [](WGPUErrorType type, char const* message, void* /* pUserData */) {
	std::cout << "Uncaptured device error: type " << type;
	if (message) std::cout << " (" << message << ")";
	std::cout << std::endl;
};
wgpuDeviceSetUncapturedErrorCallback(device, onDeviceError, nullptr /* pUserData */);
```

This defines a callback that gets executed upon errors, which is very handy for debugging, especially when we will start using *asynchronous* operations.

If you use a debugger (which I recommend), like `gdb` or you IDE, I recommend you put a breakpoint in this callback, so that your program pauses and provides you with a call stack whenever WebGPU encounters an unexpected error.

*Resulting code:* [`step015`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step015)
