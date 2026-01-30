Вчимо WebGPU
============

*Для нативної графіки на C++.*

Ця документація допоможе вам освоїти [WebGPU](https://www.w3.org/TR/webgpu) графічний API, щоб створювати **нативні 3D додатки** на C++ з нуля, для Windows, Linux і macOS.

`````{admonition} Швидкий Старт! (Натисни на Мене)
:class: foldable quickstart

*Чи хочете ви зрозуміти кожну частинку GPU коду, який ви пишете?*

````{admonition} Так, писати WebGPU код **з нуля**!
:class: foldable yes

Чудово! Ви можете просто перейти до [вступу](introduction.md) і **прочитати всі розділи** послідовно.
````

````{admonition} Ні, я краще **пропущу початковий шаблонний код**.
:class: foldable no

Це цілком логічно, ви можете завжди **повернутися до [початкових кроків](getting-started/index.md) пізніше**.

Ви, ймовірно, захочете переглянути посилання _**Кінцевий код**_ на початку та в кінці **кожної сторінки**, наприклад:

```{image} /images/intro/resulting-code-light.png
:class: only-light with-shadow
```

```{image} /images/intro/resulting-code-dark.png
:class: only-dark with-shadow
```

*Ви згодні використовувати тонку обгортку для зручнішого читання?*

```{admonition} Так, я віддаю перевагу **C++** коду.
:class: foldable yes

Зайдіть на "**З webgpu.hpp**" вкладку.
```

```{admonition} Ні, покажіть мені **сирий C WebGPU API**!
:class: foldable no

Зайдіть на "**Ванільний webgpu.h**" вкладку. *Кінцевий код* для ванільного WebGPU є менш актуальним, але ця вкладка також перемикає **всі блоки коду** всередині посібника, і вони є **актуальними**.
```

Для того, щоб **зробити збірку цього базового коду**, зверніться до [Збірка](getting-started/project-setup.md#building) секції розділу про налаштування проєкту. Ви можете додати `-DWEBGPU_BACKEND=WGPU` (стандарт) або `-DWEBGPU_BACKEND=DAWN` до `cmake -B build` команди, щоб обрати як бекенд [`wgpu-native`](https://github.com/gfx-rs/wgpu-native) або [Dawn](https://dawn.googlesource.com/dawn/) відповідно.

*Наскільки далеко ви хочете просунутися з базовим кодом?*

```{admonition} Простий трикутник
:class: foldable quickstart

Перегляньте розділ [Привіт трикутник](basic-3d-rendering/hello-triangle.md).
```

```{admonition} 3D-сітка з базовою взаємодією
:class: foldable quickstart

Я рекомендую починати з кінця розділу [Управління освітленням](basic-3d-rendering/some-interaction/lighting-control.md).
```

````

```{admonition} Я хочу, щоб все так само **запускалося в Інтернеті**.
:class: foldable warning

В основній частині посібника бракує декількох додаткових рядків, зверніться до [Збірка для Інтернету](appendices/building-for-the-web.md) додатку, щоб **адаптувати приклади** та, щоб вони запускались в Інтернеті!
```

`````

```{admonition}  🚧 Робота в процесі
Цей посібник досі **в розробці**, і **стандарт WebGPU досі еволюціонує**. Щоб допомогти читачу зрозуміти, наскільки актуальна інформація, ми використовуємо ці знаки в заголовках до кожного розділу:

🟢 **Актуальна!** *Використовує останню стабільну версію [WebGPU-distribution](https://github.com/eliemichel/WebGPU-distribution), а саме `v0.2.0`.*  
🟡 **Готове до читання** *але використовує старішу версію WebGPU.*  
🟠 **Робота в процесі**: *достатньо читабельно, але не закінчено.*  
🔴 **Треба зробити**: *ми тільки торкнулися поверхні.*  

Для попереднього огляду **майбутньої версії** цього посібника, ви можете глянути в сховану секцію [Наступне](next/index.md), але це не означає, що вона стабільна.

**Примітка:** При використанні супровідного коду з розділу, обов'язково використовуйте **саме ту версію** `webgpu/` яку вона надає, щоб уникнути розбіжностей.
```

Зміст
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

```{toctree}
:titlesonly:
:hidden:

next/index
```
