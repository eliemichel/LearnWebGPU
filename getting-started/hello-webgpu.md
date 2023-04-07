Hello WebGPU
============

```{lit-setup}
:tangle-root: 005 - Hello WebGPU
:parent: 001 - Opening a window
:fetch-files: ../data/wgpu-native-for-any.zip
```

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)

For your C++ code, WebGPU is nothing more than a single header file listing all the available procedures and data structures: [`webgpu.h`](https://github.com/webgpu-native/webgpu-headers/blob/main/webgpu.h). When building the program though, your compiler must know in the end (at the final *linking* step) where to find the actual implementation of these functions.

Installing WebGPU
-----------------

There exists mostly two implementations of the WebGPU native header:

 - [wgpu-native](https://github.com/gfx-rs/wgpu-native), exposing a native interface to the `wgpu` Rust library developed for Firefox.
 - Google's [Dawn](https://dawn.googlesource.com/dawn), developed for Chrome.

I tested both, and settled on the Firefox one for this documentation because its resulting binaries are much more lightweight than with Dawn. In both cases, the build process is a bit too heavy to be included in our CMakeLists so I provide pre-compiled builds:

 - [wgpu-native for Linux](../data/wgpu-native-for-linux.zip)
 - [wgpu-native for Windows](../data/wgpu-native-for-windows.zip)
 - [wgpu-native for MacOS](../data/wgpu-native-for-macos.zip)
 - [wgpu-native for any plateform](../data/wgpu-native-for-any.zip) (a bit heavier as it's a merge of all the above basically)
 - [GitHub repository](https://github.com/eliemichel/WebGPU-distribution/tree/wgpu)

```{important}
**WIP:** Use the GitHub repository link rather than the zip files, I haven't automated their generation yet so they are usually behind the repo.
```

Compared to the build provided by [the wgpu-native repository](https://github.com/gfx-rs/wgpu-native), I have added a simple `CMakeLists.txt` to make it as easy to integrate in our project as GLFW:

 1. Download the zip for your OS.
 2. Unzip it at the root of the project, there should be a `webgpu/` directory containing a `CMakeLists.txt` file and some other (.dll or .so).
 3. Add `add_subdirectory(webgpu)` in your `CMakeLists.txt`.
 4. Add the `webgpu` target as a dependency of our app, after GLFW in the `target_link_libraries` command.

One additional step though: call the function `target_copy_webgpu_binaries(App)` at the end of `CMakeLists.txt`, this makes sure that the .dll/.so file that your binary depends on at runtime is copied next to it. Whenever you distribute your application, make sure to also distribute this dynamic library file as well.

```{lit} CMake, Dependency subdirectories (append)
# Include webgpu directory, to define the 'webgpu' target
add_subdirectory(webgpu)
```

```{lit} CMake, Link libraries (replace)
# Add the 'webgpu' target as a dependency of our App
target_link_libraries(App PRIVATE glfw webgpu)

# The application's binary must find wgpu.dll or libwgpu.so at runtime,
# so we automatically copy it (it's called WGPU_RUNTIME_LIB in general)
# next to the binary.
target_copy_webgpu_binaries(App)
```

Testing the installation
------------------------

To test the setup, we call the `wgpuCreateInstance` function at the beginning of our main function. Like many WebGPU functions meant to **create** an entity, it takes as argument a **descriptor**, which we can use to specify options regarding how to set up this object.

And once again we meet a WebGPU idiom in the `WGPUInstanceDescriptor` structure. Its first field is a pointer called `nextInChain`. This is a generic way for the API to enable custom extensions to be added in the future, or to return multiple entries of data. In a lot of cases, we set it to `nullptr`.

```{lit} C++, file: main.cpp
#include <webgpu/webgpu.h>
#include <iostream>

int main (int, char**) {
	// We create the equivalent of the navigator.gpu if this were web code

    // 1. We create a descriptor
	WGPUInstanceDescriptor desc = {};
    desc.nextInChain = nullptr;

    // 2. We create the instance using this descriptor
	WGPUInstance instance = wgpuCreateInstance(&desc);

    // 3. We can check whether there is actually an instance created
    if (!instance) {
        std::cerr << "Could not initialize WebGPU!" << std::endl;
        return 1;
    }

    // 4. Display the object (WGPUInstance is a simple pointer, it may be
    // copied around without worrying about its size).
	std::cout << "WGPU instance: " << instance << std::endl;
}
```

This should build correctly and display something like `WGPU instance: 0000000000000008` at startup.

*Resulting code:* [`step005`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step005)
