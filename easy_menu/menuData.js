export const GUIDES = {
  example: {
    start: {
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
      buttons: [
        { text: "Next to Page 2", image: "textures/items/tsu_morph/next_button", link: "page_2" },
      ],
    },
    page_2: {
      title: "Title 2 text",
      body: "Body 2 text",
      buttons: [
        { text: "Previous to Page 1", image: "textures/items/tsu_morph/prev_button", link: "page_1" },
      ],
    },
  }
};