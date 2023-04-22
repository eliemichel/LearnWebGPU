Convolution Filters (🚧WIP)
===================

*Resulting code:* [`step215`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step215)

TODO

A first example
---------------

TODO: Sobel filter

```{figure} /images/sobel.jpg
:align: center
:class: with-shadow
A Sobel filter (left: input, right: output)
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

Uniforms
--------

*Resulting code:* [`step215`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step215)
