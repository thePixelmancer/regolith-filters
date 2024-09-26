import { ActionFormData } from "@minecraft/server-ui";
import GUIDES from "./menuData.js";
/**
 * Function to dynamically generate the guide and handle navigation
 * @param {Object} guide The guide configuration object
 * @returns {Object} The generated guide object
 */
export function generateGuide(guide = GUIDES.example) {
  let generatedGuide = {};
  // Iterate over each page in the guide object
  Object.keys(guide).forEach((pageKey) => {
    const pageData = guide[pageKey];
    
    // Store the form in generatedGuide, and associate it with a callback
    generatedGuide[pageKey] = (player, history =[]) => {
      const form = new ActionFormData();
      
      // Set the title and body of the form
      form.title(pageData.title);
      form.body(pageData.body);

      // Add buttons from the page configuration
      pageData.buttons.forEach((button) => {
        form.button(button.text, button.image);
      });

      // Add the universal "Back" button if there is a previous page in history
      if (history.length > 0) {
        form.button("Back", "textures/items/back_button");
      }

      form.show(player).then((formData) => {
        const selection = formData.selection;
        if (formData.canceled || selection === undefined) {
          player.sendMessage("You exited the guide.");
          return;
        }

        // Determine if "Back" was selected
        const isBackButton = (history.length > 0 && selection === pageData.buttons.length);

        if (isBackButton) {
          // Go back to the previous page
          const previousPage = history.pop(); // Pop the last page from the stack
          generatedGuide[previousPage](player, history); // Go back to the previous page
        } else {
          const selectedButton = pageData.buttons[selection];
          const nextPage = selectedButton.link;

          // Handle 'exit' logic
          if (nextPage === "exit") {
            player.sendMessage("Exiting the guide...");
          } else {
            // Push the current page onto the history stack
            history.push(pageKey);
            // Navigate to the next linked page
            generatedGuide[nextPage](player, history);
          }
        }
      }).catch((error) => {
        player.sendMessage(`Failed to show form: ${error}`);
      });
    };
  });
  return generatedGuide;
}

/**
 * Generates a guide with a history stack and navigates to the specified start page.
 * @param {Player} player The player to show the guide to
 * @param {string} [guide="example"] The name of the guide to show. Available guides are in the GUIDES object.
 * @param {string} [startPage="start"] The name of the page to start on. If not specified, will default to "start".
 */
export function showGuide(player, guide = "example", startPage = "start") {
  // Generate the guide with a history stack
  const generatedGuide = generateGuide(GUIDES[guide]);
  // Start with the 'start' page and no previous history
  generatedGuide[startPage](player, []);
}
