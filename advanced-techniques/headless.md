Headless context <span class="bullet">🟡</span>
================

````{tab} With webgpu.hpp
*Resulting code:* [`step030-headless`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-headless)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-headless-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-headless-vanilla)
````

Sometimes, one needs to use the GPU **without opening a window** at all. This is quite easy to do with WebGPU!

```{note}
The code of this chapter is based on the [`step030`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030) from [Hello Triangle](../basic-3d-rendering/hello-triangle.md).
```

In our *Hello Triangle* code, WebGPU interacts with the window in only two places:

 1. When creating the adapter.
 2. When setting up the swap chain.

Adapter creation
----------------

Our first change consists in replacing the `compatibleSurface` of the adapter options to `nullptr`:

````{tab} With webgpu.hpp
```C++
RequestAdapterOptions adapterOpts;
adapterOpts.compatibleSurface = nullptr;
//                              ^^^^^^^ This was 'surface'
Adapter adapter = instance.requestAdapter(adapterOpts);
```
````

````{tab} Vanilla webgpu.h
```C++
WGPURequestAdapterOptions adapterOpts = {};
adapterOpts.nextInChain = nullptr;
adapterOpts.compatibleSurface = nullptr;
//                              ^^^^^^^ This was 'surface'
WGPUAdapter adapter = requestAdapter(instance, &adapterOpts);
```
````

Swap Chain
----------

The swap chain is a mechanism meant to seamlessly display rendered images on the window. When we no longer have a window... we simply **no longer need a swap chain**!

````{tab} With webgpu.hpp
```C++
// Remove all this:
std::cout << "Creating swapchain..." << std::endl;
// [...]
std::cout << "Swapchain: " << swapChain << std::endl;

// We keep a target format though, for instance:
TextureFormat swapChainFormat = TextureFormat::RGBA8UnormSrgb;
```
````

````{tab} Vanilla webgpu.h
```C++
// Remove all this:
std::cout << "Creating swapchain..." << std::endl;
// [...]
std::cout << "Swapchain: " << swapChain << std::endl;

// We keep a target format though, for instance:
WGPUTextureFormat swapChainFormat = WGPUTextureFormat_BGRA8Unorm;
```
````

In the main render loop (which may not be a loop in a headless use case by the way) we need to **manage the target texture view** ourselves instead of using `swapChain.getCurrentTextureView()`.

````{tab} With webgpu.hpp
```C++
// Remove this:
TextureView nextTexture = swapChain.getCurrentTextureView();
```
````

````{tab} Vanilla webgpu.h
```C++
// Remove this:
WGPUTextureView nextTexture = wgpuSwapChainGetCurrentTextureView(swapChain);
```
````

### Target texture

We now create the texture to render into, for instance where we used to create the swap chain. See chapter [A first texture](../basic-3d-rendering/texturing/a-first-texture.md) for more details about the texture creation.

````{tab} With webgpu.hpp
```C++
// During initialization
TextureDescriptor targetTextureDesc;
targetTextureDesc.label = "Render target";
targetTextureDesc.dimension = TextureDimension::_2D;
// Any size works here, this is the equivalent of the window size
targetTextureDesc.size = { 640, 480, 1 };
// Use the same format here and in the render pipeline's color target
targetTextureDesc.format = swapChainFormat;
// No need for MIP maps
targetTextureDesc.mipLevelCount = 1;
// You may set up supersampling here
targetTextureDesc.sampleCount = 1;
// At least RenderAttachment usage is needed. Also add CopySrc to be able
// to retrieve the texture afterwards.
targetTextureDesc.usage = TextureUsage::RenderAttachment | TextureUsage::CopySrc;
targetTextureDesc.viewFormats = nullptr;
targetTextureDesc.viewFormatCount = 0;
Texture targetTexture = device.createTexture(targetTextureDesc);
```
````

````{tab} Vanilla webgpu.h
```C++
// During initialization
WGPUTextureDescriptor targetTextureDesc = {};
targetTextureDesc.nextInChain = nullptr;
targetTextureDesc.label = "Render target";
targetTextureDesc.dimension = WGPUTextureDimension_2D;
// Any size works here, this is the equivalent of the window size
targetTextureDesc.size = { 640, 480, 1 };
// Use the same format here and in the render pipeline's color target
targetTextureDesc.format = swapChainFormat;
// No need for MIP maps
targetTextureDesc.mipLevelCount = 1;
// You may set up supersampling here
targetTextureDesc.sampleCount = 1;
// At least RenderAttachment usage is needed. Also add CopySrc to be able
// to retrieve the texture afterwards.
targetTextureDesc.usage = WGPUTextureUsage_RenderAttachment | WGPUTextureUsage_CopySrc;
targetTextureDesc.viewFormats = nullptr;
targetTextureDesc.viewFormatCount = 0;
Texture targetTexture = wgpuDeviceCreateTexture(device, &targetTextureDesc);
```
````

