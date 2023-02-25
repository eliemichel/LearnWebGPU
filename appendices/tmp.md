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

```{lit} C++, Base skeleton
#include <iostream>
int main(int, char**) {
    {{Main content}}
}
```

```{lit} Main content
std::cout << "Hello world" << std::endl;
```

```{lit} test
foo

blup
```

```{lit} test2
bar
```

```{tangle} C++, Base skeleton
```

Known Limitations
-----------------

 - The window's ratio should be applied to the x coord instead of y to match the behavior of GLM from the very beginning of the lecture.
