console.log("Loading ui.js...");

// --- DOM Element References ---
const commandInput = document.getElementById('command-input');
const runSingleBtn = document.getElementById('run-single-btn');
const presetSelect = document.getElementById('preset-select');
const runPresetBtn = document.getElementById('run-preset-btn');
const logOutputEl = document.getElementById('log-output');
const itemTypeSelect = document.getElementById('item-type-select');
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
const addItemSaveFavorite = document.getElementById('add-item-save-favorite');
const addItemFavoriteName = document.getElementById('add-item-favorite-name');
const favoriteSelect = document.getElementById('favorite-select');
const runFavoriteBtn = document.getElementById('run-favorite-btn');
const deleteFavoriteBtn = document.getElementById('delete-favorite-btn');
const logOutputContainer = document.getElementById('log-output-container');
const toggleLogBtn = document.getElementById('toggle-log-btn');
const battleStageColumn = document.getElementById('battle-stage-column');
const battleStageContent = document.getElementById('battle-stage-content');
const toggleBattleBtn = document.getElementById('toggle-battle-btn');
const statusIndicator = document.getElementById('status-indicator');
const statusIndicatorText = document.getElementById('status-indicator-text');
const addItemContainer = document.getElementById('add-item-section');
const addItemContent = document.getElementById('add-item-content');
const toggleAddItemBtn = document.getElementById('toggle-add-item-btn');
const toggleFavoritesBtn = document.getElementById('toggle-favorites-btn');
const favoritesDropdown = document.getElementById('favorites-dropdown');
const locationCategorySelect = document.getElementById('location-category-select');
const locationSelect = document.getElementById('location-select');
const teleportButton = document.getElementById('teleport-button');
const teleportContainer = document.getElementById('teleport-section'); 
const teleportContent = document.getElementById('teleport-content'); 
const toggleTeleportBtn = document.getElementById('toggle-teleport-btn'); 

// --- Logging --- 
function logMessage(message, type = 'info') {
    console.log(`[UI] [${type.toUpperCase()}] ${message}`);
    if (!logOutputEl) return;
    const logEntry = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString();
    logEntry.textContent = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
    logEntry.className = `log-entry log-${type}`; // Add classes for styling

    logOutputEl.insertBefore(logEntry, logOutputEl.firstChild);
    // Optional: Limit log size
    // while (logOutputEl.childElementCount > 100) { 
    //     logOutputEl.removeChild(logOutputEl.lastChild);
    // }
}

// --- Status Indicator --- 
function updateStatusIndicator(statusText) {
    if (!statusIndicator || !statusIndicatorText) return;
    logMessage(`Updating status display: ${statusText}`);
    statusIndicatorText.textContent = statusText;
    statusIndicator.title = statusText;
    statusIndicator.className = ''; // Reset sphere class
    statusIndicator.classList.remove('connected', 'disconnected', 'debug'); // Clear previous

    if (statusText === 'Game Found') {
        statusIndicator.classList.add('connected');
    } else if (statusText === 'Game Not Found') {
        statusIndicator.classList.add('disconnected');
    } else if (statusText && statusText.startsWith('Debug Mode Active')) {
        statusIndicator.classList.add('debug');
    } else {
        statusIndicator.classList.add('disconnected'); // Default to disconnected
        logMessage(`Unknown status received: ${statusText}`, 'warn');
    }
}

function setStatusIndicatorError(message = 'Error') {
     if (!statusIndicator || !statusIndicatorText) return;
     statusIndicatorText.textContent = message;
     statusIndicator.className = 'disconnected'; // Red sphere on error
     statusIndicator.title = message;
}

// --- Dropdown Population ---
function populateDropdown(selectElement, options, defaultOptionText, valueKey = 'value', textKey = 'textContent') {
    if (!selectElement) return;
    selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
    selectElement.disabled = true;

    if (options && options.length > 0) {
        options.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[textKey];
             // Add data attributes if needed (e.g., item details)
             if (item.dataAttributes) {
                 Object.entries(item.dataAttributes).forEach(([key, value]) => {
                     option.dataset[key] = value;
                 });
             }
            selectElement.appendChild(option);
        });
        selectElement.disabled = false;
        logMessage(`Populated dropdown: ${selectElement.id}`);
    } else {
        selectElement.innerHTML = `<option value="">-- No Data --</option>`;
        logMessage(`No data to populate dropdown: ${selectElement.id}`, 'warn');
    }
}

function populatePresets(presets) {
    const options = presets.map(name => ({ value: name, textContent: name }));
    populateDropdown(presetSelect, options, '-- Select a Preset --');
}

