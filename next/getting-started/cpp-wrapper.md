C++ wrapper <span class="bullet">🟠</span>
===========

```{lit-setup}
:tangle-root: 028 - C++ Wrapper - Next
:parent: 025 - First Color - Next
:debug:
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

This wrapper is made of a **single header** file. **Exactly one** of your source files must define `WEBGPU_CPP_IMPLEMENTATION` before `#include <webgpu/webgpu.hpp>`. What I usually do to make sure there is no mix up with other includes is to **create a dedicated file** `implementations.cpp`.

```{lit} C++, file: implementations.cpp
// Define this in **exactly one** file
#define WEBGPU_CPP_IMPLEMENTATION
// Then include this anywhere you need the wrapper
#include <webgpu/webgpu.hpp>
// Make sure that subsequent includes do not also define the implementation
#undef WEBGPU_CPP_IMPLEMENTATION
```

```{note}
We will use other single file libraries that use the same idiom, which we will add to this same `implementations.cpp`.
```

Don't forget to add this new file to the `CMakeLists.txt`:

```{lit} CMake, App source files (append)
implementations.cpp
```

We now incrementally see the niceties that this wrapper introduces. Keep in mind that the C++ wrapper types are (almost) always **compatible with the C API**, so you can migrate your code **progressively**.

Core features
-------------

### Namespace

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

```{caution}
In the next chapters, I will add `using namespace wgpu;` in **implementation** files like `Application.cpp`, but **never do this in header files** like `Application.h`, otherwise it "invades" the namespace of all files that include you header. I this precise for instance `wgpu::Device` when defining Application attributes.
```

### Objects

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

### Scoped enumerations

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

### String View

Instead of writing conversion functions like `toStdStringView` and `toWgpuStringView`, the wrapper defines a `wgpu::StringView` type that is able to automatically convert:

```C++
deviceDesc.defaultQueue.label = toWgpuStringView("The Default Queue");
// [...]
WGPUStringView message = /* ... */;
std::cerr << "Uncaptured Error: " <<  toStdStringView(message) << std::endl;
```

becomes:

```C++
deviceDesc.defaultQueue.label = StringView("The Default Queue");
// [...]
StringView message = /* ... */;
std::cerr << "Uncaptured Error: " <<  message << std::endl;
```

### Capturing closures

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

Extensions
----------

Besides the core zero-overhead features described above, the wrapper provides some utility features. When these are used, they add a bit of runtime code, but that likely corresponds to what you would manually write without using them.

### Synchronous adapter and device requests

As we have seen in the early chapters, it can be convenient to get a version of `Instance::requestAdapter` and `Adapter::requestDevice` that are blocking instead of asynchronous. The wrapper provides a `Instance::requestAdapterSync` and a `Adapter::requestDeviceSync` that are equivalent to the utility functions that we previously introduced.

### Object pretty printing

Object wrappers (Instance, Adapter, Device, etc.) provide an overload of `operator<<` so that printing them with `std::cout` does not just give a pointer address but also prefixes it with the type name, like `<wgpu::Device 0x1234567>` instead of just `0x1234567`.

If you want to avoid this, just cast the object back to the raw type before printing it: `std::cout << (WGPUDevice)device < std::endl`.

Conclusion
----------

From now on, I will be providing two versions of each code snippet: one that uses this nice wrapper, and one that sticks with the raw C API.

Congratulations, you've made it to **the end of the "Getting Started" section**! It was not a small thing, you are now well equipped to explore and understand the various documentation about WebGPU. From here, you can decide to either move on to the [Graphics](../basic-3d-rendering/index.md) section and draw your first triangle, or go to the [Compute](../basic-compute/index.md) section and start playing with tensors.

*Resulting code:* [`step028-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step028-next)


```{lit} C++, Includes in Application.h (replace, hidden)
#include <webgpu/webgpu.hpp>

// Forward-declare
struct GLFWwindow;
```

```{lit} C++, Includes in Application.cpp (append, hidden)
using namespace wgpu; // NEW
```

```{lit} C++, Private methods (replace, hidden)
private:
	wgpu::TextureView GetNextSurfaceView(); // NEW
```

```{lit} C++, Application attributes (replace, hidden)
GLFWwindow *m_window = nullptr;
wgpu::Instance m_instance = nullptr; // NEW
wgpu::Device m_device = nullptr; // NEW
wgpu::Queue m_queue = nullptr; // NEW
wgpu::Surface m_surface = nullptr; // NEW
```

```{lit} C++, Initialize (replace, hidden)
{{Open window and get adapter}}

{{Request device}}

m_queue = m_device.getQueue(); // NEW

{{Surface Configuration}}

// We no longer need to access the adapter
adapter.release(); // NEW
```

```{lit} C++, Open window and get adapter (replace, hidden)
// Open window
glfwInit();
glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API); // <-- extra info for glfwCreateWindow
glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);
m_window = glfwCreateWindow(640, 480, "Learn WebGPU", nullptr, nullptr);

