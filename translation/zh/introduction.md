概述
============

```{translation-warning} Outdated Translation, /introduction.md
这是[原始英文页面](%original%)的**社区翻译版本**。由于原文页面在翻译后**已更新**，因此内容可能不再同步。欢迎您参与[贡献](%contribute%)！
```

什么是图形API？
-----------------------

我们的个人电脑和智能手机通常包含两个单元：**CPU**（*Central Processing Unit* 中央处理单元）和**GPU**（*Graphics Processing Unit* 图形处理单元）。编写应用程序时，**主要是为CPU编写命令**，这就是大多数编程语言的用途。

```{figure} /images/architecture-notes.png
:align: center
CPU和GPU是两种不同的处理器，我们对CPU进行编程，使其通过图形API和驱动程序指导GPU应该做什么。
```

如果想要应用程序在GPU上执行命令（如渲染3D画面），就必须由CPU**将指令发送给GPU的驱动程序**。图形API是CPU与GPU进行交互的编程接口。

有许多这样的API，例如您可能听说过的OpenGL、DirectX、Vulkan以及Metal。

```{tip}
理论上任何人都可以发明自己的图形API。每个GPU供应商都有自己的低级协议，用于驱动程序与硬件沟通，在此基础上实现了更常见的api（通常与驱动程序一起提供）。
```

本文档中，我们将学习一个名为WebGPU的图形API。它的设计目标是给GPU提供无关乎供应商和操作系统的**统一接口**。

```{figure} /images/rhi.png
:align: center
:class: with-shadow
WebGPU是一个**渲染硬件接口**，建立在您平台的驱动程序/操作系统所提供的各种API之上。这些重复的开发工作将由浏览器完成一次，并通过他们的`webgpu.h`头文件提供给我们。
```

<!--
    The different applications running on the computer are orchestrated in the CPU space, by the Operating System.

    Some APIs are directly provided by the driver, some others are an extra programming layer (a .so or .dll shared library, or some C files that needs to be compiled with your application).
-->

为何是WebGPU？
-----------

> 🤔 对啊，我为什么要用一个**web API**来开发一个**桌面应用**呢？

很高兴你这么问，简单来说就是：

 - 合理的抽象层次
 - 高性能
 - 跨平台
 - 足够标准化
 - 不会过时

事实上这是唯一一个受益于所有这些属性的图形API！

是的，WebGPU API主要是**为web设计**的，以作为JavaScript和GPU之间的接口。这**并不是缺点**，因为至今为止，web页面的性能需求已经与原生应用的需求相同。您可以在“[为什么我认为WebGPU是2023年最值得学习的图形API](appendices/teaching-native-graphics-in-2023.md)”中了解更多。

```{note}
在为Web设计API时，**隐私性**和**可移植性**是两个重要的约束，我们**受益**于为可移植性所做的努力，且当使用WebGPU为原生应用进行开发时，出于隐私考虑而对API作出的限制可以被**禁用**。
```

又为何是C++？
-------------

作为WebGPU的初始目标，我们为何不用**JavaScript**？或是编写`webgpu.h`头文件所使用的**C语言**？亦或是**Rust**？毕竟是WebGPU的其中一个后端所使用的语言。这些都是可行的，但我选择了C++，原因如下：

 - C++仍然是用于高性能图形应用（视频游戏、渲染引擎、建模工具等）的主要语言。
 - 一般来说，c++的抽象级别和控制非常适合与图形api交互。
 - 图形编程对于真正学习C++来说是非常好的机会，在一开始，我将只假设对其有非常粗浅的了解。

```{seealso}
对于Rust的等效文档，我建议您去看看Sotrh的[Learn WGPU](https://sotrh.github.io/learn-wgpu)。
```

如何使用此文档？
------------------------------

### 阅读指南

本文档的前两部分被设计成顺序阅读，以作为一个完整地教程，同时，他的不同页面也可作为特定主题的提点。

[开始](getting-started/index.md)部分处理初始化WebGPU和窗口管理（使用GLFW）所需的样板文件，并介绍API的关键概念和习惯用法。在这一部分，我们将操作原始的C语言API，并在最后介绍本文档的其余部分所使用的c++包装器。

也可以**直接前往第二部分**的[基础3D渲染](basic-3d-rendering/index.md)，并使用第1部分生成的样板代码作为入门工具包。您可以之后再回到开始部分确认细节。

如今，渲染远不是gpu的唯一用途；第3部分介绍了[基础计算](basic-compute/index.md)，即WebGPU的非渲染使用。

第四部分是[进阶技术](advanced-techniques/index.md)，重点介绍了各种计算机图形学技术，这些技术可以相互独立阅读。

### 文学化编程

```{warning}
本文档尚处于早期阶段；它只适用于前面几章。
```

本文档遵循**文学化编程**：您所阅读的所有文档都有注释，这样您就可以**自动将其代码块组合**成完整的工作代码。这是一种确保文档包含**再现结果**所需的所有内容的方法。

在支持它的章节的右侧栏，您可以选择显示/隐藏这些信息：

```{image} /images/literate-light.png
:align: center
:class: only-light
```

```{image} /images/literate-dark.png
:align: center
:class: only-dark
```

默认情况下，所有功能都是关闭的，以避免视觉混乱，您可以在您不知道在特定代码片段具体应包含在哪里时将其打开。

### 贡献

如果您遇到任何错别字或更严重的问题，您可以点击每个页面顶部的编辑按钮来修复它们！

```{image} /images/edit-light.png
:alt: 使用每个页面顶部的编辑按钮！
:class: only-light
```

```{image} /images/edit-dark.png
:alt: 使用每个页面顶部的编辑按钮！
:class: only-dark
```

更普遍地说，您可以通过[储存库的issues](https://github.com/eliemichel/LearnWebGPU/issues)讨论任何技术或组织选择。欢迎任何建设性和/或善意的反馈！

### 施工中

文档仍在构建，WebGPU亦是如此。我试图尽可能严格地遵循这些变化，但在API变得稳定之前总会导致轻微的不一致。

请务必留意最后一次修改页面和附加代码的日期（使用[git](https://github.com/eliemichel/LearnWebGPU)）。它们可能不会完全同步；我通常先更新代码，再更新文档。

<!--
    Cross-platform is not optional. It never really was, but since the global pandemic of 2020 it is even more important: students follow the lecture from a wide variety of devices and a teacher cannot rely on them using all the same machine from the university's lab room.
-->
