More uniforms <span class="bullet">🟢</span>
=============

```{lit-setup}
:tangle-root: 043 - More uniforms - vanilla
:parent: 039 - A first uniform - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 043 - More uniforms
:parent: 039 - A first uniform
```

````{tab} With webgpu.hpp
*Resulting code:* [`step043`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step043)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step043-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step043-vanilla)
````

In order to illustrate the flexibility of the uniform binding process, let us add a second uniform variable, this time controlling the overall color of our scene.

There are multiple ways to add a second uniform:

 - In a different bind group.
 - In the same bind group but different binding.
 - In the same binding, by replacing the type of the uniform with a custom struct.

The interest of using a **different bind group** is to be able to call the render pipeline with multiple combinations of uniforms. For instance, a render engine typically uses a different bind group to store the camera and lighting information (that changes only between frames) and to store object information (location, orientation, etc.), which is different for each draw call within the same frame.

The interest of using a **different binding** (within the same bind group) is to set a different `visibility` depending on the binding. In our case, the time is only used in the `Vertex` shader, while the color is only needed by the `Fragment` shader, so this could be beneficial. However, we may decide to use the time in the `Fragment` shader eventually, so we'll use the same binding.

```{note}
Another reason is that different bindings should either point to different buffers, or point in the same buffer at **an offset that is at least** `deviceLimits.minUniformBufferOffsetAlignment`. By default, this value is set to 256 bytes for me, and the minimum supported by my adapter is 64. This would be a bit of a waste to add that much padding.
```

Shader side
-----------

Let us replace the uniform `uTime` that had type `f32` with a struct, which we call for instance `uMyUniforms`, with a custom struct type `MyUniforms`:

```{lit} rust, Declare uniforms (replace, also for tangle root "Vanilla")
/**
 * A structure holding the value of our uniforms
 */
struct MyUniforms {
	time: f32,
	color: vec4f,
};

// Instead of the simple uTime variable, our uniform variable is a struct
@group(0) @binding(0) var<uniform> uMyUniforms: MyUniforms;
```

In `vs_main`, we replace  `uTime` with `uMyUniforms.time`, then we use `uMyUniforms.color` in the fragment color.

```{lit} rust, Vertex shader (hidden, replace, also for tangle root "Vanilla")
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
	let ratio = 640.0 / 480.0;

	// We now move the scene depending on the time!
	var offset = vec2f(-0.6875, -0.463);
	let time = uMyUniforms.time;
	offset += 0.3 * vec2f(cos(time), sin(time));

	out.position = vec4f(in.position.x + offset.x, (in.position.y + offset.y) * ratio, 0.0, 1.0);
	out.color = in.color;
	return out;
}
```

```{lit} rust, Fragment shader (replace, also for tangle root "Vanilla")
fn fs_main(in: VertexOutput) -> @location(0) vec4f {
	// We multiply the scene's color with our global uniform (this is one
	// possible use of the color uniform, among many others).
	let color = in.color * uMyUniforms.color.rgb;

	// Gamma-correction
	let linear_color = pow(color, vec3f(2.2));
	return vec4f(linear_color, 1.0);
}
```

Of course depending on your use case you will find a name more relevant than "MyUniforms", but let's stick to this for now.

Buffer
------

On the CPU side, we define the very same struct:

```{lit} C++, Define uniform struct (also for tangle root "Vanilla")
/**
 * The same structure as in the shader, replicated in C++
 */
struct MyUniforms {
	float time;
	std::array<float, 4> color;  // or float color[4]
};
```

````{note}
We use the `std::array` type, that requires to include its header:

```{lit} C++, Includes (append, also for tangle root "Vanilla")
#include <array>
```
````

We place this struct definition in the `Application` class definition, at the beginning of the private section, where we'll place all internal structs:

```{lit} C++, Application private structs (insert in {{Application class}} after "bool IsRunning();", also for tangle root "Vanilla")
// After public methods, before private things
private:
	// Internal structs
	{{Define uniform struct}}
```