function populateNpcs(npcs) {
    const sortedNpcs = Object.entries(npcs).sort(([, a], [, b]) => a.localeCompare(b));
    const options = sortedNpcs.map(([name, id]) => ({ value: id, textContent: name }));
    populateDropdown(npcSelect, options, '-- Select NPC --');
}

function populateFavorites(favorites) {
    const sortedFavorites = favorites.sort((a, b) => a.name.localeCompare(b.name));
    const options = sortedFavorites.map(fav => ({ value: fav.name, textContent: fav.name }));
    populateDropdown(favoriteSelect, options, '-- Select Favorite --');
    // Enable/disable buttons after populating
    handleFavoriteSelection();
}

function populateItemTypes(categories) {
    allItemCategories = categories; // Update global state
    const typeNames = Object.keys(categories).sort();
    const options = typeNames.map(name => ({ value: name, textContent: name }));
    populateDropdown(itemTypeSelect, options, '-- Select Type --');
    // Reset dependent dropdowns
    populateItemSubcategories(); 
}

function populateItemSubcategories() {
    const selectedType = itemTypeSelect.value;
    itemCategorySelect.innerHTML = '<option value="">-- Loading... --</option>';
    itemSelect.innerHTML = '<option value="">-- Select Sub-Category --</option>';
    itemCategorySelect.disabled = true;
    itemSelect.disabled = true;
    addItemBtn.disabled = true;
    displayItemDetails(null); // Clear details display

    if (!selectedType || !allItemCategories[selectedType]) {
        populateDropdown(itemCategorySelect, [], '-- Select Type First --');
        return;
    }

    const subCategories = allItemCategories[selectedType];
    const subCategoryNames = Object.keys(subCategories).sort();
    const options = subCategoryNames.map(name => ({ 
        value: subCategories[name], // Filename is value
        textContent: name 
    }));
    populateDropdown(itemCategorySelect, options, '-- Select Sub-Category --');
}

function populateItems(items) {
    itemSelect.innerHTML = '<option value="">-- Loading... --</option>';
    addItemBtn.disabled = true;
    displayItemDetails(null); // Clear details

    if (!items || Object.keys(items).length === 0) {
        populateDropdown(itemSelect, [], '-- No Items Found --');
        return;
    }
    
    const itemEntries = Object.entries(items);
    // Consider sorting if backend doesn't guarantee it
    // itemEntries.sort((a, b) => a[0].localeCompare(b[0])); 
    
    const options = itemEntries.map(([name, details]) => ({
        value: details.id, 
        textContent: name,
        dataAttributes: { details: JSON.stringify(details) } // Store details
    }));
    populateDropdown(itemSelect, options, '-- Select Item --');
}

function populateLocationCategories(categories) {
    const categoryEntries = Object.entries(categories);
    // Backend should sort, but can sort here if needed
    // categoryEntries.sort((a, b) => a[0].localeCompare(b[0])); 
    const options = categoryEntries.map(([name, filename]) => ({ 
        value: filename, 
        textContent: name 
    }));
    populateDropdown(locationCategorySelect, options, '-- Select Category --');
    // Reset dependent dropdown
    populateLocations([]);
}

function populateLocations(locations) {
    locationSelect.innerHTML = '<option value="">-- Loading... --</option>';
    teleportButton.disabled = true;

    if (!locations || Object.keys(locations).length === 0) {
        populateDropdown(locationSelect, [], '-- No Locations --');
        return;
    }
    const locationEntries = Object.entries(locations);
    // Backend should sort, but can sort here if needed
    // locationEntries.sort((a, b) => a[0].localeCompare(b[0]));
    const options = locationEntries.map(([name, id]) => ({ value: id, textContent: name }));
    populateDropdown(locationSelect, options, '-- Select Location --');
}


