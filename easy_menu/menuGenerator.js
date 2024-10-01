import { ActionFormData } from "@minecraft/server-ui";
import { GUIDES } from "./menuData.js";

class Guide {
  constructor(guideData) {
    this.pages = guideData.pages;
    this.generateBackButton = guideData.generateBackButton;
    this.backButton = guideData.backButton;
  }

  // Method to generate and show a page form
  showPage(player, pageId, history = []) {
    const pageData = this.pages[pageId];
    const form = new ActionFormData();

    // Set the title and body of the form, using player attributes
    form.title(this.interpolateText(pageData.title, player));
    form.body(this.interpolateText(pageData.body, player));

    // Add buttons from the page configuration
    pageData.buttons.forEach((button) => {
      form.button(this.interpolateText(button.text, player), button.image);
    });

    // Add the universal "Back" button if there is a previous page in history and it's enabled for the guide
    if (this.generateBackButton && history.length > 0) {
      form.button(this.interpolateText(this.backButton.text, player), this.backButton.image);
    }

    form
      .show(player)
      .then((formData) => {
        const selection = formData.selection;
        if (formData.canceled || selection === undefined) {
          return;
        }

        // Determine if "Back" was selected when back button is enabled
        const isBackButton = this.generateBackButton && history.length > 0 && selection === pageData.buttons.length;

        if (isBackButton) {
          // Go back to the previous page
          const previousPage = history.pop();
          this.showPage(player, previousPage, history);
        } else {
          const selectedButton = pageData.buttons[selection];
          const nextPage = selectedButton.link;

          // Run the callback if it is defined
          if (typeof selectedButton.callback === "function") {
            selectedButton.callback(player);
          }

          // Handle 'exit' logic
          if (nextPage === "exit") {
            return;
          } else if (nextPage) {
            // Push the current page onto the history stack
            history.push(pageId);
            // Navigate to the next linked page
            this.showPage(player, nextPage, history);
          }
        }
      })
      .catch((error) => {
        player.sendMessage(`Failed to show form: ${error}`);
      });
  }

  // Helper function to interpolate player data into the text
  interpolateText(text, player) {
    text = text.replace(/\{playerName\}/g, player.name);
    return text;
  }
}

// Function to show a guide
export function showGuide(player, guide = "example", startPage = "start") {
  const guideData = GUIDES[guide];
  const generatedGuide = new Guide(guideData);
  generatedGuide.showPage(player, startPage);
}
