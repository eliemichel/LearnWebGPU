Learn WebGPU
============

```{translation-warning} Outdated Translation, /index.md
这是[原英文页面](%original%)的**社区翻译**，自翻译以来有已更新，因此可能不再同步。欢迎您的[贡献](%contribute%)！
```

*用于C++中的原生图形开发。*

本文档将指导您使用[WebGPU](https://www.w3.org/TR/webgpu)图形API创建适用于Windows、Linux和macOS的**原生3D应用程序**。

`````{admonition} 快速开始！(点击此处)
:class: foldable quickstart

*您想了解您编写的所有GPU代码吗？*

````{admonition} 是的，从零开始WebGPU！
:class: foldable yes

非常好！您可以直接前往[概述](introduction.md)，并**依次阅读所有章节**。
````

````{admonition} 不，我希望**跳过初始的样板代码**。
:class: foldable no

没问题，您随时都可以**返回[基本步骤](getting-started/index.md)**。

您可能会想看看**每页**头尾的<span></span>_**Resulting code**_<span></span>链接，例如：

```{image} /images/intro/resulting-code-light.png
:class: only-light with-shadow
```

```{image} /images/intro/resulting-code-dark.png
:class: only-dark with-shadow
```

*您是否愿意使用浅度的封装以便于阅读？*

```{admonition} 是的，我更喜欢C++风格的代码。
:class: foldable yes

请使用“**With webgpu.hpp**”选项卡。
```

```{admonition} 不，我要看**原始的C风格API**！
:class: foldable no

请使用“**Vanilla webgpu.h**”选项卡。vanilla WebGPU中的*Resulting code*不一定是最新的，但这个选项卡中的**所有代码块**都会是**最新**的。
```

要**这个基础代码**，请参阅项目搭建章节的[构建](getting-started/project-setup.md#building)部分。您可以在`cmake -B build`后面添加`-DWEBGPU_BACKEND=WGPU`（默认）或`-DWEBGPU_BACKEND=DAWN`以选择使用[wgpu-native](https://github.com/gfx-rs/wgpu-native)或[Dawn](https://dawn.googlesource.com/dawn/)作为后端.

*您希望基础代码进展到什么程度？*

```{admonition} 一个简单的三角形
:class: foldable quickstart

请查看[你好，三角形！](basic-3d-rendering/hello-triangle.md)章节。
```

```{admonition} 一个具有基本交互功能的3D网格查看器
:class: foldable quickstart

我建议从[照明控制](basic-3d-rendering/some-interaction/lighting-control.md)章节的末尾开始。
```

````

```{admonition} 我希望它们能**在Web上运行**。
:class: foldable warning

本文档的主体部分漏掉了几行额外的内容，请参阅[Web构建](appendices/building-for-the-web.md)附录来**调整示例**，以便它们在Web上运行！
```

`````

```{admonition}  🚧 施工中
文档**仍在构建**，**WebGPU标准亦在不断发展**。为帮助读者跟踪本文档的最新进展，我们在各章标题中使用了如下标识：

🟢 **最新版**：*使用最新版本的[WebGPU分发](https://github.com/eliemichel/WebGPU-distribution)*  
🟡 **已完成**：*已完成，但用的是旧版WebGPU*  
🟠 **施工中**：*足够可读，但不完整*  
🔴 **待施工**：*只触及了表面*  

**请注意：**<span></span>当使用章节的伴随代码时，请确保使用的是与`webgpu/`**相同的版本**，以避免差异。
```

目录
--------

```{toctree}
:titlesonly:

introduction
getting-started/index
basic-3d-rendering/index
basic-compute/index
advanced-techniques/index
appendices/index
```