// Create instance ('instance' is now declared at the class level)
m_instance = createInstance(); // NEW

// Get adapter
std::cout << "Requesting adapter..." << std::endl;
{{Request adapter}}
std::cout << "Got adapter: " << adapter << std::endl;
```

```{lit} C++, Request adapter (replace, hidden)
{{Get the surface}}
RequestAdapterOptions adapterOpts = Default; // NEW
adapterOpts.compatibleSurface = m_surface;
Adapter adapter = requestAdapterSync(m_instance, &adapterOpts); // TODO
```

```{lit} C++, Request device (replace, hidden)
std::cout << "Requesting device..." << std::endl;
DeviceDescriptor deviceDesc = Default; // NEW
{{Build device descriptor}}
m_device = requestDeviceSync(m_instance, adapter, &deviceDesc); // TODO
std::cout << "Got device: " << m_device << std::endl;
```

```{lit} C++, Build device descriptor (replace, hidden)
deviceDesc.label = StringView("My Device"); // NEW

std::vector<FeatureName> features; // NEW
{{List required features}}
deviceDesc.requiredFeatureCount = features.size();
deviceDesc.requiredFeatures = (WGPUFeatureName*)features.data(); // NEW

// Make sure 'features' lives until the call to wgpuAdapterRequestDevice!
Limits requiredLimits = Default; // NEW
{{Specify required limits}}
deviceDesc.requiredLimits = &requiredLimits;

// Make sure that the 'requiredLimits' variable lives until the call to wgpuAdapterRequestDevice!
deviceDesc.defaultQueue.label = StringView("The Default Queue"); // NEW

{{Device Lost Callback}}

{{Device Error Callback}}
```

```{lit} C++, Device Lost Callback (replace, hidden)
auto onDeviceLost = []( // TODO: setter
	WGPUDevice const * device,
	WGPUDeviceLostReason reason,
	struct WGPUStringView message,
	void* /* userdata1 */,
	void* /* userdata2 */
) {
	// All we do is display a message when the device is lost
    std::cout
    	<< "Device " << device << " was lost: reason " << reason
    	<< " (" << StringView(message) << ")" // NEW
    	<< std::endl;
};
deviceDesc.deviceLostCallbackInfo.callback = onDeviceLost;
deviceDesc.deviceLostCallbackInfo.mode = WGPUCallbackMode_AllowProcessEvents;
```

```{lit} C++, Device Error Callback (replace, hidden)
auto onDeviceError = []( // TODO: setter
	WGPUDevice const * device,
	WGPUErrorType type,
	struct WGPUStringView message,
	void* /* userdata1 */,
	void* /* userdata2 */
) {
    std::cout
    	<< "Uncaptured error in device " << device << ": type " << type
    	<< " (" << StringView(message) << ")" // NEW
    	<< std::endl;
};
deviceDesc.uncapturedErrorCallbackInfo.callback = onDeviceError;
```

```{lit} C++, Surface Configuration (replace, hidden)
SurfaceConfiguration config = Default; // NEW
{{Describe the surface configuration}}
m_surface.configure(config); // NEW
```

```{lit} C++, Describe the surface configuration (replace, hidden)
// Configuration of the textures created for the underlying swap chain
config.width = 640;
config.height = 480;
config.device = m_device;
{{Describe surface format}}
config.presentMode = PresentMode::Fifo; // NEW
config.alphaMode = CompositeAlphaMode::Auto; // NEW
```

```{lit} C++, Describe surface format (replace, hidden)
SurfaceCapabilities capabilities = Default; // NEW

// We get the capabilities for a pair of (surface, adapter).
// If it works, this populates the `capabilities` structure
Status status = m_surface.getCapabilities(adapter, &capabilities); // NEW
if (status != Status::Success) { // NEW
    return false;
}

// From the capabilities, we get the preferred format: it is always the first one!
// (NB: There is always at least 1 format if the GetCapabilities was successful)
config.format = capabilities.formats[0];

