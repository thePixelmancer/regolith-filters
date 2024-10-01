export const GUIDES = {
  example: {
    clickSound: "sounds/ui/button_click", // Sound to play when buttons are clicked
    generateBackButton: true,
    backButton: {
      text: "Back",
      image: "textures/items/tsu_morph/battery_recipe",
      link: "back"
    },
    pages: {
      start: {
        title: "Welcome!",
        body: "Hello, {playerName}! Ready to begin your adventure?",
        buttons: [
          {
            text: "Start Your Journey",
            image: "textures/items/tsu_morph/start_button",
            link: "journeyStart"
          },
          {
            text: "Check Your Name",
            image: "textures/items/tsu_morph/stats_button",
            link: "nameCheck",
            callback: (player) => {
              player.sendMessage(`Your name is: ${player.name}`);
            }
          },
          {
            text: "Exit Guide",
            image: "textures/items/exit_button",
            link: "exit"
          }
        ]
      },
      journeyStart: {
        title: "Your Adventure Begins!",
        body: "What would you like to do next?",
        buttons: [
          {
            text: "Explore the Town",
            image: "textures/items/tsu_morph/town_button",
            link: "town"
          },
          {
            text: "Venture into the Forest",
            image: "textures/items/tsu_morph/forest_button",
            link: "forest"
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "start"
          }
        ]
      },
      nameCheck: {
        title: "Checking Your Name",
        body: "Click the button below to see your name.",
        buttons: [
          {
            text: "Show My Name",
            image: "textures/items/tsu_morph/name_button",
            callback: (player) => {
              player.sendMessage(`Your name is: ${player.name}`);
            }
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "start"
          }
        ]
      },
      town: {
        title: "Welcome to the Town!",
        body: "You are now in the town. What will you do?",
        buttons: [
          {
            text: "Talk to the Townsfolk",
            image: "textures/items/tsu_morph/talk_button",
            callback: (player) => {
              player.sendMessage(`${player.name}: "Hello, townsfolk!"`);
            }
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "journeyStart"
          }
        ]
      },
      forest: {
        title: "Into the Forest!",
        body: "The forest is full of wonders. What will you do?",
        buttons: [
          {
            text: "Search for Treasures",
            image: "textures/items/tsu_morph/treasure_button",
            callback: (player) => {
              player.sendMessage(`You, ${player.name}, found a hidden treasure!`);
            }
          },
          {
            text: "To start of jouney",
            image: "textures/items/tsu_morph/back_button",
            link: "journeyStart"
          }
        ]
      }
    }
  },
  second: {
    clickSound: "sounds/ui/button_click", // Sound to play when buttons are clicked
    generateBackButton: true,
    backButton: {
      text: "Back",
      image: "textures/items/tsu_morph/battery_recipe",
      link: "back"
    },
    pages: {
      start: {
        title: "Welcome!",
        body: "Hello, {playerName}! Ready to begin your adventure?",
        buttons: [
          {
            text: "Start Your Journey",
            image: "textures/items/tsu_morph/start_button",
            link: "journeyStart"
          },
          {
            text: "Check Your Name",
            image: "textures/items/tsu_morph/stats_button",
            link: "nameCheck",
            callback: (player) => {
              player.sendMessage(`Your name is: ${player.name}`);
            }
          },
          {
            text: "Exit Guide",
            image: "textures/items/exit_button",
            link: "exit"
          }
        ]
      },
      journeyStart: {
        title: "Your Adventure Begins!",
        body: "What would you like to do next?",
        buttons: [
          {
            text: "Explore the Town",
            image: "textures/items/tsu_morph/town_button",
            link: "town"
          },
          {
            text: "Venture into the Forest",
            image: "textures/items/tsu_morph/forest_button",
            link: "forest"
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "start"
          }
        ]
      },
      nameCheck: {
        title: "Checking Your Name",
        body: "Click the button below to see your name.",
        buttons: [
          {
            text: "Show My Name",
            image: "textures/items/tsu_morph/name_button",
            callback: (player) => {
              player.sendMessage(`Your name is: ${player.name}`);
            }
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "start"
          }
        ]
      },
      town: {
        title: "Welcome to the Town!",
        body: "You are now in the town. What will you do?",
        buttons: [
          {
            text: "Talk to the Townsfolk",
            image: "textures/items/tsu_morph/talk_button",
            callback: (player) => {
              player.sendMessage(`${player.name}: "Hello, townsfolk!"`);
            }
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "journeyStart"
          }
        ]
      },
      forest: {
        title: "Into the Forest!",
        body: "The forest is full of wonders. What will you do?",
        buttons: [
          {
            text: "Search for Treasures",
            image: "textures/items/tsu_morph/treasure_button",
            callback: (player) => {
              player.sendMessage(`You, ${player.name}, found a hidden treasure!`);
            }
          },
          {
            text: "To start of jouney",
            image: "textures/items/tsu_morph/back_button",
            link: "journeyStart"
          }
        ]
      }
    }
  },
  third: {
    clickSound: "sounds/ui/button_click", // Sound to play when buttons are clicked
    generateBackButton: true,
    backButton: {
      text: "Back",
      image: "textures/items/tsu_morph/battery_recipe",
      link: "back"
    },
    pages: {
      start: {
        title: "Welcome!",
        body: "Hello, {playerName}! Ready to begin your adventure?",
        buttons: [
          {
            text: "Start Your Journey",
            image: "textures/items/tsu_morph/start_button",
            link: "journeyStart"
          },
          {
            text: "Check Your Name",
            image: "textures/items/tsu_morph/stats_button",
            link: "nameCheck",
            callback: (player) => {
              player.sendMessage(`Your name is: ${player.name}`);
            }
          },
          {
            text: "Exit Guide",
            image: "textures/items/exit_button",
            link: "exit"
          }
        ]
      },
      journeyStart: {
        title: "Your Adventure Begins!",
        body: "What would you like to do next?",
        buttons: [
          {
            text: "Explore the Town",
            image: "textures/items/tsu_morph/town_button",
            link: "town"
          },
          {
            text: "Venture into the Forest",
            image: "textures/items/tsu_morph/forest_button",
            link: "forest"
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "start"
          }
        ]
      },
      nameCheck: {
        title: "Checking Your Name",
        body: "Click the button below to see your name.",
        buttons: [
          {
            text: "Show My Name",
            image: "textures/items/tsu_morph/name_button",
            callback: (player) => {
              player.sendMessage(`Your name is: ${player.name}`);
            }
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "start"
          }
        ]
      },
      town: {
        title: "Welcome to the Town!",
        body: "You are now in the town. What will you do?",
        buttons: [
          {
            text: "Talk to the Townsfolk",
            image: "textures/items/tsu_morph/talk_button",
            callback: (player) => {
              player.sendMessage(`${player.name}: "Hello, townsfolk!"`);
            }
          },
          {
            text: "Go Back",
            image: "textures/items/tsu_morph/back_button",
            link: "journeyStart"
          }
        ]
      },
      forest: {
        title: "Into the Forest!",
        body: "The forest is full of wonders. What will you do?",
        buttons: [
          {
            text: "Search for Treasures",
            image: "textures/items/tsu_morph/treasure_button",
            callback: (player) => {
              player.sendMessage(`You, ${player.name}, found a hidden treasure!`);
            }
          },
          {
            text: "To start of jouney",
            image: "textures/items/tsu_morph/back_button",
            link: "journeyStart"
          }
        ]
      }
    }
  }
};
