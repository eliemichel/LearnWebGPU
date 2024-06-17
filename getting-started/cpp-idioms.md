C++ wrapper
===========

```{lit-setup}
:tangle-root: 028 - C++ Wrapper
:parent: 025 - First Color
```

*Resulting code:* [`step028`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028)

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
WGPUInstance instance = wgpuCreateInstance(&desc);
```

becomes with namespaces:

```C++
// Using C++ webgpu.hpp
wgpu::InstanceDescriptor desc = {};
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

*Resulting code:* [`step028`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028)

```{lit} C++, Includes (replace, hidden)
#define WEBGPU_CPP_IMPLEMENTATION
#include <webgpu/webgpu.hpp>

#include <GLFW/glfw3.h>
#include <glfw3webgpu.h>

#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#endif // __EMSCRIPTEN__

#include <iostream>
#include <cassert>
#include <vector>

using namespace wgpu;
```

```{lit} C++, Application attributes (replace, hidden)
GLFWwindow *window;
Device device;
Queue queue;
Surface surface;
std::unique_ptr<ErrorCallback> uncapturedErrorCallbackHandle;
```

```{lit} C++, Initialize (replace, hidden)
{{Open window and get adapter}}

{{Request device}}
queue = device.getQueue();

{{Add device error callback}}

{{Surface Configuration}}

// We no longer need to access the adapter
adapter.release();
```

```{lit} C++, Open window and get adapter (replace, hidden)
// Open window
glfwInit();
glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);
glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);
window = glfwCreateWindow(640, 480, "Learn WebGPU", nullptr, nullptr);

// Create instance
Instance instance = wgpuCreateInstance(nullptr);

// Get adapter
std::cout << "Requesting adapter..." << std::endl;
{{Request adapter}}
std::cout << "Got adapter: " << adapter << std::endl;

// We no longer need to access the instance
instance.release();
```

```{lit} C++, Add device error callback (replace, hidden)
// Device error callback
uncapturedErrorCallbackHandle = device.setUncapturedErrorCallback([](ErrorType type, char const* message) {
	std::cout << "Uncaptured device error: type " << type;
	if (message) std::cout << " (" << message << ")";
	std::cout << std::endl;
});
```

```{lit} C++, Request device (replace, hidden)
// Get device
std::cout << "Requesting device..." << std::endl;
DeviceDescriptor deviceDesc = {};
{{Build device descriptor}}
device = adapter.requestDevice(deviceDesc);
std::cout << "Got device: " << device << std::endl;
```

```{lit} C++, Build device descriptor (replace, hidden)
deviceDesc.label = "My Device";
deviceDesc.requiredFeatureCount = 0;
deviceDesc.requiredLimits = nullptr;
deviceDesc.defaultQueue.nextInChain = nullptr;
deviceDesc.defaultQueue.label = "The default queue";
deviceDesc.deviceLostCallback = [](WGPUDeviceLostReason reason, char const* message, void* /* pUserData */) {
	std::cout << "Device lost: reason " << reason;
	if (message) std::cout << " (" << message << ")";
	std::cout << std::endl;
};
```

```{lit} C++, Request adapter (replace, hidden)
{{Get the surface}}

RequestAdapterOptions adapterOpts = {};
adapterOpts.compatibleSurface = surface;

Adapter adapter = instance.requestAdapter(adapterOpts);
```

```{lit} C++, Surface Configuration (replace, hidden)
SurfaceConfiguration config = {};

{{Describe Surface Configuration}}

surface.configure(config);
```

```{lit} C++, Describe Surface Configuration (replace, hidden)
// Configuration of the textures created for the underlying swap chain
config.width = 640;
config.height = 480;
{{Describe Surface Usage}}
{{Describe Surface Format}}
config.device = device;
config.presentMode = PresentMode::Fifo;
config.alphaMode = CompositeAlphaMode::Auto;
```

```{lit} C++, Describe Surface Format (replace, hidden)
TextureFormat surfaceFormat = surface.getPreferredFormat(adapter);
config.format = surfaceFormat;
// And we do not need any particular view format:
config.viewFormatCount = 0;
config.viewFormats = nullptr;
```

```{lit} C++, Describe Surface Usage (replace, hidden)
config.usage = TextureUsage::RenderAttachment;
config.device = device;
```

