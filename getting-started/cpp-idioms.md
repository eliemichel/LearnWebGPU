C++ wrapper
===========

*Resulting code:* [`step025`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step025)

So far we have used the raw WebGPU API, which is a C API, and this prevented us from using some nice productive features of C++. This chapter first gives imaginary examples of how this could be improved, before linking to a little library that implement all this little features.

```{important}
All the changes presented here only affect the coding time, but our shallow C++ wrapper leads to the very same runtime binaries.
```

```{caution}
This chapter is not as up to date as [the readme of WebGPU-C++](https://github.com/eliemichel/WebGPU-Cpp). I recommend you read that instead for now.
```

Default descriptor values
-------------------------

Sometimes we just need to build a descriptor by default. More generally, we rarely need to have all the fields of the descriptor deviate from the default, so we could benefit from the possibility to have a default constructor for descriptors.

Namespace
---------

The C interface could not make use of namespaces, since they only exist in C++, so you may have noticed that every single function starts with `wgpu` and every single structure starts with `WGPU`. A more C++ idiomatic way of doing this is to enclose all these functions into a namespace.

```C++
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;
WGPUInstance instance = wgpuCreateInstance(&desc);
```

becomes with namespaces:

```C++
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

Beyond namespace, most functions are also prefixed by the name of their first argument, e.g.:

```C++
WGPUBuffer wgpuDeviceCreateBuffer(WGPUDevice device, WGPUBufferDescriptor const * descriptor);
               ^^^^^^             ^^^^^^^^^^^^^^^^^
size_t wgpuAdapterEnumerateFeatures(WGPUAdapter adapter, WGPUFeatureName * features);
           ^^^^^^^                  ^^^^^^^^^^^^^^^^^^^
void wgpuBufferDestroy(WGPUBuffer buffer);
         ^^^^^^        ^^^^^^^^^^^^^^^^^
```

These functions are conceptually *methods* of the object constituted by their first argument, so in the wrapper they are exposed as such:

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

Scoped enumerations
-------------------

Because enums are *unscoped* by default, the WebGPU API is forced to prefix all values that an enum can take with the name of the enum, leading to quite long names:

```C
typedef enum WGPURequestAdapterStatus {
    WGPURequestAdapterStatus_Success = 0x00000000,
    WGPURequestAdapterStatus_Unavailable = 0x00000001,
    WGPURequestAdapterStatus_Error = 0x00000002,
    WGPURequestAdapterStatus_Unknown = 0x00000003,
    WGPURequestAdapterStatus_Force32 = 0x7FFFFFFF
} WGPURequestAdapterStatus;
```

It is possible in C++ to define *scoped* enums, which are strongly typed and can only be accessed through the name, for instance this scoped enum:

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

Library
-------

The library providing these C++ idioms is [`webgpu.hpp`](../data/webgpu.hpp). It is made of a single header file, which you just have to copy in your source tree. Exactly one of your source files must define `WEBGPU_CPP_IMPLEMENTATION` before `#include "webgpu.hpp"`:

```C++
#define WEBGPU_CPP_IMPLEMENTATION
#include <webgpu.hpp>
```

```{note}
This header is actually included in the WebGPU zip I provided you earlier.
```

More information can be found in [the webgpu-cpp repository](https://github.com/eliemichel/WebGPU-Cpp).

*Resulting code:* [`step025`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step025)
