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

Known Limitations
-----------------

 - The window's ratio should be applied to the x coord instead of y to match the behavior of GLM from the very beginning of the lecture.
