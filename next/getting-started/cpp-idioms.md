C++ wrapper
===========

*Resulting code:* [`step028-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028-next)

So far we have used the **raw WebGPU API**, which is a **C API**, and this prevented us from using some **nice productive features of C++**. This chapter first gives imaginary examples of how this could be improved, before linking to a little library that implements all these features in an alternate `webgpu.hpp` header that replaces `webgpu.h`.

The remainder of the guide **always provides snippets with both** this C++ wrapper (using `webgpu.hpp`) and the "vanilla" C API (using `webgpu.h`).

```{important}
All the changes presented here only affect the coding time, but our shallow C++ wrapper leads to the very same runtime binaries.
```

```{note}
Dawn and emscripten provide their own C++ wrapper. They follow a similar spirit as the one I introduce here, only I needed our wrapper to be valid for all possible implementations, including `wgpu-native`.
```

```{caution}
This chapter is not as up to date as [the readme of WebGPU-C++](https://github.com/eliemichel/WebGPU-Cpp). I recommend you read that instead for now.
```

Namespace
---------

The C interface could not make use of namespaces, since they only exist in C++, so you may have noticed that every single function starts with `wgpu` and every single structure starts with `WGPU`. A more C++ idiomatic way of doing this is to enclose all these functions into a **namespace**.

```C++
// Using Vanilla webgpu.h
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;
WGPUInstance instance = wgpuCreateInstance(&desc);
```

becomes with namespaces:

```C++
// Using C++ webgpu.hpp
wgpu::InstanceDescriptor desc = {};
desc.nextInChain = nullptr;
wgpu::Instance instance = wgpu::createInstance(&desc);
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
size_t wgpuAdapterEnumerateFeatures(WGPUAdapter adapter, WGPUFeatureName * features);
           ^^^^^^^                  ^^^^^^^^^^^^^^^^^^^
void wgpuBufferDestroy(WGPUBuffer buffer);
         ^^^^^^        ^^^^^^^^^^^^^^^^^
```

These functions are conceptually **methods** of the object constituted by their first argument. Once again, C does not have built-in support for methods but C++ does, so in the wrapper we expose these WebGPU functions as follows:

```C++
namespace wgpu {
	struct Device {
		// [...]
		createBuffer(BufferDescriptor const * descriptor = nullptr) const;
	};

	struct Adapter {
		// [...]
		enumerateFeatures(WGPUFeatureName * features) const;
	};

	struct Device {
		// [...]
		destroy();
	};
} // namespace wgpu
```

```{note}
The `const` qualifier is specified for some methods. This is extra information provided by the wrapper to reduce the potential programming mistakes.
```

This greatly reduces visual clutter when calling such methods:

```C++
// Using Vanilla webgpu.h
WGPUAdapter adapter = /* [...] */
size_t n = wgpuAdapterEnumerateFeatures(adapter, nullptr);
```

becomes with namespaces:

```C++
// Using C++ webgpu.hpp
Adapter adapter = /* [...] */
size_t n = adapter.enumerateFeatures(nullptr);
```

Scoped enumerations
-------------------

Because enums are *unscoped* by default, the C API is forced to **prefix all values** that an enumeration can take with the name of the enum, leading to quite long names:

```C
typedef enum WGPURequestAdapterStatus {
    WGPURequestAdapterStatus_Success = 0x00000000,
    WGPURequestAdapterStatus_Unavailable = 0x00000001,
    WGPURequestAdapterStatus_Error = 0x00000002,
    WGPURequestAdapterStatus_Unknown = 0x00000003,
    WGPURequestAdapterStatus_Force32 = 0x7FFFFFFF
} WGPURequestAdapterStatus;
```

It is possible in C++ to define **scoped** enums, which are strongly typed and can only be accessed through the name, for instance this scoped enum:

```C++
enum class RequestAdapterStatus {
    Success = 0x00000000,
    Unavailable = 0x00000001,
    Error = 0x00000002,
    Unknown = 0x00000003,
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

Default descriptor values
-------------------------

Sometimes we just need to build a descriptor by default. More generally, we rarely need to have all the fields of the descriptor deviate from the default, so we could benefit from the possibility to have a default constructor for descriptors.

Capturing closures
------------------

Many asynchronous operations use callbacks. In order to provide some context to the callback's body, there is always a `void *userdata` argument passed around. This can be alleviated in C++ by using capturing closures.

```{important}
This only alleviates the notations, but technically mechanism very similar to the user data pointer is automatically implemented when creating a capturing lambda.
```

```C++
// C style
struct Context {
	WGPUBuffer buffer;
};
auto onBufferMapped = [](WGPUBufferMapAsyncStatus status, void* pUserData) {
	Context* context = reinterpret_cast<Context*>(pUserData);
	std::cout << "Buffer mapped with status " << status << std::endl;
	unsigned char* bufferData = (unsigned char*)wgpuBufferGetMappedRange(context->buffer, 0, 16);
	std::cout << "bufferData[0] = " << (int)bufferData[0] << std::endl;
	wgpuBufferUnmap(context->buffer);
};
Context context;
wgpuBufferMapAsync(buffer, WGPUMapMode_Read, 0, 16, onBufferMapped, (void*)&context);
```

becomes

```C++
// C++ style
buffer.mapAsync(buffer, [&context](wgpu::BufferMapAsyncStatus status) {
	std::cout << "Buffer mapped with status " << status << std::endl;
	unsigned char* bufferData = (unsigned char*)context.buffer.getMappedRange(0, 16);
	std::cout << "bufferData[0] = " << (int)bufferData[0] << std::endl;
	context.buffer.unmap();
});
```

Library
-------

The library providing these C++ idioms is [`webgpu.hpp`](../data/webgpu.hpp). It is made of a single header file, which you just have to copy in your source tree. Exactly one of your source files must define `WEBGPU_CPP_IMPLEMENTATION` before `#include "webgpu.hpp"`:

```C++
#define WEBGPU_CPP_IMPLEMENTATION
#include <webgpu/webgpu.hpp>
```

```{note}
This header is actually included in the WebGPU zip I provided you earlier, at the include path `<webgpu/webgpu.hpp>`.
```

More information can be found in [the webgpu-cpp repository](https://github.com/eliemichel/WebGPU-Cpp).

*Resulting code:* [`step028-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028-next)
