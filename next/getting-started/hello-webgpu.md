Hello WebGPU <span class="bullet">🟢</span>
============

```{lit-setup}
:tangle-root: 001 - Hello WebGPU - Next
:parent: 000 - Project setup - Next
:fetch-files: ../../data/WebGPU-distribution-v0.3.0-gamma-default-to-dawn.zip
```

*Resulting code:* [`step001-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001-next)

WebGPU is a *Render Hardware Interface* (RHI), which means that it is a programming library meant to provide a **unified interface** for multiple underlying graphics hardware and operating system setups.

For your C++ code, WebGPU is nothing more than **a single header file**, which lists all the available procedures and data structures: [`webgpu.h`](https://github.com/webgpu-native/webgpu-headers/blob/main/webgpu.h).

However, when building the program, your compiler must know in the end (at the final *linking* step) **where to find** the actual implementation of these functions. Contrary to native APIs, the WebGPU implementation is not provided by the driver, so we must explicitly provide it.

```{figure} /images/rhi-vs-opengl.png
:align: center
A *Render Hardware Interface* (RHI) like WebGPU is **not directly provided by the drivers**: we need to link to a library that implements the API on top of the low-level one that the system supports.
```

Installing WebGPU
-----------------

There exists mostly two cross-platform implementations of the WebGPU native header:

 - [wgpu-native](https://github.com/gfx-rs/wgpu-native), that is based on the Rust library [`wgpu`](https://github.com/gfx-rs/wgpu), which not only fuels Firefox but also a large portion of Rust graphics applications.
 - Google's [Dawn](https://dawn.googlesource.com/dawn), the implementation of WebGPU used by Chromium and its derivatives (Google Chrome, MS Edge, etc.).

```{figure} /images/different-backend.png
:align: center
There are (at least) two implementations of WebGPU, developed for the main web engines.
```

```{note}
> A notable implementation of WebGPU that is not supported here is the one from [WebKit](https://webkit.org/). It might be added in the future, although it is not a priority since it is not as cross-platform (it does not support Windows).
```

These two implementations still have **some discrepancies**, but these will disappear as the WebGPU specification gets stable. I try to write this guide such that it **works for both** of them.

**To ease the integration** of either of these in a CMake project, I share a [WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution) repository that lets you chose details through CMake variables, but exposes the same interface whichever implementation you choose.

```{important}
When looking at **examples** provided on each page of this guide, check out the `webgpu` directory to see **which version of the distribution** it is based on. WebGPU is still evolving so each update may break things.
```

### Integration

The easiest way to integrate this distribution is to **copy its content into your source tree** (it is just a couple of CMake files):

 1. **Download** the [zip release of WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution/archive/refs/tags/main-v0.3.0-alpha.zip).
 2. **Unzip** it at the root of the project and call it `webgpu/`. This directory should directly contain a `CMakeLists.txt` file (if not, remove the extra nested directory).
 3. Add `add_subdirectory(webgpu)` in your `CMakeLists.txt`.

```{lit} CMake, Dependency subdirectories (insert in {{Define app target}} before "add_executable")
# Include webgpu directory, to define the 'webgpu' target
add_subdirectory(webgpu)
```

```{important}
The name 'webgpu' here designate the **directory** where our webgpu distribution is located, so there should be a file `webgpu/CMakeLists.txt`. Otherwise it means that `webgpu.zip` was not decompressed in the correct directory; you may either move it or adapt the `add_subdirectory` directive.
```

 4. Add the `webgpu` target as a **dependency** of our app, using the `target_link_libraries` command (after `add_executable(App main.cpp)`).

```{lit} CMake, Link libraries (insert in {{Define app target}} after "add_executable")
# Add the 'webgpu' target as a dependency of our App
target_link_libraries(App PRIVATE webgpu)
```

```{tip}
This time, the name 'webgpu' is one of the **target** defined in `webgpu/CMakeLists.txt` by calling `add_library(webgpu ...)`, it is not related to a directory name.
```

 5. One additional step is needed when using **dynamic linking** (i.e., when the WebGPU backend is distributed as a .so/.dll/.dylib file next to your executable): **call the function** `target_copy_webgpu_binaries(App)` at the end of `CMakeLists.txt` to makes sure that the .so/.dll/.dylib file is copied next to it.

```{note}
Whenever you **distribute** your application, make sure to also distribute this dynamic library file as well!
```

```{lit} CMake, Link libraries (append)
# The application's binary must find the .so/.dll/.dylib file at runtime
# so we automatically copy it next to the binary.
target_copy_webgpu_binaries(App)
```

```{tip}
In case of static linking (the opposite of dynamic linking), the function `target_copy_webgpu_binaries` is still defined (so that you do not have to adapt your `CMakeLists.txt`) but it does nothing.
```

### CMake options

CMake options and cache variables are defined to enable **picking a specific version of the backend**. You may skip this section if you do not really care. In general, CMake options can be specified on the command line when invoking CMake:

```bash
# Call CMake with the value 'MY_VALUE' assigned to the variable 'MY_OPTION'
cmake -B build -DMY_OPTION=MY_VALUE
```

#### Choice of implementation

The first variable you may want to change is `WEBGPU_BACKEND`, which can be either `WGPU`, `DAWN` or `EMSCRIPTEN`.

```{tip}
When using `emcmake` (the CMake wrapper provided by emscripten), there is **no need** to explicitly set `WEBGPU_BACKEND` to `EMSCRIPTEN`. It will be automatically detected and no implementation will be fetched.
```

#### Building from source

By default, the distribution fetches a **precompiled version** of the WebGPU implementation so that your project builds faster. If you prefer building from source, set the option `WEBGPU_BUILD_FROM_SOURCE` to `ON`. This will take longer and require extra dependencies (Python in the case of Dawn).

```{note}
Building from source is **only available with Dawn** for now. Given that wgpu-native is written in rust, its integration into our C++ build process is a bit more involving.
```

**For more options**, and more details about what could motivate their choices, I invite you to visit the [README of WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution). Meanwhile, **I recommend** using precompiled binaries at first, with either Dawn or wgpu-native.

#### Examples

To sum up, here are a couple of examples of how to customize the you build:

```bash
# Build using a precompiled wgpu-native backend
cmake -B build-wgpu -DWEBGPU_BACKEND=WGPU -DWEBGPU_BUILD_FROM_SOURCE=OFF
cmake --build build-wgpu

# Build using a Dawn backend built from source
cmake -B build-dawn -DWEBGPU_BACKEND=DAWN -DWEBGPU_BUILD_FROM_SOURCE=ON
cmake --build build-dawn

# Build using emscripten (no need for a specific backend -- see below
# if you are new to emscripten)
emcmake cmake -B build-emscripten
cmake --build build-emscripten
```

### Implementation-specific behavior

This guide intends to provide code that is **compatible with all backends**. Since there still exists slight differences between implementations, the distributions I provide define the following preprocessor variables:

```C++
// If using Dawn
#define WEBGPU_BACKEND_DAWN

// If using wgpu-native
#define WEBGPU_BACKEND_WGPU

// If using emscripten
#define WEBGPU_BACKEND_EMSCRIPTEN
```

Testing the installation
------------------------

To test the implementation, we simply create the WebGPU **instance** (the equivalent of the `navigator.gpu` we could get in JavaScript). We then check it and destroy it.

```{lit} C++, file: main.cpp
{{Includes}}

int main (int, char**) {
    {{Create WebGPU instance}}

    {{Check WebGPU instance}}

    {{Release WebGPU instance}}

    return 0;
}
```

```{important}
Make sure to include `<webgpu/webgpu.h>` before using any WebGPU function or type!
```

```{lit} C++, Includes
// Includes
#include <webgpu/webgpu.h>
#include <iostream>
```

### Descriptors and Creation

The instance is created using the `wgpuCreateInstance` function. We will see that all WebGPU functions meant to **create** an entity take as argument a **descriptor**. This descriptor is used to specify options regarding how to set up this object.

```{lit} C++, Create WebGPU instance
// We create a descriptor
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;

// We create the instance using this descriptor
WGPUInstance instance = wgpuCreateInstance(&desc);
```

```{note}
The descriptor is a kind of way to **pack many function arguments** together, because some descriptors really have a lot of fields. It can also be used to write utility functions that take care of populating the arguments, to ease the program's architecture.
```

We meet another WebGPU **idiom** in the `WGPUInstanceDescriptor` structure: the first field of a descriptor is always a pointer called `nextInChain`. This is a generic way for the API to enable **custom extensions** to be added in the future, or to return multiple entries of data. **In most cases, we set it to `nullptr`.**


### Check

A WebGPU entity created with a `wgpuCreateSomething` function is technically **just a pointer**. It is an opaque handle that identifies the actual object, which lives on the backend side and to which we never need direct access.

To check that an object is valid, we can just compare it with `nullptr`, or use the boolean operator:

```{lit} C++, Check WebGPU instance
// We can check whether there is actually an instance created
if (!instance) {
    std::cerr << "Could not initialize WebGPU!" << std::endl;
    return 1;
}

// Display the object (WGPUInstance is a simple pointer, it may be
// copied around without worrying about its size).
std::cout << "WGPU instance: " << instance << std::endl;
```

This should display something like `WGPU instance: 000001C0D2637720` at startup.

### Destruction and lifetime management

All the entities that were **created** using WebGPU must eventually be **released**. A procedure that creates an object always looks like `wgpuCreateSomething`, and its equivalent for releasing it is `wgpuSomethingRelease`.

Note that each object internally holds a reference counter, and releasing it only frees related memory if no other part of your code still references it (i.e., the counter falls to 0):

```C++
WGPUSomething sth = wgpuCreateSomething(/* descriptor */);

// This means "increase the ref counter of the object sth by 1"
wgpuSomethingAddRef(sth);
// Now the reference is 2 (it is set to 1 at creation)

// This means "decrease the ref counter of the object sth by 1
// and if it gets down to 0 then destroy the object"
wgpuSomethingRelease(sth);
// Now the reference is back to 1, the object can still be used

// Release again
wgpuSomethingRelease(sth);
// Now the reference is down to 0, the object is destroyed and
// should no longer be used!
```

In particular, we need to release the global WebGPU instance:

```{lit} C++, Release WebGPU instance
// We clean up the WebGPU instance
wgpuInstanceRelease(instance);
```

### Building for the Web

The WebGPU distribution listed above are readily compatible with [Emscripten](https://emscripten.org/docs/getting_started/downloads.html).

For some reason though the instance descriptor **must be null** (which means "use default") when using Emscripten, so we can already use our `WEBGPU_BACKEND_EMSCRIPTEN` macro:

```{lit} C++, Create WebGPU instance (replace)
// We create a descriptor
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;

// We create the instance using this descriptor
#ifdef WEBGPU_BACKEND_EMSCRIPTEN
WGPUInstance instance = wgpuCreateInstance(nullptr);
#else //  WEBGPU_BACKEND_EMSCRIPTEN
WGPUInstance instance = wgpuCreateInstance(&desc);
#endif //  WEBGPU_BACKEND_EMSCRIPTEN
```

Conclusion
----------

In this chapter we set up WebGPU and learnt that there are **multiple backends** available. We also saw the basic idioms of **object creation and destruction** that will be used all the time in WebGPU API!

*Resulting code:* [`step001-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001-next)