```{lit} C++, Terminate (replace, hidden)
surface.unconfigure();
queue.release();
surface.release();
device.release();
glfwDestroyWindow(window);
glfwTerminate();
```

```{lit} C++, Get the next target texture view (replace, hidden)
// Get the next target texture view
TextureView targetView = GetNextSurfaceTextureView();
if (!targetView) return;
```

```{lit} C++, GetNextSurfaceTextureView method (replace, hidden)
TextureView Application::GetNextSurfaceTextureView() {
    {{Get the next surface texture}}
    {{Create surface texture view}}
    return targetView;
}
```

```{lit} C++, Private methods (replace, hidden)
private:
    TextureView GetNextSurfaceTextureView();
```

```{lit} C++, Get the next surface texture (replace, hidden)
SurfaceTexture surfaceTexture;
surface.getCurrentTexture(&surfaceTexture);
Texture texture = surfaceTexture.texture;
if (surfaceTexture.status != SurfaceGetCurrentTextureStatus::Success) {
    return nullptr;
}
```

```{lit} C++, Create surface texture view (replace, hidden)
TextureViewDescriptor viewDescriptor;
viewDescriptor.label = "Surface texture view";
viewDescriptor.format = texture.getFormat();
viewDescriptor.dimension = TextureViewDimension::_2D;
viewDescriptor.baseMipLevel = 0;
viewDescriptor.mipLevelCount = 1;
viewDescriptor.baseArrayLayer = 0;
viewDescriptor.arrayLayerCount = 1;
viewDescriptor.aspect = TextureAspect::All;
TextureView targetView = texture.createView(viewDescriptor);
```

```{lit} C++, Create Command Encoder (replace, hidden)
CommandEncoderDescriptor encoderDesc = {};
encoderDesc.label = "My command encoder";
CommandEncoder encoder = device.createCommandEncoder(encoderDesc);
```

```{lit} C++, Encode Render Pass (replace, hidden)
RenderPassDescriptor renderPassDesc = {};

{{Describe Render Pass}}

RenderPassEncoder renderPass = encoder.beginRenderPass(renderPassDesc);
{{Use Render Pass}}
renderPass.end();
renderPass.release();
```

```{lit} C++, Describe Render Pass (replace, hidden)
RenderPassColorAttachment renderPassColorAttachment = {};

{{Describe the attachment}}

renderPassDesc.colorAttachmentCount = 1;
renderPassDesc.colorAttachments = &renderPassColorAttachment;
renderPassDesc.depthStencilAttachment = nullptr;
renderPassDesc.timestampWrites = nullptr;
```

```{lit} C++, Describe the attachment (replace, hidden)
renderPassColorAttachment.view = targetView;
renderPassColorAttachment.resolveTarget = nullptr;
renderPassColorAttachment.loadOp = LoadOp::Clear;
renderPassColorAttachment.storeOp = StoreOp::Store;
renderPassColorAttachment.clearValue = Color{ 0.9, 0.1, 0.2, 1.0 };
#ifndef WEBGPU_BACKEND_WGPU
renderPassColorAttachment.depthSlice = WGPU_DEPTH_SLICE_UNDEFINED;
#endif // NOT WEBGPU_BACKEND_WGPU
```

```{lit} C++, Finish encoding and submit (replace, hidden)
// Finally encode and submit the render pass
CommandBufferDescriptor cmdBufferDescriptor = {};
cmdBufferDescriptor.label = "Command buffer";
CommandBuffer command = encoder.finish(cmdBufferDescriptor);
encoder.release();

std::cout << "Submitting command..." << std::endl;
queue.submit(1, &command);
command.release();
std::cout << "Command submitted." << std::endl;
```

```{lit} C++, Present the surface onto the window (replace, hidden)
targetView.release();
#ifndef __EMSCRIPTEN__
surface.present();
#endif
```

```{lit} C++, Poll WebGPU Events (replace, hidden)
#if defined(WEBGPU_BACKEND_DAWN)
	device.tick();
#elif defined(WEBGPU_BACKEND_WGPU)
	device.poll(false);
#endif
```

```{lit} C++, Define app target (replace, hidden)
{{Dependency subdirectories}}

add_executable(App
	main.cpp
)

{{Link libraries}}
```

```{lit} C++, file: webgpu-utils.h (replace, hidden)
```

```{lit} C++, file: webgpu-utils.cpp (replace, hidden)
```
