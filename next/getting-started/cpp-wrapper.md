C++ wrapper <span class="bullet">🟠</span>
===========

```{lit-setup}
:tangle-root: 028 - C++ Wrapper - Next
:parent: 025 - First Color - Next
```

*Resulting code:* [`step028-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028-next)

So far we have been using the **raw WebGPU API**, which is a **C API**. It is important to be familiar with this raw API, but on the other hand this prevented us from using some **nice productive features of C++**.

In this chapter we introduce **a small C++ wrapper**, called `webgpu.hpp`, which is already provided with the [WebGPU-Distribution](https://github.com/eliemichel/WebGPU-distribution), and that can advantageously replace `webgpu.h`.

The remainder of the guide **always provides snippets with both** this C++ wrapper (using `webgpu.hpp`) and the "vanilla" C API (using `webgpu.h`).

```{important}
All the changes presented here only affect the coding time, but our shallow C++ wrapper (almost) leads to the very same runtime binaries.
```

```{note}
Dawn and emscripten provide their own C++ wrapper. They follow a similar spirit as the one I introduce here, only I needed our wrapper to be valid for all possible implementations, including `wgpu-native`.
```

Setup
-----

The `webgpu.hpp` wrapper that we use is **already provided** with the [WebGPU-Distribution](https://github.com/eliemichel/WebGPU-distribution) that we set up earlier.

```{note}
In case you get your implementation of WebGPU from somewhere else, you can still use this wrapper by getting its **single file** from the [WebGPU-Cpp](https://github.com/eliemichel/WebGPU-Cpp) repository.

In this case, **pay attention to the versions** because your `webgpu.hpp` must be exactly compatible with the `webgpu.h` provided by your implementation of WebGPU. **If you have a doubt**, the best solution is to generate the `webgpu.hpp`yourself using either the [web service](https://eliemichel.github.io/WebGPU-Cpp/) or the `generate.py` script.
```

This wrapper is made of a **single header** file. **Exactly one** of your source files must define `WEBGPU_CPP_IMPLEMENTATION` before `#include <webgpu/webgpu.hpp>`:

```C++
// Define this in **exactly one** file
#define WEBGPU_CPP_IMPLEMENTATION
// Then include this anywhere you need the wrapper
#include <webgpu/webgpu.hpp>
```

```{note}
For now we place this in the `main.cpp`, but you could also create a dedicated `implementations.cpp` and put this there (we will do this once we add other single file libraries following the same idiom).
```

We now incrementally see the niceties that this wrapper introduces. Keep in mind that the C++ wrapper types are (almost) always **compatible with the C API**, so you can migrate your code **progressively**.

Namespace
---------

The C interface could not make use of **namespaces**, since they only exist in C++, so you may have noticed that every single function starts with `wgpu` and every single structure starts with `WGPU`. A more C++ idiomatic way of doing this is to enclose all these functions into a **namespace**.

```C++
// Using Vanilla webgpu.h
WGPUInstanceDescriptor desc = {};
WGPUInstance instance = wgpuCreateInstance(&desc);
```

becomes with namespaces:

```C++
// Using C++ webgpu.hpp
wgpu::InstanceDescriptor desc = {};
wgpu::Instance instance = wgpu::createInstance(desc);
```

```{note}
You may also notice that the `&` disappeared: this is because `const` descriptor pointers become references in the wrapper!
```

And of course you can start your source file with `using namespace wgpu;` to avoid spelling out `wgpu::` everywhere. Coupled with default descriptor, this leads to simply:

```C++
using namespace wgpu;
Instance instance = createInstance();
```

Objects
-------

Beyond namespace, most functions are also **prefixed by the type of their first argument**, for instance:

```C++
WGPUBuffer wgpuDeviceCreateBuffer(WGPUDevice device, WGPUBufferDescriptor const * descriptor);
               ^^^^^^             ^^^^^^^^^^^^^^^^^
WGPUStatus wgpuAdapterGetInfo(WGPUAdapter adapter, WGPUAdapterInfo * info);
               ^^^^^^^        ^^^^^^^^^^^^^^^^^^^
void wgpuBufferRelease(WGPUBuffer buffer);
         ^^^^^^        ^^^^^^^^^^^^^^^^^
```

These functions are conceptually **methods** of the object constituted by their first argument. Once again, C does not have built-in support for methods but C++ does, so in the wrapper we expose these WebGPU functions as follows:

```C++
namespace wgpu {
	struct Device {
		// [...]
		Buffer createBuffer(const BufferDescriptor& descriptor);
	};

	struct Adapter {
		// [...]
		Status GetInfo(AdapterInfo * info) const;
	};

	struct Device {
		// [...]
		release();
	};
} // namespace wgpu
```

```{note}
The `const` qualifier is specified for some methods. This is extra information provided by the wrapper to reduce the potential programming mistakes.
```

This greatly reduces visual clutter when calling such methods:

```C++
// Using Vanilla webgpu.h
WGPUBufferDescriptor descriptor = WGPU_DEVICE_DESCRIPTOR_INIT;
// [...]
WGPUBuffer buffer = wgpuDeviceCreateBuffer(device, &descriptor);
```

becomes with namespaces:

```C++
// Using C++ webgpu.hpp
BufferDescriptor descriptor = Default;
// [...]
Buffer buffer = device.createBuffer(descriptor);
```

```{note}
As you can see, descriptors can also be **initialized** using the generic `wgpu::Default` object instead of the long struct-specific INIT macro.
```

Scoped enumerations
-------------------

Because enums are *unscoped* by default, the C API is forced to **prefix all values** that an enumeration can take with the name of the enum, leading to quite long names:

```C
typedef enum WGPURequestAdapterStatus {
    WGPURequestAdapterStatus_Success = 0x00000001,
    WGPURequestAdapterStatus_InstanceDropped = 0x00000002,
    WGPURequestAdapterStatus_Unavailable = 0x00000003,
    WGPURequestAdapterStatus_Error = 0x00000004,
    WGPURequestAdapterStatus_Force32 = 0x7FFFFFFF
} WGPURequestAdapterStatus;
```

It is possible in C++ to define **scoped** enums, which are strongly typed and can only be accessed through the name, for instance this scoped enum:

```C++
enum class RequestAdapterStatus {
    Success = 0x00000001,
    InstanceDropped = 0x00000002,
    Unavailable = 0x00000003,
    Error = 0x00000004,
    Force32 = 0x7FFFFFFF
};
```

This can be used as follows:

```C++
wgpu::RequestAdapterStatus::Success;
```

```{note}
The actual implementation use a little trickery so that enum names are scoped, but implicitly converted to and from the original WebGPU enum values.
```

Capturing closures
------------------

Many asynchronous operations use callbacks. In order to provide some context to the callback's body, there are always two `void *userdata` arguments passed around. This can be simplified in C++ by using capturing closures.

```{important}
This only alleviates the notations, but technically a mechanism very similar to the user data pointer is automatically implemented when creating a capturing lambda.
```

```C++
// C style
struct Context {
	WGPUBuffer buffer;
};
auto onBufferMapped = [](WGPUMapAsyncStatus status, WGPUStringView message, void* userdata1, void*) {
	Context* context = reinterpret_cast<Context*>(userdata1);
	std::cout << "Buffer mapped with status " << status << std::endl;
	unsigned char* bufferData = (unsigned char*)wgpuBufferGetMappedRange(context->buffer, 0, 16);
	std::cout << "bufferData[0] = " << (int)bufferData[0] << std::endl;
	wgpuBufferUnmap(context->buffer);
};

Context context;
WGPUBufferMapCallbackInfo callbackInfo = WGPU_BUFFER_MAP_CALLBACK_INFO_INIT;
callbackInfo.mode = WGPUCallbackMode_AllowProcessEvents;
callbackInfo.callback = onBufferMapped;
callbackInfo.userdata1 = (void*)&context;
wgpuBufferMapAsync(buffer, WGPUMapMode_Read, 0, 16, onBufferMappedCbInfo);
```

becomes

```C++
// C++ style
auto onBufferMapped = [&context](wgpu::BufferMapAsyncStatus status, StringView message) {
	std::cout << "Buffer mapped with status " << status << std::endl;
	unsigned char* bufferData = (unsigned char*)context.buffer.getMappedRange(0, 16);
	std::cout << "bufferData[0] = " << (int)bufferData[0] << std::endl;
	context.buffer.unmap();
};
buffer.mapAsync(buffer, MapMode::Read, 0, 16, CallbackMode::AllowProcessEvents, onBufferMapped);
```

```{note}
A little difference between the C and C++ versions above is that the C version allocates the `Context` statically on the stack, while rooms for the C++ lambda gets allocated dynamically in the heap. If this bothers you, the wrapper provides an in-between that enables using the object notation but still expects you to create the callback info structure yourself.
```

Conclusion
----------

From now on, I will be providing two versions of each code snippet: one that uses this nice wrapper, and one that sticks with the raw C API.

Congratulations, you've made it to **the end of the "Getting Started" section**! It was not a small thing, you are now well equipped to explore and understand the various documentation about WebGPU. From here, you can decide to either move on to the [Graphics](../basic-3d-rendering/index.md) section and draw your first triangle, or go to the [Compute](../basic-compute/index.md) section and start playing with tensors.

*Resulting code:* [`step028-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028-next)
