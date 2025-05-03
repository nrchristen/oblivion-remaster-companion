// No API_BASE_URL needed

const statusTextEl = document.getElementById('status-text');
const checkStatusBtn = document.getElementById('check-status-btn');
const commandInput = document.getElementById('command-input');
const runSingleBtn = document.getElementById('run-single-btn');
const presetSelect = document.getElementById('preset-select');
const runPresetBtn = document.getElementById('run-preset-btn');
const logOutputEl = document.getElementById('log-output');
const itemCategorySelect = document.getElementById('item-category-select');
const itemSelect = document.getElementById('item-select');
const itemQuantityInput = document.getElementById('item-quantity-input');
const addItemBtn = document.getElementById('add-item-btn');

function logMessage(message) {
    // Basic logging to the GUI log area
    const timestamp = new Date().toLocaleTimeString();
    logOutputEl.textContent += `\n[${timestamp}] ${message}`;
    logOutputEl.scrollTop = logOutputEl.scrollHeight; // Auto-scroll
}

// --- API Calls using pywebview --- 

async function checkGameStatus() {
    logMessage('Checking game status...');
    statusTextEl.textContent = 'Checking...';
    try {
        // Call Python function directly
        const result = await window.pywebview.api.check_status(); 
        statusTextEl.textContent = result.status;
        logMessage(`Status check result: ${result.status}`);
    } catch (error) {
        statusTextEl.textContent = 'Error calling API';
        logMessage(`Error checking status: ${error}`);
        console.error("Status Check Error:", error);
    }
}

async function runSingleCommand() {
    const command = commandInput.value.trim();
    if (!command) {
        logMessage('Error: Command input is empty.');
        return;
    }
    logMessage(`Sending single command: ${command}`);
    runSingleBtn.disabled = true;
    try {
        // Call Python function
        const result = await window.pywebview.api.run_single_command(command);
        logMessage(`Single command result: ${result.success ? 'Success' : 'Failure'}${result.message ? ' (' + result.message + ')' : ''}`);
    } catch (error) {
        logMessage(`Error running single command: ${error}`);
         console.error("Run Single Error:", error);
    } finally {
        runSingleBtn.disabled = false;
    }
}

async function loadPresets() {
    logMessage('Loading battle presets...');
    try {
        // Call Python function
        const result = await window.pywebview.api.get_battle_presets();
        presetSelect.innerHTML = '<option value="">-- Select a Preset --</option>';
        if (result.presets && result.presets.length > 0) {
            result.presets.forEach(presetName => {
                const option = document.createElement('option');
                option.value = presetName;
                option.textContent = presetName;
                presetSelect.appendChild(option);
            });
            logMessage('Presets loaded successfully.');
        } else {
            logMessage('No presets found or error loading.');
        }
    } catch (error) {
        presetSelect.innerHTML = '<option value="">-- Error Loading --</option>';
        logMessage(`Error loading presets: ${error}`);
        console.error("Load Presets Error:", error);
    }
}

async function runPresetBattle() {
    const presetName = presetSelect.value;
    if (!presetName) {
        logMessage('Error: No preset selected.');
        return;
    }
    logMessage(`Running preset battle: ${presetName}`);
    runPresetBtn.disabled = true;
    try {
        // Call Python function
        const result = await window.pywebview.api.run_preset_battle(presetName);
        logMessage(`Preset execution result: ${result.success ? 'Success' : 'Failure'}${result.message ? ' (' + result.message + ')' : ''}`);
    } catch (error) {
        logMessage(`Error running preset battle: ${error}`);
        console.error("Run Preset Error:", error);
    } finally {
        runPresetBtn.disabled = false;
    }
}

