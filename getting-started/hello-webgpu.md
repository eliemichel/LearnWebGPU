Hello WebGPU
============

```{lit-setup}
:tangle-root: 005 - Hello WebGPU
:parent: 001 - Opening a window
:fetch-files: ../data/webgpu-distribution.zip
```

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)

For your C++ code, WebGPU is nothing more than a single header file listing all the available procedures and data structures: [`webgpu.h`](https://github.com/webgpu-native/webgpu-headers/blob/main/webgpu.h). When building the program though, your compiler must know in the end (at the final *linking* step) where to find the actual implementation of these functions.

```{figure} /images/rhi-vs-opengl.png
:align: center
A *Render Hardware Interface* (RHI) like WebGPU is not directly provided by the drivers: we need to link to a library that implements the API on top of the low-level one that the system supports.
```

Installing WebGPU
-----------------

There exists mostly two implementations of the WebGPU native header:

 - [wgpu-native](https://github.com/gfx-rs/wgpu-native), exposing a native interface to the [`wgpu`](https://github.com/gfx-rs/wgpu) Rust library developed for Firefox.
 - Google's [Dawn](https://dawn.googlesource.com/dawn), developed for Chrome.

```{figure} /images/different-backend.png
:align: center
There are (at least) two implementations of WebGPU, developed for the two main web engines.
```

These two implementations still have **some discrepancies**, but they will disappear as the WebGPU specification gets stable. I try to write this guide such that it **works for both** of them.

To make the integration of either of these in a CMake project as easy as with GLFW and without too many extra dependencies, I share a [WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution) repository that lets you chose one of the following options:

### Option A: The lightness of wgpu-native

Since `wgpu-native` is written in rust, we cannot easily build it from scratch so the distribution includes pre-compiled libraries:

```{important}
**WIP:** Use the "for any platform" link rather than the platform-specific ones, I haven't automated their generation yet so they are usually behind the main one.
```

 - [wgpu-native for any platform](https://github.com/eliemichel/WebGPU-distribution/archive/refs/tags/wgpu-5433868.zip) (a bit heavier as it's a merge of all the above basically)
 - [wgpu-native for Linux](#)
 - [wgpu-native for Windows](#)
 - [wgpu-native for MacOS](#)

```{note}
The pre-compiled binaries are provided by the `wgpu-native` project itself so you can likely trust them. The only thing my distribution adds is a `CMakeLists.txt` that makes it easy to integrate.
```

**Pros**
 - This is the most lightweight to build with.

**Cons**
 - You do not build from source.
 - `wgpu-native` does not give as informative debug information as Dawn.

### Option B: The comfort of Dawn

Dawn gives much better error messages, and since it is written in C++ we can build it from source and thus inspect more deeply the stack trace in case of crash:

 - [Dawn for any platform](https://github.com/eliemichel/WebGPU-distribution/archive/refs/tags/dawn-5869.zip)

```{note}
The Dawn-based distribution I provide here fetches the source code of Dawn from its original repository, but in an as shallow as possible way, and pre-sets some options to avoid building parts that we do not use.
```

**Pros**

 - Dawn is much more comfortable to develop with, because it gives more detailed error messages.
 - It is in general ahead of `wgpu-native` regarding the progress of implementation (but `wgpu-native` will catch up eventually).

**Cons**
 - Although I reduced the need for extra dependencies, you still need to [install Python](https://www.python.org/) and [git](https://git-scm.com/download).
 - The distribution fetches Dawn's source code and its dependencies so the first time you build you need an **Internet connection**.
 - The initial build takes significantly longer, and occupies more disk space overall.

### Integration

Whichever distribution you choose, the integration is the same:

 1. Download the zip of your choice.
 2. Unzip it at the root of the project, there should be a `webgpu/` directory containing a `CMakeLists.txt` file and some other (.dll or .so).
 3. Add `add_subdirectory(webgpu)` in your `CMakeLists.txt`.

```{lit} CMake, Dependency subdirectories (append)
# Include webgpu directory, to define the 'webgpu' target
add_subdirectory(webgpu)
```

```{note}
When using Dawn, make sure to add the `webgpu` directory **after** you add `glfw`, otherwise Dawn provides its own version (which may be fine sometimes, but you don't get to chose the version).
```

 4. Add the `webgpu` target as a dependency of our app, after GLFW in the `target_link_libraries` command.

```{lit} CMake, Link libraries (replace)
# Add the 'webgpu' target as a dependency of our App
target_link_libraries(App PRIVATE glfw webgpu)
```

One additional step when using pre-compiled binaries: call the function `target_copy_webgpu_binaries(App)` at the end of `CMakeLists.txt`, this makes sure that the .dll/.so file that your binary depends on at runtime is copied next to it. Whenever you distribute your application, make sure to also distribute this dynamic library file as well.

```{lit} CMake, Link libraries (append)
# The application's binary must find wgpu.dll or libwgpu.so at runtime,
# so we automatically copy it (it's called WGPU_RUNTIME_LIB in general)
# next to the binary.
target_copy_webgpu_binaries(App)
```

```{note}
In the case of Dawn, there is no precompiled binaries to copy but I define the `target_copy_webgpu_binaries` function anyway (it does nothing) so that you can really use the same CMakeLists with both distributions.
```

### Option C: The flexibility of both

Bonus option that I use in the accompanying code that enables to decide on one distribution or the other upon calling `cmake`:

```
cmake -B build -DWEBGPU_BACKEND=WGPU
# or
cmake -B build -DWEBGPU_BACKEND=DAWN
```

This is given by the `main` branch of my distribution repository:

 - [WebGPU any distribution](https://github.com/eliemichel/WebGPU-distribution/archive/refs/heads/main.zip)

**Pros**
 - You can have two `build` at the same time, one that uses Dawn and one that uses `wgpu-native`

**Cons**
 - This is a "meta-distribution" that fetches the one you want at configuration time (i.e., when calling `cmake` the first time) so you need an **Internet connection** and **git** at that time.

And of course depending on your choice the pros and cons of *Option A* and *Option B* apply.

### Building for the Web

If you are interested in building your application for the web, you can consult [the dedicated appendix](../appendices/building-for-the-web.md)!

Testing the installation
------------------------

To test the implementation, we simply create the WebGPU **instance**, i.e., the equivalent of the `navigator.gpu` we could get in JavaScript. We then check it and destroy it.

```{lit} C++, file: main.cpp
#include <webgpu/webgpu.h>
#include <iostream>

int main (int, char**) {
    {{Create WebGPU instance}}

    {{Check WebGPU instance}}

    {{Destroy WebGPU instance}}

    return 0;
}
```

### Descriptors and Creation

The instance is created using the `wgpuCreateInstance` function. Like all WebGPU functions meant to **create** an entity, it takes as argument a **descriptor**, which we can use to specify options regarding how to set up this object.

````{tab} with webgpu.h
```{lit} C, -Vanilla Create WebGPU instance
// 1. We create a descriptor
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;

// 2. We create the instance using this descriptor
WGPUInstance instance = wgpuCreateInstance(&desc);
```
````

````{tab} with webgpu.hpp
```{lit} C++, Create WebGPU instance
// 1. We create a descriptor
wgpu::DeviceDescriptor desc = {};

// 2. We create the instance using this descriptor
wgpu::Instance instance = wgpu::createInstance(desc);
```
````

```{note}
The descriptor is a kind of way to pack many function arguments together, because some descriptors really have a lot of fields. It can also be used to write utility functions that take care of populating the arguments, to ease the program's architecture.
```

We meet another WebGPU idiom in the `WGPUInstanceDescriptor` structure: the first field of a descriptor is always a pointer called `nextInChain`. This is a generic way for the API to enable custom extensions to be added in the future, or to return multiple entries of data. In a lot of cases, we set it to `nullptr`.


### Check

A WebGPU entity created with a `wgpuCreateSomething` function is technically **just a pointer**. It is a blind handle that identifies the actual object, which lives on the backend side and to which we never need direct access.

To check that an object is valid, we can just compare it with `nullptr`, or use the boolean operator:

```{lit} C++, Check WebGPU instance
// 3. We can check whether there is actually an instance created
if (!instance) {
    std::cerr << "Could not initialize WebGPU!" << std::endl;
    return 1;
}

// 4. Display the object (WGPUInstance is a simple pointer, it may be
// copied around without worrying about its size).
std::cout << "WGPU instance: " << instance << std::endl;
```

This should display something like `WGPU instance: 000001C0D2637720` at startup.

### Destruction and lifetime management

All the entities that can be **created** using WebGPU must eventually be **released**. A procedure that creates an object always looks like `wgpuCreateSomething`, and its equivalent for releasing it is `wgpuSomethingRelease`.

Note that each object internally holds a reference counter, and releasing it only frees related memory if no other part of your code still references it (i.e., the counter falls to 0):

```C++
WGPUSomething sth = wgpuCreateSomething(/* descriptor */);

// This means "increase the ref counter of the object sth by 1"
wgpuSomethingReference(sth);
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


````{tab} with webgpu.h
```{lit} C++, -Vanilla Destroy WebGPU instance
// 5. We clean up the WebGPU instance
wgpuInstanceRelease(instance);
```
````

`````{tab} with webgpu.hpp
```{lit} C++, Destroy WebGPU instance
// 5. We clean up the WebGPU instance
wgpuInstanceRelease(instance);
```
`````

````{note}
In older versions of `wgpu-native`, the Release and Reference functions did not exist, and a Drop function was used to immediately free an object. See details in [this GitHub issue](https://github.com/webgpu-native/webgpu-headers/issues/9).

```C++
// With old versions of wgpu-native
WGPUSomething sth = wgpuCreateSomething(/* descriptor */);
// This means "the object sth will never be used ever again"
// and destroys the object right away:
wgpuSomethingDrop(sth);
```
````

### Implementation-specific behavior

In order to handle the slight differences between implementations, the distributions I provide also define the following preprocessor variables:

```C++
// If using Dawn
#define WEBGPU_BACKEND_DAWN

// If using wgpu-native
#define WEBGPU_BACKEND_WGPU

// If using emscripten
#define WEBGPU_BACKEND_EMSCRIPTEN
```

The case of emscripten only occurs when trying to compile our code as a WebAssembly module, which is covered in the [Building for the Web](../appendices/building-for-the-web.md) appendix.

Conclusion
----------

In this chapter we set up WebGPU and learnt that there are **multiple backends** available. We also saw the basic idioms of **object creation and destruction** that will be used all the time in WebGPU API!

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)
