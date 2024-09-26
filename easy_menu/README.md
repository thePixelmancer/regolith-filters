# Easy Menu Guide Generator

=====================================

## Table of Contents

---

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Guide Configuration](#guide-configuration)
- [Navigation](#navigation)
- [Exit Logic](#exit-logic)

## Introduction

---

The Easy Menu Guide Generator is a JavaScript module that dynamically generates guides or menus using the `@minecraft/server-ui` library. The guide is configured using a JSON object, which defines the pages, buttons, and navigation flow.

## Getting Started

---

To use the Easy Menu Guide Generator, you need to import the `showGuide` module and create a your new guide in the `menuData.js` file.

```javascript
import { generateGuide } from "./menuGenerator.js";
import { showGuide } from "./menuData.js";
```

## Guide Configuration

---

The guide configuration object is a key in the GUIDES object that defines the pages, buttons, and navigation flow. Each page is defined by a unique key, and each page has a title, body, and buttons.

```js
export const GUIDES = {
  example: { // this is the guide name
    start: { // this is the default start page
      title: "Title text",
      body: "Body text",
      buttons: [
        { text: "Button 1", image: "textures/items/tsu_morph/battery_recipe", link: "page_1" },
        { text: "Button 2", image: "textures/items/tsu_morph/battery_recipe", link: "page_2" },
        { text: "Exit", image: "textures/items/exit_button", link: "exit" },
      ],
    },
    page_1: {
      title: "Title 1 text",
      body: "Body 1 text",
      buttons: [{ text: "Next to Page 2", image: "textures/items/tsu_morph/next_button", link: "page_2" }],
    },
    page_2: {
      title: "Title 2 text",
      body: "Body 2 text",
      buttons: [{ text: "Previous to Page 1", image: "textures/items/tsu_morph/prev_button", link: "page_1" }],
    },
  },
};
```

## Navigation

---

The guide navigation is handled by the `generateGuide` function, which creates a navigation flow based on the guide configuration object. Navigation history is kept and each page has a `back` button that navigates to the previous page, and each button has a `link` property that defines the next page to navigate to.

## Exit Logic

---

The guide exit logic is handled by the `generateGuide` function, which checks if the user has clicked the `exit` button. If the user has clicked the `exit` button, the guide will exit and display a message to the user.

```javascript
{
  "example": {
    "start": {
      "title": "Welcome to the Guide",
      "body": "This is the first page of the guide.",
      "buttons": [
        {
          "text": "Exit",
          "image": "textures/items/exit_button",
          "link": "exit"
        }
      ]
    }
  }
}
```

## Showing the guide to the player

---

Once your gide is created, show the guide to the player by using the imported `showGuide` function. Specify the name of the guide (key in the `GUIDES` object) and a starting page (page key in your newly created `guide object`)

```javascript
showGuide(player, "example", "start")
```

