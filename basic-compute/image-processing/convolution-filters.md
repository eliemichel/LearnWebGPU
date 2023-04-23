Convolution Filters (🚧WIP)
===================

*Resulting code:* [`step215`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step215)

Many **image processing algorithms** are based on convolution filter operations somewhere in their pipeline.

The concept is simple: the new value of each pixel is computed by looking at a **sliding window** centered around the pixel, multiplying it by a fixed **kernel** and summing up.

```{image} /images/convolution/problem-light.png
:align: center
:class: only-light
```

```{image} /images/convolution/problem-dark.png
:align: center
:class: only-dark
```

<p class="align-center">
    <span class="caption-text"><em>An vertical Sobel filter is performed by sliding 1 pixel at a time a window of 3 by 3 pixels and multiplying its content with a given kernel.</em></span>
</p>

The **kernel** defines the way each neighbor of the pixel of interest influences its output value. In particular, a kernel that is $1$ in its center and $0$ everywhere else defines a filter that does nothing.

By changing the kernel, we can create a wide variety of filters. Some of them are **well known**, like the **Sobel** filter in the figure above or the **Gaussian blur** filter. Some others are **algorithmically discovered**, like the layers of [Convolutional Neural Networks](https://en.wikipedia.org/wiki/Convolutional_neural_network).

Sobel filter
------------

We can start with the Sobel filter from the figure above. A Sobel filter is meant to **detect edges**, either vertical ones or horizontal ones depending on how we orient the kernel.

Let us write the shader first, and then connect the dots:

```rust
@group(0) @binding(0) var inputTexture: texture_2d<f32>;
@group(0) @binding(1) var outputTexture: texture_storage_2d<rgba8unorm,write>;

@compute @workgroup_size(8, 8)
fn computeSobelX(@builtin(global_invocation_id) id: vec3<u32>) {
    let color = abs(
          1 * textureLoad(inputTexture, vec2<u32>(id.x - 1, id.y - 1), 0).rgb
        + 2 * textureLoad(inputTexture, vec2<u32>(id.x - 1, id.y + 0), 0).rgb
        + 1 * textureLoad(inputTexture, vec2<u32>(id.x - 1, id.y + 1), 0).rgb
        - 1 * textureLoad(inputTexture, vec2<u32>(id.x + 1, id.y - 1), 0).rgb
        - 2 * textureLoad(inputTexture, vec2<u32>(id.x + 1, id.y + 0), 0).rgb
        - 1 * textureLoad(inputTexture, vec2<u32>(id.x + 1, id.y + 1), 0).rgb
    );
    textureStore(outputTexture, id.xy, vec4<f32>(color, 1.0));
}
```

Simple, right? All we need is the input and output textures. **I leave it as an exercise**, as it is very similar to the setup of the first part of the [Mipmap Generation](mipmap-generation.md) chapter, except that the output is a view of a different texture instead of being a different MIP level of the same one.

````{note}
Don't forget to change the entry point of the compute pipeline:

```C++
computePipelineDesc.compute.entryPoint = "computeSobelX";
```
````

On [this input image](../../images/pexels-petr-ganaj-4121222.jpg), you should get the following result:

```{figure} /images/convolution/sobelX.jpg
:align: center
:class: with-shadow
The result of our vertical Sobel filter
```

```{note}
It is interesting to apply this filter to the different MIP levels independently, to detect edges at different scales.
```

GUI
---

TODO

```{admonition} Optional section
If you are only interested in the convolution filters themselves and that making a non-interactive command line tool is fine, you may skip this section.
```

In order to quickly experiment with our filters, we import the image viewer we had in the [First texture](../../basic-3d-rendering/texturing/a-first-texture.md) chapter, and the GUI elements from the [Simple GUI](../../basic-3d-rendering/some-interaction/simple-gui.md) chapter.

In a nutshell, we must:

 - Add the `glfw`, `glfw3webgpu` and `imgui` library as dependencies (don't forget to add a CMakeLists in the `imgui` directory).
 - Add an `initWindow`, `initSwapChain` and `initGui` init steps (and matching teminate steps).
 - Add a main application loop.
 - Add event callbacks.

To avoid building our own render pipeline, we can use ImGui to draw texture views:

```C++
void Application::onGui(RenderPassEncoder renderPass) {
	// [...]

	ImDrawList* drawList = ImGui::GetBackgroundDrawList();
	drawList->AddRectFilled({ 0, 0 }, { 20, 20 }, ImColor(255, 0, 0));
	drawList->AddImage((ImTextureID)m_textureMipViews[0], { 20, 0 }, { 220, 200 });

	// [...]
}
```

```{figure} /images/drawList.png
:align: center
:class: with-shadow
The red rectangle and the image are drawn by ImGui, no need for us to care about a render pipeline!
```

```{figure} /images/sobel.jpg
:align: center
:class: with-shadow
A Sobel filter (left: input, right: output)
```

Uniforms
--------

Gaussian blur
-------------

TODO: We iterate instead of using a large kernel.

*Resulting code:* [`step215`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step215)