// We no longer need to access the capabilities, so we release their memory.
capabilities.freeMembers(); // NEW
```

```{lit} C++, Terminate (replace, hidden)
m_surface.unconfigure(); // NEW
m_queue.release(); // NEW
{{Destroy surface}}
m_device.release(); // NEW
glfwDestroyWindow(m_window);
glfwTerminate();
```

```{lit} C++, Destroy surface (replace, hidden)
m_surface.release(); // NEW
```

```{lit} C++, Application implementation (replace, hidden)
bool Application::Initialize() {
	// Move the whole initialization here
	{{Initialize}}
	return true;
}

void Application::Terminate() {
	// Move all the release/destroy/terminate calls here
	{{Terminate}}
}

void Application::MainLoop() {
	glfwPollEvents();
	m_instance.processEvents(); // NEW

	{{Main loop content}}
}

bool Application::IsRunning() {
	return !glfwWindowShouldClose(m_window);
}

{{GetNextSurfaceView method}}
```

```{lit} C++, Get the next target texture view (replace, hidden)
// Get the next target texture view
TextureView targetView = GetNextSurfaceView(); // NEW
if (!targetView) return; // no surface texture, we skip this frame
```

```{lit} C++, Create Command Encoder (replace, hidden)
CommandEncoderDescriptor encoderDesc = Default; // NEW
encoderDesc.label = StringView("My command encoder"); // NEW
CommandEncoder encoder = m_device.createCommandEncoder(encoderDesc); // NEW
```

```{lit} C++, Encode Render Pass (replace, hidden)
RenderPassDescriptor renderPassDesc = Default; // NEW
{{Describe Render Pass}}

RenderPassEncoder renderPass = encoder.beginRenderPass(renderPassDesc); // NEW
{{Use Render Pass}}
renderPass.end(); // NEW
renderPass.release(); // NEW
```

```{lit} C++, Describe Render Pass (replace, hidden)
RenderPassColorAttachment colorAttachment = Default; // NEW
{{Describe the attachment}}
renderPassDesc.colorAttachmentCount = 1;
renderPassDesc.colorAttachments = &colorAttachment;
```

```{lit} C++, Describe the attachment (replace, hidden)
colorAttachment.view = targetView;
colorAttachment.loadOp = LoadOp::Clear; // NEW
colorAttachment.storeOp = StoreOp::Store; // NEW
colorAttachment.clearValue = Color{ 1.0, 0.8, 0.55, 1.0 }; // NEW
```

```{lit} C++, Finish encoding and submit (replace, hidden)
CommandBufferDescriptor cmdBufferDescriptor = Default; // NEW
cmdBufferDescriptor.label = StringView("Command buffer"); // NEW
CommandBuffer command = encoder.finish(cmdBufferDescriptor); // NEW
encoder.release(); // NEW // release encoder after it's finished

// Finally submit the command queue
std::cout << "Submitting command..." << std::endl;
m_queue.submit(command); // NEW
command.release(); // NEW
std::cout << "Command submitted." << std::endl;
```

```{lit} C++, Present the surface onto the window (replace, hidden)
targetView.release(); // NEW
#ifndef __EMSCRIPTEN__
m_surface.present(); // NEW
#endif
```

```{lit} C++, GetNextSurfaceView method (replace, hidden)
TextureView Application::GetNextSurfaceView() { // NEW
	{{Get the next surface texture}}
	{{Create surface texture view}}
	{{Release the texture}}
	return targetView;
}
```

```{lit} C++, Get the next surface texture (replace, hidden)
SurfaceTexture surfaceTexture = Default; // NEW
m_surface.getCurrentTexture(&surfaceTexture); // NEW
if (
    surfaceTexture.status != SurfaceGetCurrentTextureStatus::SuccessOptimal && // NEW
    surfaceTexture.status != SurfaceGetCurrentTextureStatus::SuccessSuboptimal
) {
    return nullptr;
}
```

```{lit} C++, Create surface texture view (replace, hidden)
TextureViewDescriptor viewDescriptor = Default; // NEW
viewDescriptor.label = StringView("Surface texture view"); // NEW
viewDescriptor.dimension = TextureViewDimension::_2D; // NEW // not to confuse with 2DArray
TextureView targetView = Texture(surfaceTexture.texture).createView(viewDescriptor); // NEW, TODO
```

```{lit} C++, Release the texture (replace, hidden)
Texture(surfaceTexture.texture).release(); // NEW, TODO
```
