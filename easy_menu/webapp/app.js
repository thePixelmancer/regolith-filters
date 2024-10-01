let GUIDES = {};
let CURRENT_GUIDE = {};
let CURRENT_GUIDE_KEY = "";
let DIRTY = false;

function setDirty(value) {
  if (value) {
    DIRTY = true;
    document.getElementById("save-button").classList.add("dirty");
  } else {
    DIRTY = false;
    document.getElementById("save-button").classList.remove("dirty");
  }
}

const fileInput = document.getElementById("file-input");
fileInput.addEventListener("change", function () {
  let fr = new FileReader();
  fr.readAsText(this.files[0]);
  fr.onload = function () {
    const extractDataFunc = new Function(fr.result.replace(/^\s*export\s+/, "") + "; return GUIDES;");
    GUIDES = extractDataFunc();
    selectGuide(GUIDES);
  };
  fileInput.value = "";
});
document.getElementById("download-button").addEventListener("click", function () {
  prompt("Save under different name? Renaming will leave the old guide intact.", CURRENT_GUIDE_KEY);
  GUIDES[CURRENT_GUIDE_KEY] = CURRENT_GUIDE;
  // Convert GUIDE object to JavaScript module format
  const exportString = `export const GUIDES = ${JSON.stringify(GUIDES, null, 2)};`;

  // Create a Blob with the guide content
  const blob = new Blob([exportString], { type: "text/javascript" });

  // Create a link to download the Blob
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "menuData.js"; // Filename for the downloaded file

  // Append link to the document, trigger click, and remove it
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
});
// Initialize a new empty guide named "newGuide"
function initializeNewGuide() {
  CURRENT_GUIDE_KEY = "newGuide";
  GUIDES[CURRENT_GUIDE_KEY] = {
    clickSound: "",
    generateBackButton: false,
    backButton: {},
    pages: {},
  };
  CURRENT_GUIDE = new Guide(GUIDES[CURRENT_GUIDE_KEY]);
  updateFilenameDisplay();
}

// Update the filename display in the header
function updateFilenameDisplay() {
  const filenameElement = document.getElementById("filename");
  filenameElement.innerText = `Loaded Guide: ${CURRENT_GUIDE_KEY}`;
}

// Call the function to initialize the new guide when the page loads
document.addEventListener("DOMContentLoaded", initializeNewGuide);
function selectGuide(guides) {
  const modal = document.getElementById("main-modal");
  const guideChoiceList = document.getElementById("modal-buttons-list");
  removeAllChildNodes(guideChoiceList);
  const closeButton = document.getElementById("close-main-modal");
  modal.style.display = "block";
  closeButton.onclick = function () {
    modal.style.display = "none";
  };
  const guideKeys = Object.keys(guides);
  guideKeys.forEach((guideKey) => {
    const listItem = document.createElement("li");
    const button = document.createElement("button");
    button.classList.add("mc-panel");
    button.innerText = guideKey;
    button.onclick = function () {
      CURRENT_GUIDE_KEY = guideKey;
      CURRENT_GUIDE = new Guide(guides[guideKey]);
      modal.style.display = "none";
    };
    listItem.appendChild(button);
    guideChoiceList.appendChild(listItem);
  });
}

class Guide {
  constructor(guideData) {
    this.clickSound = guideData.clickSound;
    this.generateBackButton = guideData.generateBackButton;
    this.backButton = guideData.backButton;
    this.pages = guideData.pages;
    this.populatePageList();
    updateFilenameDisplay();

    // Attach event listener to add page button
    document.getElementById("add-page-button").onclick = () => this.addNewPage();
  }