// --- UI Updates --- 
function displayItemDetails(details) {
    const detailsDiv = document.getElementById('item-details-display');
    if (!detailsDiv) return;

    if (details && typeof details === 'object') {
        try {
            let html = `<strong>${details.name || 'Unknown Item'}</strong><br>`; // Use name from details if available
            html += `ID: <code>${details.id}</code><br>`;
            // ... (rest of the detail formatting from original script.js) ...
             if (details.value !== undefined && details.value !== null) html += `Value: ${details.value}<br>`;
             if (details.weight !== undefined) html += `Weight: ${details.weight}<br>`;
             if (details.health !== undefined) html += `Health: ${details.health}<br>`;
             if (details.armor !== undefined) html += `Armor: ${details.armor}<br>`;
             if (details.damage !== undefined) {
                 html += `Damage: ${details.damage}`;
                 if (details.damage_obr !== undefined) html += ` (OBR: ${details.damage_obr})`;
                 html += `<br>`;
             }
             if (details.level !== undefined) html += `Level: ${details.level}<br>`;
             if (details.enchantment) html += `Enchantment: ${details.enchantment}<br>`;
             if (details.type) html += `Type: ${details.type}<br>`;
             if (details.skill) html += `<strong>Skill: ${details.skill}</strong><br>`;
             if (details.author) html += `Author: ${details.author}<br>`;
             if (details.description) html += `Description: ${details.description}<br>`;
             if (details.location_hint) html += `Location Hint: ${details.location_hint}<br>`;
             if (details.notes) html += `Notes: ${details.notes}<br>`;

            detailsDiv.innerHTML = html;
        } catch (e) {
            detailsDiv.innerHTML = 'Error displaying item details.';
            console.error("Error processing item details:", e, details);
        }
    } else {
        detailsDiv.innerHTML = ''; // Clear details
    }
}

function updateBattleCommandDisplay() {
    if (!currentBattleCommandsDiv || !savePresetBtn || !runCustomBattleBtn) return;
    if (currentBattleCommandList.length === 0) {
        currentBattleCommandsDiv.textContent = '(No commands added yet)';
        savePresetBtn.disabled = true;
        runCustomBattleBtn.disabled = true;
    } else {
        // Join commands, potentially escaping HTML if needed, though textContent is safer
        currentBattleCommandsDiv.textContent = currentBattleCommandList.join('\n');
        savePresetBtn.disabled = false;
        runCustomBattleBtn.disabled = false;
    }
    // Scroll to bottom
    currentBattleCommandsDiv.scrollTop = currentBattleCommandsDiv.scrollHeight;
}

// Function to handle enabling/disabling favorite buttons based on selection
function handleFavoriteSelection() {
    if (!favoriteSelect || !runFavoriteBtn || !deleteFavoriteBtn) return;
    const selectedValue = favoriteSelect.value;
    const hasSelection = selectedValue !== '';
    runFavoriteBtn.disabled = !hasSelection;
    deleteFavoriteBtn.disabled = !hasSelection;
}

// --- UI Element State Toggles ---
function setElementDisabled(element, disabled) {
    if (element) {
        element.disabled = disabled;
    }
}

function setBatchDisabled(elements, disabled) {
    elements.forEach(el => setElementDisabled(el, disabled));
}

// --- Toggle Listeners Setup --- (Moved setup logic here)
function setupToggleListeners() {
    const setupSingleToggle = (button, content, container) => {
        if (!button || !content || !container) {
            console.error('Missing elements for toggle setup:', button, content, container);
            return;
        }
        const header = container.querySelector('h2');
        const toggleAction = () => {
            const isVisible = content.classList.toggle('visible');
            button.innerHTML = isVisible ? '&#9650;' : '&#9660;'; // Up/Down arrow
        };

        button.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleAction();
        });
        if (header) {
            header.addEventListener('click', toggleAction);
        }
        // Set initial state (e.g., start collapsed)
        // content.classList.remove('visible');
        // button.innerHTML = '&#9660;'; 
    };

    // Setup individual toggles
    setupSingleToggle(toggleLogBtn, logOutputEl, logOutputContainer);
    setupSingleToggle(toggleBattleBtn, battleStageContent, document.getElementById('battle-stage-container'));
    setupSingleToggle(toggleAddItemBtn, addItemContent, addItemContainer);
    setupSingleToggle(toggleTeleportBtn, teleportContent, teleportContainer);

    // Special toggle for Favorites dropdown
    if (toggleFavoritesBtn && favoritesDropdown) {
        const toggleAction = () => {
            const isVisible = favoritesDropdown.classList.toggle('visible');
            toggleFavoritesBtn.innerHTML = isVisible ? 'Favorites &#9650;' : 'Favorites &#9660;';
        };
        toggleFavoritesBtn.addEventListener('click', toggleAction);
        document.addEventListener('click', (event) => {
            if (!toggleFavoritesBtn.contains(event.target) && !favoritesDropdown.contains(event.target) && favoritesDropdown.classList.contains('visible')) {
                toggleAction(); // Close if click outside
            }
        });
        // Start collapsed
        // favoritesDropdown.classList.remove('visible');
        // toggleFavoritesBtn.innerHTML = 'Favorites &#9660;'; 
    } else {
        console.error('Favorites toggle elements not found!');
    }
}

console.log("ui.js loaded."); 