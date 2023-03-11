Temporary page
==============

```{topic} youp
topic
```

```{admonition} youp
admonition
```

```{attention}
attention
```

```{caution}
caution
```

```{danger}
danger
```

```{error}
error
```

```{hint}
hint
```

```{important}
important
```

```{note}
note
```

```{seealso}
seealso
```

```{tip}
tip
```

```{warning}
warning
```

Streaming

Literate
--------

This is a test for the literate programming sphinx extension developped for this guide.

```{lit} C++, file: src/main.cpp
#include <iostream>
{{Includes}}

int main(int, char**) {
    {{Main content}}
}
```

Before anything, let's talk about the return value:

```{lit} C++, Main return
:caption: Main return

return EXIT_SUCCESS;
```

Note that this requires to include the `cstdlib` header:

```{lit} Includes
#include <cstdlib>
```

Then we can focus on the core content:

```{lit} Main content
std::cout << "Hello world" << std::endl;
{{Main return}}
```

```{lit} cmake, file: CMakeLists.txt
:emphasize-lines: 2, 3
project(Example)
add_executable(
    App
    {{Source files}}
)
```

```{lit} Source files
src/main.cpp
```

### Tangled result:

```{tangle} file: src/main.cpp
```

```{tangle} file: CMakeLists.txt
```

### Test

```C++
#include <webgpu/webgpu.h>

// [...]

int main (int, char**) {
    // 1. Create a descriptor
    WGPUInstanceDescriptor desc = {};
    desc.nextInChain = nullptr;

    // 2. Create the instance using this descriptor
    WGPUInstance instance = wgpuCreateInstance(&desc);

    // 3. Check for errors
    if (!instance) {
        std::cerr << "Could not initialize WebGPU!" << std::endl;
        return 1;
    }

    // 4. Display the object (WGPUInstance is a simple pointer).
    std::cout << "WGPU instance: " << instance << std::endl;
}
```

```C++
void Application::run() {
    initDevice();     // Different for native or web target

    loadResources();  // Textures, Buffers, Samplers, Shaders

    initBindings();   // Expose resources to shaders (Texture view)

    initPipelines();  // Prepare configurations of the GPU's pipeline

    submitCommands(); // Main core

    fetchResult();    // Get data back from the GPU

    cleanup();        // Different for wgpu and Dawn!
}
```

```C++
// Native
void Application::initDevice() {
    WGPUInstanceDescriptor desc;
    desc.nextInChain = nullptr;
    WGPUInstance instance = wgpuCreateInstance(&desc);

    WGPURequestAdapterOptions adapterOpts;
    adapterOpts.nextInChain = nullptr;
    // [...]
    WGPUAdapter adapter = wgpuInstanceRequestAdapterSync(instance, &adapterOpts);

    RequiredLimits requiredLimits = /* important! */;

    WGPUDeviceDescriptor deviceDesc;
    deviceDesc.nextInChain = nullptr;
    deviceDesc.requiredLimits = &requiredLimits;
    // [...]
    this->device = wgpuAdapterRequestDeviceSync(adapter, &deviceDesc);
}

// Web
#include <emscripten/html5_webgpu.h>
void Application::initDevice() {
    // Device setup goes in the JavaScript shell
    // that populates `Module.preinitializedWebGPUDevice`
    this->device = emscripten_webgpu_get_device();
}
```

```C++
// Native - webgpu.cpp

#include <webgpu/webgpu.hpp>
using namespace wgpu;

void Application::initDevice() {
    Instance instance = createInstance(InstanceDescriptor{});

    RequestAdapterOptions adapterOpts;
    // [...]
    Adapter adapter = instance.requestAdapterSync(adapterOpts);

    RequiredLimits requiredLimits = /* important! */;

    DeviceDescriptor deviceDesc;
    deviceDesc.requiredLimits = &requiredLimits;
    // [...]
    this->device = adapter.requestDeviceSync(deviceDesc);
}
```

```JavaScript
const adapter = await navigator.gpu.requestAdapter({ /* ... */ });
const device = await adapter.requestDevice({ requiredLimits: /* important! */ });
Module.preinitializedWebGPUDevice = device;
```

```html
<script>
    // From emscripten default shell
    const Module = { /* ... */ };

    // Custom for WebGPU
    (async () => {
        if (!navigator.gpu) {
            console.error("Sorry, WebGPU is not suported by your browser.");
            return;
        } else {
            const adapter = await navigator.gpu.requestAdapter();
            const device = await adapter.requestDevice();
            Module.preinitializedWebGPUDevice = device;

            const js = document.getElementById("main-script").content.cloneNode(true);
            document.body.appendChild(js);
        }
    })();
</script>
<template id="main-script">
    {{{ SCRIPT }}}
</template>
```

```C++
WGPUTexture texture = loadTexture("input.png");

WGPUComputePipeline computePipeline = initComputePipeline();

Queue queue = device.getQueue();

CommandEncoderDescriptor commandEncoderDesc = Default;
CommandEncoder encoder = m_device.createCommandEncoder(commandEncoderDesc);

ComputePassDescriptor computePassDesc = Default;
ComputePassEncoder computePass = encoder.beginComputePass(computePassDesc);

computePass.setPipeline(computePipeline);
computePass.setBindGroup(0, bindGroup, 0, nullptr);
computePass.dispatchWorkgroups(x, y, z);

computePass.end();
CommandBuffer command = encoder.finish(CommandBufferDescriptor{});
queue.submit(command);
```

Known Limitations
-----------------

 - The window's ratio should be applied to the x coord instead of y to match the behavior of GLM from the very beginning of the lecture.