  populatePageList() {
    const pageList = document.getElementById("page-list");
    removeAllChildNodes(pageList);
    const pageKeys = Object.keys(this.pages);
    pageKeys.forEach((page) => {
      const listItem = document.createElement("li");
      listItem.classList.add("mc-panel");

      // Page ID Title
      const pageId = document.createElement("span");
      pageId.classList.add("page-id");
      pageId.innerText = page;

      // Page control buttons container
      const pageControls = document.createElement("div");
      pageControls.classList.add("page-controls");

      // Edit button
      const editButton = document.createElement("button");
      editButton.classList.add("mc-panel", "edit-page");
      editButton.innerText = "Edit";
      editButton.onclick = () => {
        this.populatePageEditor(page);
      if (DIRTY) {
        const confirmMessage = `Unsaved changes will be lost when switching to editing the new page. Are you sure you want to continue?`;
        if (!confirm(confirmMessage)) {
          return;
        }
        setDirty(false);
      }
      };
      pageControls.appendChild(editButton);

      // Rename button
      const renameButton = document.createElement("button");
      renameButton.classList.add("mc-panel", "rename-page");
      renameButton.innerText = "Rename";
      renameButton.onclick = () => {
        const newPageId = prompt("Enter new page ID:", page);
        if (newPageId && newPageId !== page) {
          this.pages[newPageId] = this.pages[page];
          delete this.pages[page];
          this.populatePageList();
          this.clearPageEditor();
          this.updateButtonLinks(page, newPageId); // Update button links
        }
      };
      pageControls.appendChild(renameButton);

      // Delete button
      const deleteButton = document.createElement("button");
      deleteButton.classList.add("mc-panel", "delete-page", "delete");
      deleteButton.innerText = "Delete";
      deleteButton.onclick = () => {
        if (confirm(`Are you sure you want to delete the page "${page}"?`)) {
          delete this.pages[page];
          this.populatePageList();
          this.clearPageEditor(); // Clear page editor after deletion
        }
      };
      pageControls.appendChild(deleteButton);

      // Append elements to the list item
      listItem.appendChild(pageId);
      listItem.appendChild(pageControls);

      // Append list item to the page list
      pageList.appendChild(listItem);
    });
  }

  updateButtonLinks(oldPageId, newPageId) {
    const allButtons = Object.values(this.pages).flatMap((page) => page.buttons);
    allButtons.forEach((button) => {
      if (button.link === oldPageId) {
        button.link = newPageId; // Update the link if it matches the old page ID
      }
    });
  }

  populatePageEditor(pageId) {
    const pageData = this.pages[pageId];
    const currentPageTitle = document.getElementById("current-page-title");
    currentPageTitle.innerText = "Page ID: " + pageId;
    const pageTitleInput = document.getElementById("page-title");
    const pageBodyTextarea = document.getElementById("page-body");
    pageTitleInput.value = pageData.title;
    pageBodyTextarea.value = pageData.body;
    this.populateButtonEditor(pageData.buttons || []);

    // Set dirty flag when changes are made
    pageTitleInput.oninput = () => {
      setDirty(true);
    };
    pageBodyTextarea.oninput = () => {
      setDirty(true);
    };

    const saveButton = document.getElementById("save-button");
    saveButton.onclick = () => {
      this.savePage(pageId, pageTitleInput.value, pageBodyTextarea.value);
      setDirty(false);
    };
  }

  savePage(pageId, title, body) {
    const buttons = this.collectButtons();
    this.pages[pageId] = {
      title,
      body,
      buttons,
    };
    this.populatePageList();
  }

  clearPageEditor() {
    document.getElementById("page-title").value = "";
    document.getElementById("page-body").value = "";
    const buttonEditor = document.getElementById("button-editor");
    removeAllChildNodes(buttonEditor);
  }

  addNewPage() {
    const newPageId = prompt("Enter new page ID:");
    if (newPageId && !this.pages[newPageId]) {
      this.pages[newPageId] = {
        title: "",
        body: "",
        buttons: [],
      };
      this.populatePageList();
      this.populatePageEditor(newPageId);
    } else if (this.pages[newPageId]) {
      alert("Page ID already exists. Please choose a different ID.");
    }
  }