We also update the size of the buffer when creating it:

````{tab} With webgpu.hpp
```{lit} C++, Create uniform buffer (replace)
bufferDesc.size = sizeof(MyUniforms);
//                ^^^^^^^^^^^^^^^^^^ This was 4 * sizeof(float)

bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;
bufferDesc.mappedAtCreation = false;
uniformBuffer = device.createBuffer(bufferDesc);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create uniform buffer (replace, for tangle root "Vanilla")
bufferDesc.size = sizeof(MyUniforms);
//                ^^^^^^^^^^^^^^^^^^ This was 4 * sizeof(float)

bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Uniform;
bufferDesc.mappedAtCreation = false;
uniformBuffer = wgpuDeviceCreateBuffer(device, &bufferDesc);
```
````

The initial buffer upload thus becomes:

````{tab} With webgpu.hpp
```{lit} C++, Upload uniform values (replace)
// Upload the initial value of the uniforms
MyUniforms uniforms;
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Upload uniform values (replace, for tangle root "Vanilla")
// Upload the initial value of the uniforms
MyUniforms uniforms;
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

Updating the value of the buffer now looks like this:

````{tab} With webgpu.hpp
```{lit} C++, Update uniform buffer (replace)
// Update uniform buffer
MyUniforms uniforms;
uniforms.time = static_cast<float>(glfwGetTime());
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Update uniform buffer (replace, for tangle root "Vanilla")
// Update uniform buffer
MyUniforms uniforms;
uniforms.time = static_cast<float>(glfwGetTime());
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

And actually we can be more subtle, to only upload the bytes related to the `time` field:

````{tab} With webgpu.hpp
```{lit} C++, Update uniform buffer (replace)
float time = static_cast<float>(glfwGetTime());
// Only update the 1-st float of the buffer
queue.writeBuffer(uniformBuffer, 0, &time, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Update uniform buffer (replace, for tangle root "Vanilla")
float time = static_cast<float>(glfwGetTime());
// Only update the 1-st float of the buffer
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &time, sizeof(float));
```
````

Similarly we can update only the color bytes:

````{tab} With webgpu.hpp
```C++
// Update uniform buffer
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
queue.writeBuffer(uniformBuffer, sizeof(float), &uniforms.color, sizeof(Color));
//                               ^^^^^^^^^^^^^ offset of `color` in the uniform struct
```
````

````{tab} Vanilla webgpu.h
```C++
// Update uniform buffer
uniforms.color = { 1.0f, 0.5f, 0.0f, 1.0f };
wgpuQueueWriteBuffer(queue, uniformBuffer, sizeof(float), &uniforms.color, sizeof(Color));
//                                         ^^^^^^^^^^^^^ offset of `color` in the uniform struct
```
````

Better yet, if we forget the offset, or want to be flexible to the addition of new fields, we can use the built-in `offsetof` macro:

````{tab} With webgpu.hpp
```{lit} C++, Update uniform buffer (replace)
float time = static_cast<float>(glfwGetTime());
// Upload only the time, whichever its order in the struct
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, time), &time, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Update uniform buffer (replace, for tangle root "Vanilla")
float time = static_cast<float>(glfwGetTime());
// Upload only the time, whichever its order in the struct
wgpuQueueWriteBuffer(queue, uniformBuffer, offsetof(MyUniforms, time), &time, sizeof(float));
```
````

And if we would update the color:

````{tab} With webgpu.hpp
```C++
// Upload only the color, whichever its order in the struct
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));
```
````

````{tab} Vanilla webgpu.h
```C++
// Upload only the color, whichever its order in the struct
wgpuQueueWriteBuffer(queue, uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));
```
````


Binding layout
--------------


We increase the expected size of the buffer, first in the **layout**:

```{lit} C++, Define bindingLayout (append, also for tangle root "Vanilla")
bindingLayout.buffer.minBindingSize = sizeof(MyUniforms);
```

