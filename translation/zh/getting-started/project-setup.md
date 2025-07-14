配置项目 <span class="bullet">🟢</span>
=============

```{translation-warning} Outdated Translation, /getting-started/project-setup.md
这是[原始英文页面](%original%)的**社区翻译版本**。由于原文页面在翻译后**已更新**，因此内容可能不再同步。欢迎您参与[贡献](%contribute%)！
```

```{lit-setup}
:tangle-root: 000 - 配置项目
```

*结果代码:* [`step000`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step000)

我们会在示例代码中使用 [CMake](https://cmake.org/) 来管理代码编译. 这是跨平台构建中很标准的处理方式，同时我们遵守 [modern cmake](https://cliutils.gitlab.io/modern-cmake/) 风格编写这些配置。

必要条件
------------

我们只需要 CMake 和一个 C++ 编译器，下方提供了不同系统环境下的操作指南。

```{hint}
在完成安装后，你可以使用 `which cmake` (linux/macOS) 或 `where cmake` (Windows) 命令来查看命令行是否可以找到 `cmake` 命令的完整路径。在没有的情况下，请确保你的 `PATH` 环境变量包含 CMake 安装的目录。
```

### Linux

如果你使用的是 Ubuntu/Debian 发行版，安装以下包：

```bash
sudo apt install cmake build-essential
```

其他发行版也有类似的包，确保`cmake`, `make` 和 `g++` 命令可运行即可。

### Windows

从 [下载页面](https://cmake.org/download/) 下载并安装 CMake。你可以使用 [Visual Studio](https://visualstudio.microsoft.com/downloads/) 或 [MinGW](https://www.mingw-w64.org/) 作为编译器工具包。

### MacOS

You can install CMake using `brew install cmake`, and [XCode](https://developer.apple.com/xcode/) to build the project.
使用 `brew install cmake` 安装 CMake，然后使用 [XCode](https://developer.apple.com/xcode/) 构建项目。

最小项目
---------------

最小的项目包含一个 `main.cpp` 源文件和一个 `CMakeLists.txt` 构建文件。

让我们在 `main.cpp` 中从经典的 hello world 开始：

```{lit} C++, file: main.cpp
#include <iostream>

int main (int, char**) {
	std::cout << "Hello, world!" << std::endl;
	return 0;
}
```

在 `CMakeLists.txt` 中，我们指定我们想要创建一个类型为 *executable* 的 *target*（构建目标），名为 "App"（这将是可执行文件的名称），其源文件为 `main.cpp`：

```{lit} CMake, Define app target
add_executable(App main.cpp)
```

CMake 还期望在 `CMakeLists.txt` 的开头知道这个配置文件是为哪个版本的 CMake 编写的（<最低支持的版本>...<你使用的版本>），同时 CMake 也希望知道一些关于项目的信息：

```{lit} CMake, file: CMakeLists.txt
cmake_minimum_required(VERSION 3.0...3.25)
project(
	LearnWebGPU # 项目名称，如果你使用 Visual Studio，它也将是解决方案的名称
	VERSION 0.1.0 # 任意的版本号
	LANGUAGES CXX C # 项目使用的编程语言
)

{{Define app target}}

{{Recommended extras}}
```

构建
--------

我们现在可以开始构建我们的最小项目了。打开一个终端并跳转到包含 `CMakeLists.txt` 和 `main.cpp` 文件的目录：

```bash
cd your/project/directory
```

```{hint}
在 Windows 环境使用资源管理器打开你的项目目录时，按下 Ctrl+L，然后输入 `cmd` 并回车，就可以打开一个当前目录的终端窗口。
```

现在让我们要求 CMake 为我们的项目创建构建文件。我们通过使用 `-B build` 选项将由源代码生成的构建文件放在名为 *build/* 的目录中。我们强烈推荐这样的操作方式，它便于我们轻松地区分自动生成的文件和我们手动编写的文件（也就是源代码）：

```bash
cmake . -B build
```

这个指令会根据你的系统创建 `make`，Visual Studio 或 XCode 的构建文件（你可以使用 `-G` 选项来强制使用特定的构建系统，更多信息请参阅 `cmake -h`）。要最终构建程序并生成 `App`（或 `App.exe`）可执行文件，你可以打开生成的 Visual Studio 或 XCode 解决方案，或者在终端中输入：

```bash
cmake --build build
```

然后运行生成的程序：

```bash
build/App  # linux/macOS
build\Debug\App.exe  # Windows
```

推荐的额外配置
------------------

在调用 `add_executable` 之后的位置，我们可以通过调用 `set_target_properties` 命令来设置 `App` 目标的一些属性。

```{lit} CMake, Recommended extras
set_target_properties(App PROPERTIES
	CXX_STANDARD 17
	CXX_STANDARD_REQUIRED ON
	CXX_EXTENSIONS OFF
	COMPILE_WARNING_AS_ERROR ON
)
```

我们将 `CXX_STANDARD` 属性设置为 17 表示我们需要 C++17（它允许我们使用一些额外的语法，但不是强制性的）。`CXX_STANDARD_REQUIRED` 属性确保在 C++17 不支持时配置将失败。

我们将 `CXX_EXTENSIONS` 属性设置为 `OFF` 以禁用编译器特定的扩展（例如，在 GCC 上，这将使 CMake 使用 `-std=c++17` 而不是 `-std=gnu++17` 来设置编译标志列表）。

作为一个良好的实践，我们将 `COMPILE_WARNING_AS_ERROR` 打开，以确保没有警告被忽略。当我们学习一个新的语言/库时，警告尤其重要。因此为了确保有尽可能多的警告，我们添加下面这些编译选项：

```{lit} CMake, Recommended extras (append)
if (MSVC)
	target_compile_options(App PRIVATE /W4)
else()
	target_compile_options(App PRIVATE -Wall -Wextra -pedantic)
endif()
```

```{note}
在附带的代码中，我在 `utils.cmake` 中定义了一个名为 `target_treat_all_warnings_as_errors()` 的函数，并在 `CMakeLists.txt` 的开头包含了它。
```

在 macOS 上，CMake 可以生成 XCode 项目文件，但是默认情况下不会创建 *schemes*。XCode 可以为每个 CMake 目标生成一个 scheme，通常我们只想要主目标的方案。因此我们设置 `XCODE_GENERATE_SCHEME` 属性。同时我们启用帧捕获以进行 GPU 调试。

```{lit} CMake, Recommended extras (append)
if (XCODE)
	set_target_properties(App PROPERTIES
		XCODE_GENERATE_SCHEME ON
		XCODE_SCHEME_ENABLE_GPU_FRAME_CAPTURE_MODE "Metal"
	)
endif()
```

总结
----------

现在我们有了一个不错的**基本项目配置**，我们将在接下来的章节中以它为基础进行构建。在接下来的章节中，我们将看到如何[将WebGPU集成](hello-webgpu.md)到我们的项目中，如何[初始化它](adapter-and-device/index.md)，以及如何[打开一个窗口](opening-a-window.md)以进行绘制。

*结果代码:* [`step000`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step000)
