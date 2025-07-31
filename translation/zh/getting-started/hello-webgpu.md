Hello WebGPU <span class="bullet">🟢</span>
============

```{translation-warning} Outdated Translation, /getting-started/hello-webgpu.md
这是[原始英文页面](%original%)的**社区翻译版本**。由于原文页面在翻译后**已更新**，因此内容可能不再同步。欢迎您参与[贡献](%contribute%)！
```

```{lit-setup}
:tangle-root: zh/001 - Hello WebGPU
:parent: zh/000 - 配置项目
:fetch-files: ../../data/webgpu-distribution-v0.2.0-beta2.zip
```

*结果代码:* [`step001`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001)

WebGPU 是*渲染硬件接口* (RHI)，这代表它是一个用于对多种潜在图形硬件会操作系统提供**通用接口**的编程库。

对于你编写的 C++ 程序而言，WebGPU 仅仅是一个 **独立的头文件**，它的内部列出了所有可用的方法与数据结构：[`webgpu.h`](https://github.com/webgpu-native/webgpu-headers/blob/main/webgpu.h)。

然而，在构建程序时，你的编译器必须要在最后（在最终的*链接*步骤）知道**去哪里寻找**这些函数的具体实现。与本地 API 相反，驱动并不提供这些实现，因此我们必须要显式地提供它。

```{figure} /images/rhi-vs-opengl.png
:align: center
像 WebGPU 这样的<ins>渲染硬件接口（RHI）</ins>**并不是由驱动直接提供的**：我们需要将它链接到一个在（操作）系统之上实现了这些 API 的库。
```

安装 WebGPU
-----------------

目前，存在两套针对 WebGPU 本地头文件的实现：

 - [wgpu-native](https://github.com/gfx-rs/wgpu-native)，为 Firefox 开发的 Rust 库 [`wgpu`](https://github.com/gfx-rs/wgpu) 提供了一个原生接口。
 - Google 的 [Dawn](https://dawn.googlesource.com/dawn)，是为 Chrome 开发的库。

```{figure} /images/different-backend.png
:align: center
有（至少）两个 WebGPU 的实现，它们分别针对两大主流网页引擎开发。
```

目前这两种实现仍存在**一些差异**，但随着 WebGPU 规范趋于稳定，这些差异将会消失。本指南的编写力求**同时兼容这两种实现**。

为简化在 CMake 项目中的集成，我提供了一个[发行版 WebGPU](https://github.com/eliemichel/WebGPU-distribution) 仓库，您可以从以下选项中选择其一：

`````{admonition} 选项太多了？ (点击我)
:class: foldable quickstart

*您是否更看重快速构建而非详细的错误信息？*

````{admonition} 当然，我想要快速构建，并且不希望在首次构建时连接网络
:class: foldable yes

选择[**选项 A**](#选项-a-轻巧的-wgpu-native) (wgpu-native)！
````

````{admonition} 不，我需要更详细的错误信息。
:class: foldable no

选择[**选项 B**](#选项-b-舒适便捷的-dawn) (Dawn)！
````

```{admonition} 我不想做选择
:class: foldable warning

选择[**选项 C**](#选项-c-将二者灵活兼得)，它允许你在不同的实现后端之间自由切换！
```

`````

### 选项 A: 轻巧的 wgpu-native

由于 `wgpu-native` 是用 Rust 编写的，我们无法轻松地从头开始构建它，因此发行版中包含了预编译的库文件：

```{important}
**WIP:** 尽量使用“全平台版本”而不是针对特定平台的版本，由于我还后者完成自动化构建，所以它们一般在版本上会落后。
```

 - [wgpu-native 全平台版本](https://github.com/eliemichel/WebGPU-distribution/archive/refs/tags/wgpu-v0.19.4.1.zip) (由于针对了所有平台，所以体积会稍重)
 - [wgpu-native Linux 版](#)
 - [wgpu-native Windows 版](#)
 - [wgpu-native MacOS 版](#)

```{note}
预编译的二进文件是由 `wgpu-native` 项目直接提供的，因此你可以完全信任它。唯一的不同之处在与我在发行版中增加了一个 `CMakeLists.txt` 文件使集成更方便。
```

**优点**
 - 这是可构建的最轻量选择。

**缺点**
 - 你并不是从源代开始构建。
 - `wgpu-native` 并不能够给出像 Dawn 一样多的调试信息。

### 选项 B: 舒适便捷的 Dawn

相对而言，Down 提供了更完善的错误信息。同时，由于 Dawn 是有 C++ 编写的，所以我们可以从头构建它。在出现崩溃时我们也能够更深入的检查堆栈追踪信息：

 - [Dawn 全平台版本](https://github.com/eliemichel/WebGPU-distribution/archive/refs/tags/dawn-6536.zip)

```{note}
我提供的基于 Dawn 的发型版本是从它的原始仓库直接获取的源代码，单尽可能采取浅克隆的方式，并预设了一些选项以避免构建我们不需要使用的组件。
```

**优点**

 - 由于 Dawn 提供了更详细的错误信息，它在开发时会显著地更加便捷。
 - 相对于 `wgpu-native`，它在接口实现的进度上会更领先（不过 `wgpu-native` 最终也会赶上）。

**缺点**
 - 虽然我减少了对外部依赖的内容，但你还上需要[安装 Python](https://www.python.org/) 和 [git](https://git-scm.com/download)。
 - 发行版中会下载 Dawn 的源代码和它的依赖项，因此在初次使用时你需要连接到互联网。
 - 初次构建会显著耗费更长的时间，并且占用更多的硬盘空间。

````{note}
在 Linux 上使用时请参考 [Dawn 构建文档](https://dawn.googlesource.com/dawn/+/HEAD/docs/building.md)中需要安的包，截止到 2024 年 4 月 7 日，（在 Ubuntu 中）需要安装的包如下：

```bash
sudo apt-get install libxrandr-dev libxinerama-dev libxcursor-dev mesa-common-dev libx11-xcb-dev pkg-config nodejs npm
```
````

### 选项 C: 将二者灵活兼得

在这个选项中，我们只会包含一系列的 Cmake 文件到我们的项目中。根据我们的配置，它会自动下载 `wgpu-native` 或 Dawn。

```
cmake -B build -DWEBGPU_BACKEND=WGPU
# 或者
cmake -B build -DWEBGPU_BACKEND=DAWN
```

```{note}
**配套代码**使用了该选项。
```

This is given by the `main` branch of my distribution repository:
它在我的发行版仓库的 `main` 分支上提供：

 - [WebGPU 任意发行版](https://github.com/eliemichel/WebGPU-distribution/archive/refs/tags/main-v0.2.0-beta1.zip)

```{tip}
这个仓库的 README 文件包含了如何使用 FetchContent_Declare 将它添加到你的项目中的说明。操作完成后，根据编写的配置配置你会使用到较新版本的 Dawn 或 wgpu-native。因此本书中的示例可能会无法编译。请参考下方说明以下载本书对应的版本。
```

**优点**
 - 你可以同时拥两种`构建`，一种使用了 Dawn，另外一种使用 `wgpu-native`

**缺点**
 - 这是一个 `元发行版`，在你配置构建（也就是第一次使用 `cmake` 指令）时会下载对应的版本，所以你需要在这时拥有**网络连接**并安装好 **git**。

当然，根据你的选择，*Option A* 和 *Option B* 的优缺点也都会一同存在。

### 集成

不论你选择哪种发行版本，集成方式是相同的：

 1. 下载你所选择选项的压缩包。
 2. 把它解压到项目的根目录，解压后应当有一个 `webgpu/` 目录，它包含一个 `CMakeLists.txt` 和一些其他文件（.dll 或者 .so）。
 3. 在你的 `CMakeLists.txt` 中添加 `add_subdirectory(webgpu)`。

```{lit} CMake, 依赖子目录 (insert in {{定义应用构建目标}} before "add_executable")
# 包含 webgpu 目录, 以定义 'webgpu' 目标
add_subdirectory(webgpu)
```

```{important}
这里的“webgpu”指的是 webgpu 所在的目录，因此它应该包含一个 `webgpu/CMakeLists.txt` 文件。否则它代表了 `webgpu.zip` 并没有解压到正确的目录，你可以选择移动该目录，或修改 `add_subdirectory` 指令中的路径来解决该问题。
```

 4. 增加 `webgpu` 构建目标，并（在 `add_executable(App main.cpp)` 后）使用 `target_link_libraries` 指令将它设置为我们的应用的依赖。

```{lit} CMake, 链接库 (insert in {{定义应用构建目标}} after "add_executable")
# 向我们的 App 应用添加 `webgpu` 目标依赖
target_link_libraries(App PRIVATE webgpu)
```

```{tip}
这次，“webgpu” 指的是 `webgpu/CMakeLists.txt` 中的构建目标，它由 `add_library(webgpu ...)` 定义，它与目录名称并不相关。
```

在使用预编译二进制文件时，需额外增加一个步骤：在 `CMakeLists.txt` 文件的末尾调用函数 `target_copy_webgpu_binaries(App)`。此操作可确保运行时依赖的 .dll/.so 文件被复制到生成的可执行文件同级目录下。请注意，在发行你的应用程序时，必须同时发行此动态库文件。

```{lit} CMake, 链接库 (append)
# 应用二进制程序在运行时需要找到 wgpu.dll 或 libwgpu.so，因此我们将它自动复制到二
# 进制文件旁（它通常被称作 WGPU_RUNTIME_LIB）。
target_copy_webgpu_binaries(App)
```

```{note}
在使用 Dawn 时并不存在需要复制的预编译二进制文件，但我依然定义了 `target_copy_webgpu_binaries` 函数（它什么都不做），以便你针对两种发行版本使用完全相同的 CMakeLists。
```

测试安装
------------------------

要测试实现，我们只需创建 WebGPU **实例**，也就是我能做 JavaScript 环境中获取的d `navigator.gpu` 的等价物。然后会v检查并销毁它。

```{important}
确保在使用任何 WebGPU 函数或类型前引入 `<webgpu/webgpu.h>`！
```

```{lit} C++, 依赖引入
// 引入依赖
#include <webgpu/webgpu.h>
#include <iostream>
```

```{lit} C++, file: main.cpp
{{依赖引入}}

int main (int, char**) {
    {{新建 WebGPU 实例}}

    {{检查 WebGPU 实例}}

    {{销毁 WebGPU 实例}}

    return 0;
}
```

### 描述符和实例创建

实例通过 `wgpuCreateInstance` 函数创建。像所有用于**创建**实体的 WebGPU 函数一样，它以**描述符**作为参数，我们可以通过该描述来配置此对象的初始选项。

```{lit} C++, 新建 WebGPU 实例
// 我们创建一个描述符
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;

// 我们使用这个描述符创建一个实例
WGPUInstance instance = wgpuCreateInstance(&desc);
```

```{note}
描述符是一将**多个函数参数打包**在一起的方法，有时它们确实包含了太多参数。它也可以用于编写包含多个参数的工具函数以使程序结构简单。
```

我们在 `WGPUInstanceDescriptor` 的结构中遇到了另一个 WebGPU 的**惯用设计**：描述符的首个字段总是一个名称是 `nextInChain` 的指针。这是该 API 用于支持未来添加自定义扩展的通用机制。大部情况下，我们将它设置为 `nullptr`。

### 检查

通过 `wgpuCreateSomething` 函数创建的 WebGPU 实体在技术上**仅是一个指针**。它是一个不透明的句柄（opaque handle），用于标识后端实际存在的对象——我们永远无需直接访问该底层对象。

要验证对象是否有效，只需将其与 `nullptr` 比较，或使用布尔运算：

```{lit} C++, 检查 WebGPU 实例
// 我们检查实例是否真正被创建
if (!instance) {
    std::cerr << "Could not initialize WebGPU!" << std::endl;
    return 1;
}

// 打印对象 (WGPUInstance 是一个普通的指针，它可以被随意复制，而无需
// 关心它的体积）
std::cout << "WGPU instance: " << instance << std::endl;
```

程序时应当输出结构如 `WGPU instance: 000001C0D2637720` 的内容。

### 销毁与生命周期管理

所有通过 WebGPU 可**创建**的实体最终均需要被**释放**。创建对象的方法名称总是 `wgpuCreateSomething`，同时释放它的函数名字是 `wgpuSomethingRelease`。

需要注意的是，每个 WebGPU 对象内部都维护着一个引用计数器。只有当对象不再被代码中的其他部分引用时（即引用计数降为 0），释放该对象才会真正回收其关联的内存资源：

```C++
WGPUSomething sth = wgpuCreateSomething(/* 描述符 */);

// 这代表 “将对象 sth 的引用计数增加 1”
wgpuSomethingReference(sth);
// 现在引用数量为 2 (在创建时它被设置为 1)

// 这代表 “将对象 sth 的引用计数减少 1，如果降到了 0 就销毁对象”
wgpuSomethingRelease(sth);
// 现在引用数量为 1，对象依旧可被使用

// 再次释放
wgpuSomethingRelease(sth);
// 现在引用计数已经降到了 0，该对象会立刻销毁并不能再被使用
```

特别地，我们需要释放全局的 WebGPU 实例：

```{lit} C++, 销毁 WebGPU 实例
// 我们清除 WebGPU 实例
wgpuInstanceRelease(instance);
```

### 针对特定实现的行为

为了处理不同实现间的轻微差别，我提供的发行版本中还定义了如下预处变量：

```C++
// 如果使用 Dawn
#define WEBGPU_BACKEND_DAWN

// 如果使用 wgpu-native
#define WEBGPU_BACKEND_WGPU

// 如果使用 emscripten
#define WEBGPU_BACKEND_EMSCRIPTEN
```

### 为 Web 构建

上方列出的 WebGPU 发行版本已经与 [Emscripten](https://emscripten.org/docs/getting_started/downloads.html) 兼容。如果在构建你的 web 应用有任何问题时，你可以参考[它的专用附录](../appendices/building-for-the-web.md)。

因为我们未来会不时添加一些专为 web 构建定制的选项，我们先在 CMakeLists.txt 文件末尾新增一个专门的配置区块。

```{lit} CMake, file: CMakeLists.txt (append)
# Emscripten 的特殊配置
if (EMSCRIPTEN)
    {{Emscripten 的特殊配置}}
endif()
```

现在我们仅修改输出文件的后缀名为一个 HTML 网页（而不是一个 WebAssembly 模块或 JavaScript 库）。

```{lit} CMake, Emscripten 的特殊配置
# 输一个完整的网页，而不是一个简单的 WebAssembly 模块
set_target_properties(App PROPERTIES SUFFIX ".html")
```

由于某原因，在使用 Emscripten 时实例描述符**必须为空**（此时它表示“使用缺省值”），所以我们已经可以使用我们的 `WEBGPU_BACKEND_EMSCRIPTEN` 宏：

```{lit} C++, 新建 WebGPU 实例 (replace)
// 我们创建一个描述符
WGPUInstanceDescriptor desc = {};
desc.nextInChain = nullptr;

// 我们使用这个描述符创建一个实例
#ifdef WEBGPU_BACKEND_EMSCRIPTEN
WGPUInstance instance = wgpuCreateInstance(nullptr);
#else //  WEBGPU_BACKEND_EMSCRIPTEN
WGPUInstance instance = wgpuCreateInstance(&desc);
#endif //  WEBGPU_BACKEND_EMSCRIPTEN
```

总结
----------

在本章中，我们配置了 WebGPU 并了解到有**多个渲染后端**可用。同时，我们也掌握了 WebGPU API 中贯穿始终的核心编程范式——对象创建与销毁机制！

*结果代码:* [`step001`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step001)