// --- Item Functions ---
async function loadItemCategories() {
    logMessage('Loading item categories...');
    itemCategorySelect.innerHTML = '<option value="">-- Loading... --</option>';
    itemSelect.innerHTML = '<option value="">-- Select Category --</option>'; // Reset items
    itemSelect.disabled = true;
    addItemBtn.disabled = true;
    try {
        const result = await window.pywebview.api.get_item_categories_api();
        itemCategorySelect.innerHTML = '<option value="">-- Select Category --</option>';
        if (result.categories && Object.keys(result.categories).length > 0) {
            for (const [name, filename] of Object.entries(result.categories)) {
                const option = document.createElement('option');
                option.value = filename; // Store filename as value
                option.textContent = name; // Display name
                itemCategorySelect.appendChild(option);
            }
             logMessage('Item categories loaded.');
        } else {
            logMessage('No item categories found.');
        }
    } catch (error) {
        itemCategorySelect.innerHTML = '<option value="">-- Error Loading --</option>';
        logMessage(`Error loading item categories: ${error}`);
        console.error("Load Categories Error:", error);
    }
}

async function loadItemsForCategory() {
    const selectedFilename = itemCategorySelect.value;
    itemSelect.innerHTML = '<option value="">-- Loading Items... --</option>';
    itemSelect.disabled = true;
    addItemBtn.disabled = true;

    if (!selectedFilename) {
        itemSelect.innerHTML = '<option value="">-- Select Category First --</option>';
        return; // No category selected
    }

    logMessage(`Loading items for category file: ${selectedFilename}`);
    try {
        const result = await window.pywebview.api.get_items_in_category(selectedFilename);
        itemSelect.innerHTML = '<option value="">-- Select Item --</option>';
        if (result.items && Object.keys(result.items).length > 0) {
            for (const [name, id] of Object.entries(result.items)) {
                const option = document.createElement('option');
                option.value = id; // Store item ID as value
                option.textContent = name; // Display item name
                itemSelect.appendChild(option);
            }
            itemSelect.disabled = false;
            logMessage('Items loaded.');
        } else {
            logMessage('No items found in this category.');
             itemSelect.innerHTML = '<option value="">-- No Items Found --</option>';
        }
    } catch (error) {
         itemSelect.innerHTML = '<option value="">-- Error Loading Items --</option>';
         logMessage(`Error loading items: ${error}`);
         console.error("Load Items Error:", error);
    }
}

async function addItem() {
    const itemId = itemSelect.value;
    const quantity = itemQuantityInput.value;

    if (!itemId) {
        logMessage('Error: No item selected.');
        return;
    }
    if (!quantity || parseInt(quantity, 10) <= 0) {
        logMessage('Error: Invalid quantity.');
        return;
    }

    logMessage(`Adding item: ID=${itemId}, Qty=${quantity}`);
    addItemBtn.disabled = true;
    try {
        const result = await window.pywebview.api.add_item(itemId, parseInt(quantity, 10));
        logMessage(`Add item result: ${result.success ? 'Success' : 'Failure'}${result.message ? ' (' + result.message + ')' : ''}`);
    } catch (error) {
        logMessage(`Error adding item: ${error}`);
        console.error("Add Item Error:", error);
    } finally {
        addItemBtn.disabled = false;
    }
}

// Enable item dropdown and add button only when an item is selected
itemSelect.addEventListener('change', () => {
    addItemBtn.disabled = !itemSelect.value;
});

// --- Event Listeners ---
checkStatusBtn.addEventListener('click', checkGameStatus);
runSingleBtn.addEventListener('click', runSingleCommand);
runPresetBtn.addEventListener('click', runPresetBattle);
itemCategorySelect.addEventListener('change', loadItemsForCategory);
addItemBtn.addEventListener('click', addItem);

// --- Initial Load Actions ---
window.addEventListener('pywebviewready', () => {
    logMessage('GUI Initialized and pywebview API ready.');
    // Now it's safe to call API methods
    checkGameStatus();
    loadPresets();
    loadItemCategories(); // Load categories on startup
    // Add call to load item categories later
}); 