The `nextTexture` of the main loop is now simply a view of the target texture.

````{tab} With webgpu.hpp
```C++
// During initialization
TextureViewDescriptor targetTextureViewDesc;
targetTextureViewDesc.label = "Render texture view";
// Render to a single layer
targetTextureViewDesc.baseArrayLayer = 0;
targetTextureViewDesc.arrayLayerCount = 1;
// Render to a single mip level
targetTextureViewDesc.baseMipLevel = 0;
targetTextureViewDesc.mipLevelCount = 1;
// Render to all channels
targetTextureViewDesc.aspect = TextureAspect::All;
TextureView targetTextureView = targetTexture.createView(targetTextureViewDesc);

// In main loop, instead of using swapChain.getCurrentTextureView():
TextureView nextTexture = targetTextureView;
```
````

````{tab} Vanilla webgpu.h
```C++
// During initialization
WGPUTextureViewDescriptor targetTextureViewDesc = {};
targetTextureViewDesc.nextInChain = nullptr;
targetTextureViewDesc.label = "Render texture view";
// Render to a single layer
targetTextureViewDesc.baseArrayLayer = 0;
targetTextureViewDesc.arrayLayerCount = 1;
// Render to a single mip level
targetTextureViewDesc.baseMipLevel = 0;
targetTextureViewDesc.mipLevelCount = 1;
// Render to all channels
targetTextureViewDesc.aspect = WGPUTextureAspect_All;
WGPUTextureView targetTextureView = wgpuTextureCreateView(targetTexture, &targetTextureViewDesc);

// In main loop, instead of using swapChain.getCurrentTextureView():
WGPUTextureView nextTexture = targetTextureView;
```
````

```{note}
Depending on your use case you could have **more advanced target texture management**, with for instance multiple textures that you swap so that you can render the next frame while saving the previous one on disc for instance.
```

Since we reuse the same view from one frame to another one, **do not release it**!:

````{tab} With webgpu.hpp
```C++
// Remove this:
nextTexture.release();
```
````

````{tab} Vanilla webgpu.h
```C++
// Remove this:
wgpuTextureViewRelease(nextTexture);
```
````

### Saving frames

We no longer need to *present* the swap chain:

```C++
// Remove this
swapChain.present();
```

But this means nothing is done with the rendered texture! In order to see it, we can use the `saveImage` function provided in the [Screen capture](screen-capture.md) chapter.

With the files [save_image.h](../data/save_image.h) and [stb_image_write.h](../data/stb_image_write.h) saved next to your `main.cpp`, **replace the swap chain presentation** with the following:

```C++
saveTexture("output.png", device, targetTexture);
```

````{note}
Also include the save_image.h file at the beginning of your main file:

```C++
#include "save_image.h"
```
````

Main Loop
---------

The main loop consisted in rendering a new frame until the window gets closed:

```C++
// Previously:
while (!glfwWindowShouldClose(window)) {
	glfwPollEvents();
	// [...]
}
```

What this becomes totally depends on your use case. For the sake of this example, we will just keep the brackets but actually run its content **only once** then terminate the program:

```C++
// Now:
{ // Mock main "loop"
	// [...]
}
```

Clean-up
--------

If you run the program now, it should already create a `output.png` file (in the `build` directory)! You may finally remove all the unused parts and get rid of GLFW altogether:

```C++
#include <glfw3webgpu.h>
#include <GLFW/glfw3.h>

// [...]

if (!glfwInit()) {
	std::cerr << "Could not initialize GLFW!" << std::endl;
	return 1;
}

glfwWindowHint(GLFW_CLIENT_API, GLFW_NO_API);
glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);
GLFWwindow* window = glfwCreateWindow(640, 480, "Learn WebGPU", NULL, NULL);
if (!window) {
	std::cerr << "Could not open window!" << std::endl;
	return 1;
}

// [...]

Surface surface = glfwGetWGPUSurface(instance, window);

// [...]

swapChain.release();
surface.release();
// [...]
glfwDestroyWindow(window);
glfwTerminate();
```

You may also remove the directories `glfw` and `glfw3webgpu` and remove them from the `CMakeLists.txt`:

```CMake
# Remove this
add_subdirectory(glfw)
# and that
add_subdirectory(glfw3webgpu)

# And remove glfw and glfw3webgpu from dependencies here:
target_link_libraries(App PRIVATE webgpu)
```


````{tab} With webgpu.hpp
*Resulting code:* [`step030-headless`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-headless)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step030-headless-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step030-headless-vanilla)
````
