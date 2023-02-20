More uniforms
=============

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

The interest of using different bindings is to set a different `visibility` depending on the binding. In our case, the time is only used in the Vertex shader, while the color is only needed by the Fragment shader, so this could be beneficial. However, we may decide to use the time in the Fragment shader eventually, so we'll use the same binding.

```{note}
Another reason is that different bindings should either point to different buffers, or point in the same buffer at **an offset that is at least** `deviceLimits.minUniformBufferOffsetAlignment`. By default, this value is set to 256 bytes for me, and the minimum supported by my adapter is 64. This would be a bit of a waste to add that much padding.
```

Shader side
-----------

Let us replace the `f32` uniform with a struct:

```rust
/**
 * A structure holding the value of our uniforms
 */
struct MyUniforms {
	time: f32,
	color: vec4<f32>,
};

// Instead of the simple uTime variable, our uniform variable is a struct
@group(0) @binding(0) var<uniform> uMyUniforms: MyUniforms;

@vertex
// [...] (Replace uTime with uMyUniforms.time in here)

@fragment
fn fs_main() -> @location(0) vec4<f32> {
	// We multiply the scene's color with our global uniform (this is one
	// possible use of the color uniform, among many others).
	let color = in.color * uMyUniforms.color.rgb;
	// Gamma-correction
	let corrected_color = pow(color, vec3<f32>(2.2));
	return vec4<f32>(corrected_color, uMyUniforms.color.a);
}
```

Of course depending on your use case you will find a name more relevant than "MyUniforms", but let's stick to this for now.

Buffer
------

On the CPU side, we define the very same struct:

```C++
#include <array>

/**
 * The same structure as in the shader, replicated in C++
 */
struct MyUniforms {
	float time;
	std::array<float, 4> color;  // or float color[4]
};
```

The initial buffer upload thus becomes:

````{tab} With webgpu.hpp
```C++
// Upload the initial value of the uniforms
MyUniforms uniforms;
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

````{tab} Vanilla webgpu.h
```C++
// Upload the initial value of the uniforms
MyUniforms uniforms;
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

More generally, you should replace all instances of `sizeof(float)` by `sizeof(MyUniforms)` (when setting `bufferDesc.size`, `bindingLayout.buffer.minBindingSize` and `binding.size`).

Updating the value of the buffer now looks like this:

````{tab} With webgpu.hpp
```C++
// Update uniform buffer
uniforms.time = static_cast<float>(glfwGetTime());
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

````{tab} Vanilla webgpu.h
```C++
// Update uniform buffer
uniforms.time = static_cast<float>(glfwGetTime());
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```
````

And actually we can be more subtle, to only upload the bytes related to the `time` field:

````{tab} With webgpu.hpp
```C++
// Only update the 1-st float of the buffer
queue.writeBuffer(uniformBuffer, 0, &uniforms.time, sizeof(float));
```
````

````{tab} Vanilla webgpu.h
```C++
// Only update the 1-st float of the buffer
wgpuQueueWriteBuffer(queue, uniformBuffer, 0, &uniforms.time, sizeof(float));
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
```C++
// Upload only the time, whichever its order in the struct
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, time), &uniforms.time, sizeof(MyUniforms::time));
// Upload only the color, whichever its order in the struct
queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));
```
````

````{tab} Vanilla webgpu.h
```C++
// Upload only the time, whichever its order in the struct
wgpuQueueWriteBuffer(queue, uniformBuffer, offsetof(MyUniforms, time), &uniforms.time, sizeof(MyUniforms::time));
// Upload only the color, whichever its order in the struct
wgpuQueueWriteBuffer(queue, uniformBuffer, offsetof(MyUniforms, color), &uniforms.color, sizeof(MyUniforms::color));
```
````

Binding layout
--------------

The only thing to change in the binding layout is the visibility:

```C++
bindingLayout.visibility = ShaderStage::Vertex | ShaderStage::Fragment;
```

Memory Layout Constraints
-------------------------

### Alignment

There is one thing I have omitted until now: the architecture of the GPU imposes some constraints on the way we can organize fields in a uniform buffer.

If we look at [the uniform layout constraints](https://gpuweb.github.io/gpuweb/wgsl/#address-space-layout-constraints), we can see that **the offset** (as returned by `offsetof`) of a field of type `vec4<f32>` **must be a multiple** of the size of `vec4<f32>`, namely 16 bytes. We say that the field is **aligned** to 16 bytes.

In our current `MyUniforms` struct, this property is **not verified** because `color` as an offset of 4 bytes (`sizeof(float)`), which is obviously not a multiple of 16 bytes! An easy fix is simply to swap the `color` and `time` fields:

```C++
// Don't
struct MyUniforms {
	// offset = 0 * sizeof(f32) -> OK
	float time;

	// offset = 4 -> WRONG, not a multiple of sizeof(vec4<f32>)
	std::array<float,4> color;
};

// Do
struct MyUniforms {
	// offset = 0 * sizeof(vec4<f32>) -> OK
	std::array<float,4> color;

	// offset = 16 = 4 * sizeof(f32) -> OK
	float time;
};
```

And **don't forget** to apply the same change to the struct defined in the shader code!

```{warning}
If you used the `offsetof` macro to perform partial update of the uniform buffer, you are good to go. But if you did not, make sure to reflect this reordering of the fields of `MyUniforms` everywhere you relied on it!
```

### Padding

Another constraint on uniform types is that they must be [host-shareable](https://gpuweb.github.io/gpuweb/wgsl/#host-shareable), which comes with [a constraint on the total structure size](https://gpuweb.github.io/gpuweb/wgsl/#alignment-and-size).

Basically, the total size must be **a multiple of the alignment size of its largest field**. In our case, this means it must be a multiple of 16 bytes (the size of `vec4<f32>`).

Thus we add **padding** to our structure, namely an unused attribute at the end that fills in extra bytes:

```C++
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

````{tab} With webgpu.hpp
*Resulting code:* [`step043`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step043)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step043-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step043-vanilla)
````