  populateButtonEditor(buttons) {
    const buttonEditor = document.getElementById("button-editor");
    removeAllChildNodes(buttonEditor);

    buttons.forEach((button, index) => {
      const buttonItem = this.createButtonEditorItem(button, index);
      buttonEditor.appendChild(buttonItem);
    });

    document.getElementById("add-button-button").onclick = () => {
      const newButton = { text: "", link: "", image: "", function: "" };
      const buttonItem = this.createButtonEditorItem(newButton, buttons.length);
      buttonEditor.appendChild(buttonItem);
    };
  }

  createButtonEditorItem(buttonData, index) {
    const listItem = document.createElement("li");
    listItem.classList.add("mc-panel");

    const buttonControls = document.createElement("div");
    buttonControls.classList.add("button-controls");

    const textInput = document.createElement("input");
    textInput.name = `button-text-${index}`;
    textInput.type = "text";
    textInput.placeholder = "Button text";
    textInput.value = buttonData.text;
    textInput.oninput = () => {
      setDirty(true);
    };
    buttonControls.appendChild(textInput);

    const linkSelect = document.createElement("select");
    linkSelect.name = `button-link-${index}`;
    this.populateLinkOptions(linkSelect); // Populate dropdown with page IDs
    linkSelect.value = buttonData.link || "exit"; // Set the selected value to the current link
    linkSelect.onchange = () => {
      setDirty(true);
    };
    buttonControls.appendChild(linkSelect);

    const imageInput = document.createElement("input");
    imageInput.name = `button-image-${index}`;
    imageInput.type = "text";
    imageInput.placeholder = "Image path";
    imageInput.value = buttonData.image;
    imageInput.oninput = () => {
      setDirty(true);
    };
    buttonControls.appendChild(imageInput);

    const functionInput = document.createElement("input");
    functionInput.name = `button-function-${index}`;
    functionInput.type = "text";
    functionInput.placeholder = "Callback function";
    functionInput.value = buttonData.function || "";
    functionInput.oninput = () => {
      setDirty(true);
    };
    buttonControls.appendChild(functionInput);

    const deleteButton = document.createElement("button");
    deleteButton.classList.add("mc-panel", "delete");
    deleteButton.innerText = "-";
    deleteButton.onclick = () => {
      listItem.remove();
      setDirty(true);
    };

    listItem.appendChild(buttonControls);
    listItem.appendChild(deleteButton);

    return listItem;
  }

  populateLinkOptions(selectElement) {
    const pageKeys = Object.keys(this.pages);

    // Clear existing options
    removeAllChildNodes(selectElement);

    // Create the "exit" option
    const exitOption = document.createElement("option");
    exitOption.value = "exit"; // Set value to "exit"
    exitOption.text = "exit"; // Display text for the option
    selectElement.appendChild(exitOption);

    // Create options for each page ID
    pageKeys.forEach((key) => {
      const option = document.createElement("option");
      option.value = key; // Set the value to the page ID
      option.text = key; // Display the page ID
      selectElement.appendChild(option);
    });
  }

  collectButtons() {
    const buttonItems = document.querySelectorAll("#button-editor > li");
    const buttons = [];

    buttonItems.forEach((item) => {
      const button = {};
      const text = item.querySelector("[name^='button-text']").value;
      if (text) button.text = text;
      const link = item.querySelector("[name^='button-link']").value;
      if (link) button.link = link;
      const image = item.querySelector("[name^='button-image']").value;
      if (image) button.image = image;
      const func = item.querySelector("[name^='button-function']").value;
      if (func) button.function = func;
      if (Object.keys(button).length > 0) buttons.push(button);
    });

    return buttons;
  }
}

function removeAllChildNodes(parent) {
  while (parent.firstChild) {
    parent.removeChild(parent.firstChild);
  }
}