And in the **binding** itself:

```{lit} C++, Setup binding (append, also for tangle root "Vanilla")
binding.size = sizeof(MyUniforms);
```


We also need to change in the binding layout the visibility, so that both `Vertex` and `Fragment` shaders can access the uniforms:

````{tab} With webgpu.hpp
```{lit} C++, Define bindingLayout (append)
bindingLayout.visibility = ShaderStage::Vertex | ShaderStage::Fragment;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Define bindingLayout (append, for tangle root "Vanilla")
bindingLayout.visibility = WGPUShaderStage_Vertex | WGPUShaderStage_Fragment;
```
````


Memory Layout Constraints
-------------------------

### Alignment

There is one thing I have omitted until now: the architecture of the GPU imposes some constraints on the way we can organize fields in a uniform buffer.

If we look at [the uniform layout constraints](https://gpuweb.github.io/gpuweb/wgsl/#address-space-layout-constraints), we can see that **the offset** (as returned by `offsetof`) of a field of type `vec4f` **must be a multiple** of the size of `vec4f`, namely 16 bytes. We say that the field is **aligned** to 16 bytes.

In our current `MyUniforms` struct, this property is **not verified** because `color` as an offset of 4 bytes (`sizeof(float)`), which is obviously not a multiple of 16 bytes! An easy fix is simply to swap the `color` and `time` fields:

```C++
// Don't
struct MyUniforms {
	// offset = 0 * sizeof(f32) -> OK
	float time;

	// offset = 4 -> WRONG, not a multiple of sizeof(vec4f)
	std::array<float,4> color;
};

// Do
struct MyUniforms {
	// offset = 0 * sizeof(vec4f) -> OK
	std::array<float,4> color;

	// offset = 16 = 4 * sizeof(f32) -> OK
	float time;
};
```

```{warning}
If you used the `offsetof` macro to perform partial update of the uniform buffer, you are good to go. But if you did not, make sure to reflect this reordering of the fields of `MyUniforms` everywhere you relied on it!
```

And **don't forget** to apply the same change to the struct defined in the shader code!

```{lit} rust, Declare uniforms (replace, also for tangle root "Vanilla")
struct MyUniforms {
	color: vec4f, // <-- this is now first!
	time: f32,
};

@group(0) @binding(0) var<uniform> uMyUniforms: MyUniforms;
```

### Padding

Another constraint on uniform types is that they must be [host-shareable](https://gpuweb.github.io/gpuweb/wgsl/#host-shareable), which comes with [a constraint on the total structure size](https://gpuweb.github.io/gpuweb/wgsl/#alignment-and-size).

Basically, the total size must be **a multiple of the alignment size of its largest field**. In our case, this means it must be a multiple of 16 bytes (the size of `vec4f`).

Thus we add **padding** to our structure, namely an unused attribute at the end that fills in extra bytes:

```{lit} C++, Define uniform struct (replace, also for tangle root "Vanilla")
struct MyUniforms {
	std::array<float,4> color;
	float time;
	float _pad[3];
};
// Have the compiler check byte alignment
static_assert(sizeof(MyUniforms) % 16 == 0);
```

And this finally works!

```{figure} /images/webgpu-logo-tinted.png
:align: center
:class: with-shadow
The WebGPU logo, tinted with our new uniform color.
```

Conclusion
----------

We have seen here that providing multiple uniforms is commonly done by actually providing a single uniform that is a structure of multiple fields. Importantly these fields have memory alignment constraints.

```{seealso}
I started writing [an online utility tool](https://eliemichel.github.io/WebGPU-AutoLayout) to automatically derive a C++ struct that matches a WGSL struct. Note that it uses the type `vec3` from the GLM library instead of `std::array<float,3>` but it is easy to replace.
```

````{tab} With webgpu.hpp
*Resulting code:* [`step043`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step043)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step043-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step043-vanilla)
````
