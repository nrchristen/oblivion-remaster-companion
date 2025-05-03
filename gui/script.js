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
const npcSelect = document.getElementById('npc-select');
const npcQuantityInput = document.getElementById('npc-quantity-input');
const addNpcGroupBtn = document.getElementById('add-npc-group-btn');
const currentBattleCommandsDiv = document.getElementById('current-battle-commands');
const presetNameInput = document.getElementById('preset-name-input');
const savePresetBtn = document.getElementById('save-preset-btn');
const runCustomBattleBtn = document.getElementById('run-custom-battle-btn');
const singleCmdSaveFavorite = document.getElementById('single-cmd-save-favorite');
const singleCmdFavoriteName = document.getElementById('single-cmd-favorite-name');
const addItemSaveFavorite = document.getElementById('add-item-save-favorite');
const addItemFavoriteName = document.getElementById('add-item-favorite-name');
const favoriteSelect = document.getElementById('favorite-select');
const runFavoriteBtn = document.getElementById('run-favorite-btn');
const deleteFavoriteBtn = document.getElementById('delete-favorite-btn');

// Global state for custom battle
let currentBattleCommandList = [];

function logMessage(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    const logEntry = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString();
    logEntry.textContent = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
    if (type === 'error') {
        logEntry.classList.add('log-error'); // Use CSS class for error styling
    }
    // Prepend to keep newest logs at the top
    logOutputEl.insertBefore(logEntry, logOutputEl.firstChild);
    // Optional: Limit log size
    // while (logOutputEl.childElementCount > 100) { 
    //     logOutputEl.removeChild(logOutputEl.lastChild);
    // }
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
        logMessage('Error: Command input is empty.', 'warn');
        return;
    }
    logMessage(`Sending single command: ${command}`);
    runSingleBtn.disabled = true;
    try {
        // Call Python function
        const result = await window.pywebview.api.run_single_command(command);
        if (result.success) {
            logMessage(`Single command executed successfully.`);
            // Check if favorite needs to be saved
            if (singleCmdSaveFavorite.checked) {
                const favName = singleCmdFavoriteName.value.trim();
                if (!favName) {
                    logMessage('Favorite name cannot be empty when saving.', 'warn');
                } else {
                    await saveFavorite(favName, command, 'single'); // Call save helper
                    singleCmdFavoriteName.value = ''; // Clear name input
                    singleCmdSaveFavorite.checked = false; // Uncheck
                    singleCmdFavoriteName.style.display = 'none'; // Hide
                }
            }
        } else {
            logMessage(`Failed to execute single command: ${result.message || 'Unknown error'}`, 'error');
        }
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
        if (result.success) {
            logMessage(`Item(s) added successfully.`);
            // Check if favorite needs to be saved
            if (addItemSaveFavorite.checked && result.command) {
                const favName = addItemFavoriteName.value.trim();
                if (!favName) {
                    logMessage('Favorite name cannot be empty when saving.', 'warn');
                } else {
                     await saveFavorite(favName, result.command, 'additem'); // Call save helper
                     addItemFavoriteName.value = ''; // Clear name input
                     addItemSaveFavorite.checked = false; // Uncheck
                     addItemFavoriteName.style.display = 'none'; // Hide
                }
            }
        } else {
            logMessage(`Failed to add item: ${result.message || 'Unknown error'}`, 'error');
        }
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

// --- Custom Battle Functions ---
async function loadNpcs() {
    logMessage('Loading NPCs...');
    npcSelect.innerHTML = '<option value="">-- Loading NPCs --</option>'; // Clear existing options
    npcSelect.disabled = true;
    addNpcGroupBtn.disabled = true;
    try {
        const apiResult = await window.pywebview.api.get_npcs(); // Renamed variable for clarity
        logMessage('NPC data received from API');

        // --- BUG FIX: Access the nested 'npcs' object --- 
        const npcsData = apiResult.npcs; 

        if (!npcsData || Object.keys(npcsData).length === 0) {
            logMessage('No NPCs found in received data.', 'warn');
            npcSelect.innerHTML = '<option value="">-- No NPCs Found --</option>';
            return; // Exit if no NPC data
        }
        // ---------------------------------------------------

        // Clear the loading message
        npcSelect.innerHTML = '<option value="">-- Select NPC --</option>'; 

        // Sort NPC names alphabetically
        const sortedNpcNames = Object.keys(npcsData).sort((a, b) => a.localeCompare(b));

        // Populate dropdown with sorted names
        for (const npcName of sortedNpcNames) {
            const option = document.createElement('option');
            option.value = npcsData[npcName]; // ID is the value
            option.textContent = npcName; // Name is the text
            npcSelect.appendChild(option);
        }

        npcSelect.disabled = false;
        addNpcGroupBtn.disabled = false;
        logMessage('NPCs loaded successfully.');
    } catch (error) {
        logMessage(`Error loading NPCs: ${error}`, 'error');
        npcSelect.innerHTML = '<option value="">-- Error Loading NPCs --</option>';
        console.error("Load NPCs Error:", error); // Log the full error to console
    }
}

function updateBattleCommandDisplay() {
    if (currentBattleCommandList.length === 0) {
        currentBattleCommandsDiv.textContent = '(No commands added yet)';
        savePresetBtn.disabled = true;
        runCustomBattleBtn.disabled = true;
    } else {
        currentBattleCommandsDiv.textContent = currentBattleCommandList.join('\n');
        savePresetBtn.disabled = false;
        runCustomBattleBtn.disabled = false;
    }
    // Scroll to bottom of command list
    currentBattleCommandsDiv.scrollTop = currentBattleCommandsDiv.scrollHeight;
}

async function addNpcGroup() {
    const npcId = npcSelect.value;
    const quantity = npcQuantityInput.value;

    if (!npcId) {
        logMessage('Error: No NPC selected.');
        return;
    }
    const qtyNum = parseInt(quantity, 10);
    if (!qtyNum || qtyNum <= 0) {
        logMessage('Error: Invalid NPC quantity.');
        return;
    }

    logMessage(`Building command for NPC ID: ${npcId}, Qty: ${qtyNum}`);
    addNpcGroupBtn.disabled = true;
    try {
        const result = await window.pywebview.api.build_placeatme_command(npcId, qtyNum);
        if (result.success && result.command) {
            currentBattleCommandList.push(result.command);
            logMessage(`Added command: ${result.command}`);
            updateBattleCommandDisplay();
        } else {
            logMessage(`Error building command: ${result.message || 'Unknown error'}`);
        }
    } catch (error) {
        logMessage(`Error building NPC command: ${error}`);
        console.error("Build NPC command error:", error);
    } finally {
        addNpcGroupBtn.disabled = false;
    }
}

async function savePreset() {
    const presetName = presetNameInput.value.trim();
    if (!presetName) {
        logMessage('Error: Preset name cannot be empty.');
        return;
    }
    if (currentBattleCommandList.length === 0) {
        logMessage('Error: No commands in the current setup to save.');
        return;
    }

    logMessage(`Saving preset: ${presetName}`);
    savePresetBtn.disabled = true;
    try {
        const result = await window.pywebview.api.save_battle_preset(presetName, currentBattleCommandList);
        logMessage(result.message); // Log the message from backend
        if (result.status === 'success') {
            presetNameInput.value = ''; // Clear name on success
            loadPresets(); // Refresh preset dropdown
        }
    } catch (error) {
        logMessage(`Error saving preset: ${error}`);
        console.error("Save preset error:", error);
    } finally {
        savePresetBtn.disabled = false; // Re-enable even on failure/exists
    }
}

async function runCustomBattle() {
     if (currentBattleCommandList.length === 0) {
        logMessage('Error: No commands in the current setup to run.');
        return;
    }
    logMessage(`Running current custom battle setup (${currentBattleCommandList.length} commands)...`);
    runCustomBattleBtn.disabled = true;
    savePresetBtn.disabled = true; // Disable save while running
    addNpcGroupBtn.disabled = true; // Disable adding more while running
    try {
        const result = await window.pywebview.api.run_custom_battle(currentBattleCommandList);
        logMessage(`Custom battle result: ${result.success ? 'Success' : 'Failure'}${result.message ? ' (' + result.message + ')' : ''}`);
    } catch (error) {
        logMessage(`Error running custom battle: ${error}`);
        console.error("Run custom battle error:", error);
    } finally {
        runCustomBattleBtn.disabled = false;
        savePresetBtn.disabled = currentBattleCommandList.length === 0;
        addNpcGroupBtn.disabled = false;
    }
}

// --- Favorites Functions ---
async function loadFavorites() {
    logMessage("Loading favorites...");
    favoriteSelect.innerHTML = '<option value="">-- Loading... --</option>';
    favoriteSelect.disabled = true;
    runFavoriteBtn.disabled = true;
    deleteFavoriteBtn.disabled = true;
    try {
        const result = await window.pywebview.api.get_favorites();
        if (result.success && result.favorites) {
            favoriteSelect.innerHTML = '<option value="">-- Select Favorite --</option>'; // Clear loading
            if (result.favorites.length === 0) {
                 favoriteSelect.innerHTML = '<option value="">-- No Favorites Saved --</option>';
                 logMessage("No favorites found.");
            } else {
                 // Sort favorites by name for display
                 result.favorites.sort((a, b) => a.name.localeCompare(b.name));
                 
                 result.favorites.forEach(fav => {
                     const option = document.createElement('option');
                     // Store the unique name in the value attribute
                     option.value = fav.name;
                     option.textContent = fav.name; // Display the name
                     favoriteSelect.appendChild(option);
                 });
                 favoriteSelect.disabled = false; // Enable dropdown
                 logMessage(`Loaded ${result.favorites.length} favorites.`);
            }
        } else {
            throw new Error("Failed to load favorites or invalid data received.");
        }
    } catch (error) {
        logMessage(`Error loading favorites: ${error}`, 'error');
        favoriteSelect.innerHTML = '<option value="">-- Error Loading --</option>';
    } finally {
        // Enable/disable buttons based on whether items are loaded
        const hasFavorites = favoriteSelect.options.length > 1 && favoriteSelect.value !== '';
        runFavoriteBtn.disabled = !hasFavorites;
        deleteFavoriteBtn.disabled = !hasFavorites;
    }
}

async function saveFavorite(name, command, type) {
    logMessage(`Attempting to save favorite '${name}'...`);
    try {
        // API handles validation, duplicate check, and saving
        const result = await window.pywebview.api.save_favorite(name, command, type);
        if (result.status === 'success') {
            logMessage(result.message || `Favorite '${name}' saved.`);
            await loadFavorites(); // Reload the favorites list
        } else if (result.status === 'exists') {
             logMessage(result.message || `Favorite '${name}' already exists.`, 'warn');
        } else {
             logMessage(result.message || `Failed to save favorite '${name}'.`, 'error');
        }
    } catch (error) {
        logMessage(`Error calling save favorite API: ${error}`, 'error');
    }
}

async function runFavorite() {
    const selectedName = favoriteSelect.value;
    if (!selectedName) {
        logMessage("No favorite selected to run.", 'warn');
        return;
    }
    logMessage(`Running favorite: ${selectedName}...`);
    runFavoriteBtn.disabled = true;
    deleteFavoriteBtn.disabled = true; // Also disable delete during run
    try {
        const result = await window.pywebview.api.run_favorite(selectedName);
        // Log the detailed message from the logic layer
        logMessage(result.message || `Favorite run attempt finished. Success: ${result.success}`, result.success ? 'info' : 'error');
    } catch (error) {
        logMessage(`Error running favorite: ${error}`, 'error');
    } finally {
        runFavoriteBtn.disabled = false;
        deleteFavoriteBtn.disabled = false;
        // Update button states after run? Maybe not necessary unless list changes.
    }
}

async function deleteFavorite() {
    const selectedName = favoriteSelect.value;
    if (!selectedName) {
        logMessage("No favorite selected to delete.", 'warn');
        return;
    }
    // Simple confirmation
    if (!confirm(`Are you sure you want to delete the favorite "${selectedName}"?`)) {
        return;
    }
    
    logMessage(`Deleting favorite: ${selectedName}...`);
    deleteFavoriteBtn.disabled = true;
    runFavoriteBtn.disabled = true; // Disable run during delete
    try {
        const result = await window.pywebview.api.delete_favorite(selectedName);
        if (result.success) {
            logMessage(result.message || `Favorite '${selectedName}' deleted.`);
            await loadFavorites(); // Reload the list to reflect deletion
        } else {
            logMessage(result.message || `Failed to delete favorite '${selectedName}'.`, 'error');
            // Re-enable buttons on failure
            deleteFavoriteBtn.disabled = false;
            runFavoriteBtn.disabled = false;
        }
    } catch (error) {
        logMessage(`Error deleting favorite: ${error}`, 'error');
        deleteFavoriteBtn.disabled = false;
        runFavoriteBtn.disabled = false;
    }
    // loadFavorites will handle re-enabling buttons if successful
}

// --- Event Listeners ---
checkStatusBtn.addEventListener('click', checkGameStatus);
runSingleBtn.addEventListener('click', runSingleCommand);
runPresetBtn.addEventListener('click', runPresetBattle);
itemCategorySelect.addEventListener('change', loadItemsForCategory);
addItemBtn.addEventListener('click', addItem);
addNpcGroupBtn.addEventListener('click', addNpcGroup);
savePresetBtn.addEventListener('click', savePreset);
runCustomBattleBtn.addEventListener('click', runCustomBattle);
runFavoriteBtn.addEventListener('click', runFavorite);
deleteFavoriteBtn.addEventListener('click', deleteFavorite);

// Toggle favorite name input visibility
addItemSaveFavorite.addEventListener('change', (e) => {
    console.log('Add Item Fav checkbox changed:', e.target.checked); // DEBUG
    addItemFavoriteName.style.display = e.target.checked ? 'block' : 'none';
    if (e.target.checked) {
        console.log('Showing Add Item fav name input'); // DEBUG
        addItemFavoriteName.focus();
    } else {
        console.log('Hiding Add Item fav name input'); // DEBUG
    }
});
singleCmdSaveFavorite.addEventListener('change', (e) => {
    console.log('Single Cmd Fav checkbox changed:', e.target.checked); // DEBUG
    singleCmdFavoriteName.style.display = e.target.checked ? 'block' : 'none';
    if (e.target.checked) {
        console.log('Showing Single Cmd fav name input'); // DEBUG
        singleCmdFavoriteName.focus();
    } else {
        console.log('Hiding Single Cmd fav name input'); // DEBUG
    }
});

// Enable/disable favorite buttons based on selection
favoriteSelect.addEventListener('change', () => {
    const selectedValue = favoriteSelect.value;
    console.log('Favorite selection changed. Value:', selectedValue); // DEBUG
    const hasSelection = selectedValue !== '';
    console.log('Has selection:', hasSelection);
    runFavoriteBtn.disabled = !hasSelection;
    deleteFavoriteBtn.disabled = !hasSelection;
    console.log('Run button disabled:', runFavoriteBtn.disabled);
    console.log('Delete button disabled:', deleteFavoriteBtn.disabled);
});

// --- Initial Load Actions ---
window.addEventListener('pywebviewready', () => {
    logMessage('GUI Initialized and pywebview API ready.');
    // Now it's safe to call API methods
    checkGameStatus();
    loadPresets();
    loadItemCategories(); // Load categories on startup
    loadNpcs(); // Load NPCs on startup
    loadFavorites(); // Load favorites on startup
    updateBattleCommandDisplay(); // Initial UI state
}); 